# ============================================================
# IMPORTS
# ============================================================
import os
import torch
import torch.nn as nn
import numpy as np
import cv2

from torchvision import models, transforms
from PIL import Image

from llm_report import prepare_llm_input, generate_report

# ============================================================
# DEVICE
# ============================================================
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# ============================================================
# CLASS LABELS
# ============================================================
CLASS_NAMES = ['glioma', 'meningioma', 'notumor', 'pituitary']

# ============================================================
# PATH SETUP
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "models", "classification"))
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "outputs"))

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# TRANSFORM
# ============================================================
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ============================================================
# MODEL LOADERS
# ============================================================
def load_efficientnet():
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 4)

    path = os.path.join(MODEL_DIR, "efficientnet_b0_best.pth")
    # Add map_location handling for better compatibility
    model.load_state_dict(torch.load(path, map_location=device))

    model.to(device)
    model.eval()
    return model


def load_resnet():
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 4)

    path = os.path.join(MODEL_DIR, "resnet50_finetuned.pth")
    model.load_state_dict(torch.load(path, map_location=device))

    model.to(device)
    model.eval()
    return model

# ============================================================
# LOAD MODELS (GLOBAL)
# ============================================================
efficientnet_model = load_efficientnet()
resnet_model = load_resnet()

# REMOVE entire GradCAMPlusPlus class and replace with:

class ScoreCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.activations = None
        self.target_layer.register_forward_hook(self._save_activation)

    def _save_activation(self, module, input, output):
        self.activations = output.detach()

    def generate(self, input_tensor, class_idx):
        # Step 1: get activations
        with torch.no_grad():
            self.model(input_tensor)

        activations = self.activations[0]  # (C, H, W)
        n_channels = activations.shape[0]

        # ── ADD THESE 4 LINES HERE ──
        K = 256  # use top 256 channels instead of all 2048
        mean_acts = activations.mean(dim=(1, 2))
        top_k_idx = torch.argsort(mean_acts, descending=True)[:K]
        # ────────────────────────────  

        # Step 2: get baseline score (pure black image)
        baseline = torch.zeros_like(input_tensor).to(device)
        with torch.no_grad():
            baseline_out = self.model(baseline)
            baseline_score = torch.softmax(baseline_out, dim=1)[0, class_idx].item()

        # Step 3: for each activation map, mask input and get score
        scores = []
        for i in range(n_channels):
            # Upsample single activation map to input size
            act_map = activations[i].unsqueeze(0).unsqueeze(0)  # (1,1,H,W)
            act_map = torch.nn.functional.interpolate(
                act_map, size=(224, 224), mode='bilinear', align_corners=False
            )
            act_map = act_map.squeeze()  # (224, 224)

            # Normalize to [0, 1]
            act_min = act_map.min()
            act_max = act_map.max()
            if act_max - act_min > 1e-8:
                act_map = (act_map - act_min) / (act_max - act_min)
            else:
                act_map = torch.zeros_like(act_map)

            # Mask the input image
            masked = input_tensor * act_map.unsqueeze(0).unsqueeze(0)

            with torch.no_grad():
                out = self.model(masked)
                score = torch.softmax(out, dim=1)[0, class_idx].item()

            scores.append(score - baseline_score)

        # Step 4: weighted sum of activation maps
        scores = torch.tensor(scores).to(device)
        weights = torch.relu(scores)  # only positive contributions

        cam = torch.zeros(activations.shape[1:], dtype=torch.float32).to(device)
        for i, w in enumerate(weights):
            cam += w * activations[i]

        cam = torch.relu(cam)
        cam -= cam.min()
        cam /= (cam.max() + 1e-8)

        return cam.detach().cpu().numpy()

# ============================================================
# TARGET LAYER
# ============================================================
def get_target_layer(model):
    return model.layer4[-1]  # last residual block of ResNet50

# ============================================================
# PREDICTION FUNCTION
# ============================================================
def predict_efficientnet(model, image):
    with torch.no_grad():
        output = model(image)
        prob   = torch.softmax(output, dim=1)
        confidence, pred = torch.max(prob, dim=1)

    return pred.item(), confidence.item(), prob[0].cpu().numpy()

# ============================================================
# REGION ANALYSIS 
# ============================================================
def analyse_cam_regions(cam_resized):
    regions = {
        "top-left":     cam_resized[0:75,   0:75],
        "top-center":   cam_resized[0:75,   75:149],
        "top-right":    cam_resized[0:75,   149:224],
        "mid-left":     cam_resized[75:149, 0:75],
        "center":       cam_resized[75:149, 75:149],
        "mid-right":    cam_resized[75:149, 149:224],
        "bot-left":     cam_resized[149:224, 0:75],
        "bot-center":   cam_resized[149:224, 75:149],
        "bot-right":    cam_resized[149:224, 149:224],
    }
    scores = {k: float(np.mean(v)) for k, v in regions.items()}

    ranked   = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top3     = [r[0] for r in ranked[:3]]
    dominant = ranked[0][0]

    return {
        "region_scores": scores,
        "dominant_region": dominant,
        "top3_regions": top3,
        "max_activation": float(np.max(cam_resized)),
        "mean_activation": float(np.mean(cam_resized)),
        "coverage_pct": float(np.mean(cam_resized > 0.5) * 100),
    }

# ============================================================
# OVERLAY HELPER
# ============================================================
def _save_heatmap_overlay(img_bgr, cam_normalized, output_path):
    cam_up  = cv2.resize(cam_normalized, (224, 224))
    
    # Sharpen the CAM before applying colormap
    cam_up = np.power(cam_up, 0.5)  # gamma correction to boost contrast
    cam_up = (cam_up - cam_up.min()) / (cam_up.max() - cam_up.min() + 1e-8)
    
    heatmap = cv2.applyColorMap(np.uint8(255 * cam_up), cv2.COLORMAP_JET)
    heatmap = np.float32(heatmap) / 255
    img_f   = np.float32(img_bgr) / 255

    # Stronger heatmap, less original image
    overlay = heatmap * 0.6 + img_f * 0.4
    overlay = overlay / np.max(overlay)

    cv2.imwrite(output_path, (overlay * 255).astype(np.uint8))


# ============================================================
# MAIN PIPELINE (USED BY STREAMLIT)
# ============================================================
def run_pipeline(image_path):
    # =========================
    # PREPROCESS IMAGE
    # =========================
    image        = Image.open(image_path).convert("RGB")
    input_tensor = transform(image).unsqueeze(0).to(device)

    # =========================
    # PREDICTION (EfficientNet)
    # =========================
    pred_idx, conf, all_probs = predict_efficientnet(efficientnet_model, input_tensor)
    pred_label = CLASS_NAMES[pred_idx]
    confidence_breakdown = {
        CLASS_NAMES[i]: round(float(all_probs[i]) * 100, 2)
        for i in range(len(CLASS_NAMES))
    }

    # =========================
    # GRAD-CAM++ (ResNet)
    # =========================
    target_layer = get_target_layer(resnet_model)
    scorecam     = ScoreCAM(resnet_model, target_layer)
    cam          = scorecam.generate(input_tensor, pred_idx)

    # =========================
    # GRAD-CAM++ HEATMAP
    # =========================
    img_bgr = cv2.imread(image_path)
    img_bgr = cv2.resize(img_bgr, (224, 224))
    explanation_plot_path = os.path.join(OUTPUT_DIR, "gradcampp_output.jpg")
    _save_heatmap_overlay(img_bgr, cam, explanation_plot_path)

    # =========================
    # REGION ANALYSIS
    # =========================
    cam_resized = cv2.resize(cam, (224, 224))
    region_info = analyse_cam_regions(cam_resized)

    # =========================
    # XAI SUMMARY
    # =========================
    xai_summary = {
        "method_used":        "Score-CAM",
        "dominant_region":    region_info["dominant_region"],
        "top3_regions":       region_info["top3_regions"],
        "cam_coverage_pct":   round(region_info["coverage_pct"], 1),
        "cam_mean_activation": round(region_info["mean_activation"], 4),
        "cam_max_activation": round(region_info["max_activation"], 4),
        "region_scores":      region_info["region_scores"],
    }

    # =========================
    # RESULT STRUCTURE
    # =========================
    result = {
        "prediction":           pred_label,
        "confidence":           conf,
        "confidence_breakdown": confidence_breakdown,
        "prediction_model":     "EfficientNet-B0",
        "explanation_model": "ResNet50 (Score-CAM)",
        "observation": (
            f"Score-CAM highlights the {region_info['dominant_region']} region "
            f"with {region_info['coverage_pct']:.1f}% high-activation coverage."
        ),
        "explanation_plot_path": explanation_plot_path,
        "xai_summary":           xai_summary,
    }

    # =========================
    # LLM REPORT
    # =========================
    llm_input = prepare_llm_input(result)
    from llm_report import ReportContext

    result["report"] = generate_report(llm_input)

    return result


# ============================================================
# TEST RUN
# ============================================================
