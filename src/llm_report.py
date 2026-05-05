"""
llm_report.py
=============
Hospital-grade MRI Brain Tumor Report Generator.
- Zero AI/model/algorithm wording in report body
- Single disclaimer at end only
- Professional clinical language throughout
- Apollo-level PDF with header/footer on every page
"""

from __future__ import annotations

import io
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from openai import OpenAI
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# CONSTANTS
# ============================================================

_IST = ZoneInfo("Asia/Kolkata")
_DATETIME_FMT  = "%d %B %Y at %I:%M %p"   # e.g. 05 May 2026 at 07:39 PM
_REPORT_ID_FMT = "%Y%m%d%H%M"


# ============================================================
# REPORT CONTEXT
# ============================================================

class ReportContext:
    __slots__ = ("_ts",)

    def __init__(self) -> None:
        self._ts: datetime = datetime.now(ZoneInfo("Asia/Kolkata"))

    @property
    def timestamp_str(self) -> str:
        return self._ts.strftime(_DATETIME_FMT)

    @property
    def report_id(self) -> str:
        return self._ts.strftime(_REPORT_ID_FMT)


# ============================================================
# HELPERS
# ============================================================

def _get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


def _safe_text(value: object, default: str = "N/A") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _format_region_list(regions: list | None) -> str:
    if not regions:
        return "N/A"
    return ", ".join(str(r).strip() for r in regions)


# Full sanitiser — removes every AI/model/algorithm reference
_AI_REPLACEMENTS: list[tuple[str, str]] = [
    ("AI-Generated Medical Report",             "Medical Report"),
    ("AI Generated Medical Report",             "Medical Report"),
    ("AI GENERATED MEDICAL REPORT",             "MEDICAL REPORT"),
    ("AI-Generated",                            ""),
    ("AI Generated",                            ""),
    ("Explainable AI (XAI) Analysis",           "Heatmap Explanation Summary"),
    ("Explainable AI",                          "Heatmap Analysis"),
    ("XAI Methods Used",                        "Visualisation Method"),
    ("AI EXPLANATION (HOW THE AI DECIDED)",     "EXPLANATION"),
    ("AI EXPLANATION (HOW THE MODEL DECIDED)",  "EXPLANATION"),
    ("AI Explanation (How the AI Decided)",     "Explanation"),
    ("AI Explanation (How the Model Decided)",  "Explanation"),
    ("AI Explanation",                          "Explanation"),
    ("WHAT THIS MEANS",                         "IMPRESSION"),
    ("What This Means",                         "Impression"),
    ("WHAT TO DO NEXT",                         "RECOMMENDATION"),
    ("What To Do Next",                         "Recommendation"),
    ("our AI analysis",                         "our analysis"),
    ("Our AI analysis",                         "Our analysis"),
    ("our AI model",                            "our analysis"),
    ("Our AI model",                            "Our analysis"),
    ("our AI",                                  "our"),
    ("Our AI",                                  "Our"),
    ("the AI",                                  "the"),
    ("AI model",                                "the system"),
    ("AI focus area",                           "focus area"),
    ("Red = AI focus area",                     "Red = focus area"),
    ("deep learning model",                     "imaging analysis"),
    ("deep learning algorithm",                 "imaging analysis"),
    ("machine learning model",                  "imaging analysis"),
    ("machine learning",                        "imaging analysis"),
    ("neural network",                          "imaging analysis"),
    ("the algorithm",                           "the analysis"),
    ("an algorithm",                            "the analysis"),
    ("automated system",                        "the system"),
    ("AI-based",                                ""),
    ("AI based",                                ""),
    ("AI system",                               "the system"),
    ("AI",                                      ""),
]

def _sanitize(text: str) -> str:
    if not text:
        return ""
    cleaned = text
    for old, new in _AI_REPLACEMENTS:
        cleaned = cleaned.replace(old, new)
    cleaned = re.sub(r"\bAI\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bA\.I\.\b", "", cleaned, flags=re.IGNORECASE)
    
    # ── Strip any disclaimer block the LLM generates ──
    for marker in ["DISCLAIMER", "DISCLMER", "IMPORTANT DISCLAIMER",
                   "IMPORTANT NOTE", "Please note", "Please remember",
                   "This report was generated", "should not be considered"]:
        if marker.upper() in cleaned.upper():
            idx = cleaned.upper().rfind(marker.upper())
            cleaned = cleaned[:idx].strip()

    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


_KNOWN_HEADINGS: frozenset[str] = frozenset({
    "SUMMARY", "FINDINGS", "IMPRESSION", "RECOMMENDATION",
})

_PDF_SKIP_PREFIXES: frozenset[str] = frozenset({
    "MEDICAL REPORT", "GENERATED ON", "GENERATED:", "REPORT ID",
    "PATIENT INFORMATION", "NAME", "AGE", "GENDER",
    "DIAGNOSIS RESULT", "CONDITION", "CONFIDENCE", "CERTAINTY",
    "DISCLAIMER", "===", "---",
})


# ============================================================
# LLM CLIENT
# ============================================================

_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = _get_secret("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        _client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


# ============================================================
# DATA NORMALISATION
# ============================================================

def prepare_llm_input(result: dict, patient_info: dict | None = None) -> dict:
    confidence_pct = float(result.get("confidence", 0.0)) * 100.0
    if confidence_pct < 70.0:
        certainty = "Low"
    elif confidence_pct < 90.0:
        certainty = "Moderate"
    else:
        certainty = "High"

    data: dict = {
        "diagnosis":            result.get("prediction", "Unknown"),
        "confidence":           confidence_pct,
        "certainty":            certainty,
        "observation":          result.get("observation", "Abnormal patterns detected."),
        "xai_summary":          result.get("xai_summary", {}),
        "confidence_breakdown": result.get("confidence_breakdown", {}),
    }
    if patient_info:
        data.update(patient_info)
    return data


# ============================================================
# PROMPT
# ============================================================

def _build_prompt(data: dict) -> str:
    diagnosis    = _safe_text(data.get("diagnosis"), "Unknown")
    confidence   = float(data.get("confidence", 0.0))
    certainty    = _safe_text(data.get("certainty"))
    observation  = _safe_text(data.get("observation"))

    xai         = data.get("xai_summary", {}) or {}
    dom_region  = _safe_text(xai.get("dominant_region"))
    top3        = _format_region_list(xai.get("top3_regions", []))
    coverage    = xai.get("cam_coverage_pct", "N/A")

    breakdown   = data.get("confidence_breakdown", {}) or {}
    breakdown_str = (
        ", ".join(f"{k.capitalize()}: {float(v):.1f}%" for k, v in breakdown.items())
        if breakdown else "Not available"
    )

    return f"""You are a senior consultant radiologist writing a formal MRI brain scan report
for a tertiary-care hospital. Write exactly as a human radiologist — first-person plural,
clinical voice. This report goes directly into the patient's medical file.

══════════════════════════════════════════
ABSOLUTE RULES — ZERO EXCEPTIONS
══════════════════════════════════════════
1. Use EXACTLY these four headings in this order:
       SUMMARY
       FINDINGS
       IMPRESSION
       RECOMMENDATION

2. COMPLETELY FORBIDDEN — never write these words in any form or spelling:
       AI, A.I., artificial intelligence, artificial, automated, automation,
       model, algorithm, machine learning, deep learning, neural network,
       computer, software, technology, tool, platform, system, generated,
       auto-generated, computed, detection system, heatmap model.

3. Write as though YOU personally reviewed the scan.
   Use: "We observe…", "Our analysis…", "Findings indicate…",
   "We recommend…", "The scan demonstrates…", "Imaging reveals…"

4. NO disclaimer — it is added separately.
5. NO patient name, age, gender, or report title — already in header.
6. Each section: 2–4 sentences. Formal, concise, clinical language only.

7. Confidence phrasing — use exactly ONE matching phrase:
   - High     → "Our analysis is highly confident in this diagnosis."
   - Moderate → "Our analysis is moderately confident in this diagnosis."
   - Low      → "Findings are made with limited confidence; further evaluation is strongly advised."

══════════════════════════════════════════
CLINICAL DATA
══════════════════════════════════════════
Diagnosis              : {diagnosis}
Confidence Score       : {confidence:.2f}%
Certainty Level        : {certainty}
Observation            : {observation}
Dominant Active Region : {dom_region}
Top 3 Active Regions   : {top3}
High-Activation Coverage: {coverage}%
Class-Wise Confidence  : {breakdown_str}

══════════════════════════════════════════
OUTPUT TEMPLATE — follow exactly
══════════════════════════════════════════
SUMMARY
[2–3 sentences: key finding, diagnosis, confidence statement]

FINDINGS
[3–4 sentences: detailed radiological observations referencing
active regions, coverage, and class-wise confidence breakdown]

IMPRESSION
[2–3 sentences: clinical interpretation and radiological significance]

RECOMMENDATION
[3–4 specific numbered actionable follow-up steps for the physician]

STOP after RECOMMENDATION. Do NOT add any disclaimer, note, warning,
or any text after the RECOMMENDATION section. End immediately.
"""


# ============================================================
# PLAIN-TEXT REPORT
# ============================================================

def generate_report(data: dict) -> str:
    """Generate the plain-text clinical report. No AI references anywhere."""
    ctx = ReportContext()

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": _build_prompt(data)}],
            temperature=0.3,
            max_tokens=1024,
        )
        llm_raw  = response.choices[0].message.content or ""
        llm_body = _sanitize(llm_raw)
    except Exception as exc:
        print(f"[LLM ERROR] {exc}")
        llm_body = (
            "SUMMARY\nReport generation encountered a technical error. Please retry.\n\n"
            "FINDINGS\nNot available.\n\n"
            "IMPRESSION\nNot available.\n\n"
            "RECOMMENDATION\n1. Contact technical support.\n2. Retry report generation."
        )

    patient_name = _safe_text(data.get("name"))
    age          = _safe_text(data.get("age"))
    gender       = _safe_text(data.get("gender"))
    diagnosis    = _safe_text(data.get("diagnosis"), "Unknown")
    confidence   = float(data.get("confidence", 0.0))
    certainty    = _safe_text(data.get("certainty"))

    sep  = "=" * 64
    thin = "-" * 64

    report = (
        f"MEDICAL REPORT\n"
        f"{sep}\n"
        f"Report ID    : {ctx.report_id}\n"
        f"Generated On : {ctx.timestamp_str}\n"
        f"{sep}\n\n"
        f"PATIENT INFORMATION\n"
        f"{thin}\n"
        f"Name    : {patient_name}\n"
        f"Age     : {age}\n"
        f"Gender  : {gender}\n\n"
        f"DIAGNOSIS RESULT\n"
        f"{thin}\n"
        f"Condition  : {diagnosis}\n"
        f"Confidence : {confidence:.2f}%\n"
        f"Certainty  : {certainty}\n\n"
        f"{sep}\n\n"
        f"{llm_body}\n"
    )

    return report.strip()


# ============================================================
# PDF STYLES
# ============================================================

def _build_styles(raw: dict) -> dict:
    navy        = colors.HexColor("#1a2a4a")
    dark_navy   = colors.HexColor("#0f1b31")
    accent_blue = colors.HexColor("#1e6bb8")
    soft_blue   = colors.HexColor("#dceefb")
    pale_blue   = colors.HexColor("#f2f7fd")
    ghost_blue  = colors.HexColor("#f8fbff")
    grey_text   = colors.HexColor("#4b5563")
    mid_grey    = colors.HexColor("#6b7280")
    rule_grey   = colors.HexColor("#d1d5db")
    body_dark   = colors.HexColor("#1f2937")

    S: dict = {
        "navy": navy, "dark_navy": dark_navy, "accent_blue": accent_blue,
        "soft_blue": soft_blue, "pale_blue": pale_blue, "ghost_blue": ghost_blue,
        "grey_text": grey_text, "mid_grey": mid_grey, "rule_grey": rule_grey,
        "body_dark": body_dark,
        "raw": raw,

        "title": ParagraphStyle(
            "TitleStyle", parent=raw["Title"],
            fontName="Helvetica-Bold", fontSize=18, leading=22,
            textColor=navy, alignment=1, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleStyle", parent=raw["Normal"],
            fontName="Helvetica", fontSize=8.5, leading=11,
            textColor=grey_text, spaceAfter=4, alignment=1,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading", parent=raw["Heading2"],
            fontName="Helvetica-Bold", fontSize=11, leading=14,
            textColor=navy, spaceBefore=12, spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "BodyStyle", parent=raw["Normal"],
            fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=body_dark, spaceAfter=4,
        ),
        "label": ParagraphStyle(
            "LabelStyle", parent=raw["Normal"],
            fontName="Helvetica-Bold", fontSize=7.5, leading=10,
            textColor=grey_text,
        ),
        "value": ParagraphStyle(
            "ValueStyle", parent=raw["Normal"],
            fontName="Helvetica-Bold", fontSize=9.5, leading=12,
            textColor=navy,
        ),
        "value_accent": ParagraphStyle(
            "ValueAccent", parent=raw["Normal"],
            fontName="Helvetica-Bold", fontSize=9.5, leading=12,
            textColor=accent_blue,
        ),
        "caption": ParagraphStyle(
            "CaptionStyle", parent=raw["Normal"],
            fontName="Helvetica", fontSize=7.5, leading=9,
            alignment=1, textColor=grey_text,
        ),
        "disclaimer": ParagraphStyle(
            "DisclaimerStyle", parent=raw["Normal"],
            fontName="Helvetica", fontSize=7.8, leading=11,
            textColor=mid_grey, alignment=1,
        ),
    }
    return S


def _apply_table_style(table, S, *, header_bg, data_bg) -> None:
    table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), header_bg),
        ("BACKGROUND",    (0, 1), (-1, 1), data_bg),
        ("BOX",           (0, 0), (-1, -1), 0.5, S["rule_grey"]),
        ("INNERGRID",     (0, 0), (-1, -1), 0.4, S["rule_grey"]),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))


# ============================================================
# PDF GENERATION
# ============================================================

def generate_pdf(
    data,
    report_text,
    original_image_path,
    gradcam_image_path,
    lime_image_path=None,
):
    """Render an Apollo-level hospital-grade PDF and return raw bytes."""
    ctx = ReportContext()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.80 * inch,
        bottomMargin=0.72 * inch,
        title="Medical Report — NeuroScan",
        author="NeuroScan Imaging",
        subject="Brain MRI Analysis Report",
    )

    raw_styles = getSampleStyleSheet()
    S = _build_styles(raw_styles)
    story: list = []

    # ── Header ────────────────────────────────────────────────
    story.append(Paragraph("Brain Tumor Detection Report", S["title"]))
    story.append(Paragraph(
        f"Generated on {ctx.timestamp_str}",
        S["subtitle"],
    ))
    story.append(HRFlowable(
        width="100%", thickness=2.5,
        color=S["navy"], spaceAfter=10, spaceBefore=2,
    ))

    # ── Patient Information ───────────────────────────────────
    story.append(Paragraph("Patient Information", S["section_heading"]))
    p_name   = _safe_text(data.get("name"))
    p_age    = _safe_text(data.get("age"))
    p_gender = _safe_text(data.get("gender"))

    pt_table = Table(
        [
            [Paragraph("Name",      S["label"]),
             Paragraph("Age",       S["label"]),
             Paragraph("Gender",    S["label"]),
             Paragraph("Report ID", S["label"])],
            [Paragraph(p_name,       S["value"]),
             Paragraph(p_age,        S["value"]),
             Paragraph(p_gender,     S["value"]),
             Paragraph(ctx.report_id, S["value"])],
        ],
        colWidths=[2.50 * inch, 0.85 * inch, 1.00 * inch, 3.15 * inch],
    )
    _apply_table_style(pt_table, S, header_bg=S["pale_blue"], data_bg=colors.white)
    story.append(pt_table)
    story.append(Spacer(1, 8))

    # ── Diagnosis Result ──────────────────────────────────────
    story.append(Paragraph("Diagnosis Result", S["section_heading"]))
    confidence   = float(data.get("confidence", 0.0))
    diagnosis    = _safe_text(data.get("diagnosis"), "Unknown")
    certainty    = _safe_text(data.get("certainty"))
    diag_display = diagnosis.replace("_", " ").title()

    diag_table = Table(
        [
            [Paragraph("Detected Condition",  S["label"]),
             Paragraph("Confidence Score",    S["label"]),
             Paragraph("Certainty Level",     S["label"])],
            [Paragraph(f"{diag_display} Tumor", S["value_accent"]),
             Paragraph(f"{confidence:.2f}%",    S["value"]),
             Paragraph(certainty.upper(),        S["value"])],
        ],
        colWidths=[3.10 * inch, 2.00 * inch, 2.40 * inch],
    )
    _apply_table_style(diag_table, S, header_bg=S["pale_blue"], data_bg=S["soft_blue"])
    story.append(diag_table)

    # ── Per-Class Confidence Breakdown ────────────────────────
    breakdown = data.get("confidence_breakdown", {}) or {}
    if breakdown:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Per-Class Confidence Breakdown", S["section_heading"]))
        n_cols = len(breakdown)
        col_w  = doc.width / max(n_cols, 1)
        headers = [Paragraph(str(k).capitalize(), S["label"]) for k in breakdown]
        values  = [Paragraph(f"{float(v):.1f}%",  S["value"]) for v in breakdown.values()]
        bd_table = Table([headers, values], colWidths=[col_w] * n_cols)
        bd_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), S["pale_blue"]),
            ("BACKGROUND",    (0, 1), (-1, 1), colors.white),
            ("BOX",           (0, 0), (-1, -1), 0.5, S["rule_grey"]),
            ("INNERGRID",     (0, 0), (-1, -1), 0.4, S["rule_grey"]),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(bd_table)

    # ── MRI Scan & Heatmap Images ─────────────────────────────
    story.append(Spacer(1, 10))
    story.append(Paragraph("MRI Scan & Grad-CAM++ Analysis", S["section_heading"]))

    image_candidates = [
        ("Original MRI Scan",        original_image_path),
        ("Grad-CAM++ Heatmap",        gradcam_image_path),
    ]
    if lime_image_path:
        image_candidates.append(("Supplementary Overlay", lime_image_path))

    valid_images = [
        (lbl, pth) for lbl, pth in image_candidates
        if pth and os.path.exists(str(pth))
    ]

    if valid_images:
        n     = len(valid_images)
        gap   = 0.10 * inch
        img_w = (doc.width - gap * (n - 1)) / n
        img_h = img_w * 0.95

        img_row = [Image(p, width=img_w, height=img_h) for _, p in valid_images]
        cap_row = [Paragraph(lbl, S["caption"])         for lbl, _ in valid_images]
        img_table = Table([img_row, cap_row], colWidths=[img_w] * n, spaceBefore=4)
        img_table.setStyle(TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(img_table)

    # ── Heatmap Explanation Summary ───────────────────────────
    xai = data.get("xai_summary", {}) or {}
    if xai:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Heatmap Explanation Summary", S["section_heading"]))
        xai_rows = [
            [Paragraph("Visualisation Method",      S["label"]),
             Paragraph(_safe_text(xai.get("method_used"), "Score-CAM"), S["body"])],
            [Paragraph("Dominant Active Region",    S["label"]),
             Paragraph(_safe_text(xai.get("dominant_region")),           S["body"])],
            [Paragraph("Top 3 Active Regions",      S["label"]),
             Paragraph(_format_region_list(xai.get("top3_regions", [])), S["body"])],
            [Paragraph("High-Activation Coverage",  S["label"]),
             Paragraph(f"{float(xai.get('cam_coverage_pct', 0.0)):.1f}%", S["body"])],
            [Paragraph("Mean Activation Score",     S["label"]),
             Paragraph(f"{float(xai.get('cam_mean_activation', 0.0)):.4f}", S["body"])],
        ]
        xai_table = Table(xai_rows, colWidths=[2.10 * inch, 5.40 * inch])
        xai_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, -1), S["pale_blue"]),
            ("BOX",           (0, 0), (-1, -1), 0.5, S["rule_grey"]),
            ("INNERGRID",     (0, 0), (-1, -1), 0.4, S["rule_grey"]),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(xai_table)

    # ── Regional Activation Grid ──────────────────────────────
    region_scores = xai.get("region_scores", {}) if xai else {}
    if region_scores:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Regional Activation Grid (3x3)", S["section_heading"]))

        grid_layout = [
            ["top-left",  "top-center",  "top-right"],
            ["mid-left",  "center",      "mid-right"],
            ["bot-left",  "bot-center",  "bot-right"],
        ]

        grid_data   = []
        grid_styles = TableStyle([
            ("BOX",           (0, 0), (-1, -1), 0.5, S["rule_grey"]),
            ("INNERGRID",     (0, 0), (-1, -1), 0.4, S["rule_grey"]),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ])

        for ri, row_keys in enumerate(grid_layout):
            row = []
            for ci, key in enumerate(row_keys):
                score = float(region_scores.get(key, 0.0))
                r_int = int(min(255, score * 510))
                g_int = int(min(255, (1.0 - score) * 510))
                bg_c  = colors.Color(r_int / 255.0, g_int / 255.0, 0.12)
                txt_c = colors.white if score > 0.45 else colors.HexColor("#1a2a4a")
                grid_styles.add("BACKGROUND", (ci, ri), (ci, ri), bg_c)

                cell_style = ParagraphStyle(
                    f"GC_{key.replace('-', '_')}",
                    parent=S["raw"]["Normal"],
                    fontName="Helvetica-Bold",
                    fontSize=8, leading=11,
                    alignment=1, textColor=txt_c,
                )
                row.append(Paragraph(f"{key}<br/>{score:.3f}", cell_style))
            grid_data.append(row)

        region_table = Table(grid_data, colWidths=[2.08 * inch] * 3)
        region_table.setStyle(grid_styles)
        story.append(region_table)

    # ── Clinical Report (LLM body) ────────────────────────────
    story.append(Spacer(1, 16))
    story.append(Paragraph("Clinical Report", S["section_heading"]))
    story.append(HRFlowable(
        width="100%", thickness=0.8, color=S["rule_grey"],
        spaceAfter=8, spaceBefore=2,
    ))

    clean_text = _sanitize(report_text or "")
    for raw_line in clean_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 3))
            continue
        upper = line.upper()
        if any(upper.startswith(pfx) for pfx in _PDF_SKIP_PREFIXES):
            continue
        if upper in _KNOWN_HEADINGS:
            story.append(Spacer(1, 6))
            story.append(Paragraph(line.title(), S["section_heading"]))
        else:
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
            if text.startswith("- "):
                text = "&#8226;&nbsp;" + text[2:].strip()
            story.append(Paragraph(text, S["body"]))

    # ── Disclaimer — once, at end only ───────────────────────
    story.append(Spacer(1, 18))
    story.append(HRFlowable(
        width="100%", thickness=0.8, color=S["rule_grey"],
        spaceAfter=7, spaceBefore=2,
    ))
    story.append(Paragraph(
        "<b>DISCLAIMER:</b> The findings and recommendations in this report are intended "
        "solely to assist qualified medical professionals and do not constitute a definitive "
        "diagnosis. This report has been prepared using advanced imaging analysis and must be "
        "reviewed and validated by a licensed healthcare professional before any clinical "
        "decision is made. It should not replace a formal consultation with a specialist.",
        S["disclaimer"],
    ))

    # ── Page decoration ───────────────────────────────────────
    def _page_decoration(canvas, doc_obj):
        canvas.saveState()
        w, h = letter
        canvas.setStrokeColor(S["navy"])
        canvas.setLineWidth(0.7)
        canvas.line(doc_obj.leftMargin, h - 0.44 * inch,
                    w - doc_obj.rightMargin, h - 0.44 * inch)
        canvas.setStrokeColor(S["rule_grey"])
        canvas.setLineWidth(0.4)
        canvas.line(doc_obj.leftMargin, 0.50 * inch,
                    w - doc_obj.rightMargin, 0.50 * inch)
        canvas.setFillColor(S["grey_text"])
        canvas.setFont("Helvetica", 7.2)
        canvas.drawString(doc_obj.leftMargin, 0.32 * inch,
                          "NeuroScan Brain MRI — Confidential Medical Record")
        canvas.drawRightString(w - doc_obj.rightMargin, 0.32 * inch,
                               f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_page_decoration, onLaterPages=_page_decoration)
    buffer.seek(0)
    return buffer.getvalue()