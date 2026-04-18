import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import os
import re
import time

from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.sql_generator import ask_floatchat, run_query
from backend.fetcher import fetch_and_ingest
from backend.rag import ask_with_rag, initialize_rag

# Initialize tracking flags
if "rag_initialized" not in st.session_state:
    initialize_rag()
    st.session_state.rag_initialized = True

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if "pending_query" not in st.session_state:
    st.session_state.pending_query = ""

if "theme" not in st.session_state:
    st.session_state.theme = "dark"  # Default theme

if "viz_data" not in st.session_state:
    st.session_state.viz_data = None  # Current visualization data for right panel

# ─────────────────────────────
# Page Config
# ─────────────────────────────
st.set_page_config(
    page_title="FloatChat | Ocean Data",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────
# Theme Definitions
# ─────────────────────────────
theme = st.session_state.theme

if theme == "light":
    colors = {
        "bg": "#f0f4ff",
        "bg_secondary": "rgba(255, 255, 255, 0.72)",
        "bg_solid": "#ffffff",
        "text": "#1a1a2e",
        "text_muted": "#6b7280",
        "primary": "#0ea5e9",
        "primary_rgb": "14, 165, 233",
        "accent": "#7c3aed",
        "accent_rgb": "124, 58, 237",
        "border": "rgba(148, 163, 184, 0.25)",
        "hover": "rgba(14, 165, 233, 0.08)",
        "card_bg": "rgba(255, 255, 255, 0.6)",
        "card_border": "rgba(148, 163, 184, 0.3)",
        "user_bubble_bg": "linear-gradient(135deg, #0ea5e9, #6366f1)",
        "user_text": "#ffffff",
        "ai_bubble_bg": "#ffffff",
        "ai_border": "#e2e8f0",
        "glass_bg": "rgba(255, 255, 255, 0.55)",
        "glass_border": "rgba(255, 255, 255, 0.6)",
        "chat_panel_bg": "#f8fafc",
        "viz_panel_bg": "#ffffff",
        "plotly_template": "plotly_white",
        "plotly_grid": "rgba(148, 163, 184, 0.15)",
        "map_ocean": "rgba(14, 165, 233, 0.08)",
        "map_land": "rgba(209, 213, 219, 0.3)",
        "map_border": "rgba(148, 163, 184, 0.5)",
        "map_marker": "#0369a1",
        "gradient_start": "#e0e7ff",
        "gradient_end": "#f0f4ff",
        "shadow": "0 8px 32px rgba(0, 0, 0, 0.08)",
        "glow": "0 0 30px rgba(14, 165, 233, 0.15)",
        "timestamp_color": "#94a3b8",
        "badge_bg": "rgba(16, 185, 129, 0.1)",
        "badge_text": "#059669",
        "divider_line": "#e2e8f0",
    }
else:
    colors = {
        "bg": "#0a0e27",
        "bg_secondary": "rgba(19, 26, 58, 0.75)",
        "bg_solid": "#131a3a",
        "text": "#e8eaf6",
        "text_muted": "#8b95b8",
        "primary": "#00d4ff",
        "primary_rgb": "0, 212, 255",
        "accent": "#7c3aed",
        "accent_rgb": "124, 58, 237",
        "border": "rgba(99, 102, 241, 0.2)",
        "hover": "rgba(0, 212, 255, 0.08)",
        "card_bg": "rgba(19, 26, 58, 0.6)",
        "card_border": "rgba(99, 102, 241, 0.25)",
        "user_bubble_bg": "linear-gradient(135deg, #0ea5e9, #7c3aed)",
        "user_text": "#ffffff",
        "ai_bubble_bg": "rgba(19, 26, 58, 0.8)",
        "ai_border": "rgba(99, 102, 241, 0.2)",
        "glass_bg": "rgba(15, 20, 50, 0.65)",
        "glass_border": "rgba(99, 102, 241, 0.2)",
        "chat_panel_bg": "rgba(10, 14, 39, 0.95)",
        "viz_panel_bg": "rgba(19, 26, 58, 0.5)",
        "plotly_template": "plotly_dark",
        "plotly_grid": "rgba(99, 102, 241, 0.1)",
        "map_ocean": "rgba(0, 212, 255, 0.04)",
        "map_land": "rgba(99, 102, 241, 0.08)",
        "map_border": "rgba(99, 102, 241, 0.3)",
        "map_marker": "#00d4ff",
        "gradient_start": "#0a0e27",
        "gradient_end": "#131a3a",
        "shadow": "0 8px 32px rgba(0, 0, 0, 0.4)",
        "glow": "0 0 40px rgba(0, 212, 255, 0.12)",
        "timestamp_color": "#64748b",
        "badge_bg": "rgba(16, 185, 129, 0.15)",
        "badge_text": "#34d399",
        "divider_line": "rgba(99, 102, 241, 0.15)",
    }

# ─────────────────────────────
# Premium CSS Injection
# ─────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ═══════════════════════════════
       KEYFRAME ANIMATIONS
    ═══════════════════════════════ */
    @keyframes gradientShift {{
        0%   {{ background-position: 0% 50%; }}
        50%  {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50%      {{ transform: translateY(-12px); }}
    }}

    @keyframes pulse-ring {{
        0%   {{ transform: scale(0.5); opacity: 0.8; }}
        100% {{ transform: scale(2.5); opacity: 0; }}
    }}

    @keyframes fadeSlideUp {{
        from {{ opacity: 0; transform: translateY(18px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes shimmer {{
        0%   {{ background-position: -200% 0; }}
        100% {{ background-position: 200% 0; }}
    }}

    @keyframes typewriter {{
        from {{ width: 0; }}
        to   {{ width: 100%; }}
    }}

    @keyframes wave {{
        0%   {{ transform: translateX(0) translateZ(0) scaleY(1); }}
        50%  {{ transform: translateX(-25%) translateZ(0) scaleY(0.55); }}
        100% {{ transform: translateX(-50%) translateZ(0) scaleY(1); }}
    }}

    @keyframes dotBounce {{
        0%, 80%, 100% {{ transform: scale(0); opacity: 0.4; }}
        40%           {{ transform: scale(1); opacity: 1; }}
    }}

    @keyframes glowPulse {{
        0%, 100% {{ box-shadow: 0 0 5px rgba({colors['primary_rgb']}, 0.2); }}
        50%      {{ box-shadow: 0 0 25px rgba({colors['primary_rgb']}, 0.4); }}
    }}

    @keyframes rotate {{
        from {{ transform: rotate(0deg); }}
        to   {{ transform: rotate(360deg); }}
    }}

    @keyframes scaleIn {{
        from {{ transform: scale(0.9); opacity: 0; }}
        to   {{ transform: scale(1); opacity: 1; }}
    }}

    /* ═══════════════════════════════
       BASE & TYPOGRAPHY
    ═══════════════════════════════ */
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    /* ═══════════════════════════════
       ANIMATED BACKGROUND
    ═══════════════════════════════ */
    [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
        background: linear-gradient(135deg, {colors['gradient_start']}, {colors['bg']}, {colors['gradient_end']}, {colors['bg']}) !important;
        background-size: 400% 400% !important;
        animation: gradientShift 20s ease infinite !important;
        color: {colors['text']} !important;
    }}

    /* ═══════════════════════════════
       SIDEBAR — GLASSMORPHISM
    ═══════════════════════════════ */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child {{
        background: {colors['glass_bg']} !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border-right: 1px solid {colors['glass_border']} !important;
    }}

    /* ═══════════════════════════════
       HEADER — TRANSPARENT
    ═══════════════════════════════ */
    [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}

    /* ═══════════════════════════════
       BOTTOM CHAT INPUT AREA
    ═══════════════════════════════ */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {{
        background: linear-gradient(to top, {colors['bg']}, transparent) !important;
    }}

    [data-testid="stChatInput"] {{
        background: {colors['glass_bg']} !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid {colors['glass_border']} !important;
        border-radius: 16px !important;
        box-shadow: {colors['glow']} !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    [data-testid="stChatInput"]:focus-within {{
        border-color: rgba({colors['primary_rgb']}, 0.5) !important;
        box-shadow: 0 0 30px rgba({colors['primary_rgb']}, 0.2) !important;
    }}
    [data-testid="stChatInput"] textarea {{
        color: {colors['text']} !important;
        background-color: transparent !important;
        font-size: 0.95rem !important;
    }}

    /* ═══════════════════════════════
       MARKDOWN TEXT COLORS
    ═══════════════════════════════ */
    .stMarkdown p, .stMarkdown li, .stMarkdown span {{
        color: {colors['text']} !important;
    }}

    /* ═══════════════════════════════
       REDUCE TOP PADDING
    ═══════════════════════════════ */
    [data-testid="block-container"] {{
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 1200px;
    }}

    /* ═══════════════════════════════
       MAIN TITLE — ANIMATED GRADIENT
    ═══════════════════════════════ */
    .main-title {{
        font-size: 1.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, {colors['primary']}, {colors['accent']}, {colors['primary']});
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmer 4s linear infinite;
        margin-bottom: 0px;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }}

    .subtitle {{
        font-size: 0.82rem;
        color: {colors['text_muted']} !important;
        font-weight: 400;
        margin-top: 2px;
        margin-bottom: 12px;
        letter-spacing: 0.3px;
        margin-bottom: 2rem;
        letter-spacing: 0.5px;
    }}

    /* ═══════════════════════════════
       CHAT MESSAGE — HIDE DEFAULT
    ═══════════════════════════════ */
    [data-testid="stChatMessage"] {{
        background-color: transparent !important;
        animation: fadeSlideUp 0.4s ease-out;
    }}

    /* ═══════════════════════════════
       USER MESSAGE BUBBLE
    ═══════════════════════════════ */
    .user-msg-wrap {{
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        margin-bottom: 12px;
        animation: fadeSlideUp 0.4s ease-out;
    }}
    .user-label {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
    }}
    .user-label-badge {{
        background: {colors['user_bubble_bg']};
        color: #fff;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 10px;
        letter-spacing: 0.5px;
    }}
    .user-label-name {{
        font-weight: 700;
        font-size: 0.92rem;
        color: {colors['text']};
    }}
    .user-bubble {{
        background: {colors['user_bubble_bg']};
        color: {colors['user_text']};
        padding: 14px 20px;
        border-radius: 18px 18px 18px 4px;
        font-size: 0.95rem;
        line-height: 1.6;
        max-width: 100%;
        box-shadow: 0 4px 15px rgba({colors['primary_rgb']}, 0.2);
    }}
    .msg-timestamp {{
        font-size: 0.72rem;
        color: {colors['timestamp_color']};
        margin-top: 5px;
        font-weight: 400;
    }}

    /* ═══════════════════════════════
       AI MESSAGE BUBBLE
    ═══════════════════════════════ */
    .ai-msg-wrap {{
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        margin-bottom: 16px;
        animation: fadeSlideUp 0.4s ease-out;
    }}
    .ai-label {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
    }}
    .ai-avatar {{
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        color: #fff;
        font-weight: 800;
    }}
    .ai-label-name {{
        font-weight: 700;
        font-size: 0.92rem;
        color: {colors['text']};
    }}
    .ai-bubble {{
        background: {colors['ai_bubble_bg']};
        border: 1px solid {colors['ai_border']};
        border-left: 4px solid {colors['primary']};
        padding: 16px 22px;
        border-radius: 4px 18px 18px 18px;
        font-size: 0.93rem;
        line-height: 1.75;
        max-width: 100%;
        color: {colors['text']};
        box-shadow: {colors['shadow']};
        position: relative;
        overflow: hidden;
    }}
    .ai-bubble::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, {colors['primary']}, {colors['accent']}, transparent);
    }}
    .ai-bubble p {{
        margin: 0 0 8px 0;
        color: {colors['text']};
    }}
    .ai-bubble ul {{
        padding-left: 16px;
        margin: 8px 0;
    }}
    .ai-bubble li {{
        color: {colors['text']};
        margin-bottom: 4px;
    }}
    .response-meta {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 6px;
    }}
    .response-time-badge {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: {colors['badge_bg']};
        color: {colors['badge_text']};
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 10px;
    }}

    /* ═══════════════════════════════
       AI ANSWER BOX — GLASSMORPHISM
    ═══════════════════════════════ */
    .answer-box {{
        background: {colors['glass_bg']} !important;
        backdrop-filter: blur(16px) saturate(150%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(150%) !important;
        border: 1px solid {colors['glass_border']} !important;
        border-left: 4px solid {colors['primary']} !important;
        padding: 1.4rem 1.8rem;
        border-radius: 16px;
        margin: 0.8rem 0;
        box-shadow: {colors['shadow']};
        color: {colors['text']} !important;
        font-size: 1rem;
        line-height: 1.7;
        animation: fadeSlideUp 0.5s ease-out;
        position: relative;
        overflow: hidden;
    }}
    .answer-box::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, {colors['primary']}, {colors['accent']}, transparent);
    }}
    .answer-box p, .answer-box li {{
        color: {colors['text']} !important;
    }}
    .answer-box b {{
        background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }}

    /* ═══════════════════════════════
       SIDEBAR BUTTONS — GLASS CARDS
    ═══════════════════════════════ */
    .stButton > button {{
        background: {colors['card_bg']} !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid {colors['card_border']} !important;
        color: {colors['text']} !important;
        border-radius: 12px !important;
        padding: 0.65rem 1rem !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        text-align: left !important;
    }}
    .stButton > button:hover {{
        border-color: rgba({colors['primary_rgb']}, 0.5) !important;
        color: {colors['primary']} !important;
        background: {colors['hover']} !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba({colors['primary_rgb']}, 0.15) !important;
    }}
    .stButton > button:active {{
        transform: translateY(0px) !important;
    }}

    /* ═══════════════════════════════
       THEME TOGGLE BUTTON
    ═══════════════════════════════ */
    .theme-btn > button {{
        border-radius: 50% !important;
        width: 42px !important;
        height: 42px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 1.3rem !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        background: {colors['card_bg']} !important;
        border: 1px solid {colors['card_border']} !important;
    }}
    .theme-btn > button:hover {{
        transform: rotate(30deg) scale(1.1) !important;
        box-shadow: 0 0 20px rgba({colors['primary_rgb']}, 0.3) !important;
    }}

    /* ═══════════════════════════════
       EXPANDER — SQL / DATA BOXES
    ═══════════════════════════════ */
    [data-testid="stExpander"] {{
        background: {colors['card_bg']} !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid {colors['card_border']} !important;
        border-radius: 12px;
        animation: fadeSlideUp 0.4s ease-out;
    }}
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] p {{
        color: {colors['text']} !important;
    }}

    /* ═══════════════════════════════
       METRICS — GRADIENT CARDS
    ═══════════════════════════════ */
    [data-testid="stMetricValue"] {{
        background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: {colors['text_muted']} !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-size: 0.75rem !important;
    }}

    /* ═══════════════════════════════
       VISUALIZATION SOURCE & STATS
    ═══════════════════════════════ */
    .viz-source {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 12px;
        padding: 8px 12px;
        background: {colors['card_bg']};
        border-radius: 10px;
        font-size: 0.82rem;
        color: {colors['text_muted']};
    }}
    .viz-source a {{
        color: {colors['primary']};
        text-decoration: none;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    
    .viz-section-title {{
        font-size: 1.05rem;
        font-weight: 700;
        color: {colors['text']};
        margin: 20px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid {colors['divider_line']};
    }}

    .viz-header {{
        margin-bottom: 20px;
    }}
    .viz-title {{
        font-size: 1.35rem;
        font-weight: 800;
        color: {colors['text']};
        margin: 0;
    }}
    .viz-subtitle {{
        font-size: 0.82rem;
        color: {colors['text_muted']};
        margin-top: 2px;
    }}

    .viz-chart-label {{
        font-size: 0.95rem;
        font-weight: 600;
        color: {colors['text']};
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }}

    /* ═══════════════════════════════
       CHART CONTAINER WRAPPER
    ═══════════════════════════════ */
    .chart-container {{
        background: {colors['glass_bg']};
        backdrop-filter: blur(16px) saturate(150%);
        -webkit-backdrop-filter: blur(16px) saturate(150%);
        border: 1px solid {colors['glass_border']};
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: {colors['shadow']};
        animation: scaleIn 0.5s ease-out;
        position: relative;
        overflow: hidden;
    }}
    .chart-container::after {{
        content: '';
        position: absolute;
        top: -1px;
        left: 20%;
        right: 20%;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba({colors['primary_rgb']}, 0.5), transparent);
    }}
    .chart-title {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, rgba({colors['primary_rgb']}, 0.12), rgba({colors['accent_rgb']}, 0.08));
        border: 1px solid rgba({colors['primary_rgb']}, 0.2);
        border-radius: 10px;
        padding: 6px 14px;
        margin-bottom: 12px;
        font-weight: 600;
        font-size: 0.95rem;
        color: {colors['text']};
    }}

    /* ═══════════════════════════════
       DATAFRAME — STYLED TABLE
    ═══════════════════════════════ */
    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
    }}

    /* ═══════════════════════════════
       CUSTOM PROCESSING LOADER
    ═══════════════════════════════ */
    .processing-indicator {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px;
        background: {colors['glass_bg']};
        backdrop-filter: blur(12px);
        border: 1px solid {colors['glass_border']};
        border-radius: 16px;
        margin: 8px 0;
        animation: fadeSlideUp 0.3s ease-out;
    }}
    .dot-loader {{
        display: flex;
        gap: 5px;
    }}
    .dot-loader span {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: {colors['primary']};
        animation: dotBounce 1.4s infinite ease-in-out both;
    }}
    .dot-loader span:nth-child(1) {{ animation-delay: -0.32s; }}
    .dot-loader span:nth-child(2) {{ animation-delay: -0.16s; }}
    .dot-loader span:nth-child(3) {{ animation-delay: 0s; }}
    .processing-text {{
        color: {colors['text_muted']};
        font-size: 0.9rem;
        font-weight: 500;
    }}

    /* ═══════════════════════════════
       WELCOME HERO SECTION
    ═══════════════════════════════ */
    .hero-container {{
        text-align: center;
        padding: 3rem 1rem;
        animation: fadeSlideUp 0.6s ease-out;
    }}
    .hero-icon {{
        font-size: 4rem;
        margin-bottom: 1rem;
        display: inline-block;
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 0 20px rgba({colors['primary_rgb']}, 0.4));
    }}
    .hero-heading {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {colors['text']};
        margin-bottom: 0.5rem;
    }}
    .hero-sub {{
        font-size: 1.05rem;
        color: {colors['text_muted']};
        max-width: 500px;
        margin: 0 auto 2.5rem auto;
        line-height: 1.6;
    }}

    /* Feature cards grid */
    .features-grid {{
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 14px;
        max-width: 1100px;
        margin: 0 auto;
    }}
    .feature-card {{
        background: {colors['glass_bg']};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {colors['glass_border']};
        border-radius: 16px;
        padding: 1.35rem 0.9rem;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: default;
        position: relative;
        overflow: hidden;
    }}
    .feature-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, {colors['primary']}, {colors['accent']});
        opacity: 0;
        transition: opacity 0.3s ease;
    }}
    .feature-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba({colors['primary_rgb']}, 0.15);
        border-color: rgba({colors['primary_rgb']}, 0.4);
    }}
    .feature-card:hover::before {{
        opacity: 1;
    }}
    .feature-icon {{
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
        display: block;
    }}
    .feature-label {{
        font-size: 0.82rem;
        font-weight: 600;
        color: {colors['text']};
        margin-bottom: 2px;
    }}
    .feature-desc {{
        font-size: 0.72rem;
        color: {colors['text_muted']};
        line-height: 1.35;
    }}

    /* Sonar pulse rings */
    .sonar-wrap {{
        position: relative;
        display: inline-block;
        margin-bottom: 1.5rem;
    }}
    .sonar-ring {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 80px;
        height: 80px;
        border: 2px solid rgba({colors['primary_rgb']}, 0.3);
        border-radius: 50%;
        animation: pulse-ring 2.5s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
    }}
    .sonar-ring:nth-child(2) {{ animation-delay: 0.8s; }}
    .sonar-ring:nth-child(3) {{ animation-delay: 1.6s; }}

    /* Wave bar at bottom of hero */
    .wave-bar {{
        position: relative;
        height: 40px;
        overflow: hidden;
        margin-top: 2rem;
    }}
    .wave-bar svg {{
        position: absolute;
        bottom: 0;
        left: 0;
        width: 200%;
        height: 40px;
        animation: wave 8s linear infinite;
    }}

    /* ═══════════════════════════════
       SIDEBAR SECTION LABELS
    ═══════════════════════════════ */
    .sidebar-label {{
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: {colors['text_muted']};
        margin-bottom: 10px;
        padding-left: 4px;
    }}
    .sidebar-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, {colors['border']}, transparent);
        margin: 16px 0;
    }}
    .sidebar-brand {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .sidebar-brand-text {{
        font-size: 1.35rem;
        font-weight: 800;
        background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .sidebar-footer {{
        position: fixed;
        bottom: 16px;
        font-size: 0.7rem;
        color: {colors['text_muted']};
        opacity: 0.6;
    }}

    /* ═══════════════════════════════
       INFO BOX — STYLED
    ═══════════════════════════════ */
    [data-testid="stAlert"] {{
        background: {colors['card_bg']} !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid {colors['card_border']} !important;
        border-radius: 12px !important;
        color: {colors['text']} !important;
    }}

    /* ═══════════════════════════════
       SCROLLBAR
    ═══════════════════════════════ */
    ::-webkit-scrollbar {{
        width: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    ::-webkit-scrollbar-thumb {{
        background: rgba({colors['primary_rgb']}, 0.3);
        border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba({colors['primary_rgb']}, 0.5);
    }}

    /* ═══════════════════════════════
       SPINNER OVERRIDE
    ═══════════════════════════════ */
    .stSpinner > div {{
        border-top-color: {colors['primary']} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────
# Header
# ─────────────────────────────
st.markdown('<div class="main-title">🌊 FloatChat</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-Powered Conversational Interface for ARGO Ocean Data · INCOIS</div>',
    unsafe_allow_html=True
)

# ─────────────────────────────
# Auto Fetch
# ─────────────────────────────
def auto_fetch_if_needed(query: str):
    today_keywords = ['today', 'current', 'latest', 'now']
    if any(k in query.lower() for k in today_keywords):
        fetch_and_ingest(datetime.now())
        return

    date_patterns = [
        r'(\d{2}-\d{2}-\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, query)
        if match:
            date_str = match.group(1)
            try:
                parts = date_str.split('-')
                if len(parts[0]) == 2 and len(parts[2]) == 4:
                    date = datetime.strptime(date_str, "%d-%m-%Y")
                elif len(parts[0]) == 4:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    continue
                fetch_and_ingest(date)
            except Exception:
                pass

# ─────────────────────────────
# Smart Intent Detection
# ─────────────────────────────
def wants_map(query: str) -> bool:
    keywords = ['location', 'map', 'where', 'float location', 'show float', 'position', 'coordinates', 'locate', 'find float', 'nearest float']
    return any(k in query.lower() for k in keywords)

def wants_sql(query: str) -> bool:
    keywords = ['sql', 'query', 'code', 'how did you', 'show query', 'database query']
    return any(k in query.lower() for k in keywords)

# ─────────────────────────────
# Compute Statistics from DataFrame
# ─────────────────────────────
def compute_stats(df):
    """Extract key statistics from dataframe columns"""
    stats = []
    
    # Temperature stats
    temp_cols = [c for c in df.columns if 'temp' in c.lower() or c.lower() == 'avg']
    if temp_cols:
        temp_col = temp_cols[0]
        if pd.api.types.is_numeric_dtype(df[temp_col]):
            stats.append(("Min Temp", f"{df[temp_col].min():.2f}°C"))
            stats.append(("Max Temp", f"{df[temp_col].max():.2f}°C"))
            stats.append(("Avg Temp", f"{df[temp_col].mean():.2f}°C"))
    
    # Salinity stats
    sal_cols = [c for c in df.columns if 'sal' in c.lower()]
    if sal_cols:
        sal_col = sal_cols[0]
        if pd.api.types.is_numeric_dtype(df[sal_col]):
            stats.append(("Min Salinity", f"{df[sal_col].min():.2f} PSU"))
            stats.append(("Max Salinity", f"{df[sal_col].max():.2f} PSU"))
    
    # Count stats
    count_cols = [c for c in df.columns if 'count' in c.lower()]
    if count_cols:
        count_col = count_cols[0]
        if pd.api.types.is_numeric_dtype(df[count_col]):
            stats.append(("Total Count", f"{int(df[count_col].sum()):,}"))
    
    # Data points count
    stats.append(("Data Points", str(len(df))))
    
    return stats

# ─────────────────────────────
# Chart Function — Enhanced
# ─────────────────────────────
def show_chart(df, query=""):
    if df is None or df.empty:
        return

    cols = df.columns.tolist()

    temp_col  = next((c for c in cols if 'temp' in c.lower() or c.lower() == 'avg'), None)
    sal_col   = next((c for c in cols if 'sal'  in c.lower()), None)
    date_col  = next((c for c in cols if any(x in c.lower() for x in ['date', 'year', 'month', 'time'])), None)
    pres_col  = next((c for c in cols if 'pres' in c.lower()), None)
    count_col = next((c for c in cols if 'count' in c.lower()), None)

    plotly_layout = dict(
        template=colors['plotly_template'],
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=420,
        margin=dict(l=30, r=30, t=70, b=30),
        font=dict(family="Inter", color=colors['text'], size=12),
        xaxis=dict(gridcolor=colors['plotly_grid'], zeroline=False),
        yaxis=dict(gridcolor=colors['plotly_grid'], zeroline=False),
        hoverlabel=dict(
            bgcolor=colors['bg_solid'],
            font_size=13,
            font_family="Inter",
            bordercolor=colors['primary']
        )
    )

    if wants_map(query) and 'latitude' in cols and 'longitude' in cols:
        st.markdown(f"""<div class="chart-container">
            <div class="chart-title">🗺️ Float Locations</div>
        """, unsafe_allow_html=True)
        df_map = df.drop_duplicates(subset=['latitude', 'longitude'])
        fig = px.scatter_geo(
            df_map,
            lat='latitude',
            lon='longitude',
            hover_data=[c for c in cols if c in df_map.columns],
            color_discrete_sequence=[colors['map_marker']]
        )
        fig.update_traces(marker=dict(size=10, opacity=0.85,
                                       line=dict(width=1.5, color='white')))
        fig.update_geos(
            center=dict(lat=15, lon=75),
            projection_scale=4,
            showcountries=True,
            showcoastlines=True,
            showocean=True,
            oceancolor=colors['map_ocean'],
            showland=True,
            landcolor=colors['map_land'],
            countrycolor=colors['map_border'],
            coastlinecolor=colors['map_border']
        )
        fig.update_layout(**plotly_layout, title=dict(text="Argo Float Locations — Indian Ocean", font=dict(size=16, color=colors['text'])))
        st.plotly_chart(fig, width='stretch', theme=None)
        st.markdown("</div>", unsafe_allow_html=True)

    if temp_col and date_col:
        st.markdown(f"""<div class="chart-container">
            <div class="chart-title">🌡️ Temperature Over Time</div>
        """, unsafe_allow_html=True)
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        except Exception:
            pass

        if 'latitude' in cols and 'longitude' in cols:
            df_plot = df.drop_duplicates(subset=[date_col, 'latitude', 'longitude']).sort_values(date_col)
        else:
            df_plot = df.sort_values(date_col)

        unique_times = df_plot[date_col].nunique()
        if unique_times <= 2:
            st.metric("Average Temperature", f"{df[temp_col].mean():.2f}°C")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_plot[date_col],
                y=df_plot[temp_col],
                mode='lines',
                name='Temperature',
                line=dict(color=colors['primary'], width=2.5, shape='spline'),
                fill='tozeroy',
                fillcolor=f'rgba({colors["primary_rgb"]}, 0.08)',
            ))
            fig.update_layout(
                **plotly_layout,
                title=dict(text="Ocean Temperature Dynamics", font=dict(size=16, color=colors['text'])),
                xaxis_title="Date",
                yaxis_title="Temperature (°C)"
            )
            st.plotly_chart(fig, width='stretch', theme=None)
        st.markdown("</div>", unsafe_allow_html=True)

    if sal_col and date_col and not temp_col:
        st.markdown(f"""<div class="chart-container">
            <div class="chart-title">🧂 Salinity Readings</div>
        """, unsafe_allow_html=True)
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        except Exception:
            pass
        fig = px.scatter(
            df, x=date_col, y=sal_col,
            labels={sal_col: 'Salinity (PSU)', date_col: 'Date'}
        )
        fig.update_traces(marker=dict(
            color=colors['primary'], size=9, opacity=0.8,
            line=dict(width=1, color='white')
        ))
        fig.update_layout(
            **plotly_layout,
            title=dict(text="Ocean Salinity Tracking", font=dict(size=16, color=colors['text']))
        )
        st.plotly_chart(fig, width='stretch', theme=None)
        st.markdown("</div>", unsafe_allow_html=True)

    if pres_col and temp_col and not date_col:
        st.markdown(f"""<div class="chart-container">
            <div class="chart-title">🌊 Depth vs Temperature Profile</div>
        """, unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[temp_col],
            y=df[pres_col],
            mode='lines+markers',
            name='Temperature',
            line=dict(color=colors['primary'], width=2.5, shape='spline'),
            marker=dict(size=7, color=colors['bg_solid'],
                        line=dict(color=colors['primary'], width=2))
        ))
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            xaxis_title="Temperature (°C)",
            yaxis_title="Depth (dbar)",
            **plotly_layout,
            title=dict(text="Vertical Temperature Profile", font=dict(size=16, color=colors['text']))
        )
        st.plotly_chart(fig, width='stretch', theme=None)
        st.markdown("</div>", unsafe_allow_html=True)

    if count_col and len(df) == 1:
        st.metric(label="Total Count", value=f"{int(df[count_col].iloc[0]):,}")

# ─────────────────────────────
# Sidebar — Redesigned
# ─────────────────────────────
with st.sidebar:
    # Brand + Theme Toggle
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"""
            <div class="sidebar-brand">
                <span style="font-size:1.6rem;">🌊</span>
                <span class="sidebar-brand-text">FloatChat</span>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="theme-btn">', unsafe_allow_html=True)
        if st.session_state.theme == "light":
            if st.button("🌙", key="theme_toggle"):
                st.session_state.theme = "dark"
                st.rerun()
        else:
            if st.button("☀️", key="theme_toggle"):
                st.session_state.theme = "light"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<p style="color:{colors["text_muted"]}; margin-top:0; font-size:0.82rem;">INCOIS · Ocean Data Discovery</p>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # Quick prompts
    st.markdown('<div class="sidebar-label">💡 Quick Query</div>', unsafe_allow_html=True)
    sample_queries = [
        ("🧂", "Salinity profiles near equator in Jan 2024"),
        ("🌡️", "Avg temp in Arabian Sea in 2023?"),
        ("🔢", "How many floats in the Indian Ocean?"),
        ("📍", "Float locations in Arabian Sea in 2023"),
    ]
    for icon, q in sample_queries:
        if st.button(f"{icon}  {q}", use_container_width=True, disabled=st.session_state.is_processing):
            st.session_state.selected_query = q

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # About section
    st.markdown('<div class="sidebar-label">ℹ️ About</div>', unsafe_allow_html=True)
    st.markdown(f"""
        <div style="font-size:0.8rem; color:{colors['text_muted']}; line-height:1.6;">
            FloatChat uses <b style="color:{colors['text']}">RAG + NL-to-SQL</b> to query
            real-time ARGO float data from INCOIS.
            Ask about temperature, salinity, float locations, and more.
        </div>
    """, unsafe_allow_html=True)

    

# ─────────────────────────────
# Format AI Response HTML
# ─────────────────────────────
def format_ai_html(text):
    """Convert plain text to styled HTML with proper formatting."""
    html = text
    # Escape HTML entities first
    html = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Convert back allowed tags
    html = html.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
    html = html.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
    html = html.replace("&lt;br/&gt;", "<br/>")
    # Handle bullet points
    lines = html.split("\n")
    formatted_lines = []
    for line in lines:
        if line.strip().startswith("•") or line.strip().startswith("-"):
            formatted_lines.append(f"<li style='margin-left:20px;'>{line.strip()[1:].strip()}</li>")
        else:
            formatted_lines.append(line)
    html = "\n".join(formatted_lines)
    if "<li" in html:
        html = html.replace("<li", "<ul><li").replace("</li>\n<li", "</li><li") + "</ul>"
    # Italicize source references (words in parentheses with 'Source' or similar)
    html = html.replace("(Source:", "<i style='color:" + colors['text_muted'] + "'>(Source:")
    html = html.replace("INCOIS)", "INCOIS)</i>")
    # Highlight follow-up questions
    html = html.replace("?", f"?<span style='color:{colors['accent']}'>⚡</span>")
    return html

# ─────────────────────────────
# Chat History
# ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# Welcome hero (empty state)
if not st.session_state.messages and not st.session_state.is_processing:
    wave_color = colors['primary']
    st.markdown(f"""
    <div class="hero-container">
        <div class="sonar-wrap">
            <div class="sonar-ring"></div>
            <div class="sonar-ring"></div>
            <div class="sonar-ring"></div>
            <div class="hero-icon">🌊</div>
        </div>
        <div class="hero-heading">Welcome to FloatChat</div>
        <div class="hero-sub">
            Explore real-time ocean data from ARGO floats across the Indian Ocean.
            Ask questions in natural language — I'll fetch and visualize the data for you.
        </div>
        <div class="features-grid">
            <div class="feature-card">
                <span class="feature-icon">🌡️</span>
                <div class="feature-label">Temperature</div>
                <div class="feature-desc">Sea surface & depth profiles</div>
            </div>
            <div class="feature-card">
                <span class="feature-icon">🧂</span>
                <div class="feature-label">Salinity</div>
                <div class="feature-desc">PSU readings across regions</div>
            </div>
            <div class="feature-card">
                <span class="feature-icon">📏</span>
                <div class="feature-label">PRES</div>
                <div class="feature-desc">Pressure (depth) in dbar · 1 dbar ≈ 1 m</div>
            </div>
            <div class="feature-card">
                <span class="feature-icon">📍</span>
                <div class="feature-label">Locations</div>
                <div class="feature-desc">Float positions on maps</div>
            </div>
            <div class="feature-card">
                <span class="feature-icon">📊</span>
                <div class="feature-label">Analytics</div>
                <div class="feature-desc">Trends, counts & insights</div>
            </div>
        </div>
        <div class="wave-bar">
            <svg viewBox="0 0 1440 40" preserveAspectRatio="none">
                <path fill="rgba({colors['primary_rgb']}, 0.12)"
                      d="M0,20 C360,40 720,0 1080,20 C1260,30 1350,10 1440,20 L1440,40 L0,40 Z"/>
                <path fill="rgba({colors['accent_rgb']}, 0.08)"
                      d="M0,25 C320,10 640,35 960,20 C1120,12 1300,30 1440,22 L1440,40 L0,40 Z"/>
            </svg>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Display history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        ts = msg.get("timestamp", "")
        st.markdown(f"""
        <div style="margin-bottom:20px;">
            <div style="text-align:right;margin-bottom:8px;">
                <span style="background:linear-gradient(135deg,{colors['primary']},{colors['accent']});-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;font-weight:600;">You</span>
                <span style="color:{colors['text_muted']};font-size:0.8rem;margin-left:8px;">{ts}</span>
            </div>
            <div style="background:{colors['card_bg']};border-left:3px solid {colors['primary']};border-radius:8px;padding:12px 14px;max-width:80%;margin-left:auto;">
                {msg['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        ts = msg.get("timestamp", "")
        formatted = format_ai_html(msg["content"])
        st.markdown(f"""
        <div style="margin-bottom:20px;">
            <div style="display:flex;align-items:center;margin-bottom:8px;">
                <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,{colors['primary']},{colors['accent']});display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;margin-right:8px;">O</div>
                <span style="color:{colors['text']};font-weight:600;">FloatChat</span>
                <span style="color:{colors['text_muted']};font-size:0.8rem;margin-left:8px;">{ts}</span>
            </div>
            <div style="background:{colors['card_bg']};border-left:3px solid {colors['accent']};border-radius:8px;padding:14px 16px;max-width:85%;">
                {formatted}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # SQL expander
        if "sql" in msg and wants_sql(msg.get("query", "")):
            with st.expander("🔍 View SQL Query"):
                st.code(msg["sql"], language="sql")
        
        # Data visualization and stats
        if "data" in msg and msg["data"]:
            df = pd.DataFrame(msg["data"])
            if not df.empty:
                show_chart(df, msg.get("query", ""))
                
                # Source attribution
                st.markdown(f'<div style="text-align:center;margin:12px 0;font-size:0.75rem;color:{colors["text_muted"]}">Source: ARGO Float Network · INCOIS&nbsp;&nbsp;<a href="https://www.incois.gov.in/portal/argo/argofloats_702.jsp" target="_blank" style="color:{colors["primary"]}">🔗 View Source</a></div>', unsafe_allow_html=True)
                
                # Statistics
                stats = compute_stats(df)
                if stats:
                    st.markdown(f'<div style="margin-top:16px;font-weight:600;color:{colors["text"]};font-size:0.9rem;text-transform:uppercase;letter-spacing:1px;">📊 Statistics</div>', unsafe_allow_html=True)
                    stat_cols = st.columns(2)
                    for i, (label, value) in enumerate(stats):
                        with stat_cols[i % 2]:
                            st.markdown(f'<div style="background:{colors["card_bg"]};border:1px solid {colors["card_border"]};border-radius:12px;padding:14px 16px;text-align:center;margin-bottom:10px;"><div style="font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,{colors["primary"]},{colors["accent"]});-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{value}</div><div style="font-size:0.72rem;color:{colors["text_muted"]};text-transform:uppercase;letter-spacing:0.8px;margin-top:4px;font-weight:600;">{label}</div></div>', unsafe_allow_html=True)
                
                with st.expander("📄 View Raw Data"):
                    st.dataframe(df, use_container_width=True)

# ─────────────────────────────
# Chat Input & Action Logic
# ─────────────────────────────
default_query = st.session_state.get("selected_query", "")
if default_query:
    st.session_state.selected_query = ""

user_input = st.chat_input(
    "Ask about ocean data...",
    disabled=st.session_state.is_processing
)

# Step 1: Detect Input
if (user_input or default_query) and not st.session_state.is_processing:
    query = user_input or default_query

    st.session_state.messages.append({
        "role"   : "user",
        "content": query
    })

    st.session_state.pending_query = query
    st.session_state.is_processing = True
    st.rerun()

# Step 2: Process Input
if st.session_state.is_processing and st.session_state.pending_query:
    query = st.session_state.pending_query

    with st.chat_message("assistant"):
        # Custom animated loader
        loader_placeholder = st.empty()
        loader_placeholder.markdown("""
        <div class="processing-indicator">
            <div class="dot-loader">
                <span></span><span></span><span></span>
            </div>
            <span class="processing-text">Analyzing query & fetching ocean data...</span>
        </div>
        """, unsafe_allow_html=True)

        auto_fetch_if_needed(query)
        result = ask_with_rag(query)

        # Clear loader
        loader_placeholder.empty()

        # Answer Output
        st.markdown(f'<div class="answer-box"><b>AI Response:</b><br/>{result["answer"]}</div>', unsafe_allow_html=True)

        if wants_sql(query):
            with st.expander("🔍 View SQL Query"):
                st.code(result["sql"], language="sql")

        # Visual Output
        if result["data"] and "error" not in result["data"][0]:
            df = pd.DataFrame(result["data"])
            if not df.empty:
                show_chart(df, query)
                
                # Source attribution
                st.markdown("""<div class="viz-source">Source: ARGO Float Network · INCOIS&nbsp;&nbsp;<a href="https://www.incois.gov.in/portal/argo/argofloats_702.jsp" target="_blank">🔗 View Source</a></div>""", unsafe_allow_html=True)
                
                # Statistics
                stats = compute_stats(df)
                if stats:
                    st.markdown('<div class="viz-section-title">Statistics</div>', unsafe_allow_html=True)
                    stat_cols = st.columns(2)
                    for i, (label, value) in enumerate(stats):
                        with stat_cols[i % 2]:
                            st.markdown(f'<div style="background:{colors["card_bg"]};border:1px solid {colors["card_border"]};border-radius:12px;padding:14px 16px;text-align:center;margin-bottom:10px;"><div style="font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,{colors["primary"]},{colors["accent"]});-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{value}</div><div style="font-size:0.72rem;color:{colors["text_muted"]};text-transform:uppercase;letter-spacing:0.8px;margin-top:4px;font-weight:600;">{label}</div></div>', unsafe_allow_html=True)
                
                with st.expander("📄 View Raw Data"):
                    st.dataframe(df, width='stretch')
        else:
            st.info("No numerical or tabular data available for charting under this context.")

    # Save to history
    st.session_state.messages.append({
        "role"   : "assistant",
        "content": result['answer'],
        "sql"    : result.get("sql", ""),
        "data"   : result.get("data", None),
        "query"  : query
    })

    # Unlock
    st.session_state.is_processing = False
    st.session_state.pending_query = ""
    st.rerun()
