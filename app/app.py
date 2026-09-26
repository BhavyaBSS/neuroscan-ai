# import streamlit as st
# import sys
# import os
# import time
# import re
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.application import MIMEApplication

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# from inference import run_pipeline
# from llm_report import prepare_llm_input, generate_report, generate_pdf

# import base64

# # ── Load logo once at startup ──────────────────────────────────────────────
# def get_logo_b64():
#     # Change "logo_v3.png" to your new filename:
#     logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "final_logo.png")
#     if os.path.exists(logo_path):
#         with open(logo_path, "rb") as f:
#             return base64.b64encode(f.read()).decode()
#     return ""

# LOGO_B64 = get_logo_b64()
# LOGO_SRC = f"data:image/png;base64,{LOGO_B64}"

# # ── Page Config ───────────────────────────────────────────────────────────────
# st.set_page_config(
#     page_title="NeuroScan AI · Brain Tumor Detection",
#     page_icon="logo_v3.png",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )

# # ── Global CSS ────────────────────────────────────────────────────────────────
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,500;0,700;0,900;1,300;1,500;1,700;1,900&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@300;400;500&display=swap');

# /* ── Reset & Base ── */
# *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

# :root {
#     --bg:        #07090f;
#     --surface:   #0d1117;
#     --surface2:  #131923;
#     --border:    rgba(255,255,255,0.07);
#     --border2:   rgba(255,255,255,0.12);
#     --cyan:      #00d4ff;
#     --cyan-dim:  rgba(0,212,255,0.15);
#     --cyan-glow: rgba(0,212,255,0.35);
#     --green:     #00e5a0;
#     --red:       #ff4d6d;
#     --text:      #e2e8f0;
#     --muted:     #64748b;
#     --muted2:    #94a3b8;
# }

# /* ── MOBILE RESPONSIVENESS ── */
# @media (max-width: 768px) {
#     .ns-hero-h1 { font-size: 36px !important; letter-spacing: -1px !important; }
#     .ns-hero-sub { font-size: 14px !important; }
#     .ns-nav { padding: 0 16px !important; }
#     .ns-stats { grid-template-columns: repeat(2, 1fr) !important; }
#     .ns-feature-grid { grid-template-columns: 1fr 1fr !important; }
#     .ns-features { padding: 40px 20px !important; }
#     .ns-cta-band { margin: 0 16px 40px !important; padding: 40px 24px !important; }
#     .ns-footer { padding: 16px 20px !important; flex-direction: column !important; gap: 8px !important; }
#     .about-band { margin: 16px !important; padding: 24px !important; grid-template-columns: 1fr !important; }
#     .dash-topbar { padding: 0 16px !important; }
#     .auth-left { min-height: 30vh !important; padding: 32px 20px !important; }
# }

# @media (max-width: 480px) {
#     .ns-hero-h1 { font-size: 28px !important; }
#     .ns-stats { grid-template-columns: 1fr 1fr !important; }
#     .ns-feature-grid { grid-template-columns: 1fr !important; }
#     .ns-section-title { font-size: 28px !important; }
#     .ns-cta-title { font-size: 24px !important; }
#     .about-stats-grid { grid-template-columns: 1fr 1fr !important; }
# }

# html, body,
# [data-testid="stAppViewContainer"],
# [data-testid="stApp"] {
#     font-family: 'DM Sans', sans-serif !important;
#     background: var(--bg) !important;
#     color: var(--text) !important;
# }

# /* Hide Streamlit chrome */
# #MainMenu, footer, header,
# [data-testid="stToolbar"],
# [data-testid="stDecoration"],
# [data-testid="stStatusWidget"],
# [data-testid="collapsedControl"],
# .stDeployButton,
# section[data-testid="stSidebar"] { display: none !important; }

# .block-container {
#     padding: 0 !important;
#     max-width: 100% !important;
# }

# /* ═══════════════════════════════════════
#    SHARED COMPONENTS
# ═══════════════════════════════════════ */

# /* Scanline overlay for depth */
# body::after {
#     content: '';
#     position: fixed;
#     inset: 0;
#     background: repeating-linear-gradient(
#         0deg,
#         transparent,
#         transparent 2px,
#         rgba(0,0,0,0.03) 2px,
#         rgba(0,0,0,0.03) 4px
#     );
#     pointer-events: none;
#     z-index: 9999;
# }

# .ns-badge {
#     display: inline-flex; align-items: center; gap: 7px;
#     background: var(--cyan-dim);
#     border: 1px solid rgba(0,212,255,0.3);
#     color: var(--cyan);
#     padding: 5px 14px; border-radius: 4px;
#     font-family: 'DM Mono', monospace;
#     font-size: 11px; font-weight: 500;
#     letter-spacing: 1px;
#     text-transform: uppercase;
# }
# .ns-badge::before {
#     content: '●';
#     font-size: 8px;
#     animation: blink 1.8s infinite;
# }
# @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }

# /* ═══════════════════════════════════════
#    LANDING PAGE
# ═══════════════════════════════════════ */

# /* Top Nav */
# .ns-nav {
#     background: rgba(7,9,15,0.96);
#     backdrop-filter: blur(20px);
#     border-bottom: 1px solid var(--border);
#     padding: 0 56px;
#     height: 64px;
#     display: flex;
#     align-items: center;
#     justify-content: space-between;
# }
# .ns-logo {
#     display: flex; align-items: center; gap: 10px;
# }
# .ns-logo-mark {
#     width: 36px; height: 36px;
#     background: var(--cyan);
#     border-radius: 8px;
#     display: flex; align-items: center; justify-content: center;
#     font-size: 18px;
#     box-shadow: 0 0 20px var(--cyan-glow);
# }
# .ns-logo-mark img {
#     filter: drop-shadow(0 0 12px rgba(0,212,255,0.6));
# }
# .ns-logo-text {
#     font-family: 'Fraunces', serif;
#     font-size: 18px; font-weight: 800;
#     color: #f1f5f9;
#     letter-spacing: -0.3px;
# }
# .ns-logo-text em { color: var(--cyan); font-style: normal; }

# /* Hero */
# .ns-hero {
#     position: relative;
#     padding: 100px 48px 60px;
#     text-align: center;
#     overflow: hidden;
# }
# .ns-hero-grid {
#     position: absolute; inset: 0;
#     background-image:
#         linear-gradient(rgba(0,212,255,0.04) 1px, transparent 1px),
#         linear-gradient(90deg, rgba(0,212,255,0.04) 1px, transparent 1px);
#     background-size: 60px 60px;
#     mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, black 30%, transparent 100%);
# }
# .ns-hero-glow {
#     position: absolute;
#     top: -100px; left: 50%; transform: translateX(-50%);
#     width: 600px; height: 400px;
#     background: radial-gradient(ellipse, rgba(0,212,255,0.12) 0%, transparent 70%);
#     pointer-events: none;
# }
# .ns-hero-eyebrow {
#     font-family: 'DM Mono', monospace;
#     font-size: 11px; color: var(--cyan);
#     letter-spacing: 2px; text-transform: uppercase;
#     margin-bottom: 24px;
#     display: flex; align-items: center; justify-content: center; gap: 10px;
# }
# .ns-hero-eyebrow::before, .ns-hero-eyebrow::after {
#     content: '';
#     display: block; width: 40px; height: 1px;
#     background: linear-gradient(90deg, transparent, var(--cyan));
# }
# .ns-hero-eyebrow::after { background: linear-gradient(90deg, var(--cyan), transparent); }

# .ns-hero-h1 {
#     font-family: 'Fraunces', serif;
#     font-size: 68px; font-weight: 900;
#     color: #f8fafc;
#     line-height: 1.05;
#     letter-spacing: -2px;
#     margin-bottom: 24px;
#     position: relative; z-index: 1;
# }
# .ns-hero-h1 .line2 {
#     color: var(--cyan);
#     font-style: italic;
#     display: block;
# }
# .ns-hero-sub {
#     font-size: 18px; color: var(--muted2); line-height: 1.7;
#     max-width: 580px; margin: 0 auto 48px;
#     position: relative; z-index: 1;
# }

# /* Stats strip */
# .ns-stats {
#     display: grid; grid-template-columns: repeat(4,1fr);
#     border-top: 1px solid var(--border);
#     border-bottom: 1px solid var(--border);
#     background: var(--surface);
#     margin: 0;
# }
# .ns-stat {
#     text-align: center;
#     padding: 28px 24px;
#     border-right: 1px solid var(--border);
#     position: relative;
# }
# .ns-stat:last-child { border-right: none; }
# .ns-stat::before {
#     content: '';
#     position: absolute; top: 0; left: 50%; transform: translateX(-50%);
#     width: 40px; height: 2px;
#     background: var(--cyan);
#     opacity: 0.5;
# }
# .ns-stat-val {
#     font-family: 'Fraunces', serif;
#     font-size: 32px; font-weight: 900; color: var(--cyan);
#     letter-spacing: -1px; line-height: 1;
#     margin-bottom: 6px;
# }
# .ns-stat-label {
#     font-family: 'DM Mono', monospace;
#     font-size: 11px; color: var(--muted);
#     letter-spacing: 1px; text-transform: uppercase;
# }

# /* Features */
# .ns-features {
#     padding: 80px 80px;
#     background: var(--bg);
# }
# .ns-section-kicker {
#     font-family: 'DM Mono', monospace;
#     font-size: 11px; font-weight: 500;
#     color: var(--cyan); letter-spacing: 2px;
#     text-transform: uppercase; margin-bottom: 16px;
#     text-align: center;
# }
# .ns-section-title {
#     font-family: 'Fraunces', serif;
#     font-size: 44px; font-weight: 900; color: #f8fafc;
#     text-align: center; letter-spacing: -1.5px;
#     margin-bottom: 56px;
# }
# .ns-feature-grid {
#     display: grid; grid-template-columns: repeat(4,1fr);
#     gap: 1px;
#     border: 1px solid var(--border);
#     border-radius: 16px;
#     overflow: hidden;
#     max-width: 1200px; margin: 0 auto;
# }
# .ns-feature-card {
#     background: var(--surface);
#     padding: 36px 28px;
#     transition: all 0.3s;
#     position: relative;
# }
# .ns-feature-card::after {
#     content: '';
#     position: absolute; top: 0; left: 0; right: 0;
#     height: 2px;
#     background: linear-gradient(90deg, transparent, var(--cyan), transparent);
#     opacity: 0;
#     transition: opacity 0.3s;
# }
# .ns-feature-card:hover { background: var(--surface2); }
# .ns-feature-card:hover::after { opacity: 1; }
# .ns-feature-num {
#     font-family: 'DM Mono', monospace;
#     font-size: 11px; color: var(--muted);
#     letter-spacing: 1px; margin-bottom: 20px;
# }
# .ns-feature-icon { font-size: 28px; margin-bottom: 16px; display: block; }
# .ns-feature-kpi {
#     font-family: 'Fraunces', serif;
#     font-size: 28px; font-weight: 900;
#     color: var(--cyan); margin-bottom: 8px;
# }
# .ns-feature-name {
#     font-size: 15px; font-weight: 700;
#     color: var(--text); margin-bottom: 10px;
# }
# .ns-feature-desc { font-size: 13px; color: var(--muted); line-height: 1.7; }

# /* CTA band */
# .ns-cta-band {
#     margin: 0 80px 80px;
#     background: var(--surface);
#     border: 1px solid var(--border);
#     border-radius: 16px;
#     padding: 72px 80px;
#     text-align: center; position: relative; overflow: hidden;
# }
# .ns-cta-band::before {
#     content:'';
#     position: absolute; top: 0; left: 0; right: 0; height: 1px;
#     background: linear-gradient(90deg, transparent, var(--cyan), transparent);
# }
# .ns-cta-title {
#     font-family: 'Fraunces', serif;
#     font-size: 40px; font-weight: 900;
#     color: #fff; margin-bottom: 14px; letter-spacing: -1px;
# }
# .ns-cta-sub {
#     font-size: 16px; color: var(--muted2);
#     margin-bottom: 0; line-height: 1.7;
# }

# /* Footer */
# .ns-footer {
#     border-top: 1px solid var(--border);
#     padding: 24px 80px;
#     display: flex; align-items: center; justify-content: space-between;
#     font-family: 'DM Mono', monospace;
#     font-size: 11px; color: var(--muted);
#     letter-spacing: 0.5px;
# }
# .ns-footer-logo {
#     font-family: 'Fraunces', serif;
#     font-weight: 700; color: var(--muted2);
#     font-size: 14px; letter-spacing: -0.3px;
# }
# .ns-footer-logo em { color: var(--cyan); font-style: normal; }

# /* Demo gallery */
# .demo-gallery {
#     margin-top: 40px;
#     padding: 32px;
#     background: var(--surface);
#     border: 1px solid var(--border);
#     border-radius: 16px;
#     position: relative;
# }
# .demo-gallery::before {
#     content: '';
#     position: absolute; top: 0; left: 0; right: 0; height: 1px;
#     background: linear-gradient(90deg, transparent, var(--cyan) 30%, var(--green) 70%, transparent);
# }
# .demo-gallery-title {
#     font-family: 'DM Mono', monospace;
#     font-size: 11px; color: var(--cyan);
#     letter-spacing: 2px; text-transform: uppercase;
#     text-align: center; margin-bottom: 24px;
# }
# .demo-img-label {
#     font-family: 'DM Mono', monospace;
#     font-size: 11px; color: var(--muted2);
#     letter-spacing: 1px; text-transform: uppercase;
#     text-align: center; margin-top: 10px; margin-bottom: 8px;
# }

# /* ═══════════════════════════════════════
#    AUTH PAGE
# ═══════════════════════════════════════ */
# .auth-left {
#     background:
#         radial-gradient(ellipse 80% 60% at 30% 40%, rgba(0,212,255,0.10), transparent 70%),
#         linear-gradient(135deg, #0a1628 0%, #07090f 100%);
#     min-height: 100vh;
#     display: flex; flex-direction: column;
#     align-items: center; justify-content: center;
#     text-align: center; padding: 60px 40px;
#     position: relative;
# }
# .auth-grid-bg {
#     position: absolute; inset: 0;
#     background-image:
#         linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
#         linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
#     background-size: 40px 40px;
#     border-radius: inherit;
# }
# .auth-brain-icon {
#     font-size: 64px;
#     margin-bottom: 24px;
#     filter: drop-shadow(0 0 30px rgba(0,212,255,0.5));
#     position: relative; z-index: 1;
# }
# .auth-brand-name {
#     font-family: 'Fraunces', serif;
#     font-size: 36px; font-weight: 900; color: #f8fafc;
#     margin-bottom: 14px; letter-spacing: -1px;
#     position: relative; z-index: 1;
# }
# .auth-brand-name em { color: var(--cyan); font-style: normal; }
# .auth-brand-desc {
#     font-size: 14px; color: rgba(255,255,255,0.55);
#     line-height: 1.8; max-width: 300px;
#     position: relative; z-index: 1;
# }
# .auth-pills {
#     display: flex; gap: 8px; margin-top: 32px;
#     flex-wrap: wrap; justify-content: center;
#     position: relative; z-index: 1;
# }
# .auth-pill {
#     background: rgba(255,255,255,0.06);
#     border: 1px solid rgba(255,255,255,0.1);
#     border-radius: 4px; padding: 5px 12px;
#     font-family: 'DM Mono', monospace;
#     font-size: 11px; color: rgba(255,255,255,0.55);
#     letter-spacing: 0.5px;
# }

# /* ═══════════════════════════════════════
#    DASHBOARD
# ═══════════════════════════════════════ */
# .dash-topbar {
#     background: rgba(7,9,15,0.98);
#     backdrop-filter: blur(20px);
#     border-bottom: 1px solid var(--border);
#     padding: 0 40px;
#     height: 60px;
#     display: flex; align-items: center; justify-content: space-between;
#     position: sticky; top: 0; z-index: 999;
# }
# .dash-logo { display: flex; align-items: center; gap: 10px; }
# .dash-logo-mark {
#     width: 32px; height: 32px;
#     background: var(--cyan);
#     border-radius: 7px;
#     display: flex; align-items: center; justify-content: center;
#     font-size: 15px;
#     box-shadow: 0 0 15px var(--cyan-glow);
# }
# .dash-logo-txt {
#     font-family: 'Fraunces', serif;
#     font-size: 16px; font-weight: 700; color: #f1f5f9;
#     letter-spacing: -0.3px;
# }
# .dash-logo-txt em { color: var(--cyan); font-style: normal; }
# .dash-breadcrumb {
#     font-family: 'DM Mono', monospace;
#     font-size: 11px; color: var(--muted);
#     letter-spacing: 0.5px;
#     display: flex; align-items: center; gap: 8px;
# }
# .dash-breadcrumb span { color: var(--cyan); }

# /* Panel boxes */
# .panel {
#     background: var(--surface);
#     border: 1px solid var(--border);
#     border-radius: 14px;
#     overflow: hidden;
#     height: 100%;
# }
# .panel-header {
#     display: flex; align-items: center; gap: 12px;
#     padding: 18px 20px;
#     border-bottom: 1px solid var(--border);
#     background: var(--surface2);
# }
# .panel-icon {
#     width: 38px; height: 38px; border-radius: 9px;
#     display: flex; align-items: center; justify-content: center;
#     font-family: 'DM Mono', monospace;
#     font-size: 9px;
#     font-weight: 700;
#     letter-spacing: -0.5px;
# }
# .panel-icon.blue  { background: rgba(0,212,255,0.12); }
# .panel-icon.teal  { background: rgba(0,229,160,0.10); }
# .panel-icon.green { background: rgba(34,197,94,0.10); }
# .panel-title {
#     font-family: 'DM Sans', sans-serif;
#     font-size: 14px; font-weight: 700; color: var(--text);
# }
# .panel-sub {
#     font-family: 'DM Mono', monospace;
#     font-size: 10px; color: var(--muted);
#     letter-spacing: 0.5px; margin-top: 2px;
# }
# .panel-body { padding: 20px; }

# /* Arrow connector */
# .flow-arrow {
#     display: flex; flex-direction: column;
#     align-items: center; justify-content: center;
#     height: 100%;
# }
# .flow-dot {
#     width: 5px; height: 5px; border-radius: 50%;
#     background: var(--border2);
#     margin: 3px 0;
#     transition: all 0.3s;
# }
# .flow-dot.live {
#     background: var(--cyan);
#     box-shadow: 0 0 8px var(--cyan);
#     animation: pulse-dot 0.9s infinite alternate;
# }
# @keyframes pulse-dot { from{opacity:0.4} to{opacity:1} }
# .flow-chevron {
#     font-size: 18px; color: var(--border2);
#     margin: 2px 0; transition: color 0.3s;
# }
# .flow-chevron.live { color: var(--cyan); }

# /* Empty state */
# .empty-state {
#     display: flex; flex-direction: column;
#     align-items: center; justify-content: center;
#     text-align: center; padding: 48px 20px;
#     min-height: 220px;
# }
# .empty-icon { font-size: 36px; opacity: 0.15; margin-bottom: 14px; }
# .empty-txt {
#     font-size: 13px; color: var(--muted); line-height: 1.7;
# }
# .empty-txt strong { color: var(--muted2); }

# /* Confidence pills */
# .conf-row { display: flex; gap: 10px; margin-bottom: 16px; }
# .conf-chip {
#     flex: 1;
#     background: var(--surface2);
#     border: 1px solid var(--border);
#     border-radius: 9px; padding: 12px;
#     text-align: center;
# }
# .conf-chip-label {
#     font-family: 'DM Mono', monospace;
#     font-size: 10px; color: var(--muted);
#     letter-spacing: 0.5px; margin-bottom: 4px;
# }
# .conf-chip-val {
#     font-family: 'Fraunces', serif;
#     font-size: 22px; font-weight: 900; color: var(--text);
# }

# /* Prediction badge */
# .pred-tag {
#     display: inline-block; padding: 5px 14px;
#     border-radius: 4px; font-size: 12px; font-weight: 700;
#     font-family: 'DM Mono', monospace;
#     letter-spacing: 0.5px;
#     margin-bottom: 14px;
# }
# .pred-tag.tumor    { background: rgba(255,77,109,0.12); color: var(--red); border: 1px solid rgba(255,77,109,0.3); }
# .pred-tag.no-tumor { background: rgba(0,229,160,0.10); color: var(--green); border: 1px solid rgba(0,229,160,0.3); }

# /* Report scroll */
# .report-scroll {
#     height: 280px; overflow-y: auto;
#     font-size: 12px; color: var(--muted2); line-height: 1.8;
#     background: var(--bg);
#     border-radius: 8px; padding: 14px;
#     border: 1px solid var(--border);
#     font-family: 'DM Mono', monospace;
# }
# .report-scroll::-webkit-scrollbar { width: 4px; }
# .report-scroll::-webkit-scrollbar-track { background: transparent; }
# .report-scroll::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

# /* About band */
# .about-band {
#     margin: 32px 40px 40px;
#     background: var(--surface);
#     border: 1px solid var(--border);
#     border-radius: 16px;
#     padding: 48px 56px;
#     display: grid; grid-template-columns: 1.2fr 1fr; gap: 48px;
#     position: relative; overflow: hidden;
# }
# .about-band::before {
#     content:'';
#     position: absolute; top: 0; left: 0; right: 0; height: 1px;
#     background: linear-gradient(90deg, transparent, var(--cyan) 50%, transparent);
# }
# .about-title {
#     font-family: 'Fraunces', serif;
#     font-size: 26px; font-weight: 700; color: #f8fafc;
#     margin-bottom: 16px; letter-spacing: -0.5px;
# }
# .about-body {
#     font-size: 13px; color: var(--muted2); line-height: 1.85;
# }
# .about-stats-grid {
#     display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
# }
# .about-stat-card {
#     background: var(--surface2);
#     border: 1px solid var(--border);
#     border-radius: 10px; padding: 20px;
# }
# .about-stat-val {
#     font-family: 'Fraunces', serif;
#     font-size: 22px; font-weight: 900; color: var(--cyan);
#     margin-bottom: 4px;
# }
# .about-stat-lbl {
#     font-family: 'DM Mono', monospace;
#     font-size: 10px; color: var(--muted);
#     letter-spacing: 0.5px; text-transform: uppercase;
# }

# /* ── Streamlit widget overrides ── */
# [data-testid="stHeader"] { display: none !important; }

# .stTextInput > div > div > input,
# .stNumberInput > div > div > input,
# .stSelectbox > div > div > div {
#     font-family: 'Cabinet Grotesk', sans-serif !important;
#     border-radius: 8px !important;
#     border: 1px solid var(--border2) !important;
#     padding: 10px 14px !important;
#     font-size: 14px !important;
#     background: var(--surface2) !important;
#     color: var(--text) !important;
# }
# .stTextInput > div > div > input::placeholder { color: var(--muted) !important; }
# .stTextInput label, .stNumberInput label, .stSelectbox label {
#     color: var(--muted2) !important;
#     font-family: 'DM Mono', monospace !important;
#     font-weight: 500 !important;
#     font-size: 11px !important;
#     letter-spacing: 0.5px !important;
#     text-transform: uppercase !important;
# }
# .stTextInput > div > div > input:focus,
# .stNumberInput > div > div > input:focus {
#     border-color: var(--cyan) !important;
#     box-shadow: 0 0 0 2px rgba(0,212,255,0.12) !important;
# }
# [data-testid="stFileUploader"] {
#     background: var(--surface2) !important;
#     border: 1px dashed var(--border2) !important;
#     border-radius: 10px !important;
#     padding: 20px !important;
# }
# [data-testid="stFileUploader"]:hover { border-color: var(--cyan) !important; }

# .stButton > button {
#     font-family: 'DM Sans', sans-serif !important;
#     border-radius: 8px !important;
#     font-weight: 700 !important;
#     font-size: 13px !important;
#     padding: 10px 22px !important;
#     transition: all 0.18s !important;
#     background: var(--surface2) !important;
#     color: var(--muted2) !important;
#     border: 1px solid var(--border2) !important;
#     letter-spacing: 0.2px !important;
# }
# .stButton > button:hover {
#     border-color: var(--cyan) !important;
#     color: var(--cyan) !important;
#     background: var(--cyan-dim) !important;
# }
# .stButton > button[kind="primary"] {
#     background: var(--cyan) !important;
#     border: none !important;
#     color: #07090f !important;
#     box-shadow: 0 4px 20px var(--cyan-glow) !important;
# }
# .stButton > button[kind="primary"]:hover {
#     opacity: 0.88 !important;
#     transform: translateY(-1px) !important;
#     box-shadow: 0 8px 28px var(--cyan-glow) !important;
#     color: #07090f !important;
# }
# .stDownloadButton > button {
#     font-family: 'DM Sans', sans-serif !important;
#     background: var(--cyan) !important;
#     color: #07090f !important;
#     border: none !important;
#     border-radius: 8px !important;
#     font-weight: 700 !important;
#     padding: 11px 22px !important;
#     box-shadow: 0 4px 16px var(--cyan-glow) !important;
# }
# .stProgress > div > div > div > div {
#     background: var(--cyan) !important;
#     border-radius: 2px !important;
# }
# .stSpinner > div { border-top-color: var(--cyan) !important; }
# .stSuccess {
#     background: rgba(0,229,160,0.08) !important;
#     border-left: 3px solid var(--green) !important;
#     border-radius: 8px !important;
#     color: var(--green) !important;
# }
# .stWarning {
#     background: rgba(245,158,11,0.08) !important;
#     border-left: 3px solid #f59e0b !important;
#     border-radius: 8px !important;
# }
# .stError {
#     background: rgba(255,77,109,0.08) !important;
#     border-left: 3px solid var(--red) !important;
#     border-radius: 8px !important;
# }
# .stMarkdown p { font-family: 'Cabinet Grotesk', sans-serif !important; color: var(--muted2) !important; }
# [data-testid="stImage"] img { border-radius: 8px !important; }

# /* Auth column styling */
# .auth-page [data-testid="stColumn"]:nth-of-type(1) {
#     min-height: 100vh;
# }
# </style>
# """, unsafe_allow_html=True)


# # ── Session State Init ─────────────────────────────────────────────────────────
# def init_state():
#     defaults = {
#         "page":              "landing",
#         "auth_tab":          "signin",
#         "logged_in":         False,
#         "user_name":         "",
#         "user_email":        "",
#         "result":            None,
#         "file_path":         None,
#         "report_text":       None,
#         "report_data":       None,
#         "pdf_bytes":         None,
#         "uploaded_filename": "",
#         "_analyzing":        False,
#         "patient_name":      "",
#         "patient_age":       30,
#         "patient_gender":    "Male",
#         "show_demo":         False,
#         "show_video":        False,
#         "demo_mode":         False,
#     }
#     for k, v in defaults.items():
#         if k not in st.session_state:
#             st.session_state[k] = v

# init_state()


# # ── Email helper ───────────────────────────────────────────────────────────────
# def send_email_with_pdf(recipient_email, patient_name, pdf_bytes):
#     sender_email = st.secrets["GMAIL_SENDER"]
#     sender_password = st.secrets["GMAIL_PASSWORD"]
#     try:
#         msg = MIMEMultipart()
#         msg['From']    = sender_email
#         msg['To']      = recipient_email
#         msg['Subject'] = f"NeuroScan AI: Diagnostic Report for {patient_name}"
#         body = f"""Dear {patient_name},

# Your MRI analysis is complete. Please find your NeuroScan AI Diagnostic Report attached.

# IMPORTANT: This report is AI-generated and must be reviewed by a qualified healthcare professional.

# Best regards,
# The NeuroScan AI Team"""
#         msg.attach(MIMEText(body, 'plain'))
#         fname = f"NeuroScan_Report_{patient_name.replace(' ', '_')}.pdf"
#         part  = MIMEApplication(pdf_bytes, Name=fname)
#         part['Content-Disposition'] = f'attachment; filename="{fname}"'
#         msg.attach(part)
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(sender_email, sender_password)
#         server.send_message(msg)
#         server.quit()
#         return True
#     except Exception as e:
#         print(f"Email error: {e}")
#         return False


# # ══════════════════════════════════════════════════════════════════════════════
# # LANDING PAGE
# # ══════════════════════════════════════════════════════════════════════════════
# def page_landing():
#     # ── Nav ────────────────────────────────────────────────────────────────────
#     nav_l, _, nav_r1, nav_r2 = st.columns([5, 2, 0.9, 0.9])
#     with nav_l:
#         st.markdown(f"""
#         <div class="ns-nav" style="padding:12px 24px;">
#             <div class="ns-logo">
#             <div class="ns-logo-mark" style="background:transparent;box-shadow:none;padding:0;">
#                 <img src="{LOGO_SRC}" style="width:36px;height:36px;object-fit:contain;border-radius:8px;" />
#             </div>
#             <span class="ns-logo-text">Neuro<em>Scan</em> AI</span>
#         </div>
#         </div>""", unsafe_allow_html=True)
#     with nav_r1:
#         st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
#         if st.button("Log In", key="nav_login", use_container_width=True):
#             st.session_state.page = "auth"
#             st.session_state.auth_tab = "signin"
#             st.rerun()
#         st.markdown("</div>", unsafe_allow_html=True)
#     with nav_r2:
#         st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
#         if st.button("Sign Up", key="nav_signup", type="primary", use_container_width=True):
#             st.session_state.page = "auth"
#             st.session_state.auth_tab = "register"
#             st.rerun()
#         st.markdown("</div>", unsafe_allow_html=True)

#     # # ── Hero ───────────────────────────────────────────────────────────────────
#     # st.markdown("<div style='margin-top:60px'></div>", unsafe_allow_html=True)
#     # _, col_hero, _ = st.columns([1, 8, 1])
#     # with col_hero:
#     #     st.markdown("""
#     #     <div class="ns-hero">
#     #         <div class="ns-hero-grid"></div>
#     #         <div class="ns-hero-glow"></div>
#     #         <div class="ns-hero-eyebrow">Clinical AI Platform</div>
#     #         <h1 class="ns-hero-h1">
#     #             Detect Brain Tumors
#     #             <span class="line2">with Explainable AI</span>
#     #         </h1>
#     #         <p class="ns-hero-sub">
#     #             Upload an MRI scan and receive AI-powered classification,
#     #             GRAD-CAM++heatmaps, and a full clinical report in under 10 seconds.
#     #         </p>
#     #     </div>
#     #     """, unsafe_allow_html=True)
#     # ── Hero ───────────────────────────────────────────────────────────────────
#     st.markdown("<div style='margin-top:60px'></div>", unsafe_allow_html=True)
#     _, col_hero, _ = st.columns([1, 8, 1])
#     with col_hero:
#         st.markdown("""
#         <div class="ns-hero" style="display: flex; flex-direction: column; align-items: center; text-align: center;">
#             <div class="ns-hero-grid"></div>
#             <div class="ns-hero-glow"></div>
#             <div class="ns-hero-eyebrow">Clinical AI Platform</div>
#             <h1 class="ns-hero-h1" style="margin: 0 auto;">
#                 Detect Brain Tumors
#                 <span class="line2" style="display: block; width: 100%;">with Explainable AI</span>
#             </h1>
#             <p class="ns-hero-sub" style="margin: 20px auto; max-width: 600px;">
#                 Upload an MRI scan and receive AI-powered classification,
#                 GRAD-CAM++heatmaps, and a full clinical report in under 10 seconds.
#             </p>
#         </div>
#         """, unsafe_allow_html=True)

#         # ── Action buttons ─────────────────────────────────────────────────────
#         b1, b2, b3 = st.columns(3)
#         with b1:
#             if st.button(" Launch Dashboard", key="hero_launch",
#                          type="primary", use_container_width=True):
#                 st.session_state.page = "auth"
#                 st.rerun()
#         with b2:
#             demo_label = "✕  Close Demo" if st.session_state.show_demo else "Guest Demo"
#             if st.button(demo_label, key="hero_demo", use_container_width=True):
#                 st.session_state.show_demo  = not st.session_state.show_demo
#                 st.session_state.show_video = False
#                 st.rerun()
#         with b3:
#             vid_label = "✕  Close Video" if st.session_state.show_video else "How It Works"
#             if st.button(vid_label, key="hero_vid", use_container_width=True):
#                 st.session_state.show_video = not st.session_state.show_video
#                 st.session_state.show_demo  = False
#                 st.rerun()

#         # ── Video ──────────────────────────────────────────────────────────────
#         if st.session_state.show_video:
#             st.markdown("<div style='margin-top:32px'></div>", unsafe_allow_html=True)
#             st.video("https://youtu.be/sMCbnhHhj7w")

#         # ── Demo Gallery ───────────────────────────────────────────────────────
#         if st.session_state.show_demo:
#             st.markdown("""
#             <div class="demo-gallery">
#                 <div class="demo-gallery-title"></div>
#             </div>
#             """, unsafe_allow_html=True)

#             base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "Testing")
#             samples = [
#                 {"label": "Glioma",      "folder": "glioma",      "file": "Te-gl_0010.jpg"},
#                 {"label": "Meningioma",  "folder": "meningioma",  "file": "Te-me_0010.jpg"},
#                 {"label": "Pituitary",   "folder": "pituitary",   "file": "Te-pi_0010.jpg"},
#                 {"label": "No Tumor",    "folder": "notumor",     "file": "Te-no_0010.jpg"},
#             ]

#             d1, d2, d3, d4 = st.columns(4)
#             demo_cols = [d1, d2, d3, d4]

#             for i, s in enumerate(samples):
#                 path = os.path.join(base, s["folder"], s["file"])
#                 with demo_cols[i]:
#                     if os.path.exists(path):
#                         st.image(path, use_container_width=True)
#                         st.markdown(
#                             f"<div class='demo-img-label'>{s['label']}</div>",
#                             unsafe_allow_html=True
#                         )
#                         if st.button(f"Analyze →", key=f"demo_{i}", use_container_width=True):
#                             # Set up demo session
#                             st.session_state.file_path         = path
#                             st.session_state.uploaded_filename = s["label"]
#                             st.session_state.logged_in         = True
#                             st.session_state.demo_mode         = True
#                             st.session_state.user_name         = "Guest"
#                             st.session_state.patient_name      = "Demo Patient"
#                             st.session_state.patient_age       = "Unknown"
#                             st.session_state.patient_gender    = "Unknown"
#                             st.session_state._analyzing        = True
#                             st.session_state.result            = None
#                             st.session_state.report_text       = None
#                             st.session_state.pdf_bytes         = None
#                             st.session_state.show_demo         = False
#                             st.session_state.page              = "dashboard"
#                             st.rerun()
#                     else:
#                         st.warning(f"Not found:\n{path}")

#     # ── Stats strip ────────────────────────────────────────────────────────────
#     st.markdown("<div style='margin-top:60px'></div>", unsafe_allow_html=True)
#     st.markdown("""
#     <div class="ns-stats">
#         <div class="ns-stat">
#             <div class="ns-stat-val">98.65%</div>
#             <div class="ns-stat-label">Detection Accuracy</div>
#         </div>
#         <div class="ns-stat">
#             <div class="ns-stat-val">&lt; 10s</div>
#             <div class="ns-stat-label">Time to Full Report</div>
#         </div>
#         <div class="ns-stat">
#             <div class="ns-stat-val">EfficientNetB0</div>
#             <div class="ns-stat-label">Deep Learning Model</div>
#         </div>
#         <div class="ns-stat">
#             <div class="ns-stat-val">Score-CAM</div>
#             <div class="ns-stat-label">Visual Explainability</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # ── Feature Cards ──────────────────────────────────────────────────────────
#     st.markdown("""
#     <div class="ns-features">
#         <div class="ns-section-title">Why NeuroScan AI?</div>
#         <div class="ns-feature-grid">
#             <div class="ns-feature-card">
#                 <div class="ns-feature-kpi">98.65%</div>
#                 <div class="ns-feature-name">EfficientNetB0 Classification</div>
#                 <div class="ns-feature-desc">Deep residual network trained on curated MRI datasets delivering class-leading accuracy across all tumor types.</div>
#             </div>
#             <div class="ns-feature-card">
#                 <div class="ns-feature-name">GRAD-CAM++Heatmaps</div>
#                 <div class="ns-feature-desc">Visual saliency maps highlight the exact pixel regions driving each AI decision. Zero black box — full transparency.</div>
#             </div>
#             <div class="ns-feature-card">
#                 <div class="ns-feature-name">Confidence Scoring</div>
#                 <div class="ns-feature-desc">Per-class softmax confidence scores so you always know the model's certainty and when to seek a second opinion.</div>
#             </div>
#             <div class="ns-feature-card">
#                 <div class="ns-feature-name">LLM Clinical Reports</div>
#                 <div class="ns-feature-desc">AI-generated radiologist-grade summaries distill findings into clear, actionable narrative — PDF-ready in seconds.</div>
#             </div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # ── CTA Band ───────────────────────────────────────────────────────────────
#     st.markdown("""
#     <div class="ns-cta-band">
#         <div class="ns-cta-title">Ready to Analyze Your First Scan?</div>
#         <div class="ns-cta-sub">
#             Upload an MRI, get AI classification, a GRAD-CAM++heatmap,<br>
#             and a full clinical report in under 10 seconds.
#         </div>
#     </div>
#     """, unsafe_allow_html=True)
#     _, c_cta, _ = st.columns([3, 1.5, 3])
#     with c_cta:
#         if st.button("Get Started — Free", key="cta_start", type="primary", use_container_width=True):
#             st.session_state.page = "auth"
#             st.session_state.auth_tab = "signin"
#             st.rerun()

#     # ── Footer ─────────────────────────────────────────────────────────────────
#     st.markdown("""
#     <div class="ns-footer">
#         <span class="ns-footer-logo">Neuro<em>Scan</em> AI</span>
#         <span>© 2026 NeuroScan AI · Research &amp; clinical decision support only.</span>
#         <span>Privacy · Terms · Contact</span>
#     </div>
#     """, unsafe_allow_html=True)


# # ══════════════════════════════════════════════════════════════════════════════
# # AUTH PAGE
# # ══════════════════════════════════════════════════════════════════════════════
# def page_auth():
#     # Extra CSS scoped to auth page only
#     st.markdown("""
#     <style>
#     .block-container {
#         padding-top: 0 !important;
#         padding-bottom: 0 !important;
#     }
#     </style>
#     """, unsafe_allow_html=True)

#     left, right = st.columns([1, 1], gap="small")

#     # ── Left panel ─────────────────────────────────────────────────────────────
#     with left:
#         st.markdown(f"""
#         <div class="auth-left">
#             <div class="auth-grid-bg"></div>
#             <div class="auth-brain-icon" style="position:relative;z-index:1;">
#                 <img src="{LOGO_SRC}" style="width:80px;height:80px;object-fit:contain;filter:drop-shadow(0 0 30px rgba(0,212,255,0.5));" />
#             </div>
#             <div class="auth-brand-name">Neuro<em>Scan</em> AI</div>
#             <div class="auth-brand-desc">
#                 Explainable AI brain tumor detection —
#                 98.65% accuracy, GRAD-CAM++visualization,
#                 and automated LLM clinical reporting.
#             </div>
#             <div class="auth-pills">
#                 <div class="auth-pill">HIPAA-READY</div>
#                 <div class="auth-pill">ENCRYPTED</div>
#                 <div class="auth-pill">&lt; 10s RESULTS</div>
#                 <div class="auth-pill">GRAD-CAM++XAI</div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     # ── Right panel ────────────────────────────────────────────────────────────
#     with right:
#         st.markdown("<div style='padding: 60px 48px 0'>", unsafe_allow_html=True)

#         tab = st.session_state.get("auth_tab", "signin")
#         ta, tb = st.columns(2)
#         with ta:
#             if st.button("Sign In", key="tab_si",
#                          type="primary" if tab == "signin" else "secondary",
#                          use_container_width=True):
#                 st.session_state.auth_tab = "signin"; st.rerun()
#         with tb:
#             if st.button("Register", key="tab_reg",
#                          type="primary" if tab == "register" else "secondary",
#                          use_container_width=True):
#                 st.session_state.auth_tab = "register"; st.rerun()

#         st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

#         if tab == "signin":
#             st.markdown("""
#             <div style='margin-bottom:24px'>
#                 <div style='font-family:Fraunces,serif;font-size:26px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px'>Welcome back</div>
#                 <div style='font-size:13px;color:#64748b;margin-top:6px'>Sign in to access the diagnostic dashboard.</div>
#             </div>""", unsafe_allow_html=True)
#             email = st.text_input("Email Address", placeholder="doctor@hospital.org", key="si_email")
#             pw    = st.text_input("Password", type="password", placeholder="••••••••", key="si_pw")
#             st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
#             if st.button("Sign In  →", key="do_signin", type="primary", use_container_width=True):
#                 if email and pw:
#                     st.session_state.logged_in  = True
#                     st.session_state.user_email = email
#                     st.session_state.user_name  = email.split("@")[0].replace(".", " ").title()
#                     st.session_state.page       = "dashboard"
#                     st.rerun()
#                 else:
#                     st.warning("Please enter your email and password.")

#         else:
#             st.markdown("""
#             <div style='margin-bottom:24px'>
#                 <div style='font-family:Fraunces,serif;font-size:26px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px'>Create account</div>
#                 <div style='font-size:13px;color:#64748b;margin-top:6px'>Start analyzing MRI scans with AI precision.</div>
#             </div>""", unsafe_allow_html=True)
#             full   = st.text_input("Full Name", placeholder="Dr. Jane Smith", key="reg_name")
#             age    = st.number_input("Age", min_value=1, max_value=120, value=30, key="reg_age")
#             gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="reg_gender")
#             email  = st.text_input("Email Address", placeholder="doctor@hospital.org", key="reg_email")
#             pw     = st.text_input("Password", type="password", placeholder="Min. 8 chars, letters + numbers", key="reg_pw")
#             st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
#             if st.button("Create Account  →", key="do_reg", type="primary", use_container_width=True):
#                 if not (full and email and pw):
#                     st.warning("Please fill in all required fields.")
#                 else:
#                     email_ok = re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email)
#                     pw_ok    = re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", pw)
#                     if not email_ok:
#                         st.error("Please enter a valid email address.")
#                     elif not pw_ok:
#                         st.error("Password must be 8+ characters with letters and numbers.")
#                     else:
#                         st.session_state.logged_in     = True
#                         st.session_state.user_name     = full
#                         st.session_state.user_email    = email
#                         st.session_state.patient_name  = full
#                         st.session_state.patient_age   = int(age)
#                         st.session_state.patient_gender = gender
#                         st.session_state.page          = "dashboard"
#                         st.rerun()

#         st.markdown("</div>", unsafe_allow_html=True)


# # ══════════════════════════════════════════════════════════════════════════════
# # DASHBOARD PAGE
# # ══════════════════════════════════════════════════════════════════════════════
# def page_dashboard():

#     st.markdown("""
#     <style>
#     @media (max-width: 768px) {
#         [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
#         [data-testid="column"] { width: 100% !important; min-width: 100% !important; }
#         .flow-arrow { display: none !important; }
#         .panel { margin-bottom: 16px !important; }
#         .report-scroll { height: 200px !important; }
#     }
#     </style>
#     """, unsafe_allow_html=True)

#     st.markdown("""
#     <div style='background:rgba(245,158,11,0.08);border-left:3px solid #f59e0b;
#     border-radius:8px;padding:10px 16px;margin:0 0 16px;
#     font-size:12px;color:#f59e0b;font-family:DM Mono,monospace'>
#     ⚠ FOR RESEARCH USE ONLY — This AI output must be reviewed by a qualified 
#     medical professional before any clinical decisions are made.
#     </div>
#     """, unsafe_allow_html=True)
    
#     # ── Isolate dashboard from landing page widget bleed ───────────────────────
#     st.markdown("""
#     <style>
#     /* Hide any orphaned landing-page nav buttons that bleed into dashboard */
#     .block-container > div > div > div > div[data-testid="stHorizontalBlock"]:first-of-type
#         [data-testid="column"]:nth-child(3) button,
#     .block-container > div > div > div > div[data-testid="stHorizontalBlock"]:first-of-type
#         [data-testid="column"]:nth-child(4) button {
#         display: none !important;
#     }
#     </style>
#     """, unsafe_allow_html=True)
#     # ── Derive state ───────────────────────────────────────────────────────────
#     has_image    = bool(st.session_state.get("file_path"))
#     is_analyzing = st.session_state.get("_analyzing", False)
#     has_result   = st.session_state.get("result") is not None
#     has_report   = bool(st.session_state.get("report_text"))
#     user_name    = st.session_state.get("user_name", "Guest")
#     live_cls     = "live" if is_analyzing else ""

#     # ── Top Bar ────────────────────────────────────────────────────────────────
#     hd_l, hd_r = st.columns([5, 1])
#     with hd_l:
#         st.markdown(f"""
#         <div class="dash-topbar" style="position:relative;z-index:10;">
#             <div style="display:flex;align-items:center;gap:16px;">
#                 <div class="dash-logo">
#                     <div class="dash-logo-mark" style="background:transparent;box-shadow:none;">
#                         <img src="{LOGO_SRC}" style="width:32px;height:32px;object-fit:contain;border-radius:7px;" />
#                     </div>
#                     <span class="dash-logo-txt">Neuro<em>Scan</em> AI</span>
#                 </div>
#                 <div class="dash-breadcrumb">
#                     › Dashboard › <span>{user_name}</span>
#                 </div>
#             </div>
#         </div>""", unsafe_allow_html=True)
#     with hd_r:
#         st.markdown("<div style='padding-top:10px'>", unsafe_allow_html=True)
#         if st.button("← Log Out", key="logout", use_container_width=True):
#             for k in ["logged_in","result","file_path","report_text",
#                       "pdf_bytes","_analyzing","report_data","demo_mode","show_demo"]:
#                 st.session_state[k] = None if k not in ("logged_in","_analyzing","demo_mode","show_demo") else False
#             st.session_state.page = "landing"
#             st.rerun()
#         st.markdown("</div>", unsafe_allow_html=True)

#     st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

#     # ── Three-column layout ────────────────────────────────────────────────────
#     col1, col_arr1, col2, col_arr2, col3 = st.columns([10, 1, 10, 1, 10])

#     # ── BOX 1 — Upload / Preview ───────────────────────────────────────────────
#     with col1:
#         st.markdown("""
#         <div class="panel">
#             <div class="panel-header">
#                 <div class="panel-icon blue"></div>
#                 <div>
#                     <div class="panel-title">MRI Scan Input</div>
#                     <div class="panel-sub">upload or select sample</div>
#                 </div>
#             </div>
#         </div>""", unsafe_allow_html=True)

#         if has_image:
#             # Use st.empty() so the image slot is stable and doesn't reflow during analysis
#             img_placeholder = st.empty()
#             img_placeholder.image(st.session_state.file_path, use_container_width=True,
#                                   caption=f"📎  {st.session_state.uploaded_filename}")
#             # Only show action buttons when NOT analyzing — prevents the overlap glitch
#             if not is_analyzing:
#                 ca, cb = st.columns(2)
#                 with ca:
#                     if st.button("New Image", key="new_img", use_container_width=True):
#                         st.session_state.file_path   = None
#                         st.session_state.result      = None
#                         st.session_state.report_text = None
#                         st.session_state.pdf_bytes   = None
#                         st.session_state._analyzing  = False
#                         st.rerun()
#                 with cb:
#                     if not has_result:
#                         if st.button("Analyze Now", key="do_analyze",
#                                      type="primary", use_container_width=True):
#                             st.session_state._analyzing = True
#                             st.rerun()
#             else:
#                 # Clean status indicator — no widgets, no reflow
#                 st.markdown("""
#                 <div style='text-align:center;padding:12px 0'>
#                     <div style='font-family:DM Mono,monospace;font-size:11px;
#                                 color:var(--cyan);letter-spacing:1px'>
#                         ⟳ &nbsp;ANALYZING…
#                     </div>
#                 </div>""", unsafe_allow_html=True)
#         else:
#             # Only render the uploader when we are not mid-analysis
#             if not is_analyzing:
#                 uf = st.file_uploader(
#                     "Upload MRI scan", type=["jpg","jpeg","png"], key="dash_upload",
#                     help="Accepts JPG or PNG format MRI scans"
#                 )
#                 if uf:
#                     fp = os.path.join(os.path.dirname(__file__), "temp_scan.jpg")
#                     with open(fp, "wb") as f:
#                         f.write(uf.read())
#                     st.session_state.file_path         = fp
#                     st.session_state.uploaded_filename = uf.name
#                     st.rerun()
#                 else:
#                     st.markdown("""
#                     <div class="empty-state">
#                         <div class="empty-icon"></div>
#                         <div class="empty-txt">
#                             Upload an MRI scan above,<br>or use the
#                             <strong>Guest Demo</strong> on the landing page.
#                         </div>
#                     </div>""", unsafe_allow_html=True)

#     # ── Arrow 1 ────────────────────────────────────────────────────────────────
#     with col_arr1:
#         st.markdown(f"""
#         <div class="flow-arrow" style="height:300px;">
#             <div class="flow-dot {live_cls}"></div>
#             <div class="flow-dot {live_cls}"></div>
#             <div class="flow-chevron {live_cls}">›</div>
#             <div class="flow-dot {live_cls}"></div>
#             <div class="flow-dot {live_cls}"></div>
#         </div>""", unsafe_allow_html=True)

#     # ── BOX 2 — GRAD-CAM++Analysis ─────────────────────────────────────────────
#     with col2:
#         st.markdown("""
#         <div class="panel">
#             <div class="panel-header">
#                 <div class="panel-icon teal"></div>
#                 <div>
#                     <div class="panel-title">GRAD-CAM++Analysis</div>
#                     <div class="panel-sub">AI classification + heatmap</div>
#                 </div>
#             </div>
#         </div>""", unsafe_allow_html=True)

#         if is_analyzing and not has_result:
#             prog   = st.progress(0)
#             status = st.empty()
#             steps  = [
#                 ("Running EfficientNetB0 classification…", 25),
#                 ("Computing GRAD-CAM++saliency map…",       55),
#                 ("Generating LLM clinical report…",        85),
#             ]
#             for msg, val in steps:
#                 status.markdown(
#                     f"<p style='text-align:center;font-size:12px;color:var(--muted);font-family:DM Mono,monospace'>{msg}</p>",
#                     unsafe_allow_html=True)
#                 prog.progress(val)
#                 time.sleep(0.6)

#             result = run_pipeline(st.session_state.file_path)
#             pinfo  = {
#                 "name":   st.session_state.get("patient_name") or st.session_state.get("user_name") or "Anonymous",
#                 "age":    st.session_state.get("patient_age", "N/A"),
#                 "gender": st.session_state.get("patient_gender", "N/A"),
#             }
#             data        = prepare_llm_input(result, pinfo)
#             report_text = generate_report(data)
#             # data["tumor_size"] = result.get("tumor_size", {})
#             pdf_bytes   = generate_pdf(
#                 data=data,
#                 report_text=report_text,
#                 original_image_path=st.session_state.file_path,
#                 gradcam_image_path=result["explanation_plot_path"],
#                 lime_image_path=None,
#             )
#             prog.progress(100); status.empty()

#             st.session_state.result      = result
#             st.session_state.report_data = data
#             st.session_state.report_text = report_text
#             st.session_state.pdf_bytes   = pdf_bytes
#             st.session_state._analyzing  = False
#             time.sleep(0.2); st.rerun()

#         elif has_result:
#             result   = st.session_state.result
            
#             conf     = result["confidence"] * 100
#             pred     = result["prediction"]
#             is_tumor = "no_tumor" not in pred.lower()

#             badge_cls = "tumor" if is_tumor else "no-tumor"
#             cert      = ("High confidence" if conf >= 90
#                          else "Moderate confidence" if conf >= 70
#                          else "Low confidence")

#             # ── 1. Confidence chips + prediction badge ──
#             st.markdown(f"""
#             <div class="conf-row">
#                 <div class="conf-chip">
#                     <div class="conf-chip-label">Model Confidence</div>
#                     <div class="conf-chip-val">{conf:.1f}%</div>
#                 </div>
#                 <div class="conf-chip">
#                     <div class="conf-chip-label">GRAD-CAM++Score</div>
#                     <div class="conf-chip-val">{result.get('gradcam_accuracy', 0.92):.2f}</div>
#                 </div>
#             </div>
#             <div style="text-align:center;margin-bottom:16px">
#                 <span class="pred-tag {badge_cls}">{pred.upper()}</span>
#                 <div style="font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);margin-top:4px;letter-spacing:0.5px">{cert.upper()}</div>
#             </div>
#             <div style="display:flex;gap:8px;margin-bottom:6px">
#                 <div style="flex:1;font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);text-align:center;letter-spacing:0.5px">ORIGINAL MRI</div>
#                 <div style="flex:1;font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);text-align:center;letter-spacing:0.5px">GRAD-CAM++H</div>
#             </div>""", unsafe_allow_html=True)

#             # ── 2. Images ──
#             ic1, ic2 = st.columns(2)
#             with ic1:
#                 st.image(st.session_state.file_path, use_container_width=True)
#             with ic2:
#                 st.image(result["explanation_plot_path"], use_container_width=True)

#             # ── 4. Confidence bars ──
#             breakdown = result.get("confidence_breakdown", {})
#             if breakdown:
#                 st.markdown("""<div style='margin-top:12px;font-family:DM Mono,
#                 monospace;font-size:10px;color:#64748b;letter-spacing:1px;
#                 margin-bottom:6px;'>CLASS PROBABILITIES</div>""",
#                 unsafe_allow_html=True)
#                 for cls, pct in breakdown.items():
#                     bar_color = "#00d4ff" if cls == result["prediction"] else "#334155"
#                     st.markdown(f"""
#                     <div style='margin-bottom:6px;'>
#                         <div style='display:flex;justify-content:space-between;
#                         font-size:11px;margin-bottom:3px;'>
#                             <span style='color:#94a3b8;'>{cls.upper()}</span>
#                             <span style='color:#00d4ff;font-family:DM Mono,monospace;'>
#                             {pct:.1f}%</span>
#                         </div>
#                         <div style='background:#131923;border-radius:3px;height:6px;'>
#                             <div style='width:{min(pct,100)}%;background:{bar_color};
#                             height:6px;border-radius:3px;'></div>
#                         </div>
#                     </div>""", unsafe_allow_html=True)

#         else:
#             st.markdown("""
#             <div class="empty-state">
#                 <div class="empty-icon"></div>
#                 <div class="empty-txt">
#                     Upload a scan and click <strong>Analyze Now</strong>
#                     to see the GRAD-CAM++heatmap and classification here.
#                 </div>
#             </div>""", unsafe_allow_html=True)

#     # ── Arrow 2 ────────────────────────────────────────────────────────────────
#     with col_arr2:
#         st.markdown(f"""
#         <div class="flow-arrow" style="height:300px;">
#             <div class="flow-dot {live_cls}"></div>
#             <div class="flow-dot {live_cls}"></div>
#             <div class="flow-chevron {live_cls}">›</div>
#             <div class="flow-dot {live_cls}"></div>
#             <div class="flow-dot {live_cls}"></div>
#         </div>""", unsafe_allow_html=True)

#     # ── BOX 3 — Diagnostic Report ─────────────────────────────────────────────
#     with col3:
#         st.markdown("""
#         <div class="panel">
#             <div class="panel-header">
#                 <div class="panel-icon green"></div>
#                 <div>
#                     <div class="panel-title">Diagnostic Report</div>
#                     <div class="panel-sub">AI-generated clinical summary</div>
#                 </div>
#             </div>
#         </div>""", unsafe_allow_html=True)

#         if has_report:
#             pname = st.session_state.get("patient_name", "Patient")
#             rtext = st.session_state.report_text
#             st.markdown(
#                 f'<div class="report-scroll">{rtext.replace(chr(10), "<br>")}</div>',
#                 unsafe_allow_html=True
#             )
#             st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
#             st.download_button(
#                 label="⬇  Download PDF Report",
#                 data=st.session_state.pdf_bytes,
#                 file_name=f"neuroscan_{pname.replace(' ', '_')}.pdf",
#                 mime="application/pdf",
#                 type="primary",
#                 use_container_width=True
#             )
#             st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
#             if st.button("✉️  Send via Email", key="email_btn", use_container_width=True):
#                 uemail = st.session_state.get("user_email")
#                 if uemail:
#                     with st.spinner("Sending…"):
#                         ok = send_email_with_pdf(uemail, pname, st.session_state.pdf_bytes)
#                     if ok:
#                         st.success(f"Report sent to {uemail}")
#                     else:
#                         st.error("Email failed. Check SMTP settings.")
#                 else:
#                     st.warning("No email address found for this account.")
#         else:
#             st.markdown("""
#             <div class="empty-state">
#                 <div class="empty-icon"></div>
#                 <div class="empty-txt">
#                     The clinical report will appear here<br>after analysis is complete.
#                 </div>
#             </div>""", unsafe_allow_html=True)

#     # ── About ──────────────────────────────────────────────────────────────────
#     st.markdown("""
#     <div class="about-band">
#         <div>
#             <div class="about-title">About NeuroScan AI</div>
#             <div class="about-body">
#                 NeuroScan AI is an explainable deep-learning platform built for
#                 brain tumor detection from MRI scans.<br><br>
#                 Powered by an <strong style="color:#e2e8f0">EfficientNetB0 backbone</strong>
#                 and <strong style="color:#e2e8f0">GRAD-CAM++visualization</strong>, every
#                 prediction is transparent and traceable. The system generates
#                 LLM-assisted clinical summaries — giving radiologists and physicians
#                 actionable insights within seconds of upload.<br><br>
#                 Built to <em>support</em>, not replace, clinical expertise.
#                 NeuroScan AI streamlines diagnostic workflows while keeping humans firmly in control.
#             </div>
#         </div>
#         <div class="about-stats-grid">
#             <div class="about-stat-card">
#                 <div class="about-stat-val">98.65%</div>
#                 <div class="about-stat-lbl">Detection Accuracy</div>
#             </div>
#             <div class="about-stat-card">
#                 <div class="about-stat-val">EfficientNetB0</div>
#                 <div class="about-stat-lbl">Deep Learning Model</div>
#             </div>
#             <div class="about-stat-card">
#                 <div class="about-stat-val">Score-CAM</div>
#                 <div class="about-stat-lbl">Explainability Method</div>
#             </div>
#             <div class="about-stat-card">
#                 <div class="about-stat-val">&lt; 10s</div>
#                 <div class="about-stat-lbl">Time to Full Report</div>
#             </div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # ── Footer ─────────────────────────────────────────────────────────────────
#     st.markdown("""
#     <div class="ns-footer">
#         <span class="ns-footer-logo">Neuro<em>Scan</em> AI</span>
#         <span>© 2026 NeuroScan AI · Research &amp; clinical decision support only.</span>
#         <span>Privacy · Terms · Contact</span>
#     </div>
#     """, unsafe_allow_html=True)


# # ══════════════════════════════════════════════════════════════════════════════
# # ROUTER
# # ══════════════════════════════════════════════════════════════════════════════
# current_page = st.session_state.get("page", "landing")

# if current_page == "landing":
#     with st.container():
#         page_landing()

# elif current_page == "auth":
#     with st.container():
#         page_auth()

# elif current_page == "dashboard":
#     is_auth = st.session_state.get("logged_in", False)
#     is_demo = st.session_state.get("demo_mode", False)
#     if is_auth or is_demo:
#         with st.container():
#             page_dashboard()
#     else:
#         st.session_state.page = "auth"
#         st.rerun()

# else:
#     st.session_state.page = "landing"
#     st.rerun()

import streamlit as st
import streamlit.components.v1 as components
import sys
import os
import time
import re
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from inference import run_pipeline
from llm_report import prepare_llm_input, generate_report, generate_pdf

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


# ── Load logo once at startup ──────────────────────────────────────────────────
def get_logo_b64():
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "final_logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = get_logo_b64()
LOGO_SRC = f"data:image/png;base64,{LOGO_B64}" if LOGO_B64 else ""


# ── Load the anatomical brain model once at startup ─────────────────────────────
def get_brain_model_b64():
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "brain_model.glb")
    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

BRAIN_MODEL_B64 = get_brain_model_b64()


# ── Interactive brain explorer: hover-highlighted regions, click-to-zoom, live info panel ──
def render_brain_explorer(height=520):
    canvas_h = height - 20
    html = f"""
    <div id="explorerRoot" style="width:100%;height:{height}px;background:#05070c;position:relative;box-sizing:border-box;display:flex;align-items:center;justify-content:center;">
      <div id="explorerRow" style="display:flex;gap:18px;height:{canvas_h}px;width:100%;position:relative;">
        <button id="closeBtn" style="display:none;position:absolute;top:-44px;right:0;z-index:100;
             width:32px;height:32px;border-radius:50%;border:1px solid rgba(255,255,255,0.15);
             background:rgba(13,17,23,0.9);color:#94a3b8;font-size:16px;cursor:pointer;line-height:1;">✕</button>
        <div style="flex:0 0 56%;position:relative;border:1px solid rgba(255,255,255,0.07);
                    border-radius:12px;overflow:hidden;background:radial-gradient(circle at 50% 40%,rgba(0,40,55,0.22),rgba(4,6,10,0.5));">
          <canvas id="brainCanvas" style="width:100%;height:100%;display:block;cursor:pointer;"></canvas>
          <div id="brainLoading" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
               color:#4a5568;font-family:'DM Mono',monospace;font-size:11px;letter-spacing:1px;text-align:center;padding:20px;">
            LOADING BRAIN MODEL…
          </div>
          <div id="brainTag" style="position:absolute;pointer-events:none;display:none;
               background:rgba(8,12,20,0.92);border:1px solid rgba(0,212,255,0.35);border-radius:5px;
               padding:5px 10px;font-family:'DM Mono',monospace;font-size:11px;color:#fff;z-index:40;"></div>
          <div style="position:absolute;bottom:10px;left:0;right:0;text-align:center;font-family:'DM Mono',monospace;
               font-size:10px;letter-spacing:1px;color:#4a5568;">HOVER TO EXPLORE &nbsp;·&nbsp; CLICK TO ZOOM IN</div>
        </div>
        <div id="infoPanel" style="flex:1;border:1px solid rgba(255,255,255,0.07);border-radius:12px;
             background:#0d1117;padding:22px;overflow-y:auto;font-family:'DM Sans',sans-serif;color:#e2e8f0;
             display:flex;flex-direction:column;justify-content:center;"></div>
      </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <script>
    (function() {{
        const canvas = document.getElementById('brainCanvas');
        const tag    = document.getElementById('brainTag');
        const panel  = document.getElementById('infoPanel');
        const H = {canvas_h};
        let W = canvas.clientWidth || 400;

        const scene    = new THREE.Scene();
        const camera   = new THREE.PerspectiveCamera(42, W / H, 0.1, 100);
        camera.position.set(0, 0, 7.0);
        const renderer = new THREE.WebGLRenderer({{ canvas: canvas, alpha: true, antialias: true }});
        renderer.setSize(W, H);
        renderer.setPixelRatio(window.devicePixelRatio || 1);

        // ── Load the real anatomical brain model (.glb), Fresnel hologram shader ──
        const brain = new THREE.Group();
        scene.add(brain);
        let halfExtents = new THREE.Vector3(2, 1.64, 2.3);
        let modelReady = false;

        const hologramMaterial = new THREE.ShaderMaterial({{
            uniforms: {{
                baseColor: {{ value: new THREE.Color(0x0a6cff) }},
                rimColor:  {{ value: new THREE.Color(0x9fe8ff) }},
                opacity:   {{ value: 1.0 }}
            }},
            vertexShader: `
                varying vec3 vNormal;
                varying vec3 vViewDir;
                void main() {{
                    vNormal = normalize(normalMatrix * normal);
                    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                    vViewDir = normalize(-mvPosition.xyz);
                    gl_Position = projectionMatrix * mvPosition;
                }}
            `,
            fragmentShader: `
                uniform vec3 baseColor;
                uniform vec3 rimColor;
                uniform float opacity;
                varying vec3 vNormal;
                varying vec3 vViewDir;
                void main() {{
                    vec3 N = normalize(vNormal);
                    vec3 V = normalize(vViewDir);
                    vec3 L = normalize(vec3(0.35, 0.65, 0.9));
                    float diff = max(dot(N, L), 0.0);
                    float fresnel = pow(1.0 - max(dot(N, V), 0.0), 2.6);
                    vec3 finalColor = baseColor * (0.05 + diff * 0.55) + rimColor * fresnel * 0.85;
                    float alpha = opacity * clamp(0.55 + diff * 0.25 + fresnel * 0.45, 0.0, 1.0);
                    gl_FragColor = vec4(finalColor, alpha);
                }}
            `,
            transparent: true, blending: THREE.NormalBlending, depthWrite: true, side: THREE.FrontSide
        }});


        function b64ToArrayBuffer(b64) {{
            const binary = atob(b64);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
            return bytes.buffer;
        }}

        const loadingEl = document.getElementById('brainLoading');
        const MODEL_B64 = "{BRAIN_MODEL_B64}";
        if (MODEL_B64) {{
            const loader = new THREE.GLTFLoader();
            loader.parse(b64ToArrayBuffer(MODEL_B64), '', function(gltf) {{
                const model = gltf.scene;
                const box = new THREE.Box3().setFromObject(model);
                const size = new THREE.Vector3(); box.getSize(size);
                const center = new THREE.Vector3(); box.getCenter(center);
                const maxDim = Math.max(size.x, size.y, size.z) || 1;
                const scale = 4.2 / maxDim;
                model.position.copy(center).multiplyScalar(-scale);
                model.scale.setScalar(scale);
                halfExtents.set((size.x*scale)/2, (size.y*scale)/2, (size.z*scale)/2);
                const meshList = [];
                model.traverse(function(child) {{ if (child.isMesh) meshList.push(child); }});
                meshList.forEach(function(child) {{
                    child.material = hologramMaterial;
                    const wire = new THREE.Mesh(
                        child.geometry,
                        new THREE.MeshBasicMaterial({{ color: 0x9fe8ff, wireframe: true, transparent: true, opacity: 0.10, depthWrite: false }})
                    );
                    child.add(wire);
                }});
                brain.add(model);
                modelReady = true;
                if (loadingEl) loadingEl.style.display = 'none';
            }}, function(err) {{
                console.error('Brain model failed to load', err);
                if (loadingEl) loadingEl.textContent = 'Could not load brain_model.glb — check the file.';
            }});
        }} else if (loadingEl) {{
            loadingEl.textContent = 'brain_model.glb not found in app/assets/';
        }}

        scene.add(new THREE.AmbientLight(0x3a4a5a, 1.0));
        const key = new THREE.PointLight(0x00d4ff, 1.5, 20); key.position.set(4,3,5); scene.add(key);
        const rim = new THREE.PointLight(0x0077ff, 0.8, 20); rim.position.set(-4,-2,-5); scene.add(rim);

        // ── Soft glow sprite that snaps to whichever region is hovered/selected ──
        function buildGlowTexture() {{
            const s = 128;
            const c = document.createElement('canvas'); c.width = s; c.height = s;
            const ctx = c.getContext('2d');
            const g = ctx.createRadialGradient(s/2, s/2, 0, s/2, s/2, s/2);
            g.addColorStop(0, 'rgba(255,255,255,0.95)');
            g.addColorStop(0.35, 'rgba(255,255,255,0.55)');
            g.addColorStop(1, 'rgba(255,255,255,0)');
            ctx.fillStyle = g;
            ctx.fillRect(0, 0, s, s);
            return new THREE.CanvasTexture(c);
        }}
        const glowTex = buildGlowTexture();
        const patchMat = new THREE.SpriteMaterial({{
            map: glowTex, color: 0x00d4ff, transparent: true, opacity: 0.9,
            blending: THREE.AdditiveBlending, depthWrite: false
        }});
        const patch = new THREE.Sprite(patchMat);
        patch.scale.set(0.5, 0.5, 0.5);
        patch.visible = false;
        scene.add(patch);

        // ── Region library: geometry rule + full study info ──
        const REGIONS = [
            {{ key:'brainstem', name:'Brainstem', color:0xff3b3b, anchor:[0,-0.85,0],
               test:(n)=> n.y < -0.72 && Math.abs(n.x) < 0.22 && n.z > -0.35 && n.z < 0.35,
               fn:'Controls vital automatic functions — breathing, heart rate, blood pressure — and links the brain to the spinal cord.',
               strengthen:'Regular cardiovascular exercise and good respiratory health support the systems it regulates.',
               diseases:'Brainstem stroke or injury is serious and can affect breathing and consciousness; rare tumors can also occur here.',
               precaution:'This is a critical structure — sudden severe headache, loss of consciousness, or breathing trouble need emergency care.' }},
            {{ key:'temporal', name:'Temporal Lobe', color:0xffd400, anchor:[0.75,-0.1,0.1],
               test:(n)=> Math.abs(n.x) > 0.58,
               fn:'Handles hearing, language comprehension, and forming and recalling memories.',
               strengthen:'Listening to music, learning languages, reading, and conversation all engage this region.',
               diseases:'Linked to temporal lobe epilepsy, memory disorders, and is often among the earliest areas affected in Alzheimer\\'s disease.',
               precaution:'Protect hearing from loud noise, stay socially and mentally active, and treat hearing loss early.' }},
            {{ key:'cerebellum', name:'Cerebellum', color:0xff2e9e, anchor:[0,-0.55,-0.6],
               test:(n)=> n.y < -0.30 && n.z < -0.05,
               fn:'Coordinates balance, posture, and fine motor movements.',
               strengthen:'Balance exercises, dancing, and sports involving coordination help maintain this region.',
               diseases:'Damage or degeneration causes ataxia (loss of coordination); can be affected by alcohol misuse or genetic conditions.',
               precaution:'Limit excessive alcohol, prevent falls and head injuries, and raise balance issues with a doctor early.' }},
            {{ key:'occipital', name:'Occipital Lobe', color:0x2ee88a, anchor:[0,0.1,-0.85],
               test:(n)=> n.z < -0.42,
               fn:'The brain\\'s main visual processing center — interprets shapes, color, and motion from the eyes.',
               strengthen:'Regular eye checkups, good lighting when reading, and visual exercises support this region.',
               diseases:'Occipital strokes, migraine with visual aura, and certain seizures can originate here.',
               precaution:'Protect eyes from injury, manage migraine triggers, and get regular vision and blood pressure checks.' }},
            {{ key:'parietal', name:'Parietal Lobe', color:0x7c5cff, anchor:[0,0.65,-0.1],
               test:(n)=> n.y > 0.28,
               fn:'Processes touch and spatial awareness, and helps integrate senses for navigation and coordination.',
               strengthen:'Spatial-reasoning activities — map reading, sports, dance — stimulate this region.',
               diseases:'Certain strokes here can cause spatial neglect or coordination difficulty.',
               precaution:'Manage blood pressure and diabetes — stroke is a leading cause of parietal lobe damage.' }},
            {{ key:'frontal', name:'Frontal Lobe', color:0x00e5ff, anchor:[0,0.1,0.8],
               test:(n)=> true,
               fn:'Handles decision-making, planning, problem-solving, movement, and personality regulation.',
               strengthen:'Puzzles, learning new skills, regular exercise, and quality sleep all support this region.',
               diseases:'Linked to stroke, traumatic brain injury, frontotemporal dementia, and some frontal lobe epilepsy.',
               precaution:'Wear helmets during sports/cycling, manage blood pressure and cholesterol, and seek care after any head injury.' }},
        ];
        function classify(localPoint) {{
            const n = new THREE.Vector3(localPoint.x/halfExtents.x, localPoint.y/halfExtents.y, localPoint.z/halfExtents.z);
            for (const r of REGIONS) {{ if (r.test(n)) return r; }}
            return REGIONS[REGIONS.length-1];
        }}

        function focusRegion(region, localPt) {{
            selected = region; zoomed = true;
            targetRotY = Math.atan2(-localPt.x, localPt.z);
            targetRotX = Math.max(-0.5, Math.min(0.5, -Math.atan2(localPt.y, Math.sqrt(localPt.x*localPt.x+localPt.z*localPt.z)) * 0.5));
            renderPanel(region, localPt);
            if (root.requestFullscreen) {{ root.requestFullscreen().catch(function(){{}}); }}
        }}

        function selectRegionByKey(key) {{
            const region = REGIONS.find(function(r) {{ return r.key === key; }});
            if (!region) return;
            const localPt = new THREE.Vector3(region.anchor[0]*halfExtents.x, region.anchor[1]*halfExtents.y, region.anchor[2]*halfExtents.z);
            focusRegion(region, localPt);
        }}

        function renderDefaultPanel() {{
            let legend = '';
            REGIONS.forEach(function(r) {{
                legend += '<button class="legendBtn" data-key="' + r.key + '" style="display:flex;align-items:center;gap:8px;' +
                    'margin-bottom:7px;width:100%;background:none;border:none;text-align:left;cursor:pointer;padding:6px 8px;' +
                    'border-radius:6px;">' +
                    '<span style="width:10px;height:10px;border-radius:50%;background:#' + r.color.toString(16).padStart(6,'0') + ';flex:0 0 auto;"></span>' +
                    '<span style="font-size:12px;color:#cbd5e1;">' + r.name + '</span></button>';
            }});
            panel.innerHTML =
              '<div style="font-family:\\'DM Mono\\',monospace;font-size:10px;letter-spacing:1.5px;color:#00d4ff;margin-bottom:10px;">BRAIN EXPLORER</div>' +
              '<div style="font-size:16px;font-weight:700;color:#f8fafc;margin-bottom:8px;">Explore the regions</div>' +
              '<div style="font-size:12.5px;color:#94a3b8;line-height:1.6;margin-bottom:18px;">Hover over the brain to see each region highlighted in its own color, or click a name below to jump straight to it.</div>' +
              '<div style="font-size:11px;color:#64748b;font-weight:700;letter-spacing:0.5px;margin-bottom:10px;">REGION KEY — CLICK TO VIEW</div>' +
              legend;
            panel.querySelectorAll('.legendBtn').forEach(function(btn) {{
                btn.onmouseenter = function() {{ btn.style.background = 'rgba(255,255,255,0.06)'; }};
                btn.onmouseleave = function() {{ btn.style.background = 'none'; }};
                btn.onclick = function() {{ selectRegionByKey(btn.dataset.key); }};
            }});
        }}

        function renderPanel(region, hitLocal) {{
            patch.visible = true;
            patch.material.color.setHex(region.color);
            const worldPt = hitLocal.clone().applyMatrix4(brain.matrixWorld);
            patch.position.copy(worldPt);

            panel.innerHTML =
              '<div style="font-family:\\'DM Mono\\',monospace;font-size:10px;letter-spacing:1.5px;color:#' + region.color.toString(16).padStart(6,'0') + ';margin-bottom:10px;">SELECTED REGION</div>' +
              '<div style="font-size:18px;font-weight:800;color:#f8fafc;margin-bottom:12px;">' + region.name + '</div>' +
              '<div style="font-size:11px;color:#00d4ff;font-weight:700;letter-spacing:0.5px;margin-bottom:4px;">FUNCTION</div>' +
              '<div style="font-size:12.5px;color:#cbd5e1;line-height:1.55;margin-bottom:14px;">' + region.fn + '</div>' +
              '<div style="font-size:11px;color:#00e5a0;font-weight:700;letter-spacing:0.5px;margin-bottom:4px;">HOW TO KEEP IT STRONG</div>' +
              '<div style="font-size:12.5px;color:#cbd5e1;line-height:1.55;margin-bottom:14px;">' + region.strengthen + '</div>' +
              '<div style="font-size:11px;color:#ff4d6d;font-weight:700;letter-spacing:0.5px;margin-bottom:4px;">RELATED CONDITIONS</div>' +
              '<div style="font-size:12.5px;color:#cbd5e1;line-height:1.55;margin-bottom:14px;">' + region.diseases + '</div>' +
              '<div style="font-size:11px;color:#f59e0b;font-weight:700;letter-spacing:0.5px;margin-bottom:4px;">PRECAUTIONS</div>' +
              '<div style="font-size:12.5px;color:#cbd5e1;line-height:1.55;margin-bottom:16px;">' + region.precaution + '</div>' +
              '<div style="font-size:10px;color:#4a5568;margin-bottom:14px;">General education only — not medical advice.</div>' +
              '<button id="backBtn" style="background:#131923;border:1px solid rgba(255,255,255,0.12);color:#94a3b8;' +
              'padding:8px 16px;border-radius:6px;font-size:12px;cursor:pointer;">&larr; Back to full brain</button>';

            document.getElementById('backBtn').onclick = exitZoom;
        }}
        renderDefaultPanel();

        function exitZoom() {{
            zoomed = false; selected = null; patch.visible = false;
            if (document.fullscreenElement) document.exitFullscreen();
            renderDefaultPanel();
        }}
        document.getElementById('closeBtn').onclick = exitZoom;

        // ── Interaction state ──
        let targetRotY=0, targetRotX=0, curRotY=0, curRotX=0, autoSpin=0;
        let zoomed=false, selected=null;
        const raycaster = new THREE.Raycaster();
        const mouseNdc = new THREE.Vector2(0,0);
        const root = document.getElementById('explorerRoot');
        const row  = document.getElementById('explorerRow');

        function updateHover() {{
            if (zoomed) return;
            raycaster.setFromCamera(mouseNdc, camera);
            const hits = raycaster.intersectObject(brain, true);
            if (hits.length) {{
                const localPt = brain.worldToLocal(hits[0].point.clone());
                const region = classify(localPt);
                tag.textContent = region.name;
                tag.style.display = 'block';
                patch.visible = true;
                patch.material.color.setHex(region.color);
                patch.position.copy(hits[0].point);
            }} else {{
                tag.style.display = 'none';
                if (!selected) patch.visible = false;
            }}
        }}

        function onMove(e) {{
            const rect = canvas.getBoundingClientRect();
            const mx = (e.clientX-rect.left)/rect.width, my=(e.clientY-rect.top)/rect.height;
            mouseNdc.x = mx*2-1; mouseNdc.y = -(my*2-1);
            if (!zoomed) {{ targetRotY = (mx-0.5)*0.9; targetRotX = (my-0.5)*-0.5; }}
            tag.style.left = (e.clientX-rect.left+14)+'px';
            tag.style.top  = (e.clientY-rect.top-8)+'px';
            updateHover();
        }}
        canvas.addEventListener('mousemove', onMove);
        canvas.addEventListener('mouseleave', function() {{ if(!zoomed){{targetRotX=0;targetRotY=0;}} tag.style.display='none'; }});

        function resizeToContainer() {{
            W = canvas.clientWidth;
            const newH = canvas.clientHeight;
            camera.aspect = W / newH;
            camera.updateProjectionMatrix();
            renderer.setSize(W, newH);
        }}

        const closeBtn = document.getElementById('closeBtn');
        document.addEventListener('fullscreenchange', function() {{
            const isFs = document.fullscreenElement === root;
            if (isFs) {{
                root.style.height = '100vh';
                root.style.width = '100vw';
                root.style.maxWidth = '1600px';
                root.style.margin = '0 auto';
                root.style.padding = '32px';
                row.style.height = Math.round(window.innerHeight - 130) + 'px';
                closeBtn.style.display = 'flex';
                closeBtn.style.alignItems = 'center';
                closeBtn.style.justifyContent = 'center';
            }} else {{
                root.style.height = '{height}px';
                root.style.width = '100%';
                root.style.margin = '0';
                root.style.padding = '0';
                row.style.height = '{canvas_h}px';
                closeBtn.style.display = 'none';
            }}
            [30, 150, 350].forEach(function(ms) {{ setTimeout(resizeToContainer, ms); }});
        }});

        canvas.addEventListener('click', function() {{
            raycaster.setFromCamera(mouseNdc, camera);
            const hits = raycaster.intersectObject(brain, true);
            if (!hits.length) return;
            const localPt = brain.worldToLocal(hits[0].point.clone());
            focusRegion(classify(localPt), localPt);
        }});

        function animate() {{
            requestAnimationFrame(animate);
            autoSpin += zoomed ? 0 : 0.0015;
            curRotY += (targetRotY - curRotY) * 0.08;
            curRotX += (targetRotX - curRotX) * 0.08;
            brain.rotation.y = curRotY + autoSpin;
            brain.rotation.x = curRotX;
            camera.position.z += ((zoomed ? 4.6 : 7.0) - camera.position.z) * 0.06;
            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener('resize', resizeToContainer);
    }})();
    </script>
    """
    components.html(html, height=height, scrolling=False)


# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NeuroScan AI · Brain Tumor Detection",
    page_icon="final_logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,500;0,700;0,900;1,300;1,500;1,700;1,900&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@300;400;500&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --bg:        #07090f;
    --surface:   #0d1117;
    --surface2:  #131923;
    --border:    rgba(255,255,255,0.07);
    --border2:   rgba(255,255,255,0.12);
    --cyan:      #00d4ff;
    --cyan-dim:  rgba(0,212,255,0.15);
    --cyan-glow: rgba(0,212,255,0.35);
    --green:     #00e5a0;
    --red:       #ff4d6d;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --muted2:    #94a3b8;
}

/* ── MOBILE RESPONSIVENESS ── */
@media (max-width: 768px) {
    .ns-hero-h1 { font-size: 36px !important; letter-spacing: -1px !important; }
    .ns-hero-sub { font-size: 14px !important; }
    .ns-nav { padding: 0 16px !important; }
    .ns-stats { grid-template-columns: repeat(2, 1fr) !important; }
    .ns-feature-grid { grid-template-columns: 1fr 1fr !important; }
    .ns-features { padding: 40px 20px !important; }
    .ns-cta-band { margin: 0 16px 40px !important; padding: 40px 24px !important; }
    .ns-footer { padding: 16px 20px !important; flex-direction: column !important; gap: 8px !important; }
    .about-band { margin: 16px !important; padding: 24px !important; grid-template-columns: 1fr !important; }
    .dash-topbar { padding: 0 16px !important; }
    .auth-left { min-height: 30vh !important; padding: 32px 20px !important; }
}

@media (max-width: 480px) {
    .ns-hero-h1 { font-size: 28px !important; }
    .ns-stats { grid-template-columns: 1fr !important; }
    .ns-feature-grid { grid-template-columns: 1fr !important; }
    .ns-section-title { font-size: 28px !important; }
    .ns-cta-title { font-size: 24px !important; }
    .about-stats-grid { grid-template-columns: 1fr 1fr !important; }
}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    font-family: 'DM Sans', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="collapsedControl"],
.stDeployButton,
section[data-testid="stSidebar"] { display: none !important; }

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ═══════════════════════════════════════
   SHARED COMPONENTS
═══════════════════════════════════════ */

/* Scanline overlay for depth */
body::after {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,0,0,0.03) 2px,
        rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

.ns-badge {
    display: inline-flex; align-items: center; gap: 7px;
    background: var(--cyan-dim);
    border: 1px solid rgba(0,212,255,0.3);
    color: var(--cyan);
    padding: 5px 14px; border-radius: 4px;
    font-family: 'DM Mono', monospace;
    font-size: 11px; font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.ns-badge::before {
    content: '●';
    font-size: 8px;
    animation: blink 1.8s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }

/* ═══════════════════════════════════════
   LANDING PAGE
═══════════════════════════════════════ */

/* Top Nav */
.ns-nav {
    background: rgba(7,9,15,0.96);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border);
    padding: 0 56px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.ns-logo {
    display: flex; align-items: center; gap: 10px;
}
.ns-logo-mark {
    width: 36px; height: 36px;
    background: var(--cyan);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    box-shadow: 0 0 20px var(--cyan-glow);
}
.ns-logo-mark img {
    filter: drop-shadow(0 0 12px rgba(0,212,255,0.6));
}
.ns-logo-text {
    font-family: 'Fraunces', serif;
    font-size: 18px; font-weight: 800;
    color: #f1f5f9;
    letter-spacing: -0.3px;
}
.ns-logo-text em { color: var(--cyan); font-style: normal; }

/* Hero */
.ns-hero {
    position: relative;
    padding: 100px 48px 60px;
    text-align: center;
    overflow: hidden;
}
.ns-hero-grid {
    position: absolute; inset: 0;
    background-image:
        linear-gradient(rgba(0,212,255,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,255,0.04) 1px, transparent 1px);
    background-size: 60px 60px;
    mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, black 30%, transparent 100%);
}
.ns-hero-glow {
    position: absolute;
    top: -100px; left: 50%; transform: translateX(-50%);
    width: 600px; height: 400px;
    background: radial-gradient(ellipse, rgba(0,212,255,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.ns-hero-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 11px; color: var(--cyan);
    letter-spacing: 2px; text-transform: uppercase;
    margin-bottom: 24px;
    display: flex; align-items: center; justify-content: center; gap: 10px;
}
.ns-hero-eyebrow::before, .ns-hero-eyebrow::after {
    content: '';
    display: block; width: 40px; height: 1px;
    background: linear-gradient(90deg, transparent, var(--cyan));
}
.ns-hero-eyebrow::after { background: linear-gradient(90deg, var(--cyan), transparent); }

.ns-hero-h1 {
    font-family: 'Fraunces', serif;
    font-size: 68px; font-weight: 900;
    color: #f8fafc;
    line-height: 1.05;
    letter-spacing: -2px;
    margin-bottom: 24px;
    position: relative; z-index: 1;
}
.ns-hero-h1 .line2 {
    color: var(--cyan);
    font-style: italic;
    display: block;
}
.ns-hero-sub {
    font-size: 18px; color: var(--muted2); line-height: 1.7;
    max-width: 580px; margin: 0 auto 48px;
    position: relative; z-index: 1;
}

/* Stats strip */
.ns-stats {
    display: grid; grid-template-columns: repeat(3,1fr);
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    background: var(--surface);
    margin: 0;
}
.ns-stat {
    text-align: center;
    padding: 28px 24px;
    border-right: 1px solid var(--border);
    position: relative;
}
.ns-stat:last-child { border-right: none; }
.ns-stat::before {
    content: '';
    position: absolute; top: 0; left: 50%; transform: translateX(-50%);
    width: 40px; height: 2px;
    background: var(--cyan);
    opacity: 0.5;
}
.ns-stat-val {
    font-family: 'Fraunces', serif;
    font-size: clamp(16px, 2.5vw, 32px); font-weight: 900; color: var(--cyan);
    letter-spacing: -0.5px; line-height: 1.2;
    margin-bottom: 6px;
    word-break: break-word;
}
.ns-stat-label {
    font-family: 'DM Mono', monospace;
    font-size: 11px; color: var(--muted);
    letter-spacing: 1px; text-transform: uppercase;
}

/* Features */
.ns-features {
    padding: 80px 80px;
    background: var(--bg);
}
.ns-section-kicker {
    font-family: 'DM Mono', monospace;
    font-size: 11px; font-weight: 500;
    color: var(--cyan); letter-spacing: 2px;
    text-transform: uppercase; margin-bottom: 16px;
    text-align: center;
}
.ns-section-title {
    font-family: 'Fraunces', serif;
    font-size: 44px; font-weight: 900; color: #f8fafc;
    text-align: center; letter-spacing: -1.5px;
    margin-bottom: 56px;
}
.ns-feature-grid {
    display: grid; grid-template-columns: repeat(4,1fr);
    gap: 1px;
    border: 1px solid var(--border);
    border-radius: 16px;
    overflow: hidden;
    max-width: 1200px; margin: 0 auto;
}
.ns-feature-card {
    background: var(--surface);
    padding: 36px 28px;
    transition: all 0.3s;
    position: relative;
}
.ns-feature-card::after {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
    opacity: 0;
    transition: opacity 0.3s;
}
.ns-feature-card:hover { background: var(--surface2); }
.ns-feature-card:hover::after { opacity: 1; }
.ns-feature-num {
    font-family: 'DM Mono', monospace;
    font-size: 11px; color: var(--muted);
    letter-spacing: 1px; margin-bottom: 20px;
}
.ns-feature-icon { font-size: 28px; margin-bottom: 16px; display: block; }
.ns-feature-kpi {
    font-family: 'Fraunces', serif;
    font-size: 28px; font-weight: 900;
    color: var(--cyan); margin-bottom: 8px;
}
.ns-feature-name {
    font-size: 15px; font-weight: 700;
    color: var(--text); margin-bottom: 10px;
}
.ns-feature-desc { font-size: 13px; color: var(--muted); line-height: 1.7; }

/* CTA band */
.ns-cta-band {
    margin: 0 80px 80px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 72px 80px;
    text-align: center; position: relative; overflow: hidden;
}
.ns-cta-band::before {
    content:'';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
}
.ns-cta-title {
    font-family: 'Fraunces', serif;
    font-size: 40px; font-weight: 900;
    color: #fff; margin-bottom: 14px; letter-spacing: -1px;
}
.ns-cta-sub {
    font-size: 16px; color: var(--muted2);
    margin-bottom: 0; line-height: 1.7;
}

/* Footer */
.ns-footer {
    border-top: 1px solid var(--border);
    padding: 24px 80px;
    display: flex; align-items: center; justify-content: space-between;
    font-family: 'DM Mono', monospace;
    font-size: 11px; color: var(--muted);
    letter-spacing: 0.5px;
}
.ns-footer-logo {
    font-family: 'Fraunces', serif;
    font-weight: 700; color: var(--muted2);
    font-size: 14px; letter-spacing: -0.3px;
}
.ns-footer-logo em { color: var(--cyan); font-style: normal; }

/* Demo gallery */
.demo-gallery {
    margin-top: 40px;
    padding: 32px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    position: relative;
}
.demo-gallery::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--cyan) 30%, var(--green) 70%, transparent);
}
.demo-gallery-title {
    font-family: 'DM Mono', monospace;
    font-size: 11px; color: var(--cyan);
    letter-spacing: 2px; text-transform: uppercase;
    text-align: center; margin-bottom: 24px;
}
.demo-img-label {
    font-family: 'DM Mono', monospace;
    font-size: 11px; color: var(--muted2);
    letter-spacing: 1px; text-transform: uppercase;
    text-align: center; margin-top: 10px; margin-bottom: 8px;
}

/* ═══════════════════════════════════════
   AUTH PAGE
═══════════════════════════════════════ */
.auth-left {
    background:
        radial-gradient(ellipse 80% 60% at 30% 40%, rgba(0,212,255,0.10), transparent 70%),
        linear-gradient(135deg, #0a1628 0%, #07090f 100%);
    min-height: 100vh;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    text-align: center; padding: 60px 40px;
    position: relative;
}
.auth-grid-bg {
    position: absolute; inset: 0;
    background-image:
        linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    border-radius: inherit;
}
.auth-brain-icon {
    font-size: 64px;
    margin-bottom: 24px;
    filter: drop-shadow(0 0 30px rgba(0,212,255,0.5));
    position: relative; z-index: 1;
}
.auth-brand-name {
    font-family: 'Fraunces', serif;
    font-size: 36px; font-weight: 900; color: #f8fafc;
    margin-bottom: 14px; letter-spacing: -1px;
    position: relative; z-index: 1;
}
.auth-brand-name em { color: var(--cyan); font-style: normal; }
.auth-brand-desc {
    font-size: 14px; color: rgba(255,255,255,0.55);
    line-height: 1.8; max-width: 300px;
    position: relative; z-index: 1;
}
.auth-pills {
    display: flex; gap: 8px; margin-top: 32px;
    flex-wrap: wrap; justify-content: center;
    position: relative; z-index: 1;
}
.auth-pill {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px; padding: 5px 12px;
    font-family: 'DM Mono', monospace;
    font-size: 11px; color: rgba(255,255,255,0.55);
    letter-spacing: 0.5px;
}

/* ═══════════════════════════════════════
   DASHBOARD
═══════════════════════════════════════ */
.dash-topbar {
    background: rgba(7,9,15,0.98);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border);
    padding: 0 40px;
    height: 60px;
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 999;
}
.dash-logo { display: flex; align-items: center; gap: 10px; }
.dash-logo-mark {
    width: 32px; height: 32px;
    background: var(--cyan);
    border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px;
    box-shadow: 0 0 15px var(--cyan-glow);
}
.dash-logo-txt {
    font-family: 'Fraunces', serif;
    font-size: 16px; font-weight: 700; color: #f1f5f9;
    letter-spacing: -0.3px;
}
.dash-logo-txt em { color: var(--cyan); font-style: normal; }
.dash-breadcrumb {
    font-family: 'DM Mono', monospace;
    font-size: 11px; color: var(--muted);
    letter-spacing: 0.5px;
    display: flex; align-items: center; gap: 8px;
}
.dash-breadcrumb span { color: var(--cyan); }

/* Panel boxes */
.panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    height: 100%;
}
.panel-header {
    display: flex; align-items: center; gap: 12px;
    padding: 18px 20px;
    border-bottom: 1px solid var(--border);
    background: var(--surface2);
}
.panel-icon {
    width: 38px; height: 38px; border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: -0.5px;
}
.panel-icon.blue  { background: rgba(0,212,255,0.12); }
.panel-icon.teal  { background: rgba(0,229,160,0.10); }
.panel-icon.green { background: rgba(34,197,94,0.10); }
.panel-title {
    font-family: 'DM Sans', sans-serif;
    font-size: 14px; font-weight: 700; color: var(--text);
}
.panel-sub {
    font-family: 'DM Mono', monospace;
    font-size: 10px; color: var(--muted);
    letter-spacing: 0.5px; margin-top: 2px;
}
.panel-body { padding: 20px; }

/* Arrow connector */
.flow-arrow {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 100%;
}
.flow-dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: var(--border2);
    margin: 3px 0;
    transition: all 0.3s;
}
.flow-dot.live {
    background: var(--cyan);
    box-shadow: 0 0 8px var(--cyan);
    animation: pulse-dot 0.9s infinite alternate;
}
@keyframes pulse-dot { from{opacity:0.4} to{opacity:1} }
.flow-chevron {
    font-size: 18px; color: var(--border2);
    margin: 2px 0; transition: color 0.3s;
}
.flow-chevron.live { color: var(--cyan); }

/* Empty state */
.empty-state {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    text-align: center; padding: 48px 20px;
    min-height: 220px;
}
.empty-icon { font-size: 36px; opacity: 0.15; margin-bottom: 14px; }
.empty-txt {
    font-size: 13px; color: var(--muted); line-height: 1.7;
}
.empty-txt strong { color: var(--muted2); }

/* Confidence pills */
.conf-row { display: flex; gap: 10px; margin-bottom: 16px; }
.conf-chip {
    flex: 1;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 9px; padding: 12px;
    text-align: center;
}
.conf-chip-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px; color: var(--muted);
    letter-spacing: 0.5px; margin-bottom: 4px;
}
.conf-chip-val {
    font-family: 'Fraunces', serif;
    font-size: 22px; font-weight: 900; color: var(--text);
}

/* Prediction badge */
.pred-tag {
    display: inline-block; padding: 5px 14px;
    border-radius: 4px; font-size: 12px; font-weight: 700;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.5px;
    margin-bottom: 14px;
}
.pred-tag.tumor    { background: rgba(255,77,109,0.12); color: var(--red); border: 1px solid rgba(255,77,109,0.3); }
.pred-tag.no-tumor { background: rgba(0,229,160,0.10); color: var(--green); border: 1px solid rgba(0,229,160,0.3); }

/* Report scroll */
.report-scroll {
    height: 280px; overflow-y: auto;
    font-size: 12px; color: var(--muted2); line-height: 1.8;
    background: var(--bg);
    border-radius: 8px; padding: 14px;
    border: 1px solid var(--border);
    font-family: 'DM Mono', monospace;
}
.report-scroll::-webkit-scrollbar { width: 4px; }
.report-scroll::-webkit-scrollbar-track { background: transparent; }
.report-scroll::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

/* About band */
.about-band {
    margin: 32px 40px 40px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 48px 56px;
    display: grid; grid-template-columns: 1.2fr 1fr; gap: 48px;
    position: relative; overflow: hidden;
}
.about-band::before {
    content:'';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--cyan) 50%, transparent);
}
.about-title {
    font-family: 'Fraunces', serif;
    font-size: 26px; font-weight: 700; color: #f8fafc;
    margin-bottom: 16px; letter-spacing: -0.5px;
}
.about-body {
    font-size: 13px; color: var(--muted2); line-height: 1.85;
}
.about-stats-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
}
.about-stat-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px; padding: 20px;
}
.about-stat-val {
    font-family: 'Fraunces', serif;
    font-size: 22px; font-weight: 900; color: var(--cyan);
    margin-bottom: 4px;
}
.about-stat-lbl {
    font-family: 'DM Mono', monospace;
    font-size: 10px; color: var(--muted);
    letter-spacing: 0.5px; text-transform: uppercase;
}

/* ── Streamlit widget overrides ── */
[data-testid="stHeader"] { display: none !important; }

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div {
    font-family: 'DM Sans', sans-serif !important;
    border-radius: 8px !important;
    border: 1px solid var(--border2) !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    background: var(--surface2) !important;
    color: var(--text) !important;
}
.stTextInput > div > div > input::placeholder { color: var(--muted) !important; }
.stTextInput label, .stNumberInput label, .stSelectbox label {
    color: var(--muted2) !important;
    font-family: 'DM Mono', monospace !important;
    font-weight: 500 !important;
    font-size: 11px !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 2px rgba(0,212,255,0.12) !important;
}
[data-testid="stFileUploader"] {
    background: var(--surface2) !important;
    border: 1px dashed var(--border2) !important;
    border-radius: 10px !important;
    padding: 20px !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--cyan) !important; }

.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 10px 22px !important;
    transition: all 0.18s !important;
    background: var(--surface2) !important;
    color: var(--muted2) !important;
    border: 1px solid var(--border2) !important;
    letter-spacing: 0.2px !important;
}
.stButton > button:hover {
    border-color: var(--cyan) !important;
    color: var(--cyan) !important;
    background: var(--cyan-dim) !important;
}
.stButton > button[kind="primary"] {
    background: var(--cyan) !important;
    border: none !important;
    color: #07090f !important;
    box-shadow: 0 4px 20px var(--cyan-glow) !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 28px var(--cyan-glow) !important;
    color: #07090f !important;
}
.stDownloadButton > button {
    font-family: 'DM Sans', sans-serif !important;
    background: var(--cyan) !important;
    color: #07090f !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 11px 22px !important;
    box-shadow: 0 4px 16px var(--cyan-glow) !important;
}
.stProgress > div > div > div > div {
    background: var(--cyan) !important;
    border-radius: 2px !important;
}
.stSpinner > div { border-top-color: var(--cyan) !important; }
.stSuccess {
    background: rgba(0,229,160,0.08) !important;
    border-left: 3px solid var(--green) !important;
    border-radius: 8px !important;
    color: var(--green) !important;
}
.stWarning {
    background: rgba(245,158,11,0.08) !important;
    border-left: 3px solid #f59e0b !important;
    border-radius: 8px !important;
}
.stError {
    background: rgba(255,77,109,0.08) !important;
    border-left: 3px solid var(--red) !important;
    border-radius: 8px !important;
}
.stMarkdown p { font-family: 'DM Sans', sans-serif !important; color: var(--muted2) !important; }
[data-testid="stImage"] img { border-radius: 8px !important; }

/* Auth column styling */
.auth-page [data-testid="stColumn"]:nth-of-type(1) {
    min-height: 100vh;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Init ─────────────────────────────────────────────────────────
def init_state():
    CACHE_VERSION = "v3"  # bump this to force full reset
    if st.session_state.get("_cache_version") != CACHE_VERSION:
        st.session_state.clear()
        st.session_state["_cache_version"] = CACHE_VERSION

    defaults = {
        "page":              "landing",
        "auth_tab":          "signin",
        "logged_in":         False,
        "user_name":         "",
        "user_email":        "",
        "result":            None,
        "file_path":         None,
        "report_text":       None,
        "report_data":       None,
        "pdf_bytes":         None,
        "uploaded_filename": "",
        "_analyzing":        False,
        "patient_name":      "",
        "patient_age":       30,
        "patient_gender":    "Male",
        "show_demo":         False,
        "show_video":        False,
        "demo_mode":         False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Email helper ───────────────────────────────────────────────────────────────
def send_email_with_pdf(recipient_email, patient_name, pdf_bytes):
    try:
        sender_email    = st.secrets["GMAIL_SENDER"]
        sender_password = st.secrets["GMAIL_PASSWORD"]
    except Exception:
        return False
    try:
        msg = MIMEMultipart()
        msg['From']    = sender_email
        msg['To']      = recipient_email
        msg['Subject'] = f"NeuroScan AI: Diagnostic Report for {patient_name}"
        # REPLACE WITH:
        body = f"""Dear {patient_name},

Your MRI scan analysis from NeuroScan is complete.
Please find your diagnostic report attached to this email.

This report has been prepared for review by your healthcare provider.
Please consult your doctor before making any medical decisions.

Best regards,
NeuroScan Imaging
neuroscan.clinical@gmail.com"""
        msg.attach(MIMEText(body, 'plain'))
        fname = f"NeuroScan_Report_{patient_name.replace(' ', '_')}.pdf"
        part  = MIMEApplication(pdf_bytes, Name=fname)
        part['Content-Disposition'] = f'attachment; filename="{fname}"'
        msg.attach(part)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# LANDING PAGE
# ══════════════════════════════════════════════════════════════════════════════
def page_landing():
    # ── Nav ────────────────────────────────────────────────────────────────────
    nav_l, _, nav_r1, nav_r2 = st.columns([5, 2, 0.9, 0.9])
    with nav_l:
        st.markdown(f"""
        <div class="ns-nav" style="padding:12px 24px;">
            <div class="ns-logo">
                <div class="ns-logo-mark" style="background:transparent;box-shadow:none;padding:0;">
                    <img src="{LOGO_SRC}" style="width:36px;height:36px;object-fit:contain;border-radius:8px;" />
                </div>
                <span class="ns-logo-text">Neuro<em>Scan</em> AI</span>
            </div>
        </div>""", unsafe_allow_html=True)
    with nav_r1:
        st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
        if st.button("Log In", key="nav_login", use_container_width=True):
            st.session_state.page = "auth"
            st.session_state.auth_tab = "signin"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with nav_r2:
        st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
        if st.button("Sign Up", key="nav_signup", type="primary", use_container_width=True):
            st.session_state.page = "auth"
            st.session_state.auth_tab = "register"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Hero title (centered, above the explorer) ───────────────────────────────
    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="ns-hero" style="display: flex; flex-direction: column; align-items: center; text-align: center;">
        <div class="ns-hero-eyebrow">Clinical AI Platform</div>
        <h1 class="ns-hero-h1" style="margin: 0 auto;">
            Detect Brain Tumors
            <span class="line2" style="display: block; width: 100%;">with Explainable AI</span>
        </h1>
        <p class="ns-hero-sub" style="margin: 18px auto 0; max-width: 600px;">
            Upload an MRI scan and receive AI-powered classification,
            GRAD-CAM++ heatmaps, and a full clinical report in under 10 seconds.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Brain Explorer (full width: brain left, live info panel right) ─────────
    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
    _, exp_col, _ = st.columns([1, 10, 1])
    with exp_col:
        render_brain_explorer(height=520)

    # ── Action buttons (full width, below both columns, as in the original) ────
    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
    _, btn_row, _ = st.columns([1, 8, 1])
    with btn_row:
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button(" Launch Dashboard", key="hero_launch",
                         type="primary", use_container_width=True):
                st.session_state.page = "auth"
                st.rerun()
        with b2:
            demo_label = "✕  Close Demo" if st.session_state.show_demo else "Guest Demo"
            if st.button(demo_label, key="hero_demo", use_container_width=True):
                st.session_state.show_demo  = not st.session_state.show_demo
                st.session_state.show_video = False
                st.rerun()
        with b3:
            vid_label = "✕  Close Video" if st.session_state.show_video else "How It Works"
            if st.button(vid_label, key="hero_vid", use_container_width=True):
                st.session_state.show_video = not st.session_state.show_video
                st.session_state.show_demo  = False
                st.rerun()

    # ── Video (full width, below hero) ────────────────────────────────────────
    if st.session_state.show_video:
        st.markdown("<div style='margin-top:32px'></div>", unsafe_allow_html=True)
        st.video("https://youtu.be/12r392eTpTg")

    # ── Demo Gallery (full width, below hero) ─────────────────────────────────
    if st.session_state.show_demo:
        st.markdown("""
        <div class="demo-gallery">
            <div class="demo-gallery-title"></div>
        </div>
        """, unsafe_allow_html=True)

        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "Testing")
        samples = [
            {"label": "Glioma",      "folder": "glioma",      "file": "Te-gl_0010.jpg"},
            {"label": "Meningioma",  "folder": "meningioma",  "file": "Te-me_0010.jpg"},
            {"label": "Pituitary",   "folder": "pituitary",   "file": "Te-pi_0010.jpg"},
            {"label": "No Tumor",    "folder": "notumor",     "file": "Te-no_0010.jpg"},
        ]

        d1, d2, d3, d4 = st.columns(4)
        demo_cols = [d1, d2, d3, d4]

        for i, s in enumerate(samples):
            path = os.path.join(base, s["folder"], s["file"])
            with demo_cols[i]:
                if os.path.exists(path):
                    st.image(path, use_container_width=True)
                    st.markdown(
                        f"<div class='demo-img-label'>{s['label']}</div>",
                        unsafe_allow_html=True
                    )
                    if st.button(f"Analyze →", key=f"demo_{i}", use_container_width=True):
                        st.session_state.file_path         = path
                        st.session_state.uploaded_filename = s["label"]
                        st.session_state.logged_in         = True
                        st.session_state.demo_mode         = True
                        st.session_state.user_name         = "Guest"
                        st.session_state.patient_name      = "Demo Patient"
                        st.session_state.patient_age       = 0
                        st.session_state.patient_gender    = "Unknown"
                        st.session_state._analyzing        = True
                        st.session_state.result            = None
                        st.session_state.report_text       = None
                        st.session_state.pdf_bytes         = None
                        st.session_state.show_demo         = False
                        st.session_state.page              = "dashboard"
                        st.rerun()
                else:
                    st.warning(f"Not found:\n{path}")

    # ── Stats strip ────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="ns-stats">
        <div class="ns-stat">
            <div class="ns-stat-val">98.65%</div>
            <div class="ns-stat-label">Detection Accuracy</div>
        </div>
        <div class="ns-stat">
            <div class="ns-stat-val">&lt; 10s</div>
            <div class="ns-stat-label">Time to Full Report</div>
        </div>
        <div class="ns-stat">
            <div class="ns-stat-val">Visual Explainability</div>
            <div class="ns-stat-label">GRAD-CAM Powered</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature Cards ──────────────────────────────────────────────────────────
    st.markdown("""
    <div class="ns-features">
        <div class="ns-section-title">Why NeuroScan AI?</div>
        <div class="ns-feature-grid">
            <div class="ns-feature-card">
                <div class="ns-feature-kpi">98.65%</div>
                <div class="ns-feature-name">EfficientNetB0 Classification</div>
                <div class="ns-feature-desc">Deep residual network trained on curated MRI datasets delivering class-leading accuracy across all tumor types.</div>
            </div>
            <div class="ns-feature-card">
                <div class="ns-feature-name">GRAD-CAM++ Heatmaps</div>
                <div class="ns-feature-desc">Visual saliency maps highlight the exact pixel regions driving each AI decision. Zero black box — full transparency.</div>
            </div>
            <div class="ns-feature-card">
                <div class="ns-feature-name">Confidence Scoring</div>
                <div class="ns-feature-desc">Per-class softmax confidence scores so you always know the model's certainty and when to seek a second opinion.</div>
            </div>
            <div class="ns-feature-card">
                <div class="ns-feature-name">LLM Clinical Reports</div>
                <div class="ns-feature-desc">AI-generated radiologist-grade summaries distill findings into clear, actionable narrative — PDF-ready in seconds.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA Band ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="ns-cta-band">
        <div class="ns-cta-title">Ready to Analyze Your First Scan?</div>
        <div class="ns-cta-sub">
            Upload an MRI, get AI classification, a GRAD-CAM++ heatmap,<br>
            and a full clinical report in under 10 seconds.
        </div>
    </div>
    """, unsafe_allow_html=True)
    _, c_cta, _ = st.columns([3, 1.5, 3])
    with c_cta:
        if st.button("Get Started — Free", key="cta_start", type="primary", use_container_width=True):
            st.session_state.page = "auth"
            st.session_state.auth_tab = "signin"
            st.rerun()

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="ns-footer">
        <span class="ns-footer-logo">Neuro<em>Scan</em> AI</span>
        <span>© 2026 NeuroScan AI · Research &amp; clinical decision support only.</span>
        <span>Privacy · Terms · Contact</span>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# AUTH PAGE
# ══════════════════════════════════════════════════════════════════════════════
def page_auth():
    st.markdown("""
    <style>
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    .auth-back-btn button {
        background: transparent !important;
        border: none !important;
        color: var(--muted2) !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 12px !important;
        padding: 14px 20px !important;
        text-align: left !important;
        box-shadow: none !important;
    }
    .auth-back-btn button:hover {
        color: var(--cyan) !important;
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Back to Home ───────────────────────────────────────────────────────────
    st.markdown("<div class='auth-back-btn' style='position:relative;z-index:20;'>", unsafe_allow_html=True)
    back_col, _ = st.columns([2, 10])
    with back_col:
        if st.button("← Back to Home", key="auth_back_home"):
            st.session_state.page = "landing"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([1, 1], gap="small")

    # ── Left panel ─────────────────────────────────────────────────────────────
    with left:
        st.markdown(f"""
        <div class="auth-left">
            <div class="auth-grid-bg"></div>
            <div class="auth-brain-icon" style="position:relative;z-index:1;">
                <img src="{LOGO_SRC}" style="width:160px;height:160px;object-fit:contain;filter:drop-shadow(0 0 30px rgba(0,212,255,0.7));" />
            </div>
            <div class="auth-brand-name">Neuro<em>Scan</em> AI</div>
            <div class="auth-brand-desc">
                Explainable AI brain tumor detection —
                98.65% accuracy, GRAD-CAM++ visualization,
                and automated LLM clinical reporting.
            </div>
            <div class="auth-pills">
                <div class="auth-pill">HIPAA-READY</div>
                <div class="auth-pill">ENCRYPTED</div>
                <div class="auth-pill">&lt; 10s RESULTS</div>
                <div class="auth-pill">GRAD-CAM++ XAI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Right panel ────────────────────────────────────────────────────────────
    with right:
        st.markdown("<div style='padding: 60px 48px 0'>", unsafe_allow_html=True)

        tab = st.session_state.get("auth_tab", "signin")
        ta, tb = st.columns(2)
        with ta:
            if st.button("Sign In", key="tab_si",
                         type="primary" if tab == "signin" else "secondary",
                         use_container_width=True):
                st.session_state.auth_tab = "signin"; st.rerun()
        with tb:
            if st.button("Register", key="tab_reg",
                         type="primary" if tab == "register" else "secondary",
                         use_container_width=True):
                st.session_state.auth_tab = "register"; st.rerun()

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        if tab == "signin":
            st.markdown("""
            <div style='margin-bottom:24px'>
                <div style='font-family:Fraunces,serif;font-size:26px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px'>Welcome back</div>
                <div style='font-size:13px;color:#64748b;margin-top:6px'>Sign in to access the diagnostic dashboard.</div>
            </div>""", unsafe_allow_html=True)
            email = st.text_input("Email Address", placeholder="doctor@hospital.org", key="si_email")
            pw    = st.text_input("Password", type="password", placeholder="••••••••", key="si_pw")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Sign In  →", key="do_signin", type="primary", use_container_width=True):
                if email and pw:
                    st.session_state.logged_in  = True
                    st.session_state.user_email = email
                    st.session_state.user_name  = email.split("@")[0].replace(".", " ").title()
                    st.session_state.page       = "dashboard"
                    st.rerun()
                else:
                    st.warning("Please enter your email and password.")

        else:
            st.markdown("""
            <div style='margin-bottom:24px'>
                <div style='font-family:Fraunces,serif;font-size:26px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px'>Create account</div>
                <div style='font-size:13px;color:#64748b;margin-top:6px'>Start analyzing MRI scans with AI precision.</div>
            </div>""", unsafe_allow_html=True)
            full   = st.text_input("Full Name", placeholder="Dr. Jane Smith", key="reg_name")
            age    = st.number_input("Age", min_value=1, max_value=120, value=30, key="reg_age")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="reg_gender")
            email  = st.text_input("Email Address", placeholder="doctor@hospital.org", key="reg_email")
            pw     = st.text_input("Password", type="password", placeholder="Min. 8 chars, letters + numbers", key="reg_pw")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Create Account  →", key="do_reg", type="primary", use_container_width=True):
                if not (full and email and pw):
                    st.warning("Please fill in all required fields.")
                else:
                    email_ok = re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email)
                    pw_ok    = re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", pw)
                    if not email_ok:
                        st.error("Please enter a valid email address.")
                    elif not pw_ok:
                        st.error("Password must be 8+ characters with letters and numbers.")
                    else:
                        st.session_state.logged_in      = True
                        st.session_state.user_name      = full
                        st.session_state.user_email     = email
                        st.session_state.patient_name   = full
                        st.session_state.patient_age    = int(age)
                        st.session_state.patient_gender = gender
                        st.session_state.page           = "dashboard"
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD PAGE
# ══════════════════════════════════════════════════════════════════════════════
def page_dashboard():

    st.markdown("""
    <style>
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
        [data-testid="column"] { width: 100% !important; min-width: 100% !important; }
        .flow-arrow { display: none !important; }
        .panel { margin-bottom: 16px !important; }
        .report-scroll { height: 200px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:rgba(245,158,11,0.08);border-left:3px solid #f59e0b;
    border-radius:8px;padding:10px 16px;margin:0 0 16px;
    font-size:12px;color:#f59e0b;font-family:DM Mono,monospace'>
    ⚠ FOR RESEARCH USE ONLY — This AI output must be reviewed by a qualified 
    medical professional before any clinical decisions are made.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .block-container > div > div > div > div[data-testid="stHorizontalBlock"]:first-of-type
        [data-testid="column"]:nth-child(3) button,
    .block-container > div > div > div > div[data-testid="stHorizontalBlock"]:first-of-type
        [data-testid="column"]:nth-child(4) button {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Derive state ───────────────────────────────────────────────────────────
    has_image    = bool(st.session_state.get("file_path")) and os.path.exists(st.session_state.get("file_path", ""))
    is_analyzing = st.session_state.get("_analyzing", False)
    has_result   = st.session_state.get("result") is not None
    has_report   = bool(st.session_state.get("report_text"))
    user_name    = st.session_state.get("user_name", "Guest")
    live_cls     = "live" if is_analyzing else ""

    # ── Top Bar ────────────────────────────────────────────────────────────────
    hd_l, hd_r = st.columns([5, 1])
    with hd_l:
        st.markdown(f"""
        <div class="dash-topbar" style="position:relative;z-index:10;">
            <div style="display:flex;align-items:center;gap:16px;">
                <div class="dash-logo">
                    <div class="dash-logo-mark" style="background:transparent;box-shadow:none;">
                        <img src="{LOGO_SRC}" style="width:32px;height:32px;object-fit:contain;border-radius:7px;" />
                    </div>
                    <span class="dash-logo-txt">Neuro<em>Scan</em> AI</span>
                </div>
                <div class="dash-breadcrumb">
                    › Dashboard › <span>{user_name}</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
    with hd_r:
        st.markdown("<div style='padding-top:10px'>", unsafe_allow_html=True)
        if st.button("← Log Out", key="logout", use_container_width=True):
            for k in ["logged_in","result","file_path","report_text",
                      "pdf_bytes","_analyzing","report_data","demo_mode","show_demo"]:
                st.session_state[k] = None if k not in ("logged_in","_analyzing","demo_mode","show_demo") else False
            st.session_state.page = "landing"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Three-column layout ────────────────────────────────────────────────────
    col1, col_arr1, col2, col_arr2, col3 = st.columns([10, 1, 10, 1, 10])

    # ── BOX 1 — Upload / Preview ───────────────────────────────────────────────
    with col1:
        st.markdown("""
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon blue"></div>
                <div>
                    <div class="panel-title">MRI Scan Input</div>
                    <div class="panel-sub">upload or select sample</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        if has_image:
            img_placeholder = st.empty()
            img_placeholder.image(st.session_state.file_path, use_container_width=True,
                                  caption=f"📎  {st.session_state.uploaded_filename}")
            if not is_analyzing:
                ca, cb = st.columns(2)
                with ca:
                    if st.button("New Image", key="new_img", use_container_width=True):
                        st.session_state.file_path   = None
                        st.session_state.result      = None
                        st.session_state.report_text = None
                        st.session_state.pdf_bytes   = None
                        st.session_state._analyzing  = False
                        st.rerun()
                with cb:
                    if not has_result:
                        if st.button("Analyze Now", key="do_analyze",
                            type="primary", use_container_width=True):

                            # 🔥 RESET OLD DATA
                            st.session_state.report_text = None
                            st.session_state.pdf_bytes = None
                            st.session_state.result = None

                            st.session_state._analyzing = True
                            st.rerun()
            else:
                st.markdown("""
                <div style='text-align:center;padding:12px 0'>
                    <div style='font-family:DM Mono,monospace;font-size:11px;
                                color:var(--cyan);letter-spacing:1px'>
                        ⟳ &nbsp;ANALYZING…
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            if not is_analyzing:
                uf = st.file_uploader(
                    "Upload MRI scan", type=["jpg","jpeg","png"], key="dash_upload",
                    help="Accepts JPG or PNG format MRI scans"
                )
                if uf:
                    fp = os.path.join(os.path.dirname(__file__), "temp_scan.jpg")
                    with open(fp, "wb") as f:
                        f.write(uf.read())
                    st.session_state.file_path         = fp
                    st.session_state.uploaded_filename = uf.name
                    st.rerun()
                else:
                    st.markdown("""
                    <div class="empty-state">
                        <div class="empty-icon"></div>
                        <div class="empty-txt">
                            Upload an MRI scan above,<br>or use the
                            <strong>Guest Demo</strong> on the landing page.
                        </div>
                    </div>""", unsafe_allow_html=True)

    # ── Arrow 1 ────────────────────────────────────────────────────────────────
    with col_arr1:
        st.markdown(f"""
        <div class="flow-arrow" style="height:300px;">
            <div class="flow-dot {live_cls}"></div>
            <div class="flow-dot {live_cls}"></div>
            <div class="flow-chevron {live_cls}">›</div>
            <div class="flow-dot {live_cls}"></div>
            <div class="flow-dot {live_cls}"></div>
        </div>""", unsafe_allow_html=True)

    # ── BOX 2 — GRAD-CAM++Analysis ─────────────────────────────────────────────
    with col2:
        st.markdown("""
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon teal"></div>
                <div>
                    <div class="panel-title">GRAD-CAM Analysis</div>
                    <div class="panel-sub">GRAD-CAM++ classification + heatmap</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        if is_analyzing and not has_result:
            prog   = st.progress(0)
            status = st.empty()
            steps  = [
                ("Running EfficientNetB0 classification…", 25),
                ("Computing GRAD-CAM++ saliency map…",       55),
                ("Generating LLM clinical report…",        85),
            ]
            for msg, val in steps:
                status.markdown(
                    f"<p style='text-align:center;font-size:12px;color:var(--muted);font-family:DM Mono,monospace'>{msg}</p>",
                    unsafe_allow_html=True)
                prog.progress(val)
                time.sleep(0.6)

            result = run_pipeline(st.session_state.file_path)

            pinfo  = {
                "name":   st.session_state.get("patient_name") or st.session_state.get("user_name") or "Anonymous",
                "age":    st.session_state.get("patient_age", "N/A"),
                "gender": st.session_state.get("patient_gender", "N/A"),
            }
            data        = prepare_llm_input(result, pinfo)
            report_text = generate_report(data)          # no ctx
            pdf_bytes   = generate_pdf(
                data=data,
                report_text=report_text,
                original_image_path=st.session_state.get("file_path"),
                gradcam_image_path=result.get("explanation_plot_path"),
                lime_image_path=None,
            )     
            prog.progress(100); status.empty()

            st.session_state.result      = result
            st.session_state.report_data = data
            st.session_state.report_text = report_text
            st.session_state.pdf_bytes   = pdf_bytes
            st.session_state._analyzing  = False
            time.sleep(0.2); st.rerun()

        elif has_result:
            result   = st.session_state.result
            conf     = result["confidence"] * 100
            pred     = result["prediction"]
            is_tumor = "no_tumor" not in pred.lower()

            badge_cls = "tumor" if is_tumor else "no-tumor"
            cert      = ("High confidence" if conf >= 90
                         else "Moderate confidence" if conf >= 70
                         else "Low confidence")

            st.markdown(f"""
            <div class="conf-row">
                <div class="conf-chip">
                    <div class="conf-chip-label">Model Confidence</div>
                    <div class="conf-chip-val">{conf:.1f}%</div>
                </div>
                <div class="conf-chip">
                    <div class="conf-chip-label">GRAD-CAM++ Score</div>
                    <div class="conf-chip-val">{result.get('gradcam_accuracy', 0.92):.2f}</div>
                </div>
            </div>
            <div style="text-align:center;margin-bottom:16px">
                <span class="pred-tag {badge_cls}">{pred.upper()}</span>
                <div style="font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);margin-top:4px;letter-spacing:0.5px">{cert.upper()}</div>
            </div>
            <div style="display:flex;gap:8px;margin-bottom:6px">
                <div style="flex:1;font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);text-align:center;letter-spacing:0.5px">ORIGINAL MRI</div>
                <div style="flex:1;font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);text-align:center;letter-spacing:0.5px">GRAD-CAM++ HEATMAP</div>
            </div>""", unsafe_allow_html=True)

            ic1, ic2 = st.columns(2)
            with ic1:
                st.image(st.session_state.file_path, use_container_width=True)
            with ic2:
                st.image(result["explanation_plot_path"], use_container_width=True)

            breakdown = result.get("confidence_breakdown", {})
            if breakdown:
                st.markdown("""<div style='margin-top:12px;font-family:DM Mono,
                monospace;font-size:10px;color:#64748b;letter-spacing:1px;
                margin-bottom:6px;'>CLASS PROBABILITIES</div>""",
                unsafe_allow_html=True)
                for cls, pct in breakdown.items():
                    bar_color = "#00d4ff" if cls == result["prediction"] else "#334155"
                    st.markdown(f"""
                    <div style='margin-bottom:6px;'>
                        <div style='display:flex;justify-content:space-between;
                        font-size:11px;margin-bottom:3px;'>
                            <span style='color:#94a3b8;'>{cls.upper()}</span>
                            <span style='color:#00d4ff;font-family:DM Mono,monospace;'>
                            {pct:.1f}%</span>
                        </div>
                        <div style='background:#131923;border-radius:3px;height:6px;'>
                            <div style='width:{min(pct,100)}%;background:{bar_color};
                            height:6px;border-radius:3px;'></div>
                        </div>
                    </div>""", unsafe_allow_html=True)

        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon"></div>
                <div class="empty-txt">
                    Upload a scan and click <strong>Analyze Now</strong>
                    to see the GRAD-CAM++ heatmap and classification here.
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Arrow 2 ────────────────────────────────────────────────────────────────
    with col_arr2:
        st.markdown(f"""
        <div class="flow-arrow" style="height:300px;">
            <div class="flow-dot {live_cls}"></div>
            <div class="flow-dot {live_cls}"></div>
            <div class="flow-chevron {live_cls}">›</div>
            <div class="flow-dot {live_cls}"></div>
            <div class="flow-dot {live_cls}"></div>
        </div>""", unsafe_allow_html=True)

    # ── BOX 3 — Diagnostic Report ─────────────────────────────────────────────
    with col3:
        st.markdown("""
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon green"></div>
                <div>
                    <div class="panel-title">Diagnostic Report</div>
                    <div class="panel-sub">AI-generated clinical summary</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        if has_report:
            pname = st.session_state.get("patient_name", "Patient")
            rtext = st.session_state.report_text

            # Aggressively strip any disclaimer the LLM added
            for marker in ["DISCLAIMER", "DISCLMER", "IMPORTANT DISCLAIMER",
                            "IMPORTANT NOTE", "Please note", "Please remember",
                            "This report was generated"]:
                if marker.upper() in rtext.upper():
                    idx = rtext.upper().rfind(marker.upper())
                    rtext = rtext[:idx].strip()

            # Remove trailing separator lines
            lines = rtext.split("\n")
            while lines and set(lines[-1].strip()) <= {"=", "-", " "}:
                lines.pop()
            rtext = "\n".join(lines).strip()

            st.markdown(
                f'<div class="report-scroll">{rtext.replace(chr(10), "<br>")}</div>',
                unsafe_allow_html=True
            )

            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            st.download_button(
                label="⬇  Download PDF Report",
                data=st.session_state.pdf_bytes,
                file_name=f"neuroscan_{pname.replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("✉️  Send via Email", key="email_btn", use_container_width=True):
                uemail = st.session_state.get("user_email")
                if uemail:
                    with st.spinner("Sending…"):
                        ok = send_email_with_pdf(uemail, pname, st.session_state.pdf_bytes)
                    if ok:
                        st.success(f"Report sent to {uemail}")
                    else:
                        st.error("Email failed. Check SMTP settings.")
                else:
                    st.warning("No email address found for this account.")
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon"></div>
                <div class="empty-txt">
                    The clinical report will appear here<br>after analysis is complete.
                </div>
            </div>""", unsafe_allow_html=True)

    # ── About ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="about-band">
        <div>
            <div class="about-title">About NeuroScan AI</div>
            <div class="about-body">
                NeuroScan AI is an explainable deep-learning platform built for
                brain tumor detection from MRI scans.<br><br>
                Powered by an <strong style="color:#e2e8f0">EfficientNetB0 backbone</strong>
                and <strong style="color:#e2e8f0">GRAD-CAM++ visualization</strong>, every
                prediction is transparent and traceable. The system generates
                LLM-assisted clinical summaries — giving radiologists and physicians
                actionable insights within seconds of upload.<br><br>
                Built to <em>support</em>, not replace, clinical expertise.
                NeuroScan AI streamlines diagnostic workflows while keeping humans firmly in control.
            </div>
        </div>
        <div class="about-stats-grid">
            <div class="about-stat-card">
                <div class="about-stat-val">98.65%</div>
                <div class="about-stat-lbl">Detection Accuracy</div>
            </div>
            <div class="about-stat-card">
                <div class="about-stat-val">EfficientNetB0</div>
                <div class="about-stat-lbl">Deep Learning Model</div>
            </div>
            <div class="about-stat-card">
                <div class="about-stat-val">GRAD-CAM++</div>
                <div class="about-stat-lbl">Explainability Method</div>
            </div>
            <div class="about-stat-card">
                <div class="about-stat-val">&lt; 10s</div>
                <div class="about-stat-lbl">Time to Full Report</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="ns-footer">
        <span class="ns-footer-logo">Neuro<em>Scan</em> AI</span>
        <span>© 2026 NeuroScan AI · Research &amp; clinical decision support only.</span>
        <span>Privacy · Terms · Contact</span>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
current_page = st.session_state.get("page", "landing")

if current_page == "landing":
    with st.container():
        page_landing()

elif current_page == "auth":
    with st.container():
        page_auth()

elif current_page == "dashboard":
    is_auth = st.session_state.get("logged_in", False)
    is_demo = st.session_state.get("demo_mode", False)
    if is_auth or is_demo:
        with st.container():
            page_dashboard()
    else:
        st.session_state.page = "auth"
        st.rerun()

else:
    st.session_state.page = "landing"
    st.rerun()