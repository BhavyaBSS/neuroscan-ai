# # src/llm_report.py
# st.cache_data.clear()
# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib import colors
# from reportlab.lib.units import inch
# from datetime import datetime
# import pytz

# def get_current_time():
#     ist = pytz.timezone("Asia/Kolkata")
#     return datetime.now(ist).strftime("%d-%m-%Y %H:%M:%S")

# report_time = get_current_time()

# import os
# import io
# import streamlit as st
# from openai import OpenAI
# import re

# client = OpenAI(
#     api_key=st.secrets["GROQ_API_KEY"], 
#     base_url="https://api.groq.com/openai/v1"
# )

# # ============================================================
# # PREPARE LLM INPUT
# # ============================================================
# def prepare_llm_input(result, patient_info=None):
#     confidence_percent = result["confidence"] * 100

#     if confidence_percent < 70:
#         certainty = "low"
#     elif confidence_percent < 90:
#         certainty = "moderate"
#     else:
#         certainty = "high"


#     data = {
#         "diagnosis":         result["prediction"],
#         "confidence":        confidence_percent,
#         "certainty":         certainty,
#         "prediction_model":  result["prediction_model"],
#         "explanation_model": result["explanation_model"],
#         "observation":       result.get("observation", "Highlighted regions indicate abnormal patterns"),
#         "xai_summary":            result.get("xai_summary", {}),
#         "confidence_breakdown":   result.get("confidence_breakdown", {}),
#         # "tumor_size":        result.get("tumor_size", {}),
#         # "tumor_size_str":    tumor_size_str,
#     }

#     if patient_info:
#         data.update(patient_info)

#     return data


# # ============================================================
# # GENERATE LLM REPORT
# # ============================================================
# def generate_report(data):
#     try:
#         patient_context = ""
#         if data.get("name"):
#             patient_context = f"""
#         Patient Name: {data.get('name', 'N/A')}
#         Age: {data.get('age', 'N/A')}
#         Gender: {data.get('gender', 'N/A')}
#         """

#         # Build XAI context paragraph for the prompt
#         xai = data.get("xai_summary", {})
#         xai_context = ""
#         if xai:
#             xai_context = f"""
#         XAI Analysis:
#           - Method: {xai.get('method_used', 'GradCAM++')}
#           - Most active brain region: {xai.get('dominant_region', 'N/A')}
#           - Top 3 regions: {', '.join(xai.get('top3_regions', []))}
#           - High-activation coverage: {xai.get('cam_coverage_pct', 'N/A')}%
#         """

#         breakdown = data.get("confidence_breakdown", {})
#         breakdown_str = ""
#         if breakdown:
#             breakdown_str = "Per-class scores: " + ", ".join(
#                 f"{k}: {v:.1f}%" for k, v in breakdown.items()
#             )

#         prompt = f"""
#         You are an AI medical assistant writing a report for a PATIENT (not a doctor).
#         Use simple, clear, everyday language that anyone can understand. Avoid complex medical jargon.

#         {patient_context}
#         Diagnosis: {data['diagnosis']} tumor
#         Confidence: {data['confidence']:.2f}%  ({breakdown_str})
#         Certainty Level: {data['certainty']}
#         AI Model Used: {data['prediction_model']}
#         What the scan shows: {data['observation']}

#         # Tumor Size Information: {data.get('tumor_size_str', 'Not available')}

#         {xai_context}

#         Write a report with EXACTLY these 5 sections using these exact headings:

#         **SUMMARY**
#         In 2-3 simple sentences, explain what was found including the tumor size category if available.

#         **WHAT THIS MEANS**
#         Explain what this type of tumor is in simple terms. Mention the estimated size and what 
#         that might mean for the patient. What part of the brain is affected?
#         Mention which region the AI focused on during analysis and what that suggests.

#         **EXPLANATION (HOW TUMOR IS DECIDED)**
#         In plain language, explain what the GradCAM++ heatmap showed. Mention the brain region the
#         heatmap highlighted. Keep it simple and reassuring.

#         **WHAT TO DO NEXT**
#         Give 3-4 clear action steps the patient should take. Be specific and practical.

#         **IMPORTANT DISCLAIMER**
#         Brief note: this is an AI-generated report and must be reviewed by a qualified doctor.

#         Keep the entire report under 500 words. Be warm, clear, and supportive in tone.
#         """

#         response = client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "user", "content": prompt}]
#         )

#         return response.choices[0].message.content

#     except Exception as e:
#         print("LLM ERROR:", e)
#         return "Report generation failed. Check API key or encoding."


# # ============================================================
# # GENERATE PDF
# # ============================================================
# def generate_pdf(data, report_text, original_image_path, gradcam_image_path, lime_image_path=None):
#     """Generate a professional PDF report and return it as bytes."""
    
#     # DEBUG - remove after fix
#     # print("DEBUG tumor_size in generate_pdf:", data.get("tumor_size"))
    
#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(
#         buffer,
#         pagesize=letter,
#         rightMargin=0.75*inch,
#         leftMargin=0.75*inch,
#         topMargin=0.75*inch,
#         bottomMargin=0.75*inch
#     )

#     styles = getSampleStyleSheet()

#     # ── Custom styles ────────────────────────────────────────
#     title_style = ParagraphStyle(
#         'CustomTitle', parent=styles['Title'],
#         fontSize=22, textColor=colors.HexColor('#1a1a2e'),
#         spaceAfter=4, fontName='Helvetica-Bold'
#     )
#     subtitle_style = ParagraphStyle(
#         'Subtitle', parent=styles['Normal'],
#         fontSize=11, textColor=colors.HexColor('#666666'), spaceAfter=2
#     )
#     section_heading = ParagraphStyle(
#         'SectionHeading', parent=styles['Heading2'],
#         fontSize=13, textColor=colors.HexColor('#1a1a2e'),
#         spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold'
#     )
#     body_style = ParagraphStyle(
#         'CustomBody', parent=styles['Normal'],
#         fontSize=10, leading=15, textColor=colors.HexColor('#333333'), spaceAfter=6
#     )
#     label_style = ParagraphStyle(
#         'Label', parent=styles['Normal'],
#         fontSize=9, textColor=colors.HexColor('#888888'), fontName='Helvetica'
#     )
#     value_style = ParagraphStyle(
#         'Value', parent=styles['Normal'],
#         fontSize=11, textColor=colors.HexColor('#1a1a2e'), fontName='Helvetica-Bold'
#     )
#     xai_label_style = ParagraphStyle(
#         'XAILabel', parent=styles['Normal'],
#         fontSize=9, textColor=colors.HexColor('#555555'), fontName='Helvetica-Bold'
#     )
#     xai_value_style = ParagraphStyle(
#         'XAIValue', parent=styles['Normal'],
#         fontSize=9, textColor=colors.HexColor('#1a1a2e'), fontName='Helvetica'
#     )
#     img_caption_style = ParagraphStyle(
#         'ImgCaption', parent=styles['Normal'],
#         fontSize=9, alignment=1, textColor=colors.HexColor('#555555')
#     )

#     story = []

#     # ── Header ──────────────────────────────────────────────
#     story.append(Paragraph("Brain Tumor Detection Report", title_style))
#     story.append(Paragraph(
#         f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
#         subtitle_style
#     ))
#     story.append(HRFlowable(width="100%", thickness=2,
#                              color=colors.HexColor('#1a1a2e'), spaceAfter=12))

#     # ── Patient Info ─────────────────────────────────────────
#     story.append(Paragraph("Patient Information", section_heading))

#     patient_data = [
#         [Paragraph("Name", label_style), Paragraph("Age", label_style),
#          Paragraph("Gender", label_style), Paragraph("Report ID", label_style)],
#         [Paragraph(str(data.get('name', 'N/A')), value_style),
#          Paragraph(str(data.get('age', 'N/A')), value_style),
#          Paragraph(str(data.get('gender', 'N/A')), value_style),
#          Paragraph(datetime.now().strftime('%Y%m%d%H%M'), value_style)],
#     ]
#     patient_table = Table(patient_data, colWidths=[1.7*inch, 1.2*inch, 1.2*inch, 2*inch])
#     patient_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f2f5')),
#         ('BACKGROUND', (0, 1), (-1, 1), colors.white),
#         ('BOX',        (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
#         ('INNERGRID',  (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
#         ('TOPPADDING',    (0, 0), (-1, -1), 8),
#         ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
#         ('LEFTPADDING',   (0, 0), (-1, -1), 10),
#     ]))
#     story.append(patient_table)

#     # ── Diagnosis Result ─────────────────────────────────────
#     story.append(Paragraph("Diagnosis Result", section_heading))

#     confidence  = data.get('confidence', 0)
#     diagnosis   = data.get('diagnosis', 'Unknown')
#     certainty   = data.get('certainty', 'N/A')
#     breakdown   = data.get('confidence_breakdown', {})

#     diag_data = [
#         [Paragraph("Detected Condition", label_style),
#          Paragraph("Confidence Score", label_style),
#          Paragraph("Certainty Level", label_style)],
#         [Paragraph(f"{diagnosis.upper()} Tumor", value_style),
#          Paragraph(f"{confidence:.2f}%", value_style),
#          Paragraph(certainty.upper(), value_style)],
#     ]
#     diag_table = Table(diag_data, colWidths=[2.3*inch, 2*inch, 2*inch])
#     diag_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f2f5')),
#         ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e8f4fd')),
#         ('BOX',       (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
#         ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
#         ('TOPPADDING',    (0, 0), (-1, -1), 8),
#         ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
#         ('LEFTPADDING',   (0, 0), (-1, -1), 10),
#     ]))
#     story.append(diag_table)

#     # ── Per-class confidence bar table ───────────────────────
#     if breakdown:
#         story.append(Spacer(1, 6))
#         story.append(Paragraph("Per-Class Confidence Breakdown", xai_label_style))
#         story.append(Spacer(1, 4))

#         bd_header = [Paragraph(cls.capitalize(), label_style) for cls in breakdown.keys()]
#         bd_values = [Paragraph(f"{v:.1f}%", value_style) for v in breakdown.values()]

#         bd_table = Table(
#             [bd_header, bd_values],
#             colWidths=[1.6*inch] * len(breakdown)
#         )
#         bd_table.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f2f5')),
#             ('BOX',       (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
#             ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
#             ('TOPPADDING',    (0, 0), (-1, -1), 6),
#             ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
#             ('LEFTPADDING',   (0, 0), (-1, -1), 8),
#             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ]))
#         story.append(bd_table)

#     # ── MRI Images ───────────────────────────────────────────
#     story.append(Paragraph("MRI Scan & Grad-CAM++ Analysis", section_heading))

#     img_width  = 3.1 * inch  # Made slightly larger since we now only have 2 images
#     img_height = 3.1 * inch

#     images_row   = []
#     captions_row = []

#     def _add_img(path, caption):
#         if path and os.path.exists(path):
#             images_row.append(Image(path, width=img_width, height=img_height))
#         else:
#             images_row.append(Paragraph("N/A", body_style))
#         captions_row.append(Paragraph(caption, img_caption_style))

#     _add_img(original_image_path,  "Original MRI Scan")
#     _add_img(gradcam_image_path,   "Grad-CAM++ Heatmap\n(Red = focus area)")

#     n_cols     = len(images_row)
#     col_w      = 3.3 * inch
#     img_table  = Table([images_row, captions_row], colWidths=[col_w] * n_cols)
#     img_table.setStyle(TableStyle([
#         ('ALIGN',   (0, 0), (-1, -1), 'CENTER'),
#         ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
#         ('TOPPADDING',    (0, 0), (-1, -1), 6),
#         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
#     ]))
#     story.append(img_table)


#     # ── XAI SECTION ──────────────────────────────────────────
#     xai = data.get("xai_summary", {})
#     if xai:
#         story.append(Paragraph("Explainable AI (XAI) Analysis", section_heading))
#         story.append(HRFlowable(width="100%", thickness=1,
#                                  color=colors.HexColor('#dddddd'), spaceAfter=6))

#         # Summary metrics table
#         xai_rows = [
#             [Paragraph("XAI Methods Used", xai_label_style),
#              Paragraph(str(xai.get("method_used", "GradCAM++")), xai_value_style)],
#             [Paragraph("Dominant Activation Region", xai_label_style),
#              Paragraph(str(xai.get("dominant_region", "N/A")), xai_value_style)],
#             [Paragraph("Top 3 Active Regions", xai_label_style),
#              Paragraph(", ".join(xai.get("top3_regions", [])) or "N/A", xai_value_style)],
#             [Paragraph("High-Activation Coverage", xai_label_style),
#              Paragraph(f"{xai.get('cam_coverage_pct', 0):.1f}% of scan", xai_value_style)],
#             [Paragraph("Mean CAM Activation", xai_label_style),
#              Paragraph(f"{xai.get('cam_mean_activation', 0):.4f}", xai_value_style)]
#         ]

#         xai_table = Table(xai_rows, colWidths=[2.4*inch, 4.2*inch])
#         xai_table.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
#             ('BOX',       (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
#             ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
#             ('TOPPADDING',    (0, 0), (-1, -1), 7),
#             ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
#             ('LEFTPADDING',   (0, 0), (-1, -1), 10),
#             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#         ]))
#         story.append(xai_table)

#         # Region heat-map grid (text-based)
#         region_scores = xai.get("region_scores", {})
#         if region_scores:
#             story.append(Spacer(1, 10))
#             story.append(Paragraph("Brain Regional Activation Grid (3×3)", xai_label_style))
#             story.append(Spacer(1, 4))

#             grid_order = [
#                 ["top-left",  "top-center",  "top-right"],
#                 ["mid-left",  "center",       "mid-right"],
#                 ["bot-left",  "bot-center",   "bot-right"],
#             ]
#             grid_data = []
#             for row_keys in grid_order:
#                 row = []
#                 for key in row_keys:
#                     score = region_scores.get(key, 0)
#                     # Color intensity: green → yellow → red
#                     r = int(min(255, score * 510))
#                     g = int(min(255, (1 - score) * 510))
#                     cell_color = colors.Color(r/255, g/255, 0.1)
#                     cell_text  = Paragraph(
#                         f"<b>{key}</b><br/>{score:.3f}",
#                         ParagraphStyle('grid', parent=styles['Normal'],
#                                        fontSize=8, alignment=1,
#                                        textColor=colors.white
#                                        if score > 0.4 else colors.HexColor('#222'))
#                     )
#                     row.append(cell_text)
#                 grid_data.append(row)

#             region_table = Table(grid_data, colWidths=[2.1*inch]*3)
#             # Apply per-cell background colors
#             ts = TableStyle([
#                 ('BOX',       (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
#                 ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
#                 ('ALIGN',  (0, 0), (-1, -1), 'CENTER'),
#                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#                 ('TOPPADDING',    (0, 0), (-1, -1), 10),
#                 ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
#             ])
#             for ri, row_keys in enumerate(grid_order):
#                 for ci, key in enumerate(row_keys):
#                     score = region_scores.get(key, 0)
#                     r_int = int(min(255, score * 510))
#                     g_int = int(min(255, (1 - score) * 510))
#                     ts.add('BACKGROUND', (ci, ri), (ci, ri),
#                            colors.Color(r_int/255, g_int/255, 0.1))
#             region_table.setStyle(ts)
#             story.append(region_table)

#     # ── AI Report ────────────────────────────────────────────
#     story.append(Paragraph("Medical Report", section_heading))
#     story.append(HRFlowable(width="100%", thickness=1,
#                              color=colors.HexColor('#dddddd'), spaceAfter=8))

#     for line in report_text.split('\n'):
#         line = line.strip()
#         if not line:
#             story.append(Spacer(1, 4))
#         elif line.startswith('**') and line.endswith('**'):
#             heading_text = line.replace('**', '')
#             story.append(Paragraph(heading_text, section_heading))
#         else:
#             # Convert markdown bold to ReportLab bold tags
#             clean = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
#             story.append(Paragraph(clean, body_style))

#     # ── Footer ───────────────────────────────────────────────
#     story.append(Spacer(1, 16))
#     story.append(HRFlowable(width="100%", thickness=1,
#                              color=colors.HexColor('#cccccc'), spaceAfter=6))
#     story.append(Paragraph(
#         "This report was generated by an AI system and is intended for informational purposes only. "
#         "It is NOT a substitute for professional medical advice, diagnosis, or treatment. "
#         "Please consult a qualified healthcare provider before making any medical decisions.",
#         ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
#                        textColor=colors.HexColor('#999999'), alignment=1)
#     ))

#     doc.build(story)
#     buffer.seek(0)
#     return buffer.getvalue()


# # ============================================================
# # TEST
# # ============================================================
# if __name__ == "__main__":
#     test_result = {
#         "prediction": "Glioma",
#         "confidence": 0.92,
#         "prediction_model": "EfficientNet-B0",
#         "explanation_model": "ResNet50 (GradCAM++)",
#         "observation": "GradCAM++ highlights top-center region with 43.2% high-activation coverage.",
#         "confidence_breakdown": {
#             "glioma": 92.0, "meningioma": 5.1, "notumor": 1.4, "pituitary": 1.5
#         },
#         "xai_summary": {
#             "method_used": "GradCAM++",
#             "dominant_region": "top-center",
#             "top3_regions": ["top-center", "center", "top-right"],
#             "cam_coverage_pct": 43.2,
#             "cam_mean_activation": 0.312,
#             "cam_max_activation": 1.0,
#             "region_scores": {
#                 "top-left": 0.21, "top-center": 0.78, "top-right": 0.44,
#                 "mid-left": 0.15, "center": 0.51, "mid-right": 0.30,
#                 "bot-left": 0.08, "bot-center": 0.12, "bot-right": 0.10
#             }
#         }
#     }
#     patient_info = {"name": "John Doe", "age": 45, "gender": "Male"}
#     data   = prepare_llm_input(test_result, patient_info)
#     report = generate_report(data)
#     print(report)

# src/llm_report.py

# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib import colors
# from reportlab.lib.units import inch
# from datetime import datetime
# import pytz
# import os
# import io
# import streamlit as st
# from openai import OpenAI
# import re


# # ============================================================
# # TIME FUNCTION (FIXED)
# # ============================================================
# def get_current_time():
#     ist = pytz.timezone("Asia/Kolkata")
#     return datetime.now(ist).strftime("%d-%m-%Y %H:%M:%S")


# # ============================================================
# # LLM CLIENT
# # ============================================================
# client = OpenAI(
#     api_key=st.secrets["GROQ_API_KEY"],
#     base_url="https://api.groq.com/openai/v1"
# )


# # ============================================================
# # PREPARE INPUT
# # ============================================================
# def prepare_llm_input(result, patient_info=None):
#     confidence_percent = result["confidence"] * 100

#     if confidence_percent < 70:
#         certainty = "low"
#     elif confidence_percent < 90:
#         certainty = "moderate"
#     else:
#         certainty = "high"

#     data = {
#         "diagnosis": result["prediction"],
#         "confidence": confidence_percent,
#         "certainty": certainty,
#         "prediction_model": result["prediction_model"],
#         "observation": result.get("observation", "Abnormal patterns detected"),
#         "xai_summary": result.get("xai_summary", {}),
#         "confidence_breakdown": result.get("confidence_breakdown", {}),
#     }

#     if patient_info:
#         data.update(patient_info)

#     return data


# # ============================================================
# # GENERATE REPORT (FIXED)
# # ============================================================
# def generate_report(data):
#     try:
#         patient_context = f"""
# Patient Name: {data.get('name', 'N/A')}
# Age: {data.get('age', 'N/A')}
# Gender: {data.get('gender', 'N/A')}
# """

#         xai = data.get("xai_summary", {})
#         xai_context = ""
#         if xai:
#             xai_context = f"""
# XAI Analysis:
# - Dominant Region: {xai.get('dominant_region', 'N/A')}
# - Top Regions: {', '.join(xai.get('top3_regions', []))}
# - Coverage: {xai.get('cam_coverage_pct', 'N/A')}%
# """

#         prompt = f"""
# You are a clinical report writer.

# STRICT RULES:
# - DO NOT use words like "AI", "model", "algorithm"
# - Use formal medical language
# - Be concise and structured
# - Use headings: SUMMARY, FINDINGS, IMPRESSION, RECOMMENDATION

# {patient_context}

# Findings:
# Condition: {data['diagnosis']}
# Confidence: {data['confidence']:.2f}%
# Certainty: {data['certainty']}
# Observations: {data['observation']}

# {xai_context}

# Generate a professional clinical report.
# """

#         response = client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "user", "content": prompt}]
#         )

#         llm_text = response.choices[0].message.content

#         # ✅ Add disclaimer manually
#         final_report = f"""
# NEUROSCAN MRI REPORT
# Generated On: {get_current_time()}

# ----------------------------------------

# {llm_text}

# ----------------------------------------

# DISCLAIMER:
# This report is generated using AI assistance and must be reviewed by a qualified healthcare professional.
# """

#         return final_report

#     except Exception as e:
#         print("LLM ERROR:", e)
#         return "Report generation failed."


# # ============================================================
# # GENERATE PDF (FIXED TIME + CLEAN)
# # ============================================================
# def generate_pdf(data, report_text, original_image_path, gradcam_image_path):

#     buffer = io.BytesIO()

#     doc = SimpleDocTemplate(
#         buffer,
#         pagesize=letter,
#         rightMargin=0.75*inch,
#         leftMargin=0.75*inch,
#         topMargin=0.75*inch,
#         bottomMargin=0.75*inch
#     )

#     styles = getSampleStyleSheet()

#     title_style = ParagraphStyle(
#         'Title', parent=styles['Title'],
#         fontSize=20, textColor=colors.black
#     )

#     body_style = ParagraphStyle(
#         'Body', parent=styles['Normal'],
#         fontSize=10, leading=14
#     )

#     story = []

#     # Header
#     story.append(Paragraph("Brain Tumor MRI Report", title_style))
#     story.append(Paragraph(f"Generated on: {get_current_time()}", body_style))
#     story.append(Spacer(1, 12))

#     # Patient Info
#     story.append(Paragraph("Patient Information", styles['Heading2']))

#     patient_table = Table([
#         ["Name", data.get("name", "N/A")],
#         ["Age", data.get("age", "N/A")],
#         ["Gender", data.get("gender", "N/A")],
#     ])

#     story.append(patient_table)
#     story.append(Spacer(1, 12))

#     # Images
#     if os.path.exists(original_image_path):
#         story.append(Image(original_image_path, width=3*inch, height=3*inch))
#     if os.path.exists(gradcam_image_path):
#         story.append(Image(gradcam_image_path, width=3*inch, height=3*inch))

#     story.append(Spacer(1, 12))

#     # Report Text
#     for line in report_text.split("\n"):
#         story.append(Paragraph(line, body_style))

#     # Footer
#     story.append(Spacer(1, 12))
#     story.append(Paragraph(
#         "This report is generated using AI and must be verified by a doctor.",
#         styles['Normal']
#     ))

#     doc.build(story)
#     buffer.seek(0)
#     return buffer.getvalue()

# src/llm_report.py

from datetime import datetime
from zoneinfo import ZoneInfo
import io
import os
import re

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
# HELPERS
# ============================================================

def _get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


def get_current_time() -> str:
    """Return current time in IST."""
    ist = ZoneInfo("Asia/Kolkata")
    return datetime.now(ist).strftime("%d-%m-%Y %H:%M:%S")


def get_report_id() -> str:
    """Stable report id in IST timestamp format."""
    ist = ZoneInfo("Asia/Kolkata")
    return datetime.now(ist).strftime("%Y%m%d%H%M%S")


def _safe_text(value, default="N/A") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _capitalize_region_list(regions):
    if not regions:
        return "N/A"
    return ", ".join(str(r) for r in regions)


def _sanitize_report_text(text: str) -> str:
    """
    Remove/replace AI wording from the report body.
    Disclaimer is appended separately, so this function only cleans the LLM output.
    """
    if not text:
        return ""

    replacements = [
        ("AI-Generated Medical Report", "Medical Report"),
        ("AI GENERATED MEDICAL REPORT", "MEDICAL REPORT"),
        ("AI Explanation", "Explanation"),
        ("AI EXPLANATION", "EXPLANATION"),
        ("AI EXPLANATION (HOW THE AI DECIDED)", "Explanation (How Decision is Made)"),
        ("AI EXPLANATION (HOW THE MODEL DECIDED)", "Explanation (How Decision is Made)"),
        ("AI EXPLANATION (HOW THE SYSTEM DECIDED)", "Explanation (How Decision is Made)"),
        ("Our AI analysis", "Our analysis"),
        ("our AI analysis", "our analysis"),
        ("our AI", "our"),
        ("Our AI", "Our"),
        ("the AI", "the system"),
        ("the AI-based", "the"),
        ("AI-based", "automated"),
        ("AI analysis", "analysis"),
        ("AI used", "analysis used"),
        ("AI decided", "decision was made"),
        ("AI decided.", "decision was made."),
        ("AI decides", "decision is made"),
        ("AI generated", "generated"),
        ("AI-generated", "generated"),
    ]

    cleaned = text
    for old, new in replacements:
        cleaned = cleaned.replace(old, new)

    # Remove any leftover standalone "AI" tokens from the body.
    cleaned = re.sub(r"\bAI\b", "", cleaned, flags=re.IGNORECASE)

    # Remove any duplicated spaces caused by replacements.
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def _looks_like_heading(line: str) -> bool:
    normalized = line.strip().upper()
    headings = {
        "MEDICAL REPORT",
        "SUMMARY",
        "WHAT THIS MEANS",
        "EXPLANATION (HOW DECISION IS MADE)",
        "WHAT TO DO NEXT",
    }
    return normalized in headings


def _line_to_paragraph(line: str, body_style: ParagraphStyle) -> Paragraph:
    """
    Convert a line to a ReportLab paragraph while preserving simple markdown-like bullets.
    """
    text = line.strip()

    # Convert markdown bold to ReportLab bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # Bullets
    if text.startswith("- "):
        text = "&bull; " + text[2:].strip()

    return Paragraph(text, body_style)


# ============================================================
# LLM CLIENT
# ============================================================

_api_key = _get_secret("GROQ_API_KEY", "")
client = OpenAI(
    api_key=_api_key if _api_key else None,
    base_url="https://api.groq.com/openai/v1",
)


# ============================================================
# PREPARE LLM INPUT
# ============================================================

def prepare_llm_input(result, patient_info=None):
    confidence_percent = float(result.get("confidence", 0.0)) * 100.0

    if confidence_percent < 70:
        certainty = "low"
    elif confidence_percent < 90:
        certainty = "moderate"
    else:
        certainty = "high"

    data = {
        "diagnosis": result.get("prediction", "Unknown"),
        "confidence": confidence_percent,
        "certainty": certainty,
        "prediction_model": result.get("prediction_model", "EfficientNet-B0"),
        "explanation_model": result.get("explanation_model", "GradCAM++"),
        "observation": result.get("observation", "Abnormal patterns detected."),
        "xai_summary": result.get("xai_summary", {}),
        "confidence_breakdown": result.get("confidence_breakdown", {}),
    }

    if patient_info:
        data.update(patient_info)

    return data


# ============================================================
# GENERATE LLM REPORT
# ============================================================

def generate_report(data):
    """
    Generate a clean, clinical-style report.

    Rules enforced:
    - No use of the word "AI" in the report body.
    - No disclaimer in the LLM output.
    - One disclaimer appended at the end by this function.
    - Output should follow a medical-report style.
    """
    try:
        if client is None:
            raise RuntimeError("GROQ_API_KEY is missing or not configured.")

        patient_name = _safe_text(data.get("name"), "N/A")
        age = _safe_text(data.get("age"), "N/A")
        gender = _safe_text(data.get("gender"), "N/A")

        diagnosis = _safe_text(data.get("diagnosis"), "Unknown")
        confidence = float(data.get("confidence", 0.0))
        certainty = _safe_text(data.get("certainty"), "N/A")
        observation = _safe_text(data.get("observation"), "N/A")

        xai = data.get("xai_summary", {}) or {}
        method_used = _safe_text(xai.get("method_used"), "GradCAM++")
        dominant_region = _safe_text(xai.get("dominant_region"), "N/A")
        top3_regions = _capitalize_region_list(xai.get("top3_regions", []))
        cam_coverage = xai.get("cam_coverage_pct", "N/A")

        breakdown = data.get("confidence_breakdown", {}) or {}
        breakdown_str = ""
        if breakdown:
            breakdown_str = ", ".join(f"{k}: {v:.1f}%" for k, v in breakdown.items())

        # We tell the LLM exactly what to output.
        # No "AI" word in the body. No disclaimer in the body.
        prompt = f"""
You are writing a professional MRI brain medical report.

STRICT RULES:
- Do NOT use the words "AI", "model", or "algorithm" anywhere in the report body.
- Do NOT write a disclaimer section.
- Use formal, concise, clinical language.
- Use ONLY the following headings, in this exact order:
  1. SUMMARY
  2. WHAT THIS MEANS
  3. EXPLANATION (HOW DECISION IS MADE)
  4. WHAT TO DO NEXT
- Keep the language medical and professional, but still understandable.
- Mention that the analysis is highly confident in this diagnosis.
- Use "Our analysis is highly confident in this diagnosis." if appropriate.
- Do not mention code, prompt, system, or implementation details.
- Do not mention the word "AI" anywhere in the body.

Patient Information:
Name: {patient_name}
Age: {age}
Gender: {gender}

Clinical Findings:
Diagnosis: {diagnosis}
Confidence: {confidence:.2f}%
Certainty: {certainty}
Observation: {observation}

XAI / Heatmap Information:
Method: {method_used}
Dominant Region: {dominant_region}
Top Regions: {top3_regions}
Coverage: {cam_coverage}%

Class Breakdown:
{breakdown_str if breakdown_str else "Not available"}

Write a structured report with:
- SUMMARY: 2-3 concise sentences
- WHAT THIS MEANS: explain the likely condition and anatomical relevance
- EXPLANATION (HOW DECISION IS MADE): explain the heatmap interpretation without using the word AI
- WHAT TO DO NEXT: give 3-4 practical clinical follow-up suggestions

Do not include any disclaimer. Do not repeat the title at the end.
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=900,
        )

        llm_text = response.choices[0].message.content or ""
        llm_text = _sanitize_report_text(llm_text)

        report_time = get_current_time()

        final_report = f"""MEDICAL REPORT
Generated On: {report_time}

SUMMARY
{llm_text}
"""

        # The LLM may already emit headings; to keep the output clean and readable,
        # we prepend the title/time, then append the disclaimer only once.
        final_report += f"""

DISCLAIMER
This report is generated using automated analysis and must be reviewed by a qualified healthcare professional before any clinical decision is made.
"""

        return final_report.strip()

    except Exception as e:
        print("LLM ERROR:", e)
        return "Report generation failed. Check API key or prompt settings."


# ============================================================
# GENERATE PDF
# ============================================================

def generate_pdf(data, report_text, original_image_path, gradcam_image_path, lime_image_path=None):
    """
    Generate an Apollo-style, polished PDF report and return it as bytes.
    Uses IST time everywhere and keeps the disclaimer only once.
    """

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.70 * inch,
        bottomMargin=0.65 * inch,
    )

    styles = getSampleStyleSheet()

    # Colors
    navy = colors.HexColor("#1f2a44")
    deep_navy = colors.HexColor("#172033")
    soft_blue = colors.HexColor("#eef5ff")
    light_blue = colors.HexColor("#f7fbff")
    grey_text = colors.HexColor("#4b5563")
    light_grey = colors.HexColor("#e5e7eb")
    accent = colors.HexColor("#0ea5e9")

    # Styles
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=navy,
        alignment=0,
        spaceAfter=2,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=12,
        textColor=grey_text,
        spaceAfter=8,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=navy,
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14.5,
        textColor=colors.HexColor("#2f3747"),
        spaceAfter=5,
    )

    small_body = ParagraphStyle(
        "SmallBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=grey_text,
    )

    label_style = ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=grey_text,
    )

    value_style = ParagraphStyle(
        "ValueStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=navy,
    )

    caption_style = ParagraphStyle(
        "CaptionStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=grey_text,
    )

    disclaimer_style = ParagraphStyle(
        "DisclaimerStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.3,
        leading=11,
        textColor=colors.HexColor("#6b7280"),
        alignment=1,
    )

    report_text = _sanitize_report_text(report_text or "")
    generated_on = get_current_time()
    report_id = get_report_id()

    story = []

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------
    story.append(Paragraph("NeuroScan MRI Medical Report", title_style))
    story.append(Paragraph(f"Generated on {generated_on}  |  Report ID: {report_id}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=navy, spaceAfter=10))

    # --------------------------------------------------------
    # Patient Information
    # --------------------------------------------------------
    story.append(Paragraph("Patient Information", section_heading))

    patient_name = _safe_text(data.get("name"), "Demo Patient")
    age = data.get("age", "N/A")
    gender = _safe_text(data.get("gender"), "Unknown")

    patient_rows = [
        [
            Paragraph("Name", label_style),
            Paragraph("Age", label_style),
            Paragraph("Gender", label_style),
            Paragraph("Report ID", label_style),
        ],
        [
            Paragraph(patient_name, value_style),
            Paragraph(str(age), value_style),
            Paragraph(gender, value_style),
            Paragraph(report_id, value_style),
        ],
    ]

    patient_table = Table(
        patient_rows,
        colWidths=[2.15 * inch, 1.05 * inch, 1.20 * inch, 3.10 * inch],
    )
    patient_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), light_blue),
        ("BACKGROUND", (0, 1), (-1, 1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, light_grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, light_grey),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 10))

    # --------------------------------------------------------
    # Diagnosis Result
    # --------------------------------------------------------
    story.append(Paragraph("Diagnosis Result", section_heading))

    confidence = float(data.get("confidence", 0.0))
    diagnosis = _safe_text(data.get("diagnosis"), "Unknown")
    certainty = _safe_text(data.get("certainty"), "N/A")

    diagnosis_display = diagnosis.replace("_", " ").title()

    diag_rows = [
        [
            Paragraph("Detected Condition", label_style),
            Paragraph("Confidence Score", label_style),
            Paragraph("Certainty Level", label_style),
        ],
        [
            Paragraph(f"{diagnosis_display} Tumor", value_style),
            Paragraph(f"{confidence:.2f}%", value_style),
            Paragraph(certainty.upper(), value_style),
        ],
    ]

    diag_table = Table(
        diag_rows,
        colWidths=[3.05 * inch, 1.95 * inch, 2.50 * inch],
    )
    diag_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), light_blue),
        ("BACKGROUND", (0, 1), (-1, 1), soft_blue),
        ("BOX", (0, 0), (-1, -1), 0.6, light_grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, light_grey),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(diag_table)

    # --------------------------------------------------------
    # Confidence Breakdown
    # --------------------------------------------------------
    breakdown = data.get("confidence_breakdown", {}) or {}
    if breakdown:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Per-Class Confidence Breakdown", section_heading))

        cols = len(breakdown)
        available_width = doc.width
        col_width = available_width / max(cols, 1)

        bd_header = [Paragraph(str(cls).capitalize(), label_style) for cls in breakdown.keys()]
        bd_values = [Paragraph(f"{float(v):.1f}%", value_style) for v in breakdown.values()]

        bd_table = Table([bd_header, bd_values], colWidths=[col_width] * cols)
        bd_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), light_blue),
            ("BACKGROUND", (0, 1), (-1, 1), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.6, light_grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, light_grey),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(bd_table)

    # --------------------------------------------------------
    # MRI Images
    # --------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("MRI Scan & Heatmap Analysis", section_heading))

    image_items = [
        ("Original MRI Scan", original_image_path),
        ("Heatmap Overlay", gradcam_image_path),
    ]

    if lime_image_path:
        image_items.append(("Optional Additional Explanation", lime_image_path))

    existing_images = [(label, path) for label, path in image_items if path and os.path.exists(path)]

    if existing_images:
        n = len(existing_images)
        img_w = (doc.width - (0.12 * inch * (n - 1))) / n
        img_h = img_w * 0.95

        img_row = []
        cap_row = []

        for label, path in existing_images:
            img_row.append(Image(path, width=img_w, height=img_h))
            cap_row.append(Paragraph(label, caption_style))

        img_table = Table([img_row, cap_row], colWidths=[img_w] * n)
        img_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(img_table)

    # --------------------------------------------------------
    # XAI Summary
    # --------------------------------------------------------
    xai = data.get("xai_summary", {}) or {}
    if xai:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Explanation Summary", section_heading))

        xai_rows = [
            [Paragraph("Method", label_style), Paragraph(_safe_text(xai.get("method_used"), "GradCAM++"), body_style)],
            [Paragraph("Dominant Region", label_style), Paragraph(_safe_text(xai.get("dominant_region"), "N/A"), body_style)],
            [Paragraph("Top 3 Active Regions", label_style), Paragraph(_capitalize_region_list(xai.get("top3_regions", [])), body_style)],
            [Paragraph("High-Activation Coverage", label_style), Paragraph(f"{float(xai.get('cam_coverage_pct', 0.0)):.1f}%", body_style)],
            [Paragraph("Mean Activation", label_style), Paragraph(f"{float(xai.get('cam_mean_activation', 0.0)):.4f}", body_style)],
        ]

        xai_table = Table(xai_rows, colWidths=[2.20 * inch, 5.30 * inch])
        xai_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), light_blue),
            ("BOX", (0, 0), (-1, -1), 0.6, light_grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, light_grey),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(xai_table)

        # Optional 3x3 regional grid if available
        region_scores = xai.get("region_scores", {}) or {}
        if region_scores:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Regional Activation Grid (3×3)", section_heading))

            grid_order = [
                ["top-left", "top-center", "top-right"],
                ["mid-left", "center", "mid-right"],
                ["bot-left", "bot-center", "bot-right"],
            ]

            grid_data = []
            for row_keys in grid_order:
                row = []
                for key in row_keys:
                    score = float(region_scores.get(key, 0.0))
                    txt_color = colors.white if score > 0.40 else colors.HexColor("#202635")
                    cell_style = ParagraphStyle(
                        "GridCell",
                        parent=styles["Normal"],
                        fontName="Helvetica-Bold",
                        fontSize=8,
                        leading=10,
                        alignment=1,
                        textColor=txt_color,
                    )
                    row.append(Paragraph(f"{key}<br/>{score:.3f}", cell_style))
                grid_data.append(row)

            region_table = Table(grid_data, colWidths=[2.08 * inch] * 3)
            region_style = TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.6, light_grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, light_grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ])

            for ri, row_keys in enumerate(grid_order):
                for ci, key in enumerate(row_keys):
                    score = float(region_scores.get(key, 0.0))
                    r_int = int(min(255, score * 510))
                    g_int = int(min(255, (1 - score) * 510))
                    region_style.add(
                        "BACKGROUND",
                        (ci, ri),
                        (ci, ri),
                        colors.Color(r_int / 255.0, g_int / 255.0, 0.12),
                    )

            region_table.setStyle(region_style)
            story.append(region_table)

    # --------------------------------------------------------
    # LLM Report Body
    # --------------------------------------------------------
    story.append(Spacer(1, 12))
    story.append(Paragraph("Clinical Report", section_heading))
    story.append(HRFlowable(width="100%", thickness=1, color=light_grey, spaceAfter=8))

    for raw_line in report_text.splitlines():
        line = raw_line.strip()

        if not line:
            story.append(Spacer(1, 4))
            continue

        # Skip duplicated title/time if the LLM echoes them.
        upper_line = line.upper()
        if upper_line.startswith("MEDICAL REPORT"):
            continue
        if upper_line.startswith("GENERATED ON"):
            continue
        if upper_line.startswith("DISCLAIMER"):
            continue

        if _looks_like_heading(line):
            story.append(Spacer(1, 4))
            story.append(Paragraph(line, section_heading))
        else:
            story.append(_line_to_paragraph(line, body_style))

    # --------------------------------------------------------
    # Disclaimer (only once)
    # --------------------------------------------------------
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=light_grey, spaceAfter=6))
    story.append(
        Paragraph(
            "DISCLAIMER: This report is generated using automated analysis and must be reviewed by a qualified healthcare professional before any clinical decision is made.",
            disclaimer_style,
        )
    )

    # --------------------------------------------------------
    # Page decorations
    # --------------------------------------------------------
    def _decorate_page(canvas, doc_obj):
        canvas.saveState()
        width, height = letter

        # Top thin line
        canvas.setStrokeColor(deep_navy)
        canvas.setLineWidth(0.5)
        canvas.line(doc_obj.leftMargin, height - 0.45 * inch, width - doc_obj.rightMargin, height - 0.45 * inch)

        # Bottom footer line
        canvas.setStrokeColor(light_grey)
        canvas.line(doc_obj.leftMargin, 0.55 * inch, width - doc_obj.rightMargin, 0.55 * inch)

        # Footer text
        canvas.setFillColor(grey_text)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(doc_obj.leftMargin, 0.38 * inch, "NeuroScan MRI Medical Report")
        canvas.drawRightString(width - doc_obj.rightMargin, 0.38 * inch, f"Page {doc_obj.page}")

        canvas.restoreState()

    doc.build(story, onFirstPage=_decorate_page, onLaterPages=_decorate_page)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    test_result = {
        "prediction": "Glioma",
        "confidence": 0.9287,
        "prediction_model": "EfficientNet-B0",
        "explanation_model": "GradCAM++",
        "observation": "High-confidence pattern detected in the central region of the scan.",
        "confidence_breakdown": {
            "glioma": 92.0,
            "meningioma": 5.1,
            "notumor": 1.4,
            "pituitary": 1.5,
        },
        "xai_summary": {
            "method_used": "GradCAM++",
            "dominant_region": "center",
            "top3_regions": ["center", "top-center", "top-right"],
            "cam_coverage_pct": 43.2,
            "cam_mean_activation": 0.312,
            "cam_max_activation": 1.0,
            "region_scores": {
                "top-left": 0.21,
                "top-center": 0.78,
                "top-right": 0.44,
                "mid-left": 0.15,
                "center": 0.51,
                "mid-right": 0.30,
                "bot-left": 0.08,
                "bot-center": 0.12,
                "bot-right": 0.10,
            },
        },
    }

    patient_info = {"name": "John Doe", "age": 45, "gender": "Male"}
    data = prepare_llm_input(test_result, patient_info)
    report = generate_report(data)
    print(report)