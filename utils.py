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
    Inject custom CSS to give MindBloom a premium, elderly-friendly
    look: rounded cards, large touch-friendly buttons, generous
    spacing, and high-contrast colors when enabled.
    """
    sizes = FONT_SIZE_MAP.get(font_size, FONT_SIZE_MAP["Normal"])

    if high_contrast:
        bg_color = "#000000"
        text_color = "#FFFFFF"
        card_color = "#1a1a1a"
        primary_color = "#FFD60A"
        primary_text = "#000000"
        border_color = "#FFD60A"
    else:
        bg_color = "#F7F9F7"
        text_color = "#1F2A24"
        card_color = "#FFFFFF"
        primary_color = "#3E8E5A"
        primary_text = "#FFFFFF"
        border_color = "#E1E8E3"

    st.markdown(f"""
    <style>
        html, body, [class*="css"] {{
            font-size: {sizes['base']} !important;
            color: {text_color};
        }}
        .stApp {{
            background-color: {bg_color};
        }}
        h1 {{
            font-size: {sizes['heading']} !important;
            font-weight: 800 !important;
            color: {text_color} !important;
        }}
        h2 {{
            font-size: calc({sizes['heading']} * 0.65) !important;
            font-weight: 700 !important;
            color: {text_color} !important;
        }}
        h3 {{
            font-size: calc({sizes['heading']} * 0.5) !important;
            font-weight: 700 !important;
            color: {text_color} !important;
        }}
        p, span, label, div {{
            font-size: {sizes['base']};
        }}

        /* Buttons: large, rounded, high-contrast, touch friendly */
        .stButton > button {{
            background-color: {primary_color};
            color: {primary_text};
            font-size: {sizes['button']} !important;
            font-weight: 700;
            border-radius: 18px;
            border: none;
            padding: 0.9em 1.2em;
            width: 100%;
            min-height: 3.2em;
            box-shadow: 0 3px 10px rgba(0,0,0,0.12);
            transition: transform 0.05s ease-in-out;
        }}
        .stButton > button:hover {{
            transform: scale(1.02);
            filter: brightness(1.05);
        }}

        /* Cards */
        .mb-card {{
            background-color: {card_color};
            border: 1px solid {border_color};
            border-radius: 22px;
            padding: 1.6em;
            margin-bottom: 1.2em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        }}
        .mb-badge {{
            display: inline-block;
            background-color: {primary_color};
            color: {primary_text};
            border-radius: 30px;
            padding: 0.4em 1em;
            font-weight: 700;
            margin: 0.2em;
        }}
        .mb-center {{
            text-align: center;
        }}
        .mb-muted {{
            color: {"#CCCCCC" if high_contrast else "#5B6B62"};
            font-size: calc({sizes['base']} * 0.9);
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {card_color};
        }}

        /* Radio buttons used as nav - make them big and tappable */
        div[role="radiogroup"] label {{
            font-size: {sizes['button']} !important;
            padding: 0.5em 0;
        }}
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
