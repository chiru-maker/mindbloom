"""
utils.py
---------
Shared helper functions for MindBloom: custom CSS/theming, streak
calculation, achievement checking, and small safe-guard utilities so
the app never crashes on missing or empty data.
"""

from datetime import datetime, timedelta
import streamlit as st

import database as db


# ---------------------------------------------------------------------
# STYLING
# ---------------------------------------------------------------------

FONT_SIZE_MAP = {
    "Normal": {"base": "18px", "heading": "36px", "button": "20px"},
    "Large": {"base": "22px", "heading": "42px", "button": "24px"},
    "Extra Large": {"base": "27px", "heading": "50px", "button": "29px"},
}


def apply_custom_style(font_size="Normal", high_contrast=False):
    """
    Inject custom CSS to give MindBloom a stunning, modern dark liquid glass
    aesthetic with frosted glass cards, glowing neon accents, elegant typography,
    and responsive layout.
    """
    sizes = FONT_SIZE_MAP.get(font_size, FONT_SIZE_MAP["Normal"])

    if high_contrast:
        bg_color = "#000000"
        text_color = "#FFFFFF"
        card_bg = "rgba(20, 20, 20, 0.95)"
        primary_color = "#FFD60A"
        primary_text = "#000000"
        border_color = "#FFD60A"
        sidebar_bg = "#0a0a0a"
    else:
        bg_color = "#07090e"
        text_color = "#f8fafc"
        card_bg = "linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.02) 100%), rgba(15, 21, 37, 0.72)"
        primary_color = "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%)"
        primary_text = "#FFFFFF"
        border_color = "rgba(255, 255, 255, 0.12)"
        sidebar_bg = "rgba(10, 14, 26, 0.85)"

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"], .stApp {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            font-size: {sizes['base']} !important;
            background-color: {bg_color} !important;
            color: {text_color} !important;
        }}

        h1 {{
            font-family: 'Outfit', sans-serif !important;
            font-size: {sizes['heading']} !important;
            font-weight: 800 !important;
            color: #ffffff !important;
            letter-spacing: -0.02em;
        }}
        h2 {{
            font-family: 'Outfit', sans-serif !important;
            font-size: calc({sizes['heading']} * 0.7) !important;
            font-weight: 700 !important;
            color: #f1f5f9 !important;
        }}
        h3 {{
            font-family: 'Outfit', sans-serif !important;
            font-size: calc({sizes['heading']} * 0.52) !important;
            font-weight: 700 !important;
            color: #e2e8f0 !important;
        }}
        h4, h5, h6 {{
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
            color: #f8fafc !important;
        }}
        p, span, label, div, li, .stMarkdown p, .stMarkdown span {{
            font-size: {sizes['base']};
            color: #e2e8f0 !important;
        }}

        /* Buttons: Glassmorphic with gradient & press physics */
        .stButton > button {{
            background: {primary_color if not high_contrast else primary_color} !important;
            color: {primary_text} !important;
            font-family: 'Outfit', sans-serif !important;
            font-size: {sizes['button']} !important;
            font-weight: 700 !important;
            border-radius: 16px !important;
            border: 1px solid rgba(255, 255, 255, 0.25) !important;
            padding: 0.8em 1.4em !important;
            width: 100% !important;
            min-height: 3.1em !important;
            box-shadow: 0 8px 24px -4px rgba(99, 102, 241, 0.45), inset 0 1px 1px rgba(255, 255, 255, 0.4) !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            cursor: pointer !important;
        }}
        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 12px 30px -4px rgba(139, 92, 246, 0.65), 0 0 20px rgba(217, 70, 239, 0.4) !important;
            filter: brightness(1.08) !important;
        }}
        .stButton > button:active {{
            transform: translateY(1px) !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
        }}

        /* Glass Cards */
        .mb-card, .mb-glass-card {{
            background: {card_bg} !important;
            backdrop-filter: blur(24px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
            border: 1px solid {border_color} !important;
            border-top: 1px solid rgba(255, 255, 255, 0.25) !important;
            border-left: 1px solid rgba(255, 255, 255, 0.18) !important;
            border-radius: 24px !important;
            padding: 1.6em !important;
            margin-bottom: 1.2em !important;
            box-shadow: 0 20px 50px -10px rgba(0,0,0,0.65), inset 0 1px 1px rgba(255, 255, 255, 0.2) !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        }}
        .mb-card:hover, .mb-glass-card:hover {{
            border-color: rgba(255, 255, 255, 0.22) !important;
            box-shadow: 0 24px 60px -8px rgba(0,0,0,0.75), 0 0 30px rgba(99, 102, 241, 0.15) !important;
        }}

        .mb-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: rgba(99, 102, 241, 0.2);
            color: #c7d2fe;
            border: 1px solid rgba(129, 140, 248, 0.35);
            border-radius: 100px;
            padding: 0.35em 0.9em;
            font-weight: 600;
            font-size: 0.9rem;
            margin: 0.2em;
        }}
        .mb-center {{
            text-align: center;
        }}
        .mb-muted {{
            color: #94a3b8;
            font-size: calc({sizes['base']} * 0.9);
        }}

        /* Hero Welcome Banner */
        .mb-hero-banner {{
            position: relative;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.1) 50%, rgba(6, 182, 212, 0.08) 100%), rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(28px);
            -webkit-backdrop-filter: blur(28px);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-top: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 28px;
            padding: 2rem 2.2rem;
            margin-bottom: 1.8rem;
            box-shadow: 0 24px 60px -12px rgba(0, 0, 0, 0.7), 0 0 40px rgba(99, 102, 241, 0.15), inset 0 1px 1px rgba(255, 255, 255, 0.3);
        }}

        /* Stat Tile Card */
        .mb-stat-tile {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.015) 100%), rgba(15, 21, 37, 0.65);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.11);
            border-top: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 22px;
            padding: 1.4rem;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 14px 35px -6px rgba(0, 0, 0, 0.55), inset 0 1px 1px rgba(255, 255, 255, 0.15);
            transition: all 0.3s ease;
        }}
        .mb-stat-tile:hover {{
            transform: translateY(-3px);
            border-color: rgba(139, 92, 246, 0.4);
            box-shadow: 0 18px 45px -6px rgba(0, 0, 0, 0.7), 0 0 25px rgba(99, 102, 241, 0.2);
        }}

        /* Progress Bar */
        .mb-progress-track {{
            width: 100%;
            height: 10px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 100px;
            overflow: hidden;
            margin: 0.8rem 0;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .mb-progress-fill {{
            height: 100%;
            border-radius: 100px;
            background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #06b6d4 100%);
            box-shadow: 0 0 12px rgba(168, 85, 247, 0.6);
            transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        /* Quick Play Launch Card */
        .mb-game-card {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%), rgba(18, 24, 43, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 1.2rem;
            margin-bottom: 0.9rem;
            box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
            transition: all 0.25s ease;
        }}
        .mb-game-card:hover {{
            border-color: rgba(168, 85, 247, 0.45);
            box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.65), 0 0 25px rgba(139, 92, 246, 0.2);
            transform: translateY(-2px);
        }}

        /* Glass Trophy Card */
        .mb-trophy-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%), rgba(20, 26, 45, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 16px;
            padding: 0.65rem 1.1rem;
            margin: 0.3rem;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2);
            transition: transform 0.2s ease;
        }}
        .mb-trophy-badge:hover {{
            transform: scale(1.04);
            border-color: rgba(234, 179, 8, 0.5);
            box-shadow: 0 10px 25px rgba(234, 179, 8, 0.25);
        }}

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            backdrop-filter: blur(25px) !important;
            -webkit-backdrop-filter: blur(25px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }}

        /* Radio buttons used as nav - glowing pills */
        div[role="radiogroup"] label {{
            font-family: 'Outfit', sans-serif !important;
            font-size: calc({sizes['button']} * 0.9) !important;
            font-weight: 600 !important;
            padding: 0.6em 1em !important;
            margin-bottom: 0.3em !important;
            border-radius: 14px !important;
            transition: all 0.2s ease !important;
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            color: #f1f5f9 !important;
        }}
        div[role="radiogroup"] label:hover {{
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(165, 180, 252, 0.35) !important;
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.2) !important;
        }}

        /* Streamlit Input Elements (Dark Themed) */
        div[data-baseweb="input"] {{
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
            border-radius: 14px !important;
            transition: all 0.25s ease !important;
        }}
        div[data-baseweb="input"]:focus-within {{
            border-color: rgba(139, 92, 246, 0.85) !important;
            box-shadow: 0 0 18px rgba(129, 140, 248, 0.35) !important;
            background-color: rgba(255, 255, 255, 0.08) !important;
        }}
        input {{
            color: #ffffff !important;
        }}
        input::placeholder {{
            color: rgba(255, 255, 255, 0.4) !important;
        }}

        /* Streamlit Selectbox & Popovers */
        div[data-baseweb="select"] > div {{
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
            border-radius: 14px !important;
            color: #f8fafc !important;
        }}
        div[data-baseweb="select"] * {{
            color: #f8fafc !important;
        }}
        div[data-baseweb="popover"], div[data-baseweb="menu"] {{
            background-color: #0d1322 !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 14px !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8) !important;
        }}
        li[role="option"] {{
            color: #f1f5f9 !important;
            background-color: transparent !important;
        }}
        li[role="option"]:hover, li[aria-selected="true"] {{
            background-color: rgba(99, 102, 241, 0.25) !important;
            color: #ffffff !important;
        }}

        /* Streamlit Sliders & Toggles */
        div[data-testid="stSlider"] label, div[data-testid="stToggle"] label, div[data-testid="stCheckbox"] label {{
            color: #e2e8f0 !important;
            font-weight: 500 !important;
        }}
        div[data-testid="stSlider"] div[role="slider"] {{
            background-color: #a855f7 !important;
            box-shadow: 0 0 12px rgba(168, 85, 247, 0.8) !important;
        }}

        /* Streamlit Metrics */
        div[data-testid="stMetric"] {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.015) 100%), rgba(15, 21, 37, 0.65) !important;
            border: 1px solid rgba(255, 255, 255, 0.11) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.22) !important;
            border-radius: 20px !important;
            padding: 1.1rem 1.3rem !important;
            box-shadow: 0 10px 30px -6px rgba(0, 0, 0, 0.55) !important;
        }}
        div[data-testid="stMetricLabel"] * {{
            color: #94a3b8 !important;
            font-weight: 600 !important;
        }}
        div[data-testid="stMetricValue"] * {{
            color: #ffffff !important;
            font-weight: 800 !important;
            font-family: 'Outfit', sans-serif !important;
        }}

        /* Streamlit DataFrames */
        div[data-testid="stDataFrame"] {{
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 16px !important;
            overflow: hidden !important;
            background-color: rgba(15, 23, 42, 0.6) !important;
        }}

        /* Captions & Info */
        .stCaption, small, p.caption {{
            color: #94a3b8 !important;
        }}
        div[data-testid="stAlert"] {{
            background-color: rgba(15, 23, 42, 0.7) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 16px !important;
            color: #f1f5f9 !important;
        }}

        /* Custom scrollbars */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.2);
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.15);
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255, 255, 255, 0.3);
        }}
    </style>
    """, unsafe_allow_html=True)


def apply_liquid_glass_auth_style():
    """
    Inject ultra-premium Liquid Glass / Glassmorphism styling for the
    Authentication (Login / Sign Up) screen.
    Includes atmospheric deep dark canvas, multi-color glowing floating orbs,
    backdrop-filter frosted glass surfaces, specular highlights, glowing inputs,
    and fluid micro-animations.
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

        /* Dark Atmospheric Space Base */
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            background-color: #06080e !important;
            color: #f1f5f9 !important;
            overflow-x: hidden !important;
        }

        /* Hide Sidebar on Auth View */
        section[data-testid="stSidebar"] {
            display: none !important;
        }

        /* Header Bar & App Controls Styling */
        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        /* Ambient Animated Glowing Liquid Orbs */
        .mb-ambient-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            pointer-events: none;
            z-index: 0;
        }

        .mb-orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(95px);
            opacity: 0.65;
            will-change: transform;
        }

        .mb-orb-1 {
            top: 5%;
            left: 15%;
            width: 480px;
            height: 480px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.5) 0%, rgba(139, 92, 246, 0.3) 50%, transparent 70%);
            animation: orbFloat1 18s ease-in-out infinite alternate;
        }

        .mb-orb-2 {
            bottom: 8%;
            right: 12%;
            width: 520px;
            height: 520px;
            background: radial-gradient(circle, rgba(6, 182, 212, 0.45) 0%, rgba(59, 130, 246, 0.25) 50%, transparent 70%);
            animation: orbFloat2 22s ease-in-out infinite alternate;
        }

        .mb-orb-3 {
            top: 45%;
            left: 55%;
            width: 420px;
            height: 420px;
            background: radial-gradient(circle, rgba(236, 72, 153, 0.38) 0%, rgba(168, 85, 247, 0.2) 50%, transparent 70%);
            animation: orbFloat3 20s ease-in-out infinite alternate;
        }

        .mb-orb-4 {
            bottom: 30%;
            left: 5%;
            width: 350px;
            height: 350px;
            background: radial-gradient(circle, rgba(16, 185, 129, 0.25) 0%, rgba(6, 182, 212, 0.15) 50%, transparent 70%);
            animation: orbFloat4 25s ease-in-out infinite alternate;
        }

        @keyframes orbFloat1 {
            0% { transform: translate(0px, 0px) scale(1); }
            50% { transform: translate(60px, 80px) scale(1.1); }
            100% { transform: translate(-40px, 40px) scale(0.95); }
        }

        @keyframes orbFloat2 {
            0% { transform: translate(0px, 0px) scale(1); }
            50% { transform: translate(-80px, -60px) scale(1.15); }
            100% { transform: translate(50px, -30px) scale(0.9); }
        }

        @keyframes orbFloat3 {
            0% { transform: translate(0px, 0px) scale(0.95); }
            50% { transform: translate(-50px, 60px) scale(1.08); }
            100% { transform: translate(70px, -50px) scale(1); }
        }

        @keyframes orbFloat4 {
            0% { transform: translate(0px, 0px) scale(1); }
            50% { transform: translate(50px, -40px) scale(1.12); }
            100% { transform: translate(-30px, 60px) scale(0.88); }
        }

        /* Frosted Liquid Glass Card Container */
        .mb-auth-wrapper {
            position: relative;
            z-index: 1;
            max-width: 470px;
            margin: 1.5rem auto 3rem auto;
            padding: 0 1rem;
        }

        .mb-glass-panel {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%), rgba(12, 16, 28, 0.72) !important;
            backdrop-filter: blur(28px) saturate(190%) !important;
            -webkit-backdrop-filter: blur(28px) saturate(190%) !important;
            border: 1px solid rgba(255, 255, 255, 0.13) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.28) !important;
            border-left: 1px solid rgba(255, 255, 255, 0.22) !important;
            border-radius: 28px !important;
            box-shadow: 
                0 30px 70px -15px rgba(0, 0, 0, 0.85),
                0 0 50px rgba(99, 102, 241, 0.12),
                inset 0 1px 1px rgba(255, 255, 255, 0.3),
                inset 0 -1px 1px rgba(0, 0, 0, 0.4) !important;
            padding: 2.4rem 2.2rem 2.2rem 2.2rem;
            animation: glassFloatIn 0.75s cubic-bezier(0.16, 1, 0.3, 1) both;
            transition: box-shadow 0.4s ease, border-color 0.4s ease;
        }

        .mb-glass-panel:hover {
            border-color: rgba(255, 255, 255, 0.18) !important;
            box-shadow: 
                0 35px 80px -12px rgba(0, 0, 0, 0.9),
                0 0 60px rgba(139, 92, 246, 0.18),
                inset 0 1px 2px rgba(255, 255, 255, 0.35) !important;
        }

        @keyframes glassFloatIn {
            0% {
                opacity: 0;
                transform: translateY(28px) scale(0.96);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        /* Brand & Headers */
        .mb-brand-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.6rem;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.03) 100%);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 100px;
            padding: 0.45rem 1.1rem;
            margin-bottom: 1.2rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 4px 15px rgba(0, 0, 0, 0.3);
        }

        .mb-brand-logo {
            font-size: 1.25rem;
            filter: drop-shadow(0 0 8px rgba(244, 114, 182, 0.6));
        }

        .mb-brand-title {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700;
            font-size: 1.05rem;
            letter-spacing: 0.04em;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .mb-auth-heading {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 800 !important;
            font-size: 1.85rem !important;
            line-height: 1.2 !important;
            margin: 0.2rem 0 0.4rem 0 !important;
            background: linear-gradient(135deg, #ffffff 20%, #e2e8f0 70%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }

        .mb-auth-subheading {
            color: #94a3b8 !important;
            font-size: 0.96rem !important;
            margin-bottom: 1.5rem !important;
            font-weight: 400 !important;
        }

        /* Glass Input Fields */
        div[data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
        }

        .stTextInput label {
            color: #cbd5e1 !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            margin-bottom: 0.35rem !important;
            letter-spacing: 0.01em !important;
        }

        div[data-baseweb="input"] {
            background-color: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 14px !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.25) !important;
        }

        div[data-baseweb="input"]:focus-within {
            border-color: rgba(129, 140, 248, 0.85) !important;
            background-color: rgba(255, 255, 255, 0.08) !important;
            box-shadow: 
                0 0 22px rgba(99, 102, 241, 0.35),
                inset 0 0 8px rgba(99, 102, 241, 0.15),
                inset 0 1px 1px rgba(255, 255, 255, 0.2) !important;
        }

        input {
            color: #f8fafc !important;
            font-size: 0.98rem !important;
            font-family: inherit !important;
            padding: 0.75rem 1rem !important;
        }

        input::placeholder {
            color: rgba(148, 163, 184, 0.45) !important;
            font-weight: 400 !important;
        }

        /* Show/Hide Password Checkbox / Helper */
        div[data-testid="stCheckbox"] label {
            color: #94a3b8 !important;
            font-size: 0.85rem !important;
            cursor: pointer !important;
        }

        /* Primary Glassmorphism Button */
        div[data-testid="stFormSubmitButton"] > button {
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%) !important;
            color: #ffffff !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
            letter-spacing: 0.02em !important;
            border-radius: 16px !important;
            border: 1px solid rgba(255, 255, 255, 0.32) !important;
            padding: 0.9rem 1.6rem !important;
            width: 100% !important;
            min-height: 3.2rem !important;
            box-shadow: 
                0 10px 28px -4px rgba(99, 102, 241, 0.55),
                0 0 20px rgba(168, 85, 247, 0.3),
                inset 0 1px 1px rgba(255, 255, 255, 0.5) !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            cursor: pointer !important;
            margin-top: 0.8rem !important;
        }

        div[data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 
                0 16px 36px -4px rgba(139, 92, 246, 0.75),
                0 0 30px rgba(217, 70, 239, 0.55),
                inset 0 1px 2px rgba(255, 255, 255, 0.6) !important;
            filter: brightness(1.08) !important;
        }

        div[data-testid="stFormSubmitButton"] > button:active {
            transform: translateY(1px) !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4) !important;
        }

        /* Glass Switcher Button (Don't have an account / Already have an account) */
        .mb-auth-switch-btn > button {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.09) !important;
            color: #a5b4fc !important;
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            border-radius: 12px !important;
            padding: 0.6rem 1.2rem !important;
            width: 100% !important;
            min-height: 2.6rem !important;
            box-shadow: none !important;
            transition: all 0.25s ease !important;
            margin-top: 0.6rem !important;
        }

        .mb-auth-switch-btn > button:hover {
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(165, 180, 252, 0.4) !important;
            color: #ffffff !important;
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.25) !important;
            transform: translateY(-1px) !important;
        }

        /* Glass Error Alert Box */
        .mb-glass-error {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.16) 0%, rgba(185, 28, 28, 0.08) 100%) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(248, 113, 113, 0.38) !important;
            border-top: 1px solid rgba(254, 202, 202, 0.5) !important;
            border-radius: 16px !important;
            padding: 0.85rem 1.1rem !important;
            color: #fecaca !important;
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            margin-bottom: 1.2rem !important;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            box-shadow: 0 8px 24px -4px rgba(239, 68, 68, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
            animation: alertShake 0.4s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
        }

        @keyframes alertShake {
            10%, 90% { transform: translate3d(-1px, 0, 0); }
            20%, 80% { transform: translate3d(2px, 0, 0); }
            30%, 50%, 70% { transform: translate3d(-3px, 0, 0); }
            40%, 60% { transform: translate3d(3px, 0, 0); }
        }

        /* Responsive Breakpoints */
        @media (max-width: 640px) {
            .mb-auth-wrapper {
                margin: 0.5rem auto 2rem auto;
                padding: 0 0.5rem;
            }
            .mb-glass-panel {
                padding: 1.8rem 1.4rem 1.6rem 1.4rem;
                border-radius: 22px !important;
            }
            .mb-auth-heading {
                font-size: 1.55rem !important;
            }
            .mb-orb {
                filter: blur(75px);
            }
        }
    </style>

    <!-- Floating Background Orbs Markup -->
    <div class="mb-ambient-container">
        <div class="mb-orb mb-orb-1"></div>
        <div class="mb-orb mb-orb-2"></div>
        <div class="mb-orb mb-orb-3"></div>
        <div class="mb-orb mb-orb-4"></div>
    </div>
    """, unsafe_allow_html=True)


def apply_caregiver_dashboard_style():
    """
    Injects a unique, high-tech Medical-Grade Neurotech background and UI styling
    specifically tailored for the Caregiver & Clinician Dashboard.
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        /* Custom Caregiver Ambient Cyber-Grid & Neuro Aurora Background */
        .stApp {
            background-color: #030712 !important;
            background-image: 
                radial-gradient(at 0% 0%, rgba(6, 182, 212, 0.18) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.22) 0px, transparent 50%),
                radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.14) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(56, 189, 248, 0.16) 0px, transparent 50%),
                linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px) !important;
            background-size: 100% 100%, 100% 100%, 100% 100%, 100% 100%, 36px 36px, 36px 36px !important;
            background-attachment: fixed !important;
        }

        /* Caregiver Header Banner */
        .mb-cg-banner {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.14) 0%, rgba(15, 23, 42, 0.85) 60%, rgba(99, 102, 241, 0.16) 100%);
            border: 1px solid rgba(6, 182, 212, 0.3);
            border-radius: 20px;
            padding: 1.8rem 2rem;
            margin-bottom: 1.6rem;
            box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.6), 0 0 25px rgba(6, 182, 212, 0.12);
            backdrop-filter: blur(20px);
            position: relative;
            overflow: hidden;
        }
        .mb-cg-banner::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 50%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.06), transparent);
            animation: cgShimmer 8s infinite linear;
        }
        @keyframes cgShimmer {
            0% { left: -100%; }
            100% { left: 200%; }
        }

        /* Medical Telemetry Cards */
        .mb-cg-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.75) 0%, rgba(30, 41, 59, 0.45) 100%);
            border: 1px solid rgba(56, 189, 248, 0.18);
            border-radius: 18px;
            padding: 1.4rem;
            backdrop-filter: blur(20px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 1rem;
        }
        .mb-cg-card:hover {
            border-color: rgba(56, 189, 248, 0.45);
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.55), 0 0 20px rgba(6, 182, 212, 0.2);
            transform: translateY(-2px);
        }

        /* Status Live Indicator Badge */
        .mb-cg-status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 9999px;
            padding: 4px 14px;
            font-size: 0.82rem;
            font-weight: 600;
            color: #34d399;
            letter-spacing: 0.04em;
        }
        .mb-cg-pulse-dot {
            width: 8px;
            height: 8px;
            background-color: #34d399;
            border-radius: 50%;
            box-shadow: 0 0 8px #34d399;
            animation: cgPulse 1.8s infinite ease-in-out;
        }
        @keyframes cgPulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.4); opacity: 0.5; }
        }

        /* Telemetry Metric Tile */
        .mb-cg-metric-tile {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-left: 3px solid #06b6d4;
            border-radius: 14px;
            padding: 1.1rem 1.3rem;
            margin-bottom: 0.8rem;
            transition: all 0.25s ease;
        }
        .mb-cg-metric-tile:hover {
            border-left-color: #38bdf8;
            background: rgba(15, 23, 42, 0.85);
            box-shadow: 0 8px 24px rgba(6, 182, 212, 0.15);
        }

        /* Caregiver PIN Vault Card */
        .mb-cg-vault-box {
            max-width: 480px;
            margin: 2.5rem auto;
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.6) 100%);
            border: 1px solid rgba(6, 182, 212, 0.35);
            border-radius: 24px;
            padding: 2.4rem 2rem;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(6, 182, 212, 0.18);
            backdrop-filter: blur(28px);
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)


def apply_home_style():
    """
    Botanical Bloom & Morning Sanctuary Background (Warm Lotus, Mint Emerald & Morning Gold).
    """
    st.markdown("""
    <style>
        .stApp {
            background-color: #030a0d !important;
            background-image: 
                radial-gradient(at 10% 15%, rgba(244, 114, 182, 0.18) 0px, transparent 45%),
                radial-gradient(at 90% 20%, rgba(52, 211, 153, 0.20) 0px, transparent 50%),
                radial-gradient(at 50% 85%, rgba(251, 191, 36, 0.14) 0px, transparent 55%),
                radial-gradient(at 85% 90%, rgba(167, 139, 250, 0.16) 0px, transparent 50%),
                radial-gradient(rgba(52, 211, 153, 0.08) 1.5px, transparent 1.5px) !important;
            background-size: 100% 100%, 100% 100%, 100% 100%, 100% 100%, 32px 32px !important;
            background-attachment: fixed !important;
        }
        .mb-hero-banner {
            border: 1px solid rgba(244, 114, 182, 0.25) !important;
            background: linear-gradient(135deg, rgba(244, 114, 182, 0.12) 0%, rgba(15, 23, 42, 0.85) 50%, rgba(52, 211, 153, 0.12) 100%) !important;
            box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.5), 0 0 25px rgba(244, 114, 182, 0.12) !important;
        }
        .mb-stat-tile {
            border-top: 3px solid #34d399 !important;
        }
    </style>
    """, unsafe_allow_html=True)


def apply_play_style():
    """
    Cyber-Arcade & Cognitive Arena Background (Electric Cyan & Neon Fuchsia Matrix).
    """
    st.markdown("""
    <style>
        .stApp {
            background-color: #080318 !important;
            background-image: 
                radial-gradient(at 15% 10%, rgba(236, 72, 153, 0.24) 0px, transparent 50%),
                radial-gradient(at 85% 15%, rgba(6, 182, 212, 0.26) 0px, transparent 50%),
                radial-gradient(at 50% 60%, rgba(147, 51, 234, 0.20) 0px, transparent 60%),
                radial-gradient(at 20% 90%, rgba(59, 130, 246, 0.22) 0px, transparent 50%),
                radial-gradient(rgba(236, 72, 153, 0.12) 1.5px, transparent 1.5px),
                linear-gradient(rgba(6, 182, 212, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(6, 182, 212, 0.03) 1px, transparent 1px) !important;
            background-size: 100% 100%, 100% 100%, 100% 100%, 100% 100%, 28px 28px, 28px 28px, 28px 28px !important;
            background-attachment: fixed !important;
        }
        .mb-card, .mb-game-card {
            background: linear-gradient(135deg, rgba(26, 16, 51, 0.8) 0%, rgba(15, 10, 36, 0.6) 100%) !important;
            border: 1px solid rgba(236, 72, 153, 0.25) !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 15px rgba(236, 72, 153, 0.1) !important;
        }
        .mb-card:hover, .mb-game-card:hover {
            border-color: rgba(6, 182, 212, 0.5) !important;
            box-shadow: 0 14px 40px rgba(0, 0, 0, 0.6), 0 0 25px rgba(6, 182, 212, 0.25) !important;
        }
    </style>
    """, unsafe_allow_html=True)


def apply_progress_style():
    """
    Celestial Galaxy & Astral Ascent Background (Deep Nebula Starlight & Royal Sapphire).
    """
    st.markdown("""
    <style>
        .stApp {
            background-color: #020617 !important;
            background-image: 
                radial-gradient(at 20% 20%, rgba(37, 99, 235, 0.28) 0px, transparent 50%),
                radial-gradient(at 80% 25%, rgba(168, 85, 247, 0.25) 0px, transparent 50%),
                radial-gradient(at 50% 80%, rgba(234, 179, 8, 0.18) 0px, transparent 55%),
                radial-gradient(at 90% 85%, rgba(56, 189, 248, 0.20) 0px, transparent 50%),
                radial-gradient(rgba(255, 255, 255, 0.15) 1px, transparent 1px) !important;
            background-size: 100% 100%, 100% 100%, 100% 100%, 100% 100%, 40px 40px !important;
            background-attachment: fixed !important;
        }
        .mb-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.5) 100%) !important;
            border: 1px solid rgba(59, 130, 246, 0.25) !important;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.55), 0 0 20px rgba(37, 99, 235, 0.15) !important;
        }
        .mb-badge {
            background: rgba(234, 179, 8, 0.15) !important;
            border: 1px solid rgba(234, 179, 8, 0.45) !important;
            color: #fef08a !important;
            box-shadow: 0 0 15px rgba(234, 179, 8, 0.2) !important;
        }
    </style>
    """, unsafe_allow_html=True)


def apply_reminders_style():
    """
    Zen Twilight Sunset & Chronos Horizon Background (Coral Amber & Twilight Lavender).
    """
    st.markdown("""
    <style>
        .stApp {
            background-color: #0c051a !important;
            background-image: 
                radial-gradient(at 10% 25%, rgba(249, 115, 22, 0.26) 0px, transparent 50%),
                radial-gradient(at 85% 20%, rgba(225, 29, 72, 0.22) 0px, transparent 50%),
                radial-gradient(at 50% 70%, rgba(139, 92, 246, 0.24) 0px, transparent 55%),
                radial-gradient(at 90% 90%, rgba(251, 146, 60, 0.18) 0px, transparent 50%),
                radial-gradient(circle at center, transparent 30%, rgba(249, 115, 22, 0.04) 31%, transparent 32%) !important;
            background-size: 100% 100%, 100% 100%, 100% 100%, 100% 100%, 60px 60px !important;
            background-attachment: fixed !important;
        }
        .mb-card {
            background: linear-gradient(135deg, rgba(30, 15, 45, 0.8) 0%, rgba(20, 10, 35, 0.6) 100%) !important;
            border: 1px solid rgba(249, 115, 22, 0.3) !important;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.55), 0 0 20px rgba(249, 115, 22, 0.15) !important;
        }
    </style>
    """, unsafe_allow_html=True)


def apply_settings_style():
    """
    Titanium Obsidian & Precision Studio Background (Brushed Slate & Ice Cobalt Grid).
    """
    st.markdown("""
    <style>
        .stApp {
            background-color: #080c14 !important;
            background-image: 
                radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.18) 0px, transparent 45%),
                radial-gradient(at 100% 0%, rgba(148, 163, 184, 0.18) 0px, transparent 50%),
                radial-gradient(at 50% 90%, rgba(99, 102, 241, 0.18) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(15, 118, 110, 0.15) 0px, transparent 50%),
                linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px) !important;
            background-size: 100% 100%, 100% 100%, 100% 100%, 100% 100%, 24px 24px, 24px 24px !important;
            background-attachment: fixed !important;
        }
        .mb-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.82) 0%, rgba(30, 41, 59, 0.55) 100%) !important;
            border: 1px solid rgba(148, 163, 184, 0.25) !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 15px rgba(56, 189, 248, 0.1) !important;
        }
    </style>
    """, unsafe_allow_html=True)


def card_start():
    st.markdown('<div class="mb-card">', unsafe_allow_html=True)


def card_end():
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------
# STREAK CALCULATION
# ---------------------------------------------------------------------

def calculate_streak(history):
    """
    Calculate the user's current daily streak (consecutive days with
    at least one game played, counting back from today).
    Safe against empty history.
    """
    if not history:
        return 0

    played_dates = set()
    for g in history:
        played_at = g.get("played_at")
        if not played_at:
            continue
        try:
            date = datetime.fromisoformat(played_at).date()
            played_dates.add(date)
        except (ValueError, TypeError):
            continue

    if not played_dates:
        return 0

    streak = 0
    day = datetime.now().date()
    while day in played_dates:
        streak += 1
        day = day - timedelta(days=1)

    return streak


# ---------------------------------------------------------------------
# ACHIEVEMENTS
# ---------------------------------------------------------------------

def check_and_award_achievements(user_id, history):
    """
    Look at a user's history and award any newly-earned engagement
    achievements. These reflect participation, NOT medical outcomes.
    """
    if not history:
        return

    total_games = len(history)
    streak = calculate_streak(history)

    if total_games >= 1:
        db.add_achievement(user_id, "First Game")
    if streak >= 3:
        db.add_achievement(user_id, "3 Day Streak")
    if total_games >= 10:
        db.add_achievement(user_id, "10 Games")

    memory_games = [g for g in history if g.get("game_name") == "Memory Match"]
    if len(memory_games) >= 5:
        db.add_achievement(user_id, "Memory Master")


ACHIEVEMENT_ICONS = {
    "First Game": "🎮",
    "3 Day Streak": "🔥",
    "10 Games": "🏅",
    "Memory Master": "🧠",
}


# ---------------------------------------------------------------------
# SAFE HELPERS
# ---------------------------------------------------------------------

def safe_average(values):
    """Return the average of a list, or 0 if the list is empty."""
    values = [v for v in values if v is not None]
    if not values:
        return 0
    return sum(values) / len(values)


def safe_get(d, key, default=None):
    """Safely get a key from a dict that might be None."""
    if not d:
        return default
    return d.get(key, default)
