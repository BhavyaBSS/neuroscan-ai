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

"""
llm_report.py
=============
Hospital-grade (Apollo-level) MRI Brain Tumor Report Generator.

Features
--------
- IST timezone throughout (text report, PDF, Report ID)
- Zero "AI" wording in report body (LLM-enforced + post-processing sanitiser)
- Single disclaimer, placed only at the end
- Correct section headings
- Professional clinical language
- Apollo-level PDF: header/footer, tables, heatmap, regional grid
- Fully modular, no global mutable state
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
_DATETIME_FMT = "%d-%m-%Y %H:%M:%S IST"
_REPORT_ID_FMT = "%Y%m%d%H%M%S"

# Words/phrases that must NEVER appear in the report body.
# Each entry: (pattern_to_replace, replacement)
_AI_REPLACEMENTS: list[tuple[str, str]] = [
    # Heading fixes
    ("AI-Generated Medical Report",             "Medical Report"),
    ("AI GENERATED MEDICAL REPORT",             "MEDICAL REPORT"),
    ("AI Explanation (How the AI Decided)",     "Explanation (How Decision is Made)"),
    ("AI Explanation (How the Model Decided)",  "Explanation (How Decision is Made)"),
    ("AI EXPLANATION (HOW THE AI DECIDED)",     "EXPLANATION (HOW DECISION IS MADE)"),
    ("AI EXPLANATION (HOW THE MODEL DECIDED)",  "EXPLANATION (HOW DECISION IS MADE)"),
    ("AI EXPLANATION (HOW THE SYSTEM DECIDED)", "EXPLANATION (HOW DECISION IS MADE)"),
    ("AI Explanation",                          "Explanation"),
    ("AI EXPLANATION",                          "EXPLANATION"),
    # Phrase fixes (longer first to avoid partial-match issues)
    ("Our AI analysis is highly confident",     "Our analysis is highly confident"),
    ("our AI analysis is highly confident",     "our analysis is highly confident"),
    ("Our AI analysis",                         "Our analysis"),
    ("our AI analysis",                         "our analysis"),
    ("the AI-based system",                     "the system"),
    ("the AI-based",                            "the"),
    ("AI-based analysis",                       "automated analysis"),
    ("AI-based",                                "automated"),
    ("AI analysis",                             "analysis"),
    ("AI-generated",                            "generated"),
    ("AI generated",                            "generated"),
    ("AI used",                                 "analysis used"),
    ("AI decided",                              "the decision was made"),
    ("AI decides",                              "the decision is made"),
    ("the AI",                                  "the system"),
    ("our AI",                                  "our"),
    ("Our AI",                                  "Our"),
]

_KNOWN_HEADINGS: frozenset[str] = frozenset({
    "SUMMARY",
    "FINDINGS",
    "IMPRESSION",
    "WHAT THIS MEANS",
    "EXPLANATION (HOW DECISION IS MADE)",
    "WHAT TO DO NEXT",
    "RECOMMENDATION",
})

# ============================================================
# HELPERS — TIME
# ============================================================


def _now_ist() -> datetime:
    """Return the current datetime in IST. Single source of truth."""
    return datetime.now(_IST)


def get_current_time() -> str:
    """Human-readable IST timestamp: DD-MM-YYYY HH:MM:SS IST"""
    return _now_ist().strftime(_DATETIME_FMT)


def get_report_id() -> str:
    """Unique report ID based on IST timestamp: YYYYMMDDHHMMSS"""
    return _now_ist().strftime(_REPORT_ID_FMT)


# ============================================================
# HELPERS — TEXT UTILITIES
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


def _sanitize_report_text(text: str) -> str:
    """
    Strip all AI-wording from LLM output (report body only).
    Disclaimer block is handled separately and never passed here.
    """
    if not text:
        return ""

    cleaned = text

    # Apply explicit string replacements first (case-sensitive)
    for old, new in _AI_REPLACEMENTS:
        cleaned = cleaned.replace(old, new)

    # Nuclear fallback: remove any remaining standalone "AI" tokens
    # Use word-boundary regex to avoid hitting words like "MAIN", "RAIN"
    cleaned = re.sub(r"\bAI\b", "", cleaned, flags=re.IGNORECASE)

    # Tidy up spacing artefacts
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def _is_heading(line: str) -> bool:
    return line.strip().upper() in _KNOWN_HEADINGS


def _line_to_paragraph(line: str, body_style: ParagraphStyle) -> Paragraph:
    """Convert a plain text line to a ReportLab Paragraph with light markdown support."""
    text = line.strip()
    # Bold: **text** → <b>text</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Bullet
    if text.startswith("- "):
        text = "&bull;&nbsp;" + text[2:].strip()
    return Paragraph(text, body_style)


# ============================================================
# LLM CLIENT  (lazy singleton — avoids module-level side effects)
# ============================================================

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = _get_secret("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured. "
                "Add it to Streamlit secrets or set the environment variable."
            )
        _client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


# ============================================================
# PREPARE DATA FOR LLM
# ============================================================


def prepare_llm_input(result: dict, patient_info: dict | None = None) -> dict:
    """Normalise raw model result + patient info into a flat dict for report generation."""
    confidence_pct = float(result.get("confidence", 0.0)) * 100.0

    if confidence_pct < 70:
        certainty = "Low"
    elif confidence_pct < 90:
        certainty = "Moderate"
    else:
        certainty = "High"

    data: dict = {
        "diagnosis":          result.get("prediction", "Unknown"),
        "confidence":         confidence_pct,
        "certainty":          certainty,
        "prediction_model":   result.get("prediction_model", "EfficientNet-B0"),
        "explanation_model":  result.get("explanation_model", "GradCAM++"),
        "observation":        result.get("observation", "Abnormal patterns detected."),
        "xai_summary":        result.get("xai_summary", {}),
        "confidence_breakdown": result.get("confidence_breakdown", {}),
    }

    if patient_info:
        data.update(patient_info)

    return data


# ============================================================
# LLM PROMPT
# ============================================================


def _build_prompt(data: dict) -> str:
    """
    Construct the LLM system + user prompt.
    The LLM is explicitly forbidden from using 'AI', 'model', or 'algorithm'.
    No disclaimer should appear in the LLM output.
    """
    patient_name = _safe_text(data.get("name"))
    age          = _safe_text(data.get("age"))
    gender       = _safe_text(data.get("gender"))
    diagnosis    = _safe_text(data.get("diagnosis"), "Unknown")
    confidence   = float(data.get("confidence", 0.0))
    certainty    = _safe_text(data.get("certainty"))
    observation  = _safe_text(data.get("observation"))

    xai = data.get("xai_summary", {}) or {}
    method       = _safe_text(xai.get("method_used"), "GradCAM++")
    dom_region   = _safe_text(xai.get("dominant_region"))
    top3         = _format_region_list(xai.get("top3_regions", []))
    coverage     = xai.get("cam_coverage_pct", "N/A")

    breakdown = data.get("confidence_breakdown", {}) or {}
    breakdown_str = (
        ", ".join(f"{k.capitalize()}: {float(v):.1f}%" for k, v in breakdown.items())
        if breakdown else "Not available"
    )

    return f"""You are a senior radiologist writing a formal MRI brain scan report for a hospital record.

============================
STRICT FORMATTING RULES
============================
1. Use EXACTLY these four headings, in this order, nothing else:
   SUMMARY
   FINDINGS
   IMPRESSION
   RECOMMENDATION

2. NEVER use the words: "AI", "artificial intelligence", "model", "algorithm",
   "machine learning", "deep learning", "neural network", "automated system",
   "system", "software", or any synonym. Write as if you personally reviewed the scan.

3. Do NOT write a Disclaimer section. It will be added separately.

4. Do NOT repeat patient details or the report title in your output.

5. Keep language formal, clinical, concise. Each section: 2–4 sentences.

6. Use first-person plural clinical voice: "We observe…", "Our analysis indicates…",
   "Findings are consistent with…"

7. Confidence phrasing: if certainty is High, write
   "Our analysis is highly confident in this diagnosis."
   if Moderate: "Our analysis is moderately confident…"
   if Low: "Our analysis is made with limited confidence…"

============================
PATIENT & CLINICAL DATA
============================
Patient Name  : {patient_name}
Age           : {age}
Gender        : {gender}

Diagnosis     : {diagnosis}
Confidence    : {confidence:.2f}%
Certainty     : {certainty}
Observation   : {observation}

Heatmap Method     : {method}
Dominant Region    : {dom_region}
Top Active Regions : {top3}
Coverage           : {coverage}%

Class Confidence   : {breakdown_str}

============================
OUTPUT FORMAT (follow exactly)
============================
SUMMARY
[2–3 sentence summary of key finding]

FINDINGS
[Detailed clinical observation referencing the scan regions and confidence breakdown]

IMPRESSION
[Radiological interpretation: what the findings likely indicate clinically]

RECOMMENDATION
[3–4 specific clinical follow-up actions the treating physician should consider]
"""


# ============================================================
# GENERATE TEXT REPORT
# ============================================================


def generate_report(data: dict) -> str:
    """
    Call the LLM, sanitise output, and assemble the final plain-text report.

    Returns a clean string with:
      - Header (title, generated time, report ID)
      - LLM body (sanitised of any AI wording)
      - ONE disclaimer at the end
    """
    # Capture a single consistent timestamp for this report instance
    report_time = get_current_time()
    report_id   = get_report_id()

    try:
        client = _get_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": _build_prompt(data)}],
            temperature=0.15,   # Near-deterministic for clinical reproducibility
            max_tokens=950,
        )

        llm_raw  = response.choices[0].message.content or ""
        llm_body = _sanitize_report_text(llm_raw)

    except Exception as exc:
        print(f"[LLM ERROR] {exc}")
        llm_body = (
            "SUMMARY\n"
            "Report generation encountered a technical error. "
            "Please retry or contact support.\n\n"
            "FINDINGS\nNot available.\n\n"
            "IMPRESSION\nNot available.\n\n"
            "RECOMMENDATION\nContact technical support and retry."
        )

    patient_name = _safe_text(data.get("name"), "N/A")
    age          = _safe_text(data.get("age"),  "N/A")
    gender       = _safe_text(data.get("gender"), "N/A")
    diagnosis    = _safe_text(data.get("diagnosis"), "Unknown")
    confidence   = float(data.get("confidence", 0.0))
    certainty    = _safe_text(data.get("certainty"), "N/A")

    report = (
        f"MEDICAL REPORT\n"
        f"{'=' * 60}\n"
        f"Report ID   : {report_id}\n"
        f"Generated On: {report_time}\n"
        f"{'=' * 60}\n\n"
        f"PATIENT INFORMATION\n"
        f"Name    : {patient_name}\n"
        f"Age     : {age}\n"
        f"Gender  : {gender}\n\n"
        f"DIAGNOSIS RESULT\n"
        f"Condition  : {diagnosis}\n"
        f"Confidence : {confidence:.2f}%\n"
        f"Certainty  : {certainty}\n\n"
        f"{'-' * 60}\n\n"
        f"{llm_body}\n\n"
        f"{'=' * 60}\n"
        f"DISCLAIMER\n"
        f"This report is generated using automated imaging analysis tools and must be "
        f"reviewed and validated by a qualified, licensed healthcare professional before "
        f"any clinical decision is made. It does not constitute a definitive diagnosis "
        f"and should not replace a formal consultation with a specialist.\n"
    )

    return report.strip()


# ============================================================
# PDF STYLES — APOLLO-GRADE DESIGN
# ============================================================


def _build_styles(styles: dict) -> dict:
    """
    Return a dict of named ParagraphStyle objects.
    All colours, fonts, and spacing are defined here — single source of truth.
    """
    # Colour palette
    navy        = colors.HexColor("#1a2a4a")
    dark_navy   = colors.HexColor("#0f1b31")
    accent_blue = colors.HexColor("#1e6bb8")
    soft_blue   = colors.HexColor("#eaf3fb")
    pale_blue   = colors.HexColor("#f4f8fd")
    grey_text   = colors.HexColor("#4b5563")
    mid_grey    = colors.HexColor("#6b7280")
    rule_grey   = colors.HexColor("#d1d5db")
    body_dark   = colors.HexColor("#1f2937")

    return {
        "navy":        navy,
        "dark_navy":   dark_navy,
        "accent_blue": accent_blue,
        "soft_blue":   soft_blue,
        "pale_blue":   pale_blue,
        "grey_text":   grey_text,
        "mid_grey":    mid_grey,
        "rule_grey":   rule_grey,
        "body_dark":   body_dark,

        # --- Paragraph styles ---
        "title": ParagraphStyle(
            "TitleStyle", parent=styles["Title"],
            fontName="Helvetica-Bold", fontSize=20, leading=24,
            textColor=navy, alignment=0, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleStyle", parent=styles["Normal"],
            fontName="Helvetica", fontSize=9, leading=11,
            textColor=grey_text, spaceAfter=6,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading", parent=styles["Heading2"],
            fontName="Helvetica-Bold", fontSize=11.5, leading=14,
            textColor=navy, spaceBefore=10, spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "BodyStyle", parent=styles["Normal"],
            fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=body_dark, spaceAfter=4,
        ),
        "label": ParagraphStyle(
            "LabelStyle", parent=styles["Normal"],
            fontName="Helvetica-Bold", fontSize=8, leading=10,
            textColor=grey_text,
        ),
        "value": ParagraphStyle(
            "ValueStyle", parent=styles["Normal"],
            fontName="Helvetica-Bold", fontSize=9.5, leading=12,
            textColor=navy,
        ),
        "caption": ParagraphStyle(
            "CaptionStyle", parent=styles["Normal"],
            fontName="Helvetica", fontSize=7.5, leading=9,
            alignment=1, textColor=grey_text,
        ),
        "disclaimer": ParagraphStyle(
            "DisclaimerStyle", parent=styles["Normal"],
            fontName="Helvetica", fontSize=7.8, leading=10.5,
            textColor=mid_grey, alignment=1,
        ),
        "small": ParagraphStyle(
            "SmallStyle", parent=styles["Normal"],
            fontName="Helvetica", fontSize=8.5, leading=11,
            textColor=grey_text,
        ),
    }


# ============================================================
# PDF GENERATION
# ============================================================


def generate_pdf(
    data: dict,
    report_text: str,
    original_image_path: str | None,
    gradcam_image_path: str | None,
    lime_image_path: str | None = None,
) -> bytes:
    """
    Render an Apollo-level hospital-grade PDF.

    Layout
    ------
    1. Header (title, report ID, generated time in IST)
    2. Patient Information table
    3. Diagnosis Result table
    4. Per-Class Confidence Breakdown table
    5. MRI Scan & Heatmap images
    6. Heatmap Explanation Summary table
    7. Regional Activation Grid (3×3)
    8. Clinical Report (LLM body, sanitised)
    9. Disclaimer (ONCE, at the very end)
    10. Page header/footer decorations on every page
    """

    buffer = io.BytesIO()

    # --- Capture IST time once for the whole document ---
    generated_on = get_current_time()
    report_id    = get_report_id()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.70 * inch,
        title="Medical Report — NeuroScan",
        author="NeuroScan Imaging",
    )

    raw_styles = getSampleStyleSheet()
    S = _build_styles(raw_styles)   # S["key"] for colours & styles

    story: list = []

    # --------------------------------------------------------
    # 1. DOCUMENT HEADER
    # --------------------------------------------------------
    story.append(Paragraph("NeuroScan Brain MRI — Medical Report", S["title"]))
    story.append(Paragraph(
        f"Generated: {generated_on}&nbsp;&nbsp;|&nbsp;&nbsp;Report ID: {report_id}",
        S["subtitle"],
    ))
    story.append(HRFlowable(
        width="100%", thickness=2, color=S["navy"],
        spaceAfter=10, spaceBefore=2,
    ))

    # --------------------------------------------------------
    # 2. PATIENT INFORMATION
    # --------------------------------------------------------
    story.append(Paragraph("Patient Information", S["section_heading"]))

    p_name   = _safe_text(data.get("name"), "N/A")
    p_age    = _safe_text(data.get("age"),  "N/A")
    p_gender = _safe_text(data.get("gender"), "N/A")

    pt_table = Table(
        [
            [Paragraph("Full Name", S["label"]),
             Paragraph("Age", S["label"]),
             Paragraph("Gender", S["label"]),
             Paragraph("Report ID", S["label"])],
            [Paragraph(p_name, S["value"]),
             Paragraph(str(p_age), S["value"]),
             Paragraph(p_gender, S["value"]),
             Paragraph(report_id, S["value"])],
        ],
        colWidths=[2.40 * inch, 0.90 * inch, 1.10 * inch, 3.10 * inch],
    )
    pt_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), S["pale_blue"]),
        ("BACKGROUND",    (0, 1), (-1, 1), colors.white),
        ("BOX",           (0, 0), (-1, -1), 0.5, S["rule_grey"]),
        ("INNERGRID",     (0, 0), (-1, -1), 0.4, S["rule_grey"]),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(pt_table)
    story.append(Spacer(1, 8))

    # --------------------------------------------------------
    # 3. DIAGNOSIS RESULT
    # --------------------------------------------------------
    story.append(Paragraph("Diagnosis Result", S["section_heading"]))

    confidence   = float(data.get("confidence", 0.0))
    diagnosis    = _safe_text(data.get("diagnosis"), "Unknown")
    certainty    = _safe_text(data.get("certainty"), "N/A")
    diag_display = diagnosis.replace("_", " ").title()

    diag_table = Table(
        [
            [Paragraph("Detected Condition", S["label"]),
             Paragraph("Confidence Score", S["label"]),
             Paragraph("Certainty Level", S["label"])],
            [Paragraph(f"{diag_display} Tumor", S["value"]),
             Paragraph(f"{confidence:.2f}%", S["value"]),
             Paragraph(certainty.upper(), S["value"])],
        ],
        colWidths=[3.10 * inch, 2.00 * inch, 2.40 * inch],
    )
    diag_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), S["pale_blue"]),
        ("BACKGROUND",    (0, 1), (-1, 1), S["soft_blue"]),
        ("BOX",           (0, 0), (-1, -1), 0.5, S["rule_grey"]),
        ("INNERGRID",     (0, 0), (-1, -1), 0.4, S["rule_grey"]),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(diag_table)

    # --------------------------------------------------------
    # 4. PER-CLASS CONFIDENCE BREAKDOWN
    # --------------------------------------------------------
    breakdown = data.get("confidence_breakdown", {}) or {}
    if breakdown:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Per-Class Confidence Breakdown", S["section_heading"]))

        n_cols      = len(breakdown)
        col_w       = doc.width / max(n_cols, 1)
        bd_headers  = [Paragraph(str(cls).capitalize(), S["label"]) for cls in breakdown]
        bd_values   = [Paragraph(f"{float(v):.1f}%", S["value"]) for v in breakdown.values()]

        bd_table = Table([bd_headers, bd_values], colWidths=[col_w] * n_cols)
        bd_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), S["pale_blue"]),
            ("BACKGROUND",    (0, 1), (-1, 1), colors.white),
            ("BOX",           (0, 0), (-1, -1), 0.5, S["rule_grey"]),
            ("INNERGRID",     (0, 0), (-1, -1), 0.4, S["rule_grey"]),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(bd_table)

    # --------------------------------------------------------
    # 5. MRI IMAGES
    # --------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("MRI Scan & Heatmap Analysis", S["section_heading"]))

    image_candidates = [
        ("Original MRI Scan",     original_image_path),
        ("GradCAM++ Heatmap",     gradcam_image_path),
    ]
    if lime_image_path:
        image_candidates.append(("Supplementary Analysis", lime_image_path))

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
    # 6. HEATMAP EXPLANATION SUMMARY
    # --------------------------------------------------------
    xai = data.get("xai_summary", {}) or {}
    if xai:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Heatmap Explanation Summary", S["section_heading"]))

        xai_rows = [
            [Paragraph("Visualisation Method",  S["label"]),
             Paragraph(_safe_text(xai.get("method_used"), "GradCAM++"), S["body"])],
            [Paragraph("Dominant Region",        S["label"]),
             Paragraph(_safe_text(xai.get("dominant_region")), S["body"])],
            [Paragraph("Top 3 Active Regions",   S["label"]),
             Paragraph(_format_region_list(xai.get("top3_regions", [])), S["body"])],
            [Paragraph("High-Activation Coverage", S["label"]),
             Paragraph(f"{float(xai.get('cam_coverage_pct', 0.0)):.1f}%", S["body"])],
            [Paragraph("Mean Activation Score",  S["label"]),
             Paragraph(f"{float(xai.get('cam_mean_activation', 0.0)):.4f}", S["body"])],
        ]

        xai_table = Table(xai_rows, colWidths=[2.20 * inch, 5.30 * inch])
        xai_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, -1), S["pale_blue"]),
            ("BOX",           (0, 0), (-1, -1), 0.5, S["rule_grey"]),
            ("INNERGRID",     (0, 0), (-1, -1), 0.4, S["rule_grey"]),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(xai_table)

    # --------------------------------------------------------
    # 7. REGIONAL ACTIVATION GRID (3×3)
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

        grid_data = []
        for row_keys in grid_layout:
            row = []
            for key in row_keys:
                score = float(region_scores.get(key, 0.0))
                txt_c = colors.white if score > 0.40 else colors.HexColor("#1a2a4a")
                cell_style = ParagraphStyle(
                    f"GridCell_{key.replace('-', '_')}",
                    parent=raw_styles["Normal"],
                    fontName="Helvetica-Bold",
                    fontSize=8, leading=10,
                    alignment=1,
                    textColor=txt_c,
                )
                row.append(Paragraph(f"{key}<br/>{score:.3f}", cell_style))
            grid_data.append(row)

        region_table = Table(grid_data, colWidths=[2.08 * inch] * 3)
        r_style = TableStyle([
            ("BOX",           (0, 0), (-1, -1), 0.5, S["rule_grey"]),
            ("INNERGRID",     (0, 0), (-1, -1), 0.4, S["rule_grey"]),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])

        for ri, row_keys in enumerate(grid_layout):
            for ci, key in enumerate(row_keys):
                score  = float(region_scores.get(key, 0.0))
                r_int  = int(min(255, score * 510))
                g_int  = int(min(255, (1 - score) * 510))
                r_style.add("BACKGROUND", (ci, ri), (ci, ri),
                            colors.Color(r_int / 255.0, g_int / 255.0, 0.12))

        region_table.setStyle(r_style)
        story.append(region_table)

    # --------------------------------------------------------
    # 8. CLINICAL REPORT (LLM body)
    # --------------------------------------------------------
    story.append(Spacer(1, 14))
    story.append(Paragraph("Clinical Report", S["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=S["rule_grey"], spaceAfter=8))

    clean_text = _sanitize_report_text(report_text or "")

    # Lines to skip if LLM echoed them
    _SKIP_PREFIXES = frozenset({
        "MEDICAL REPORT",
        "GENERATED ON",
        "GENERATED:",
        "REPORT ID",
        "PATIENT INFORMATION",
        "NAME",
        "AGE",
        "GENDER",
        "DISCLAIMER",
        "===",
        "---",
    })

    for raw_line in clean_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 3))
            continue

        upper = line.upper()

        # Skip lines the PDF already renders in structured tables
        if any(upper.startswith(pfx) for pfx in _SKIP_PREFIXES):
            continue

        if _is_heading(line):
            story.append(Spacer(1, 4))
            story.append(Paragraph(line.title(), S["section_heading"]))
        else:
            story.append(_line_to_paragraph(line, S["body"]))

    # --------------------------------------------------------
    # 9. DISCLAIMER — single occurrence, end of document
    # --------------------------------------------------------
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.8, color=S["rule_grey"], spaceAfter=6))
    story.append(Paragraph(
        "<b>DISCLAIMER:</b> This report is generated using automated imaging analysis tools "
        "and must be reviewed and validated by a qualified, licensed healthcare professional "
        "before any clinical decision is made. It does not constitute a definitive diagnosis "
        "and should not replace a formal consultation with a specialist.",
        S["disclaimer"],
    ))

    # --------------------------------------------------------
    # 10. PAGE DECORATIONS (header line + footer)
    # --------------------------------------------------------
    def _page_decoration(canvas, doc_obj):
        canvas.saveState()
        w, h = letter

        # Top rule
        canvas.setStrokeColor(S["navy"])
        canvas.setLineWidth(0.6)
        canvas.line(
            doc_obj.leftMargin, h - 0.42 * inch,
            w - doc_obj.rightMargin, h - 0.42 * inch,
        )

        # Bottom rule
        canvas.setStrokeColor(S["rule_grey"])
        canvas.setLineWidth(0.4)
        canvas.line(
            doc_obj.leftMargin, 0.50 * inch,
            w - doc_obj.rightMargin, 0.50 * inch,
        )

        # Footer — left: facility name; right: page number
        canvas.setFillColor(S["grey_text"])
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(
            doc_obj.leftMargin, 0.34 * inch,
            "NeuroScan Brain MRI — Confidential Medical Record",
        )
        canvas.drawRightString(
            w - doc_obj.rightMargin, 0.34 * inch,
            f"Page {doc_obj.page}",
        )

        canvas.restoreState()

    doc.build(story, onFirstPage=_page_decoration, onLaterPages=_page_decoration)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# SELF-TEST
# ============================================================
if __name__ == "__main__":
    _test_result = {
        "prediction": "Glioma",
        "confidence": 0.9287,
        "prediction_model": "EfficientNet-B0",
        "explanation_model": "GradCAM++",
        "observation": "High-confidence activation detected in the central and peri-ventricular regions.",
        "confidence_breakdown": {
            "glioma":      92.87,
            "meningioma":   4.11,
            "notumor":      1.38,
            "pituitary":    1.64,
        },
        "xai_summary": {
            "method_used":       "GradCAM++",
            "dominant_region":   "center",
            "top3_regions":      ["center", "top-center", "top-right"],
            "cam_coverage_pct":  43.2,
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
    _report  = generate_report(_data)

    print(_report)

    # Validate constraints
    body_section = _report.split("DISCLAIMER")[0]   # Everything before disclaimer
    assert "AI" not in body_section, "FAIL: 'AI' found in report body!"
    assert _report.count("DISCLAIMER") == 1,         "FAIL: Disclaimer appears more than once!"
    assert "IST" in _report,                          "FAIL: IST not in report timestamp!"
    print("\n✅ All self-checks passed.")