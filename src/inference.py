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

# ============================================================
# GRAD-CAM++ CLASS 
# ============================================================
class GradCAMPlusPlus:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer

        self.gradients = None
        self.activations = None

        self.target_layer.register_forward_hook(self._save_activation)
        self.target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input, output):
        self.activations = output

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def generate(self, input_image, class_idx):
        output = self.model(input_image)

        self.model.zero_grad()
        loss = output[0, class_idx]
        loss.backward()

        gradients = self.gradients[0]        # (C, H, W)
        activations = self.activations[0]    # (C, H, W)

        # ── Grad-CAM++ weight formula ──────────────────────────────
        grad_sq  = gradients ** 2
        grad_cu  = gradients ** 3

        denom = 2 * grad_sq + (grad_cu * activations).sum(dim=(1, 2), keepdim=True)
        denom = torch.where(denom != 0, denom, torch.ones_like(denom))

        alpha = grad_sq / denom                          # (C, H, W)
        weights = (alpha * torch.relu(gradients)).sum(dim=(1, 2))  # (C,)

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
    target_layer  = get_target_layer(resnet_model)
    gradcampp     = GradCAMPlusPlus(resnet_model, target_layer)
    cam           = gradcampp.generate(input_tensor, pred_idx)

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

    # # =========================
    # # TUMOR SIZE ESTIMATION
    # # =========================
    # MM_PER_PIXEL = 0.25  # Assumed spacing for standard brain MRI (1.5T)
    # tumor_size = {}

    # if "no_tumor" not in pred_label.lower():
    #     # Threshold CAM to get activation mask
    #     threshold = 0.75  # higher threshold = tighter around actual tumor
    #     tumor_mask = (cam_resized >= threshold).astype(np.uint8)

    #     # Morphological cleanup to remove noise
    #     kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    #     tumor_mask = cv2.morphologyEx(tumor_mask, cv2.MORPH_OPEN, kernel)
    #     tumor_mask = cv2.morphologyEx(tumor_mask, cv2.MORPH_CLOSE, kernel)

    #     # Pixel counts
    #     tumor_pixels = int(np.sum(tumor_mask))
    #     total_pixels = 224 * 224

    #     # Brain area — exclude dark background
    #     img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    #     _, brain_mask = cv2.threshold(img_gray, 15, 255, cv2.THRESH_BINARY)
    #     brain_pixels = int(np.sum(brain_mask > 0))
    #     brain_pct = (tumor_pixels / brain_pixels * 100) if brain_pixels > 0 else 0.0

    #     # Bounding box → estimated real-world diameter
    #     contours, _ = cv2.findContours(tumor_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #     bbox_info = {}
    #     diameter_cm = None
    #     if contours:
    #         largest = max(contours, key=cv2.contourArea)
    #         x, y, bw, bh = cv2.boundingRect(largest)
    #         avg_dim_px = (bw + bh) / 2
    #         diameter_cm = round((avg_dim_px * MM_PER_PIXEL) / 10, 2)
    #         bbox_info = {
    #             "width_px": bw,
    #             "height_px": bh,
    #             "width_cm": round((bw * MM_PER_PIXEL) / 10, 2),
    #             "height_cm": round((bh * MM_PER_PIXEL) / 10, 2),
    #         }

    #     # Size category
    #     if brain_pct < 2:
    #         size_category = "Minimal / Trace"
    #     elif brain_pct < 8:
    #         size_category = "Small"
    #     elif brain_pct < 20:
    #         size_category = "Moderate"
    #     else:
    #         size_category = "Large"

    #     tumor_size = {
    #         "tumor_pixels":       tumor_pixels,
    #         "brain_pixels":       brain_pixels,
    #         "tumor_pct_of_brain": round(brain_pct, 2),
    #         "diameter_cm":        diameter_cm,        # e.g. 1.8
    #         "size_category":      size_category,      # Small / Moderate / Large
    #         "bbox":               bbox_info,
    #         "note": "Pixel-based estimate assuming 0.7mm/pixel. Not a clinical measurement."
    #     }
    # else:
    #     # No tumor detected — return empty/zero size info
    #     tumor_size = {
    #         "tumor_pixels":       0,
    #         "brain_pixels":       0,
    #         "tumor_pct_of_brain": 0.0,
    #         "diameter_cm":        None,
    #         "size_category":      "None",
    #         "bbox":               {},
    #         "note":               "No tumor detected."
    #     }

    # =========================
    # XAI SUMMARY
    # =========================
    xai_summary = {
        "method_used":        "GradCAM++",
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
        "explanation_model":    "ResNet50 (GradCAM++)",
        "observation": (
            f"GradCAM++ highlights the {region_info['dominant_region']} region "
            f"with {region_info['coverage_pct']:.1f}% high-activation coverage."
        ),
        "explanation_plot_path": explanation_plot_path,
        "xai_summary":           xai_summary,
        # "tumor_size":            tumor_size,          # <-- NEW
    }

    # =========================
    # LLM REPORT
    # =========================
    llm_input = prepare_llm_input(result)
    report    = generate_report(llm_input)
    result["report"] = report

    return result


# ============================================================
# TEST RUN
# ============================================================
if __name__ == "__main__":
    test_img = os.path.join(BASE_DIR, "..", "data/Testing/meningioma/Te-me_0010.jpg")

    if os.path.exists(test_img):
        result = run_pipeline(test_img)
        print("\nPrediction:  ", result["prediction"])
        print("Confidence:  ", result["confidence"])
        print("Heatmap:     ", result["explanation_plot_path"])

        print("\nXAI Summary:")
        for k, v in result["xai_summary"].items():
            print(f"  {k}: {v}")

        print("\nTumor Size:")
        for k, v in result["tumor_size"].items():
            print(f"  {k}: {v}")
    else:
        print("Test image not found.")