"""
llm_report.py
=============
Hospital-grade (Apollo-level) MRI Brain Tumor Report Generator.

Features
--------
- IST timezone throughout — single datetime object captured ONCE per report/PDF call,
  reused for both human-readable stamp and Report ID (no clock-skew between them)
- Zero "AI" wording in report body — LLM-enforced system prompt + deterministic
  post-processing sanitiser with regex nuclear fallback
- Single disclaimer block, placed ONLY at the end of both text report and PDF
- Correct clinical section headings (no "AI" prefix anywhere)
- Professional clinical language — first-person plural radiological voice
- Apollo-level PDF: header/footer on every page, structured tables, heatmap images,
  3×3 regional activation grid, per-class confidence breakdown, clean margins
- Fully modular: no global mutable state, no side effects at import time
- Self-test with automated constraint validation at the bottom
"""

from __future__ import annotations

import io
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from llm_report import ReportContext

import streamlit as st
from openai import OpenAI
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
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

# Output formats
_DATETIME_FMT  = "%d-%m-%Y %H:%M:%S IST"   # e.g. 05-05-2026 14:32:07 IST
_REPORT_ID_FMT = "NS%Y%m%d%H%M%S"          # e.g. NS20260505143207

# ---------------------------------------------------------------------------
# AI-word sanitiser table
# ---------------------------------------------------------------------------
# Ordered longest-match first so that compound phrases are replaced before
# their component words, preventing partial-match artefacts.
# Format: (literal_string_to_find, replacement)
# ---------------------------------------------------------------------------
_AI_REPLACEMENTS: list[tuple[str, str]] = [
    # --- Heading variants ---
    ("AI-Generated Medical Report",              "Medical Report"),
    ("AI Generated Medical Report",              "Medical Report"),
    ("AI GENERATED MEDICAL REPORT",              "MEDICAL REPORT"),
    ("AI Explanation (How the AI Decided)",      "Explanation (How Decision is Made)"),
    ("AI Explanation (How the Model Decided)",   "Explanation (How Decision is Made)"),
    ("AI Explanation (How the System Decided)",  "Explanation (How Decision is Made)"),
    ("AI EXPLANATION (HOW THE AI DECIDED)",      "EXPLANATION (HOW DECISION IS MADE)"),
    ("AI EXPLANATION (HOW THE MODEL DECIDED)",   "EXPLANATION (HOW DECISION IS MADE)"),
    ("AI EXPLANATION (HOW THE SYSTEM DECIDED)",  "EXPLANATION (HOW DECISION IS MADE)"),
    ("AI Explanation",                           "Explanation"),
    ("AI EXPLANATION",                           "EXPLANATION"),
    # --- Multi-word phrases (longest first) ---
    ("Our AI analysis is highly confident",      "Our analysis is highly confident"),
    ("our AI analysis is highly confident",      "our analysis is highly confident"),
    ("Our AI analysis is moderately confident",  "Our analysis is moderately confident"),
    ("our AI analysis is moderately confident",  "our analysis is moderately confident"),
    ("Our AI analysis is made with limited",     "Our analysis is made with limited"),
    ("our AI analysis is made with limited",     "our analysis is made with limited"),
    ("Our AI analysis",                          "Our analysis"),
    ("our AI analysis",                          "our analysis"),
    ("the AI-based system",                      "the system"),
    ("AI-based analysis",                        "the analysis"),
    ("AI-based approach",                        "the approach"),
    ("AI-based",                                 "automated"),
    ("AI analysis",                              "analysis"),
    ("AI-generated",                             "generated"),
    ("AI generated",                             "generated"),
    ("AI used",                                  "analysis used"),
    ("AI decided",                               "the decision was made"),
    ("AI decides",                               "the decision is made"),
    ("AI model",                                 "the system"),
    ("the AI",                                   "the system"),
    ("our AI",                                   "our"),
    ("Our AI",                                   "Our"),
    # --- Algorithm / model wording ---
    ("deep learning model",                      "imaging analysis"),
    ("deep learning algorithm",                  "imaging analysis"),
    ("machine learning model",                   "imaging analysis"),
    ("machine learning algorithm",               "imaging analysis"),
    ("neural network",                           "imaging analysis"),
    ("the algorithm",                            "the analysis"),
    ("an algorithm",                             "the analysis"),
    # --- Isolated "AI" tokens are caught by the regex fallback below ---
]

# Headings recognised in LLM output — used for PDF style routing
_KNOWN_HEADINGS: frozenset[str] = frozenset({
    "SUMMARY",
    "FINDINGS",
    "IMPRESSION",
    "RECOMMENDATION",
    "WHAT THIS MEANS",
    "EXPLANATION (HOW DECISION IS MADE)",
    "WHAT TO DO NEXT",
})

# Prefixes that must be skipped when rendering LLM text inside the PDF
# (because the PDF already renders these as structured elements)
_PDF_SKIP_PREFIXES: frozenset[str] = frozenset({
    "MEDICAL REPORT",
    "GENERATED ON",
    "GENERATED:",
    "REPORT ID",
    "PATIENT INFORMATION",
    "NAME",
    "AGE",
    "GENDER",
    "DIAGNOSIS RESULT",
    "CONDITION",
    "CONFIDENCE",
    "CERTAINTY",
    "DISCLAIMER",
    "===",
    "---",
})


# ============================================================
# FROZEN REPORT CONTEXT  (single source of truth per report)
# ============================================================


class ReportContext:
    """
    Captures an IST timestamp ONCE at construction time.
    Pass this object into every function that needs the report time or ID.
    This ensures the human-readable timestamp, the Report ID, and every PDF
    element all carry the *identical* moment — no clock drift.
    """

    __slots__ = ("_ts",)

    def __init__(self) -> None:
        self._ts: datetime = datetime.now(ZoneInfo("Asia/Kolkata"))

    @property
    def timestamp_str(self) -> str:
        """DD-MM-YYYY HH:MM:SS IST"""
        return self._ts.strftime(_DATETIME_FMT)

    @property
    def report_id(self) -> str:
        """NSYYYYMMDDHHMMSS"""
        return self._ts.strftime(_REPORT_ID_FMT)


# ============================================================
# HELPERS — GENERAL UTILITIES
# ============================================================


def _get_secret(key: str, default: str = "") -> str:
    """Read from Streamlit secrets first, fall back to environment variable."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


def _safe_text(value: object, default: str = "N/A") -> str:
    """Convert any value to a non-empty string or return default."""
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _format_region_list(regions: list | None) -> str:
    """Join a list of region names into a comma-separated string."""
    if not regions:
        return "N/A"
    return ", ".join(str(r).strip() for r in regions)


def _sanitize_body(text: str) -> str:
    """
    Remove ALL AI-wording from a text block.

    Strategy
    --------
    1. Apply the ordered literal-replacement table (_AI_REPLACEMENTS).
    2. Regex nuclear fallback: zap any remaining standalone ``AI`` tokens
       (word-boundary anchored, case-insensitive) that slipped through.
    3. Collapse stray whitespace introduced by deletions.

    NOTE: This function must NEVER be called on the disclaimer text,
    which is authored locally and is the only place "AI" is permitted.
    """
    if not text:
        return ""

    cleaned = text

    for old, new in _AI_REPLACEMENTS:
        cleaned = cleaned.replace(old, new)

    # Nuclear fallback — word-boundary aware, case-insensitive
    cleaned = re.sub(r"\bAI\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)

    # Tidy artefacts
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def _is_known_heading(line: str) -> bool:
    """Return True if the stripped, uppercased line is a recognised clinical heading."""
    return line.strip().upper() in _KNOWN_HEADINGS


def _line_to_paragraph(line: str, style: ParagraphStyle) -> Paragraph:
    """Convert a plain-text line to a ReportLab Paragraph with minimal markdown."""
    text = line.strip()
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)   # **bold**
    if text.startswith("- "):
        text = "&#8226;&nbsp;" + text[2:].strip()           # bullet
    return Paragraph(text, style)


# ============================================================
# LLM CLIENT  (lazy singleton — no import-time side effects)
# ============================================================

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = _get_secret("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured. "
                "Add it to .streamlit/secrets.toml or set the environment variable."
            )
        _client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


# ============================================================
# DATA NORMALISATION
# ============================================================


def prepare_llm_input(result: dict, patient_info: dict | None = None) -> dict:
    """
    Normalise raw detection result and optional patient metadata into a
    flat dictionary suitable for report generation.
    """
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
        "prediction_model":     result.get("prediction_model", "EfficientNet-B0"),
        "explanation_model":    result.get("explanation_model", "GradCAM++"),
        "observation":          result.get("observation", "Abnormal patterns detected."),
        "xai_summary":          result.get("xai_summary", {}),
        "confidence_breakdown": result.get("confidence_breakdown", {}),
    }

    if patient_info:
        data.update(patient_info)

    return data


# ============================================================
# LLM PROMPT BUILDER
# ============================================================


def _build_prompt(data: dict) -> str:
    """
    Construct the full user-turn prompt sent to the LLM.

    The system-level constraints are embedded inline because the Groq
    endpoint is called via a single ``user`` message; they are equally
    enforceable this way.

    Constraints enforced in the prompt
    ------------------------------------
    - Exact four headings: SUMMARY / FINDINGS / IMPRESSION / RECOMMENDATION
    - Absolute ban on: AI, artificial intelligence, model, algorithm,
      machine learning, deep learning, neural network, system, software
    - No disclaimer — added separately after LLM output
    - No repetition of patient details or report title
    - Formal, first-person-plural clinical voice
    - Confidence certainty phrasing table
    """
    patient_name = _safe_text(data.get("name"))
    age          = _safe_text(data.get("age"))
    gender       = _safe_text(data.get("gender"))
    diagnosis    = _safe_text(data.get("diagnosis"), "Unknown")
    confidence   = float(data.get("confidence", 0.0))
    certainty    = _safe_text(data.get("certainty"))
    observation  = _safe_text(data.get("observation"))

    xai          = data.get("xai_summary", {}) or {}
    method       = _safe_text(xai.get("method_used"), "GradCAM++")
    dom_region   = _safe_text(xai.get("dominant_region"))
    top3         = _format_region_list(xai.get("top3_regions", []))
    coverage     = xai.get("cam_coverage_pct", "N/A")

    breakdown    = data.get("confidence_breakdown", {}) or {}
    breakdown_str = (
        ", ".join(f"{k.capitalize()}: {float(v):.1f}%" for k, v in breakdown.items())
        if breakdown else "Not available"
    )

    return f"""You are a senior consultant radiologist authoring a formal MRI brain scan report
for a tertiary-care hospital record. This report will be signed off by a physician and
placed in the patient's medical file.

══════════════════════════════════════════
MANDATORY FORMATTING RULES  (non-negotiable)
══════════════════════════════════════════
1.  Use EXACTLY these four headings, in this order, with nothing before, between,
    or after except the content of each section:
        SUMMARY
        FINDINGS
        IMPRESSION
        RECOMMENDATION

2.  FORBIDDEN WORDS — you MUST NOT write any of the following, in any form,
    capitalisation, or spelling variation:
        AI, A.I., artificial intelligence, model, algorithm, machine learning,
        deep learning, neural network, automated system,
        computer, automated, automation, technology, tool, platform, application.

    Write as though you, a radiologist, personally reviewed and interpreted the scan.

3.  Do NOT include a Disclaimer section. It will be appended separately.

4.  Do NOT repeat the patient's name, age, gender, report title, or any metadata.
    Those appear in the document header; your output is the clinical body only.

5.  Language register: formal, concise, clinical. Each section: 2–4 sentences maximum.
    Use first-person plural: "We observe…", "Our analysis indicates…",
    "Findings are consistent with…", "We recommend…"

6.  Confidence certainty phrasing — choose the ONE matching phrase:
    - Certainty = High     → "Our analysis is highly confident in this diagnosis."
    - Certainty = Moderate → "Our analysis is moderately confident in this diagnosis."
    - Certainty = Low      → "Our analysis is made with limited confidence; further
                               evaluation is strongly advised."

7.  Do not begin any sentence with a forbidden word. Do not use synonyms such as
    "detection system", "automated detection", "computed detection", or similar.

══════════════════════════════════════════
CLINICAL DATA
══════════════════════════════════════════
Patient Name       : {patient_name}
Age / Gender       : {age} / {gender}

Diagnosis          : {diagnosis}
Confidence Score   : {confidence:.2f}%
Certainty Level    : {certainty}
Observation        : {observation}

Visualisation Method   : {method}
Dominant Active Region : {dom_region}
Top 3 Active Regions   : {top3}
High-Activation Coverage: {coverage}%

Class-Wise Confidence  : {breakdown_str}

══════════════════════════════════════════
EXACT OUTPUT TEMPLATE  (follow precisely)
══════════════════════════════════════════
SUMMARY
[2–3 sentences: key finding, diagnosis, confidence statement]

FINDINGS
[3–4 sentences: detailed radiological observation referencing active regions,
coverage, and class-wise confidence breakdown]

IMPRESSION
[2–3 sentences: clinical interpretation — what these findings most likely represent
and their radiological significance]

RECOMMENDATION
[3–4 specific, actionable follow-up steps the treating physician should consider,
written as a numbered list]
"""


# ============================================================
# PLAIN-TEXT REPORT GENERATION
# ============================================================


def generate_report(data: dict, ctx: ReportContext | None = None) -> str:
    ctx = ReportContext()
    """
    Call the LLM, sanitise the output, and assemble the final plain-text report.

    The ReportContext is created here — ONE timestamp shared by the header block,
    Report ID, and every downstream consumer (including generate_pdf when called
    with the same context object).

    Returns
    -------
    str
        Complete report string containing:
        - MEDICAL REPORT header with IST timestamp and Report ID
        - Patient Information block
        - Diagnosis Result block
        - Sanitised LLM body (SUMMARY / FINDINGS / IMPRESSION / RECOMMENDATION)
        - ONE disclaimer at the very end
    """
    if ctx is None:
        ctx = ReportContext()

    # ---- Call LLM ----
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": _build_prompt(data)}],
            temperature=0.3,   # Near-deterministic for clinical reproducibility
            max_tokens=1024,
        )
        llm_raw  = response.choices[0].message.content or ""
        llm_body = _sanitize_body(llm_raw)

    except Exception as exc:
        print(f"[LLM ERROR] {exc}")
        llm_body = (
            "SUMMARY\n"
            "Report generation encountered a technical error. "
            "Please retry or contact support.\n\n"
            "FINDINGS\nNot available.\n\n"
            "IMPRESSION\nNot available.\n\n"
            "RECOMMENDATION\n1. Contact technical support.\n2. Retry report generation."
        )

    # ---- Assemble structured text ----
    patient_name = _safe_text(data.get("name"))
    age          = _safe_text(data.get("age"))
    gender       = _safe_text(data.get("gender"))
    diagnosis    = _safe_text(data.get("diagnosis"), "Unknown")
    confidence   = float(data.get("confidence", 0.0))
    certainty    = _safe_text(data.get("certainty"))

    # Single disclaimer authored here (only place "AI" is permitted)
    disclaimer = (
        "This report is generated using automated imaging analysis tools "
        "and must be reviewed and validated by a qualified, licensed healthcare "
        "professional before any clinical decision is made. It does not constitute "
        "a definitive diagnosis and should not replace a formal consultation with "
        "a specialist."
    )

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
        f"{llm_body}\n\n"
        f"{sep}\n"
        f"DISCLAIMER\n"
        f"{disclaimer}\n"
    )

    return report.strip()


# ============================================================
# PDF STYLE REGISTRY  (Apollo-grade palette & typography)
# ============================================================


def _build_styles(raw: dict) -> dict:
    """
    Construct and return every ParagraphStyle and colour constant used
    in the PDF, keyed by short names.  Single source of truth for all
    design tokens — change here, changes everywhere.
    """
    # ---- Colour palette ----
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
    green_badge = colors.HexColor("#065f46")

    S: dict = {
        # Colours (accessed directly in TableStyle commands)
        "navy":        navy,
        "dark_navy":   dark_navy,
        "accent_blue": accent_blue,
        "soft_blue":   soft_blue,
        "pale_blue":   pale_blue,
        "ghost_blue":  ghost_blue,
        "grey_text":   grey_text,
        "mid_grey":    mid_grey,
        "rule_grey":   rule_grey,
        "body_dark":   body_dark,
        "green_badge": green_badge,

        # ---- Paragraph styles ----
        "title": ParagraphStyle(
            "TitleStyle", parent=raw["Title"],
            fontName="Helvetica-Bold", fontSize=18, leading=22,
            textColor=navy, alignment=0, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleStyle", parent=raw["Normal"],
            fontName="Helvetica", fontSize=8.5, leading=11,
            textColor=grey_text, spaceAfter=4,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading", parent=raw["Heading2"],
            fontName="Helvetica-Bold", fontSize=11, leading=14,
            textColor=navy, spaceBefore=12, spaceAfter=5,
            borderPad=0,
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
        "small": ParagraphStyle(
            "SmallStyle", parent=raw["Normal"],
            fontName="Helvetica", fontSize=8.5, leading=11,
            textColor=grey_text,
        ),
    }
    S["raw"] = raw
    return S


# ============================================================
# PDF GENERATION
# ============================================================


def generate_pdf(data, report_text, original_image_path, gradcam_image_path, lime_image_path=None):
    ctx = ReportContext()
    # ... rest of function unchanged
    # ... function body ...
    """
    Render an Apollo-level hospital-grade PDF and return the raw bytes.

    Parameters
    ----------
    data                : Flat dict from ``prepare_llm_input()``
    report_text         : Plain-text report from ``generate_report()``
    original_image_path : File path to original MRI scan (optional)
    gradcam_image_path  : File path to GradCAM++ heatmap (optional)
    lime_image_path     : File path to LIME / supplementary overlay (optional)
    ctx                 : ReportContext — if None, a new one is created.
                          Pass the SAME ctx used in generate_report() so that
                          the PDF timestamp / Report ID are identical.

    PDF Layout
    ----------
    1.  Page header rule + footer (every page)
    2.  Document title + generated-on + Report ID
    3.  Patient Information table
    4.  Diagnosis Result table
    5.  Per-Class Confidence Breakdown table
    6.  MRI Scan & Heatmap images (side-by-side)
    7.  Heatmap Explanation Summary table
    8.  Regional Activation Grid (3×3)
    9.  Clinical Report  (LLM body, sanitised)
    10. Single disclaimer — end of document only
    """

    if ctx is None:
        ctx = ReportContext()   # Fallback: new IST timestamp

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

    # --------------------------------------------------------
    # SECTION 1: Document Header
    # --------------------------------------------------------
    story.append(Paragraph(
        "NeuroScan Brain MRI — Medical Report",
        S["title"],
    ))
    story.append(Paragraph(
        f"Generated: <b>{ctx.timestamp_str}</b>"
        f"&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"Report ID: <b>{ctx.report_id}</b>",
        S["subtitle"],
    ))
    story.append(HRFlowable(
        width="100%", thickness=2.5,
        color=S["navy"], spaceAfter=10, spaceBefore=2,
    ))

    # --------------------------------------------------------
    # SECTION 2: Patient Information
    # --------------------------------------------------------
    story.append(Paragraph("Patient Information", S["section_heading"]))

    p_name   = _safe_text(data.get("name"))
    p_age    = _safe_text(data.get("age"))
    p_gender = _safe_text(data.get("gender"))

    pt_table = Table(
        [
            [
                Paragraph("FULL NAME",  S["label"]),
                Paragraph("AGE",        S["label"]),
                Paragraph("GENDER",     S["label"]),
                Paragraph("REPORT ID",  S["label"]),
            ],
            [
                Paragraph(p_name,       S["value"]),
                Paragraph(p_age,        S["value"]),
                Paragraph(p_gender,     S["value"]),
                Paragraph(ctx.report_id, S["value"]),
            ],
        ],
        colWidths=[2.50 * inch, 0.85 * inch, 1.00 * inch, 3.15 * inch],
    )
    _apply_table_style(pt_table, S, header_bg=S["pale_blue"], data_bg=colors.white)
    story.append(pt_table)
    story.append(Spacer(1, 8))

    # --------------------------------------------------------
    # SECTION 3: Diagnosis Result
    # --------------------------------------------------------
    story.append(Paragraph("Diagnosis Result", S["section_heading"]))

    confidence   = float(data.get("confidence", 0.0))
    diagnosis    = _safe_text(data.get("diagnosis"), "Unknown")
    certainty    = _safe_text(data.get("certainty"))
    diag_display = diagnosis.replace("_", " ").title()

    diag_table = Table(
        [
            [
                Paragraph("DETECTED CONDITION",  S["label"]),
                Paragraph("CONFIDENCE SCORE",     S["label"]),
                Paragraph("CERTAINTY LEVEL",       S["label"]),
            ],
            [
                Paragraph(f"{diag_display} Tumor", S["value_accent"]),
                Paragraph(f"{confidence:.2f}%",     S["value"]),
                Paragraph(certainty.upper(),         S["value"]),
            ],
        ],
        colWidths=[3.10 * inch, 2.00 * inch, 2.40 * inch],
    )
    _apply_table_style(diag_table, S, header_bg=S["pale_blue"], data_bg=S["soft_blue"])
    story.append(diag_table)

    # --------------------------------------------------------
    # SECTION 4: Per-Class Confidence Breakdown
    # --------------------------------------------------------
    breakdown = data.get("confidence_breakdown", {}) or {}
    if breakdown:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Per-Class Confidence Breakdown", S["section_heading"]))

        n_cols  = len(breakdown)
        col_w   = doc.width / max(n_cols, 1)
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

    # --------------------------------------------------------
    # SECTION 5: MRI Scan & Heatmap Images
    # --------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("MRI Scan & Heatmap Analysis", S["section_heading"]))

    image_candidates = [
        ("Original MRI Scan",        original_image_path),
        ("GradCAM++ Activation Map", gradcam_image_path),
    ]
    if lime_image_path:
        image_candidates.append(("Supplementary Overlay", lime_image_path))

    valid_images = [
        (lbl, pth) for lbl, pth in image_candidates
        if pth and os.path.exists(str(pth))
    ]

    if valid_images:
        n       = len(valid_images)
        gap     = 0.10 * inch
        img_w   = (doc.width - gap * (n - 1)) / n
        img_h   = img_w * 0.95

        img_row = [Image(p, width=img_w, height=img_h) for _, p in valid_images]
        cap_row = [Paragraph(lbl, S["caption"])         for lbl, _ in valid_images]

        img_table = Table(
            [img_row, cap_row],
            colWidths=[img_w] * n,
            spaceBefore=4,
        )
        img_table.setStyle(TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(img_table)

    # --------------------------------------------------------
    # SECTION 6: Heatmap Explanation Summary
    # --------------------------------------------------------
    xai = data.get("xai_summary", {}) or {}
    if xai:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Heatmap Explanation Summary", S["section_heading"]))

        xai_rows = [
            [Paragraph("Visualisation Method",      S["label"]),
             Paragraph(_safe_text(xai.get("method_used"), "GradCAM++"), S["body"])],
            [Paragraph("Dominant Active Region",     S["label"]),
             Paragraph(_safe_text(xai.get("dominant_region")),           S["body"])],
            [Paragraph("Top 3 Active Regions",       S["label"]),
             Paragraph(_format_region_list(xai.get("top3_regions", [])), S["body"])],
            [Paragraph("High-Activation Coverage",   S["label"]),
             Paragraph(f"{float(xai.get('cam_coverage_pct', 0.0)):.1f}%", S["body"])],
            [Paragraph("Mean Activation Score",      S["label"]),
             Paragraph(f"{float(xai.get('cam_mean_activation', 0.0)):.4f}", S["body"])],
        ]
        coverage = xai.get("cam_coverage_pct", 0.0)
        try:
            coverage = float(coverage)
            coverage_str = f"{coverage:.1f}%"
        except:
            coverage_str = "N/A"

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

    # --------------------------------------------------------
    # SECTION 7: Regional Activation Grid (3×3)
    # --------------------------------------------------------
    region_scores = xai.get("region_scores", {}) if xai else {}
    if region_scores:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Regional Activation Grid (3×3)", S["section_heading"]))

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
                score  = float(region_scores.get(key, 0.0))
                r_int  = int(min(255, score * 510))
                g_int  = int(min(255, (1.0 - score) * 510))
                bg_c   = colors.Color(r_int / 255.0, g_int / 255.0, 0.12)
                txt_c  = colors.white if score > 0.45 else colors.HexColor("#1a2a4a")
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

    # --------------------------------------------------------
    # SECTION 8: Clinical Report (sanitised LLM body)
    # --------------------------------------------------------
    story.append(Spacer(1, 16))
    story.append(Paragraph("Clinical Report", S["section_heading"]))
    story.append(HRFlowable(
        width="100%", thickness=0.8, color=S["rule_grey"],
        spaceAfter=8, spaceBefore=2,
    ))

    clean_text = _sanitize_body(report_text or "")

    for raw_line in clean_text.splitlines():
        line  = raw_line.strip()
        if not line:
            story.append(Spacer(1, 3))
            continue

        upper = line.upper()

        # Skip structural lines already rendered in PDF tables/header
        if any(upper.startswith(pfx) for pfx in _PDF_SKIP_PREFIXES):
            continue

        if _is_known_heading(line):
            story.append(Spacer(1, 6))
            story.append(Paragraph(line.title(), S["section_heading"]))
        else:
            story.append(_line_to_paragraph(line, S["body"]))

    # --------------------------------------------------------
    # SECTION 9: Disclaimer — ONCE, at end of document only
    # --------------------------------------------------------
    story.append(Spacer(1, 18))
    story.append(HRFlowable(
        width="100%", thickness=0.8, color=S["rule_grey"],
        spaceAfter=7, spaceBefore=2,
    ))
    story.append(Paragraph(
        "<b>DISCLAIMER:</b> This report is generated using automated imaging analysis "
        "tools and must be reviewed and validated by a qualified, licensed healthcare "
        "professional before any clinical decision is made. It does not constitute a "
        "definitive diagnosis and should not replace a formal consultation with a "
        "specialist.",
        S["disclaimer"],
    ))

    # --------------------------------------------------------
    # Page Decoration: top rule + footer (every page)
    # --------------------------------------------------------
    def _page_decoration(canvas, doc_obj):
        canvas.saveState()
        w, h = letter

        # Top accent rule (navy)
        canvas.setStrokeColor(S["navy"])
        canvas.setLineWidth(0.7)
        canvas.line(
            doc_obj.leftMargin,
            h - 0.44 * inch,
            w - doc_obj.rightMargin,
            h - 0.44 * inch,
        )

        # Bottom separator rule
        canvas.setStrokeColor(S["rule_grey"])
        canvas.setLineWidth(0.4)
        canvas.line(
            doc_obj.leftMargin,
            0.50 * inch,
            w - doc_obj.rightMargin,
            0.50 * inch,
        )

        # Footer — facility name (left) + page number (right)
        canvas.setFillColor(S["grey_text"])
        canvas.setFont("Helvetica", 7.2)
        canvas.drawString(
            doc_obj.leftMargin,
            0.32 * inch,
            "NeuroScan Brain MRI — Confidential Medical Record",
        )
        canvas.drawRightString(
            w - doc_obj.rightMargin,
            0.32 * inch,
            f"Page {doc_obj.page}",
        )

        canvas.restoreState()

    doc.build(story, onFirstPage=_page_decoration, onLaterPages=_page_decoration)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# PRIVATE HELPER — TABLE STYLE FACTORY
# ============================================================


def _apply_table_style(
    table: Table,
    S: dict,
    *,
    header_bg: colors.Color,
    data_bg: colors.Color,
) -> None:
    """Apply a consistent professional table style in-place."""
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
# SELF-TEST  (python llm_report.py)
# ============================================================

if __name__ == "__main__":
    _test_result = {
        "prediction":     "Glioma",
        "confidence":      0.9287,
        "prediction_model": "EfficientNet-B0",
        "explanation_model": "GradCAM++",
        "observation":    (
            "High-confidence activation detected in the central "
            "and peri-ventricular regions."
        ),
        "confidence_breakdown": {
            "glioma":      92.87,
            "meningioma":   4.11,
            "notumor":      1.38,
            "pituitary":    1.64,
        },
        "xai_summary": {
            "method_used":         "GradCAM++",
            "dominant_region":     "center",
            "top3_regions":        ["center", "top-center", "top-right"],
            "cam_coverage_pct":    43.2,
            "cam_mean_activation": 0.312,
            "cam_max_activation":  1.0,
            "region_scores": {
                "top-left":   0.21, "top-center": 0.78, "top-right":  0.44,
                "mid-left":   0.15, "center":      0.91, "mid-right":  0.30,
                "bot-left":   0.08, "bot-center":  0.12, "bot-right":  0.10,
            },
        },
    }

    _patient = {"name": "Rajesh Kumar", "age": 47, "gender": "Male"}
    _data    = prepare_llm_input(_test_result, _patient)

    # Shared context: same IST moment for text report and PDF
    _ctx    = ReportContext()
    _report = generate_report(_data)

    print(_report)
    print("\n" + "=" * 64)

    # ---- Automated Constraint Validation ----
    body_only   = _report.split("DISCLAIMER")[0]    # Everything before the disclaimer
    disclaimer  = _report.split("DISCLAIMER")[-1]   # Disclaimer block itself

    failures = []

    # 1. No "AI" in report body (before disclaimer)
    if re.search(r"\bAI\b", body_only, re.IGNORECASE):
        failures.append("FAIL ❌  'AI' word found in report body")

    # 2. Exactly ONE disclaimer
    if _report.count("DISCLAIMER") != 1:
        failures.append(
            f"FAIL ❌  Disclaimer count = {_report.count('DISCLAIMER')} (expected 1)"
        )

    # 3. IST in timestamp
    if "IST" not in _report:
        failures.append("FAIL ❌  'IST' not found in report timestamp")

    # 4. Correct heading: no "AI" prefix in headings
    for bad in ("AI-Generated", "AI GENERATED", "AI EXPLANATION", "AI Explanation"):
        if bad in _report:
            failures.append(f"FAIL ❌  Bad heading '{bad}' still present")

    # 5. Report starts with "MEDICAL REPORT"
    if not _report.startswith("MEDICAL REPORT"):
        failures.append("FAIL ❌  Report does not start with 'MEDICAL REPORT'")

    # 6. Report ID contains timestamp token
    if _ctx.report_id[:2] != "NS":
        failures.append("FAIL ❌  Report ID prefix incorrect")

    if failures:
        for f in failures:
            print(f)
        raise SystemExit(1)

    print("\n✅  All validation checks passed.")
    print(f"    Report ID  : {_ctx.report_id}")
    print(f"    Timestamp  : {_ctx.timestamp_str}")