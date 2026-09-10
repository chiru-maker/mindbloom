"""
app.py
-------
MindBloom - AI-powered cognitive gaming platform (SIH hackathon prototype)

Run with:  streamlit run app.py

IMPORTANT: This is an educational hackathon prototype. It does NOT
diagnose, prevent, cure, or treat dementia or any medical condition.
It is a simple, friendly brain-training and engagement tool.
"""

import time
import random
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px

import database as db
import utils
import games
import voice
import liquid_chrome
from adaptive_engine import calculate_adaptive_difficulty, get_difficulty_settings
from translations import get_text as _t

# ---------------------------------------------------------------------
# PAGE CONFIG + DATABASE INIT (runs once, safe every time)
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="MindBloom",
    page_icon="🌸",
    layout="centered",
    initial_sidebar_state="expanded",
)

db.init_db()

# ---------------------------------------------------------------------
# SESSION STATE DEFAULTS
# ---------------------------------------------------------------------

DEFAULTS = {
    "user_id": None,
    "page": "Home",
    "font_size": "Large",
    "high_contrast": False,
    "active_game": None,
    "caregiver_unlocked": False,
    "last_difficulty_note": None,
    "auth_mode": "login",
    "auth_show_password": False,
    "auth_error": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def lang():
    """Return the current user's preferred language, defaulting to English."""
    user = db.get_user(st.session_state.user_id)
    return utils.safe_get(user, "language", "English")


# =======================================================================
# LIQUID GLASS AUTHENTICATION (LOGIN & SIGN UP)
# =======================================================================

def render_auth_page():
    """
    Renders the ultra-premium Liquid Glass / Glassmorphism Authentication UI.
    Strictly uses Email + Password for both Login and Sign Up.
    """
    utils.apply_liquid_glass_auth_style()

    auth_mode = st.session_state.get("auth_mode", "login")
    show_pw = st.session_state.get("auth_show_password", False)
    error_msg = st.session_state.get("auth_error", None)

    st.markdown('<div class="mb-auth-wrapper"><div class="mb-glass-panel">', unsafe_allow_html=True)

    # Floating Glowing Brand Header with Interactive LiquidChrome
    liquid_chrome.render_liquid_chrome(
        base_color=[0.1, 0.1, 0.1],
        speed=0.3,
        amplitude=0.4,
        frequency_x=2.5,
        frequency_y=2.5,
        interactive=True,
        height=140,
        border_radius="14px",
        overlay_html="<div style='font-size:1.5rem; font-weight:800; letter-spacing:0.04em;'>🌸 MindBloom</div><div style='font-size:0.82rem; opacity:0.85; margin-top:2px;'>Interactive Liquid Surface • Move cursor to ripple</div>"
    )

    # ------------------------------------------------------------------
    # LOGIN VIEW
    # ------------------------------------------------------------------
    if auth_mode == "login":
        st.markdown("""
        <div class="mb-center">
            <h1 class="mb-auth-heading">Welcome Back</h1>
            <p class="mb-auth-subheading">Sign in to continue</p>
        </div>
        """, unsafe_allow_html=True)

        if error_msg:
            st.markdown(f"""
            <div class="mb-glass-error">
                <span>⚠️</span>
                <span>{error_msg}</span>
            </div>
            """, unsafe_allow_html=True)

        with st.form("liquid_glass_login_form", clear_on_submit=False):
            email = st.text_input(
                "Email",
                placeholder="name@example.com",
                key="input_login_email",
            ).strip()

            password = st.text_input(
                "Password",
                type="default" if show_pw else "password",
                placeholder="Enter your password",
                key="input_login_password",
            )

            show_pw_toggle = st.checkbox(
                "👁️ Show Password",
                value=show_pw,
                key="toggle_login_pw",
            )

            submitted = st.form_submit_button("Log In", use_container_width=True)

            if submitted:
                # Update password visibility preference
                st.session_state.auth_show_password = show_pw_toggle

                if not email:
                    st.session_state.auth_error = "Please enter your email address."
                    st.rerun()
                elif "@" not in email or "." not in email:
                    st.session_state.auth_error = "Please enter a valid email address."
                    st.rerun()
                elif not password:
                    st.session_state.auth_error = "Please enter your password."
                    st.rerun()
                else:
                    user = db.authenticate_user(email, password)
                    if user:
                        st.session_state.user_id = user["id"]
                        st.session_state.page = "Home"
                        st.session_state.auth_error = None
                        st.rerun()
                    else:
                        st.session_state.auth_error = "Invalid email or password."
                        st.rerun()

        st.markdown('<div class="mb-center" style="margin-top: 1.1rem; color: #94a3b8; font-size: 0.85rem;">— OR QUICK DEMO MODE —</div>', unsafe_allow_html=True)
        if st.button("🚀 1-Click Demo Login (Anandi Sharma • 72y)", key="btn_quick_demo_login", use_container_width=True):
            users = db.get_all_users()
            demo_u = next((u for u in users if u.get("email") == "demo@mindbloom.com"), None)
            if not demo_u and users:
                demo_u = users[0]
            if demo_u:
                st.session_state.user_id = demo_u["id"]
                st.session_state.page = "Home"
                st.session_state.auth_error = None
                st.rerun()

        st.markdown('<div class="mb-center" style="margin-top: 1.2rem; color: #94a3b8; font-size: 0.92rem;">Don\'t have an account?</div>', unsafe_allow_html=True)
        st.markdown('<div class="mb-auth-switch-btn">', unsafe_allow_html=True)
        if st.button("Create Account — Sign Up", key="btn_switch_to_signup", use_container_width=True):
            st.session_state.auth_mode = "signup"
            st.session_state.auth_error = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # SIGN UP VIEW
    # ------------------------------------------------------------------
    else:
        st.markdown("""
        <div class="mb-center">
            <h1 class="mb-auth-heading">Create Your Account</h1>
            <p class="mb-auth-subheading">Join us and get started</p>
        </div>
        """, unsafe_allow_html=True)

        if error_msg:
            st.markdown(f"""
            <div class="mb-glass-error">
                <span>⚠️</span>
                <span>{error_msg}</span>
            </div>
            """, unsafe_allow_html=True)

        with st.form("liquid_glass_signup_form", clear_on_submit=False):
            email = st.text_input(
                "Email",
                placeholder="name@example.com",
                key="input_signup_email",
            ).strip()

            password = st.text_input(
                "Password",
                type="default" if show_pw else "password",
                placeholder="Enter password (min 6 characters)",
                key="input_signup_password",
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="default" if show_pw else "password",
                placeholder="Re-enter your password",
                key="input_signup_confirm_password",
            )

            show_pw_toggle = st.checkbox(
                "👁️ Show Password",
                value=show_pw,
                key="toggle_signup_pw",
            )

            submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                # Update password visibility preference
                st.session_state.auth_show_password = show_pw_toggle

                if not email:
                    st.session_state.auth_error = "Please enter your email address."
                    st.rerun()
                elif "@" not in email or "." not in email:
                    st.session_state.auth_error = "Please enter a valid email address."
                    st.rerun()
                elif not password:
                    st.session_state.auth_error = "Please enter a password."
                    st.rerun()
                elif len(password) < 6:
                    st.session_state.auth_error = "Password must be at least 6 characters long."
                    st.rerun()
                elif password != confirm_password:
                    st.session_state.auth_error = "Passwords do not match."
                    st.rerun()
                else:
                    existing = db.get_user_by_email(email)
                    if existing:
                        st.session_state.auth_error = "An account with this email already exists. Please log in."
                        st.rerun()
                    else:
                        new_id = db.register_user(email, password)
                        st.session_state.user_id = new_id
                        st.session_state.page = "Home"
                        st.session_state.auth_error = None
                        st.rerun()

        st.markdown('<div class="mb-center" style="margin-top: 1.4rem; color: #94a3b8; font-size: 0.92rem;">Already have an account?</div>', unsafe_allow_html=True)
        st.markdown('<div class="mb-auth-switch-btn">', unsafe_allow_html=True)
        if st.button("Sign In — Log In", key="btn_switch_to_login", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.session_state.auth_error = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)


# =======================================================================
# SIDEBAR NAVIGATION
# =======================================================================

def render_sidebar(user):
    with st.sidebar:
        st.markdown(f"### 🌸 {_t('app_name', lang())}")
        st.markdown(f"**{_t('welcome', lang())}, {user['name']}!**")

        nav_options = [
            _t("home", lang()),
            _t("play", lang()),
            _t("progress", lang()),
            _t("reminder", lang()),
            _t("settings", lang()),
            _t("caregiver", lang()),
        ]
        nav_keys = ["Home", "Play", "Progress", "Reminders", "Settings", "Caregiver"]

        current_index = nav_keys.index(st.session_state.page) if st.session_state.page in nav_keys else 0
        choice = st.radio("Navigate", nav_options, index=current_index, label_visibility="collapsed")
        st.session_state.page = nav_keys[nav_options.index(choice)]

        st.markdown("---")
        if st.button("🔄 Log Out / Switch Account", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.active_game = None
            st.session_state.caregiver_unlocked = False
            st.session_state.auth_error = None
            st.session_state.auth_mode = "login"
            st.rerun()


# =======================================================================
# HOME PAGE (PREMIUM LIQUID GLASS DASHBOARD)
# =======================================================================

def render_home(user):
    utils.apply_home_style()
    L = user["language"]
    
    # Calculate time-based greeting
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting = "Good morning"
    elif current_hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    history = db.get_game_history(user["id"])
    streak = utils.calculate_streak(history)
    games_today = [
        g for g in history
        if g.get("played_at") and datetime.fromisoformat(g["played_at"]).date() == datetime.now().date()
    ]
    daily_goal = max(1, user.get("daily_goal", 3))
    progress_pct = min(100, int((len(games_today) / daily_goal) * 100))
    achievements = db.get_achievements(user["id"])

    # 1. HERO GREETING BANNER
    st.markdown(f"""
    <div class="mb-hero-banner">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
            <div>
                <div class="mb-badge" style="margin-bottom: 0.6rem;">
                    <span>🌸</span> <span>MindBloom Cognitive Hub</span>
                </div>
                <h1 style="margin: 0.2rem 0; font-size: 2.1rem; background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 60%, #cbd5e1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    {greeting}, {user['name']}!
                </h1>
                <p style="color: #94a3b8; margin: 0.4rem 0 0 0; font-size: 1.05rem;">
                    {_t('tagline', L)} • Keep your focus sharp, active, and blooming today.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Audio Read Aloud helper
    voice.read_aloud_button(
        f"{greeting}, {user['name']}. Welcome to MindBloom. {_t('tagline', L)}",
        language=L,
        key="home_read_aloud",
    )

    st.write("")

    # 2. KEY STAT TILES (3 COLUMNS)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="mb-stat-tile">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #94a3b8; font-weight: 600; font-size: 0.9rem;">{_t('current_streak', L).upper()}</span>
                    <span style="font-size: 1.3rem;">🔥</span>
                </div>
                <div style="font-size: 2.4rem; font-weight: 800; font-family: 'Outfit', sans-serif; color: #f8fafc; margin: 0.4rem 0;">
                    {streak} <span style="font-size: 1rem; color: #94a3b8; font-weight: 500;">Days</span>
                </div>
            </div>
            <div style="font-size: 0.85rem; color: #38bdf8; font-weight: 500;">
                {"🔥 On a great streak!" if streak >= 3 else "✨ Play today to build your streak"}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="mb-stat-tile">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #94a3b8; font-weight: 600; font-size: 0.9rem;">{_t('todays_activity', L).upper()}</span>
                    <span style="font-size: 1.3rem;">🎯</span>
                </div>
                <div style="font-size: 2.4rem; font-weight: 800; font-family: 'Outfit', sans-serif; color: #f8fafc; margin: 0.4rem 0;">
                    {len(games_today)} <span style="font-size: 1rem; color: #94a3b8; font-weight: 500;">/ {daily_goal} games</span>
                </div>
                <div class="mb-progress-track">
                    <div class="mb-progress-fill" style="width: {progress_pct}%;"></div>
                </div>
            </div>
            <div style="font-size: 0.85rem; color: {'#34d399' if progress_pct >= 100 else '#a78bfa'}; font-weight: 500;">
                {"🎉 Goal completed for today!" if progress_pct >= 100 else f"🎯 {daily_goal - len(games_today)} more to hit goal"}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        diff_label = user.get('difficulty', 'Easy')
        diff_icon = "🌱" if diff_label == "Easy" else ("🌿" if diff_label == "Medium" else "🌳")
        st.markdown(f"""
        <div class="mb-stat-tile">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #94a3b8; font-weight: 600; font-size: 0.9rem;">{_t('difficulty', L).upper()} LEVEL</span>
                    <span style="font-size: 1.3rem;">🧠</span>
                </div>
                <div style="font-size: 2rem; font-weight: 800; font-family: 'Outfit', sans-serif; color: #f8fafc; margin: 0.4rem 0;">
                    {diff_icon} {diff_label}
                </div>
            </div>
            <div style="font-size: 0.85rem; color: #94a3b8;">
                {len(history)} total brain sessions played
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 3. DAILY WORKOUT HERO ACTION
    st.markdown('<div class="mb-glass-card">', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem;">
        <div>
            <h3 style="margin: 0; font-size: 1.35rem; color: #ffffff;">⚡ Daily Cognitive Workout</h3>
            <p style="margin: 0.2rem 0 0 0; color: #94a3b8; font-size: 0.95rem;">
                Engage your memory, focus, and reflexes with today's personalized brain training session.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"▶️  {_t('start_game', L)} — Quick Workout", use_container_width=True, key="home_start_workout_btn"):
        st.session_state.page = "Play"
        st.session_state.active_game = None
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # 4. DIRECT GAME LAUNCHPAD (GRID)
    st.markdown(f"### 🎮 Quick Game Launchpad")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        # Game 1: Memory Match
        st.markdown("""
        <div class="mb-game-card">
            <h4 style="margin: 0; color: #f8fafc;">🧩 Memory Match</h4>
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 0.3rem 0 0.8rem 0;">
                Flip cards, match pairs, and strengthen your visual recall memory.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Play Memory Match", key="launch_memory_match", use_container_width=True):
            st.session_state.page = "Play"
            st.session_state.active_game = "Memory Match"
            reset_game_state("Memory Match")
            st.rerun()

        # Game 2: Word Recall
        st.markdown("""
        <div class="mb-game-card">
            <h4 style="margin: 0; color: #f8fafc;">📝 Word Recall</h4>
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 0.3rem 0 0.8rem 0;">
                Memorize everyday word lists to stimulate lexical retention.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Play Word Recall", key="launch_word_recall", use_container_width=True):
            st.session_state.page = "Play"
            st.session_state.active_game = "Word Recall"
            reset_game_state("Word Recall")
            st.rerun()

        # Game 3: Daily Quiz
        st.markdown("""
        <div class="mb-game-card">
            <h4 style="margin: 0; color: #f8fafc;">❓ Daily Quiz</h4>
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 0.3rem 0 0.8rem 0;">
                Answer engaging general knowledge questions to keep facts fresh.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Play Daily Quiz", key="launch_daily_quiz", use_container_width=True):
            st.session_state.page = "Play"
            st.session_state.active_game = "Daily Quiz"
            reset_game_state("Daily Quiz")
            st.rerun()

    with col_g2:
        # Game 4: Number Memory
        st.markdown("""
        <div class="mb-game-card">
            <h4 style="margin: 0; color: #f8fafc;">🔢 Number Memory</h4>
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 0.3rem 0 0.8rem 0;">
                Retain number sequences and boost short-term digit span memory.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Play Number Memory", key="launch_number_memory", use_container_width=True):
            st.session_state.page = "Play"
            st.session_state.active_game = "Number Memory"
            reset_game_state("Number Memory")
            st.rerun()

        # Game 5: Pattern Recognition
        st.markdown("""
        <div class="mb-game-card">
            <h4 style="margin: 0; color: #f8fafc;">🔁 Pattern Recognition</h4>
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 0.3rem 0 0.8rem 0;">
                Identify symbols and patterns to enhance cognitive deduction.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Play Pattern Recognition", key="launch_pattern_rec", use_container_width=True):
            st.session_state.page = "Play"
            st.session_state.active_game = "Pattern Recognition"
            reset_game_state("Pattern Recognition")
            st.rerun()

        # Caregiver Portal Quick Card
        st.markdown("""
        <div class="mb-game-card" style="border-color: rgba(56, 189, 248, 0.25);">
            <h4 style="margin: 0; color: #38bdf8;">🧑‍⚕️ Caregiver Hub</h4>
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 0.3rem 0 0.8rem 0;">
                Access detailed cognitive analytics, accuracy trends & progress.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Caregiver Hub", key="home_caregiver_shortcut", use_container_width=True):
            st.session_state.page = "Caregiver"
            st.rerun()

    st.write("")

    # 5. TROPHY CABINET / RECENT ACHIEVEMENTS
    st.markdown("### 🏆 Your Achievements & Trophies")
    utils.card_start()
    if achievements:
        st.markdown("<div style='display: flex; flex-wrap: wrap; gap: 0.6rem;'>", unsafe_allow_html=True)
        for ach in achievements:
            icon = utils.ACHIEVEMENT_ICONS.get(ach["achievement"], "🏅")
            earned_date = ""
            if ach.get("earned_at"):
                try:
                    earned_date = datetime.fromisoformat(ach["earned_at"]).strftime("%b %d")
                except Exception:
                    pass
            st.markdown(f"""
            <div class="mb-trophy-badge">
                <span style="font-size: 1.4rem;">{icon}</span>
                <div>
                    <div style="font-weight: 700; color: #f8fafc; font-size: 0.95rem;">{ach['achievement']}</div>
                    <div style="font-size: 0.78rem; color: #94a3b8;">{earned_date if earned_date else 'Unlocked'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 1.2rem 0; color: #94a3b8;">
            <div style="font-size: 2.2rem; margin-bottom: 0.4rem;">🌟</div>
            <div style="font-weight: 600; color: #f8fafc;">Start Playing to Unlock Badges!</div>
            <div style="font-size: 0.9rem; margin-top: 0.2rem;">Complete your first game today to earn your first trophy.</div>
        </div>
        """, unsafe_allow_html=True)
    utils.card_end()

    # 6. LIQUID CHROME RELAXATION & SENSORY ZONE
    st.write("")
    st.markdown("### 🌊 Liquid Chrome Sensory Relaxation")
    st.caption("Interact with the liquid surface to soothe stress, stimulate motor reflexes, and relax.")
    
    with st.expander("🎨 Customize Liquid Canvas & Shaders", expanded=False):
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            theme_choice = st.selectbox(
                "Color Theme Preset",
                ["Deep Space ([0.1, 0.1, 0.1])", "Emerald Bloom ([0.05, 0.35, 0.25])", "Calming Indigo ([0.15, 0.18, 0.45])", "Sunset Amber ([0.4, 0.18, 0.1])"],
                index=0,
                key="lc_theme_select"
            )
            lc_speed = st.slider("Animation Speed", min_value=0.05, max_value=2.0, value=0.3, step=0.05, key="lc_speed_slider")
        with c_col2:
            lc_amp = st.slider("Distortion Amplitude", min_value=0.1, max_value=1.5, value=0.4, step=0.05, key="lc_amp_slider")
            lc_freq = st.slider("Wave Frequency", min_value=1.0, max_value=6.0, value=3.0, step=0.5, key="lc_freq_slider")
        
        theme_map = {
            "Deep Space ([0.1, 0.1, 0.1])": [0.1, 0.1, 0.1],
            "Emerald Bloom ([0.05, 0.35, 0.25])": [0.05, 0.35, 0.25],
            "Calming Indigo ([0.15, 0.18, 0.45])": [0.15, 0.18, 0.45],
            "Sunset Amber ([0.4, 0.18, 0.1])": [0.4, 0.18, 0.1],
        }
        chosen_color = theme_map.get(theme_choice, [0.1, 0.1, 0.1])

    # If expander was not opened/customized, use default params
    if "lc_theme_select" not in st.session_state:
        chosen_color = [0.1, 0.1, 0.1]
        lc_speed = 0.3
        lc_amp = 0.4
        lc_freq = 3.0

    liquid_chrome.render_liquid_chrome(
        base_color=chosen_color,
        speed=lc_speed,
        amplitude=lc_amp,
        frequency_x=lc_freq,
        frequency_y=lc_freq,
        interactive=True,
        height=320,
        border_radius="16px",
        overlay_html="<div style='font-size:1.4rem; font-weight:700; text-shadow:0 3px 10px rgba(0,0,0,0.7);'>🌸 MindBloom • Interactive Liquid Canvas</div><div style='font-size:0.88rem; opacity:0.85; margin-top:4px;'>Move your cursor or touch to create calming liquid waves</div>"
    )


# =======================================================================
# PLAY PAGE - GAME SELECTION
# =======================================================================

GAME_LIST = [
    ("Memory Match", "🧩", "Remember the symbols you see."),
    ("Number Memory", "🔢", "Remember a short number sequence."),
    ("Word Recall", "📝", "Remember simple words."),
    ("Pattern Recognition", "🔁", "Find what comes next."),
    ("Daily Quiz", "❓", "Answer simple everyday questions."),
]


def render_play_selector(user):
    L = user["language"]
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(236, 72, 153, 0.18) 0%, rgba(30, 16, 60, 0.8) 50%, rgba(6, 182, 212, 0.18) 100%); border: 1px solid rgba(236, 72, 153, 0.35); border-radius: 20px; padding: 1.5rem 1.8rem; margin-bottom: 1.5rem; text-align: center; box-shadow: 0 12px 35px rgba(0,0,0,0.5), 0 0 20px rgba(236, 72, 153, 0.15);">
        <div style="font-size: 2.2rem; margin-bottom: 0.2rem;">🎮</div>
        <h1 style="margin: 0; font-size: 1.9rem; background: linear-gradient(135deg, #ffffff, #f472b6, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{_t('games', L)} • Cognitive Arena</h1>
        <p style="color: #cbd5e1; margin-top: 0.3rem; font-size: 0.95rem;">Select any brain exercise below to stimulate visual recall, numbers, words, and logical deductions.</p>
    </div>
    """, unsafe_allow_html=True)

    for name, icon, desc in GAME_LIST:
        utils.card_start()
        st.markdown(f"### {icon} {name}")
        st.markdown(f"<p class='mb-muted'>{desc}</p>", unsafe_allow_html=True)
        if st.button(f"{_t('start_game', L)} - {name}", key=f"start_{name}", use_container_width=True):
            st.session_state.active_game = name
            reset_game_state(name)
            st.rerun()
        utils.card_end()


def reset_game_state(game_name):
    """Clear any leftover session state for a fresh round of a game."""
    prefix = game_name.replace(" ", "_").lower()
    for k in list(st.session_state.keys()):
        if k.startswith(prefix + "_"):
            del st.session_state[k]
    st.session_state[f"{prefix}_stage"] = "instructions"


def get_current_settings(user):
    """Get difficulty settings, using the user's stored difficulty level."""
    return get_difficulty_settings(user["difficulty"])


def finish_round(user, game_name, score, accuracy, response_time, difficulty):
    """Save a completed round, update achievements, and show adaptive-difficulty feedback."""
    db.save_game_result(user["id"], game_name, score, accuracy, response_time, difficulty)
    history = db.get_game_history(user["id"])
    utils.check_and_award_achievements(user["id"], history)

    result = calculate_adaptive_difficulty(history, current_difficulty=user["difficulty"])
    if result["difficulty"] != user["difficulty"]:
        db.update_user_settings(user["id"], difficulty=result["difficulty"])
    st.session_state.last_difficulty_note = result["explanation"]


def render_result_screen(user, game_name, score, accuracy):
    L = user["language"]
    st.markdown(f"<h2 class='mb-center'>{_t('your_result', L)}</h2>", unsafe_allow_html=True)
    utils.card_start()
    st.markdown(f"<h1 class='mb-center'>{int(accuracy)}%</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='mb-center'>{_t('score', L)}: {score}</p>", unsafe_allow_html=True)
    encouragement = games.get_encouragement(accuracy)
    st.markdown(f"<h3 class='mb-center'>✨ {encouragement}</h3>", unsafe_allow_html=True)
    if st.session_state.last_difficulty_note:
        st.markdown(f"<p class='mb-center mb-muted'>🧠 {st.session_state.last_difficulty_note}</p>", unsafe_allow_html=True)
    utils.card_end()

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🔁 {_t('try_again', L)}", use_container_width=True, key=f"retry_{game_name}"):
            reset_game_state(game_name)
            st.rerun()
    with col2:
        if st.button(f"🏠 {_t('back_home', L)}", use_container_width=True, key=f"home_after_{game_name}"):
            st.session_state.active_game = None
            st.session_state.page = "Home"
            st.rerun()


# ---- GAME 1: MEMORY MATCH -------------------------------------------

def play_memory_match(user):
    L = user["language"]
    prefix = "memory_match"
    stage = st.session_state.get(f"{prefix}_stage", "instructions")
    settings = get_current_settings(user)

    st.markdown("## 🧩 Memory Match")

    if stage == "instructions":
        utils.card_start()
        st.write("You will see a few pictures. Try to remember them. "
                 "Then we will ask you which ones you saw.")
        utils.card_end()
        if st.button(f"▶️ {_t('start_game', L)}", use_container_width=True):
            st.session_state[f"{prefix}_data"] = games.generate_memory_match(settings)
            st.session_state[f"{prefix}_stage"] = "memorize"
            st.session_state[f"{prefix}_shown_at"] = time.time()
            st.rerun()

    elif stage == "memorize":
        data = st.session_state[f"{prefix}_data"]
        utils.card_start()
        st.markdown("<h1 class='mb-center'>" + "  ".join(data["shown"]) + "</h1>", unsafe_allow_html=True)
        st.markdown("<p class='mb-center mb-muted'>Remember these!</p>", unsafe_allow_html=True)
        utils.card_end()
        if st.button("I remember them - Continue ➡️", use_container_width=True):
            st.session_state[f"{prefix}_stage"] = "input"
            st.session_state[f"{prefix}_start_time"] = time.time()
            st.rerun()

    elif stage == "input":
        data = st.session_state[f"{prefix}_data"]
        st.write("Which of these did you see? Select all that apply.")
        selected = st.multiselect("Options", data["options"], key=f"{prefix}_selected", label_visibility="collapsed")
        if st.button(f"✅ Submit", use_container_width=True):
            response_time = round(time.time() - st.session_state.get(f"{prefix}_start_time", time.time()), 1)
            score, accuracy = games.score_memory_match(data, selected)
            finish_round(user, "Memory Match", score, accuracy, response_time, user["difficulty"])
            st.session_state[f"{prefix}_score"] = score
            st.session_state[f"{prefix}_accuracy"] = accuracy
            st.session_state[f"{prefix}_stage"] = "result"
            st.rerun()

    elif stage == "result":
        render_result_screen(user, "Memory Match", st.session_state[f"{prefix}_score"], st.session_state[f"{prefix}_accuracy"])


# ---- GAME 2: NUMBER MEMORY ------------------------------------------

def play_number_memory(user):
    L = user["language"]
    prefix = "number_memory"
    stage = st.session_state.get(f"{prefix}_stage", "instructions")
    settings = get_current_settings(user)

    st.markdown("## 🔢 Number Memory")

    if stage == "instructions":
        utils.card_start()
        st.write("You will see a short list of numbers. Try to remember the order. "
                 "Then type them back in the same order.")
        utils.card_end()
        if st.button(f"▶️ {_t('start_game', L)}", use_container_width=True):
            st.session_state[f"{prefix}_data"] = games.generate_number_memory(settings)
            st.session_state[f"{prefix}_stage"] = "memorize"
            st.rerun()

    elif stage == "memorize":
        data = st.session_state[f"{prefix}_data"]
        utils.card_start()
        st.markdown(
            "<h1 class='mb-center'>" + "   ".join(str(n) for n in data["sequence"]) + "</h1>",
            unsafe_allow_html=True,
        )
        st.markdown("<p class='mb-center mb-muted'>Remember this order!</p>", unsafe_allow_html=True)
        utils.card_end()
        if st.button("I remember it - Continue ➡️", use_container_width=True):
            st.session_state[f"{prefix}_stage"] = "input"
            st.session_state[f"{prefix}_start_time"] = time.time()
            st.rerun()

    elif stage == "input":
        data = st.session_state[f"{prefix}_data"]
        st.write(f"Enter the {len(data['sequence'])} numbers you saw, in order (separated by spaces).")
        user_input = st.text_input("Your answer", key=f"{prefix}_answer_input", label_visibility="collapsed")
        if st.button("✅ Submit", use_container_width=True):
            try:
                user_sequence = [int(x) for x in user_input.strip().split()]
            except ValueError:
                user_sequence = []
            response_time = round(time.time() - st.session_state.get(f"{prefix}_start_time", time.time()), 1)
            score, accuracy = games.score_number_memory(data, user_sequence)
            finish_round(user, "Number Memory", score, accuracy, response_time, user["difficulty"])
            st.session_state[f"{prefix}_score"] = score
            st.session_state[f"{prefix}_accuracy"] = accuracy
            st.session_state[f"{prefix}_stage"] = "result"
            st.rerun()

    elif stage == "result":
        render_result_screen(user, "Number Memory", st.session_state[f"{prefix}_score"], st.session_state[f"{prefix}_accuracy"])


# ---- GAME 3: WORD RECALL ---------------------------------------------

def play_word_recall(user):
    L = user["language"]
    prefix = "word_recall"
    stage = st.session_state.get(f"{prefix}_stage", "instructions")
    settings = get_current_settings(user)

    st.markdown("## 📝 Word Recall")

    if stage == "instructions":
        utils.card_start()
        st.write("You will see a few simple words. Try to remember them. "
                 "Then we will ask you which words you saw.")
        utils.card_end()
        if st.button(f"▶️ {_t('start_game', L)}", use_container_width=True):
            st.session_state[f"{prefix}_data"] = games.generate_word_recall(settings)
            st.session_state[f"{prefix}_stage"] = "memorize"
            st.rerun()

    elif stage == "memorize":
        data = st.session_state[f"{prefix}_data"]
        utils.card_start()
        st.markdown(
            "<h2 class='mb-center'>" + "  •  ".join(data["shown"]) + "</h2>",
            unsafe_allow_html=True,
        )
        st.markdown("<p class='mb-center mb-muted'>Remember these words!</p>", unsafe_allow_html=True)
        utils.card_end()
        if st.button("I remember them - Continue ➡️", use_container_width=True):
            st.session_state[f"{prefix}_stage"] = "input"
            st.session_state[f"{prefix}_start_time"] = time.time()
            st.rerun()

    elif stage == "input":
        data = st.session_state[f"{prefix}_data"]
        st.write("Which words did you see? Select all that apply.")
        selected = st.multiselect("Options", data["options"], key=f"{prefix}_selected", label_visibility="collapsed")
        if st.button("✅ Submit", use_container_width=True):
            response_time = round(time.time() - st.session_state.get(f"{prefix}_start_time", time.time()), 1)
            score, accuracy = games.score_word_recall(data, selected)
            finish_round(user, "Word Recall", score, accuracy, response_time, user["difficulty"])
            st.session_state[f"{prefix}_score"] = score
            st.session_state[f"{prefix}_accuracy"] = accuracy
            st.session_state[f"{prefix}_stage"] = "result"
            st.rerun()

    elif stage == "result":
        render_result_screen(user, "Word Recall", st.session_state[f"{prefix}_score"], st.session_state[f"{prefix}_accuracy"])


# ---- GAME 4: PATTERN RECOGNITION --------------------------------------

def play_pattern(user):
    L = user["language"]
    prefix = "pattern_recognition"
    stage = st.session_state.get(f"{prefix}_stage", "instructions")
    settings = get_current_settings(user)

    st.markdown("## 🔁 Pattern Recognition")

    if stage == "instructions":
        utils.card_start()
        st.write("Look at the pattern of numbers. Choose what number comes next.")
        utils.card_end()
        if st.button(f"▶️ {_t('start_game', L)}", use_container_width=True):
            st.session_state[f"{prefix}_data"] = games.generate_pattern(settings)
            st.session_state[f"{prefix}_stage"] = "input"
            st.session_state[f"{prefix}_start_time"] = time.time()
            st.rerun()

    elif stage == "input":
        data = st.session_state[f"{prefix}_data"]
        utils.card_start()
        st.markdown(
            "<h1 class='mb-center'>" + "  ,  ".join(str(n) for n in data["sequence"]) + "  ,  ?</h1>",
            unsafe_allow_html=True,
        )
        utils.card_end()
        st.write("What comes next?")
        choice = st.radio("Choose one", data["options"], key=f"{prefix}_choice", label_visibility="collapsed")
        if st.button("✅ Submit", use_container_width=True):
            response_time = round(time.time() - st.session_state.get(f"{prefix}_start_time", time.time()), 1)
            score, accuracy = games.score_pattern(data, choice)
            finish_round(user, "Pattern Recognition", score, accuracy, response_time, user["difficulty"])
            st.session_state[f"{prefix}_score"] = score
            st.session_state[f"{prefix}_accuracy"] = accuracy
            st.session_state[f"{prefix}_stage"] = "result"
            st.rerun()

    elif stage == "result":
        render_result_screen(user, "Pattern Recognition", st.session_state[f"{prefix}_score"], st.session_state[f"{prefix}_accuracy"])


# ---- GAME 5: DAILY QUIZ ------------------------------------------------

def play_quiz(user):
    L = user["language"]
    prefix = "daily_quiz"
    stage = st.session_state.get(f"{prefix}_stage", "instructions")
    settings = get_current_settings(user)

    st.markdown("## ❓ Daily Quiz")

    if stage == "instructions":
        utils.card_start()
        st.write("Answer a few simple everyday questions. Take your time.")
        utils.card_end()
        if st.button(f"▶️ {_t('start_game', L)}", use_container_width=True):
            st.session_state[f"{prefix}_data"] = games.generate_quiz(settings)
            st.session_state[f"{prefix}_stage"] = "input"
            st.session_state[f"{prefix}_start_time"] = time.time()
            st.rerun()

    elif stage == "input":
        data = st.session_state[f"{prefix}_data"]
        answers = []
        for i, q in enumerate(data["questions"]):
            utils.card_start()
            st.markdown(f"**{i + 1}. {q['q']}**")
            ans = st.radio("Choose one", q["options"], key=f"{prefix}_q{i}", label_visibility="collapsed")
            answers.append(ans)
            utils.card_end()
        if st.button("✅ Submit All Answers", use_container_width=True):
            response_time = round(time.time() - st.session_state.get(f"{prefix}_start_time", time.time()), 1)
            score, accuracy = games.score_quiz(data, answers)
            finish_round(user, "Daily Quiz", score, accuracy, response_time, user["difficulty"])
            st.session_state[f"{prefix}_score"] = score
            st.session_state[f"{prefix}_accuracy"] = accuracy
            st.session_state[f"{prefix}_stage"] = "result"
            st.rerun()

    elif stage == "result":
        render_result_screen(user, "Daily Quiz", st.session_state[f"{prefix}_score"], st.session_state[f"{prefix}_accuracy"])


GAME_RUNNERS = {
    "Memory Match": play_memory_match,
    "Number Memory": play_number_memory,
    "Word Recall": play_word_recall,
    "Pattern Recognition": play_pattern,
    "Daily Quiz": play_quiz,
}


def render_play_page(user):
    utils.apply_play_style()
    if st.session_state.active_game is None:
        render_play_selector(user)
    else:
        if st.button("⬅️ Back to Games", key="back_to_games"):
            st.session_state.active_game = None
            st.rerun()
        runner = GAME_RUNNERS.get(st.session_state.active_game)
        if runner:
            try:
                runner(user)
            except Exception:
                st.warning("Something went wrong with this game. Let's start fresh.")
                reset_game_state(st.session_state.active_game)
                st.rerun()


# =======================================================================
# PROGRESS PAGE
# =======================================================================

def render_progress(user):
    utils.apply_progress_style()
    L = user["language"]
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(37, 99, 235, 0.2) 0%, rgba(15, 23, 42, 0.85) 50%, rgba(168, 85, 247, 0.2) 100%); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 20px; padding: 1.5rem 1.8rem; margin-bottom: 1.5rem; text-align: center; box-shadow: 0 12px 35px rgba(0,0,0,0.5), 0 0 20px rgba(37, 99, 235, 0.18);">
        <div style="font-size: 2.2rem; margin-bottom: 0.2rem;">📈</div>
        <h1 style="margin: 0; font-size: 1.9rem; background: linear-gradient(135deg, #ffffff, #93c5fd, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{_t('progress', L)} • Celestial Orbit</h1>
        <p style="color: #cbd5e1; margin-top: 0.3rem; font-size: 0.95rem;">Track your long-term cognitive milestones, accuracy evolution, and earned trophies.</p>
    </div>
    """, unsafe_allow_html=True)

    history = db.get_game_history(user["id"])

    if not history:
        st.info("No games played yet. Play your first game to see your progress here!")
        return

    total_games = len(history)
    avg_score = round(utils.safe_average([g["score"] for g in history]), 1)
    best_score = max((g["score"] or 0) for g in history)
    avg_accuracy = round(utils.safe_average([g["accuracy"] for g in history]), 1)
    streak = utils.calculate_streak(history)

    col1, col2 = st.columns(2)
    with col1:
        utils.card_start()
        st.metric("🔥 " + _t("current_streak", L), streak)
        st.metric("🎮 Total Games", total_games)
        utils.card_end()
    with col2:
        utils.card_start()
        st.metric("⭐ Average Score", avg_score)
        st.metric("🏆 Best Score", best_score)
        utils.card_end()

    utils.card_start()
    st.metric("🎯 Average Accuracy", f"{avg_accuracy}%")
    utils.card_end()

    # Weekly activity chart
    try:
        df = pd.DataFrame(history)
        df["played_at"] = pd.to_datetime(df["played_at"])
        df["date"] = df["played_at"].dt.date
        daily_counts = df.groupby("date").size().reset_index(name="games")
        fig = px.bar(daily_counts, x="date", y="games", title="Weekly Activity")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.02)",
            font=dict(color="#e2e8f0", family="Plus Jakarta Sans", size=14),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        fig.update_traces(marker_color="#a855f7")
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.info("Not enough data yet to show a chart.")

    # Achievements
    st.markdown("### 🏅 Achievements")
    achievements = db.get_achievements(user["id"])
    if achievements:
        badge_html = "".join(
            f"<span class='mb-badge'>{utils.ACHIEVEMENT_ICONS.get(a['achievement'], '🏅')} {a['achievement']}</span>"
            for a in achievements
        )
        st.markdown(badge_html, unsafe_allow_html=True)
    else:
        st.write("No achievements yet - keep playing!")


# =======================================================================
# REMINDERS PAGE
# =======================================================================

def render_reminders(user):
    utils.apply_reminders_style()
    L = user["language"]
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(249, 115, 22, 0.2) 0%, rgba(30, 15, 45, 0.85) 50%, rgba(139, 92, 246, 0.2) 100%); border: 1px solid rgba(249, 115, 22, 0.35); border-radius: 20px; padding: 1.5rem 1.8rem; margin-bottom: 1.5rem; text-align: center; box-shadow: 0 12px 35px rgba(0,0,0,0.5), 0 0 20px rgba(249, 115, 22, 0.18);">
        <div style="font-size: 2.2rem; margin-bottom: 0.2rem;">⏰</div>
        <h1 style="margin: 0; font-size: 1.9rem; background: linear-gradient(135deg, #ffffff, #fdba74, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{_t('reminder', L)} • Daily Zen Schedule</h1>
        <p style="color: #cbd5e1; margin-top: 0.3rem; font-size: 0.95rem;">Configure your peaceful daily routine and gentle audio notifications.</p>
    </div>
    """, unsafe_allow_html=True)

    reminder = db.get_reminder(user["id"]) or {"reminder_time": "09:00", "enabled": 0}

    utils.card_start()
    enabled = st.toggle("Enable Daily Reminder", value=bool(reminder["enabled"]))
    try:
        default_time = datetime.strptime(reminder["reminder_time"], "%H:%M").time()
    except (ValueError, TypeError):
        default_time = datetime.strptime("09:00", "%H:%M").time()
    reminder_time = st.time_input("Preferred Reminder Time", value=default_time)

    if st.button("💾 Save Reminder", use_container_width=True):
        db.update_reminder(user["id"], reminder_time.strftime("%H:%M"), enabled)
        st.success("Reminder saved!")
        st.rerun()
    utils.card_end()

    if enabled:
        utils.card_start()
        st.markdown(f"### 🔔 Today's reminder: It's time for your MindBloom activity!")
        st.markdown(f"<p class='mb-muted'>Set for {reminder_time.strftime('%I:%M %p')}</p>", unsafe_allow_html=True)
        utils.card_end()

    st.caption("Note: In this prototype, reminders are shown inside the app. "
               "Real push/browser notifications would require additional "
               "notification infrastructure beyond this hackathon prototype.")


# =======================================================================
# SETTINGS PAGE
# =======================================================================

def render_settings(user):
    utils.apply_settings_style()
    L = user["language"]
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(56, 189, 248, 0.16) 0%, rgba(15, 23, 42, 0.85) 50%, rgba(99, 102, 241, 0.16) 100%); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 20px; padding: 1.5rem 1.8rem; margin-bottom: 1.5rem; text-align: center; box-shadow: 0 12px 35px rgba(0,0,0,0.5), 0 0 20px rgba(56, 189, 248, 0.12);">
        <div style="font-size: 2.2rem; margin-bottom: 0.2rem;">⚙️</div>
        <h1 style="margin: 0; font-size: 1.9rem; background: linear-gradient(135deg, #ffffff, #94a3b8, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{_t('settings', L)} • Accessibility Studio</h1>
        <p style="color: #cbd5e1; margin-top: 0.3rem; font-size: 0.95rem;">Personalize language, high contrast, typography scaling, and adaptive parameters.</p>
    </div>
    """, unsafe_allow_html=True)

    utils.card_start()
    st.markdown(f"### {_t('select_language', L)}")
    new_lang = st.selectbox("Language", ["English", "Hindi", "Kannada"],
                             index=["English", "Hindi", "Kannada"].index(user["language"]))
    if new_lang != user["language"]:
        db.update_user_settings(user["id"], language=new_lang)
        st.rerun()
    utils.card_end()

    utils.card_start()
    st.markdown("### 🔤 Font Size")
    font_size = st.radio("Font Size", ["Normal", "Large", "Extra Large"],
                          index=["Normal", "Large", "Extra Large"].index(st.session_state.font_size),
                          horizontal=True)
    if font_size != st.session_state.font_size:
        st.session_state.font_size = font_size
        st.rerun()
    utils.card_end()

    utils.card_start()
    st.markdown("### 🌓 High Contrast Mode")
    high_contrast = st.toggle("Enable High Contrast", value=st.session_state.high_contrast)
    if high_contrast != st.session_state.high_contrast:
        st.session_state.high_contrast = high_contrast
        st.rerun()
    utils.card_end()

    utils.card_start()
    st.markdown(f"### {_t('difficulty', L)}")
    st.write(f"Current level: **{user['difficulty']}**")
    st.caption("Difficulty automatically adjusts as you play, based on your recent performance.")
    utils.card_end()

    utils.card_start()
    st.markdown(f"### {_t('daily_goal', L)}")
    new_goal = st.slider("Games per day", 1, 5, value=user["daily_goal"])
    if new_goal != user["daily_goal"]:
        db.update_user_settings(user["id"], daily_goal=new_goal)
        st.rerun()
    utils.card_end()


# =======================================================================
# CAREGIVER DASHBOARD
# =======================================================================

def render_caregiver(user):
    utils.apply_caregiver_dashboard_style()

    # Medical Telemetry LiquidChrome Hero Banner
    liquid_chrome.render_liquid_chrome(
        base_color=[0.05, 0.25, 0.35],
        speed=0.22,
        amplitude=0.4,
        frequency_x=3.0,
        frequency_y=2.0,
        interactive=True,
        height=165,
        border_radius="18px",
        overlay_html="<div style='font-size:1.6rem; font-weight:800; letter-spacing:0.04em;'>🧑‍⚕️ MindBloom Caregiver Hub</div><div style='font-size:0.85rem; opacity:0.9; margin-top:4px;'>Clinical Cognitive Telemetry & Long-Term Retention Insights</div>"
    )

    if not st.session_state.caregiver_unlocked:
        st.markdown("""
        <div class="mb-cg-vault-box">
            <div style="font-size: 3rem; margin-bottom: 0.8rem;">🔒</div>
            <h2 style="font-size: 1.6rem; color: #ffffff; margin-bottom: 0.3rem;">Clinician & Caregiver Portal</h2>
            <p style="color: #94a3b8; font-size: 0.92rem; margin-bottom: 1.4rem;">
                Enter your authorized 4-digit security PIN to inspect cognitive telemetry, accuracy trends, and engagement reports.
            </p>
        """, unsafe_allow_html=True)
        
        pin = st.text_input("Security PIN (Demo: 1234)", type="password", key="cg_pin_input")
        if st.button("🔓 Unlock Caregiver Dashboard", use_container_width=True, key="btn_unlock_cg"):
            if pin == "1234":
                st.session_state.caregiver_unlocked = True
                st.rerun()
            else:
                st.error("⚠️ Incorrect PIN. Please try again.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Unlocked Caregiver Dashboard Header
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin: 1rem 0;">
        <div class="mb-cg-status-badge">
            <span class="mb-cg-pulse-dot"></span>
            <span>TELEMETRY STREAM ACTIVE</span>
        </div>
        <div style="color: #94a3b8; font-size: 0.85rem;">
            Cognitive Assistance & Monitoring Protocol • SIH 2026
        </div>
    </div>
    """, unsafe_allow_html=True)

    users = db.get_all_users()
    if not users:
        st.info("No user profiles available in database.")
        return

    st.markdown('<div class="mb-cg-card">', unsafe_allow_html=True)
    c_sel1, c_sel2 = st.columns([3, 2])
    with c_sel1:
        names = [u["name"] for u in users]
        selected_name = st.selectbox("Select Patient Profile", names, index=names.index(user["name"]) if user["name"] in names else 0)
        selected_user = next(u for u in users if u["name"] == selected_name)
    with c_sel2:
        st.write("")
        st.write("")
        if st.button("🧪 Load Presentation Demo Data", use_container_width=True, key="btn_load_cg_demo"):
            db.load_demo_data(selected_user["id"])
            st.success("Telemetry dataset refreshed!")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    history = db.get_game_history(selected_user["id"])

    if not history:
        st.info("No activity telemetry logged yet for this patient. Click 'Load Presentation Demo Data' above.")
        return

    total_games = len(history)
    avg_score = round(utils.safe_average([g["score"] for g in history]), 1)
    avg_accuracy = round(utils.safe_average([g["accuracy"] for g in history]), 1)
    streak = utils.calculate_streak(history)
    reminder = db.get_reminder(selected_user["id"])
    last_activity = history[0]["played_at"] if history else "N/A"

    # Top Clinical Metric Cards (2 rows of 3)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="mb-cg-metric-tile">
            <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 600;">TOTAL SESSIONS</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #38bdf8; font-family: 'Outfit', sans-serif;">{total_games}</div>
            <div style="font-size: 0.78rem; color: #94a3b8;">Games Completed</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        acc_color = "#34d399" if avg_accuracy >= 75 else ("#facc15" if avg_accuracy >= 50 else "#f87171")
        st.markdown(f"""
        <div class="mb-cg-metric-tile" style="border-left-color: {acc_color};">
            <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 600;">MEAN ACCURACY</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {acc_color}; font-family: 'Outfit', sans-serif;">{avg_accuracy}%</div>
            <div style="font-size: 0.78rem; color: #94a3b8;">Retention benchmark</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="mb-cg-metric-tile" style="border-left-color: #818cf8;">
            <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 600;">AVERAGE SCORE</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #818cf8; font-family: 'Outfit', sans-serif;">{avg_score}</div>
            <div style="font-size: 0.78rem; color: #94a3b8;">Points per round</div>
        </div>
        """, unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown(f"""
        <div class="mb-cg-metric-tile" style="border-left-color: #f97316;">
            <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 600;">CONSISTENCY STREAK</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #fb923c; font-family: 'Outfit', sans-serif;">{streak} Days</div>
            <div style="font-size: 0.78rem; color: #94a3b8;">Active habit adherence</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="mb-cg-metric-tile" style="border-left-color: #a855f7;">
            <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 600;">ADAPTIVE DIFFICULTY</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #c084fc; font-family: 'Outfit', sans-serif;">{selected_user['difficulty']}</div>
            <div style="font-size: 0.78rem; color: #94a3b8;">Auto-calibrated level</div>
        </div>
        """, unsafe_allow_html=True)
    with col6:
        rem_status = "Active" if reminder and reminder["enabled"] else "Disabled"
        rem_color = "#34d399" if rem_status == "Active" else "#94a3b8"
        st.markdown(f"""
        <div class="mb-cg-metric-tile" style="border-left-color: {rem_color};">
            <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 600;">DAILY REMINDER</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {rem_color}; font-family: 'Outfit', sans-serif;">{rem_status}</div>
            <div style="font-size: 0.78rem; color: #94a3b8;">{reminder.get('reminder_time', 'N/A') if reminder else 'Not set'}</div>
        </div>
        """, unsafe_allow_html=True)

    st.caption(f"Last recorded telemetry session: {last_activity}")

    try:
        df = pd.DataFrame(history)
        df["played_at"] = pd.to_datetime(df["played_at"])
        df["date"] = df["played_at"].dt.date

        # Accuracy Trend Graph
        st.markdown('<div class="mb-cg-card">', unsafe_allow_html=True)
        st.markdown("#### 📈 Longitudinal Cognitive Accuracy Trend")
        fig1 = px.line(df.sort_values("played_at"), x="played_at", y="accuracy", markers=True)
        fig1.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(6, 182, 212, 0.03)",
            font=dict(color="#e2e8f0", family="Plus Jakarta Sans"),
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Session Timestamp"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Accuracy (%)", range=[0, 105]),
        )
        fig1.update_traces(line=dict(color="#06b6d4", width=3.5), marker=dict(size=8, color="#38bdf8", symbol="circle"))
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown('<div class="mb-cg-card">', unsafe_allow_html=True)
            st.markdown("#### 📅 Daily Session Frequency")
            daily_counts = df.groupby("date").size().reset_index(name="games")
            fig2 = px.bar(daily_counts, x="date", y="games")
            fig2.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(168, 85, 247, 0.03)",
                font=dict(color="#e2e8f0", family="Plus Jakarta Sans"),
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Date"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Games Played"),
            )
            fig2.update_traces(marker_color="#8b5cf6")
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_g2:
            st.markdown('<div class="mb-cg-card">', unsafe_allow_html=True)
            st.markdown("#### 🎮 Mean Performance by Domain")
            by_game = df.groupby("game_name")["score"].mean().reset_index()
            fig3 = px.bar(by_game, x="game_name", y="score")
            fig3.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(16, 185, 129, 0.03)",
                font=dict(color="#e2e8f0", family="Plus Jakarta Sans"),
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Cognitive Domain"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Average Score"),
            )
            fig3.update_traces(marker_color="#10b981")
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception:
        st.info("Not enough telemetry logged yet to render analytical charts.")

    st.markdown('<div class="mb-cg-card">', unsafe_allow_html=True)
    st.markdown("#### 📋 Recent Session Logs (Audit Trail)")
    recent_df = pd.DataFrame(history[:10])[["game_name", "score", "accuracy", "difficulty", "played_at"]]
    recent_df.columns = ["Game Type", "Score", "Accuracy (%)", "Difficulty", "Played At"]
    st.dataframe(recent_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Clinical Cognitive Telemetry Report Generator & Export
    st.markdown('<div class="mb-cg-card">', unsafe_allow_html=True)
    st.markdown("#### 📄 Clinical Cognitive Telemetry Report (Export)")
    st.caption("Generate a structured assessment report formatted for consultations with neurologists, physicians, and caregivers.")
    
    if st.button("⚡ Generate Clinical Summary Report", key="btn_gen_clinical_report", use_container_width=True):
        st.session_state.show_clinical_report = True

    if st.session_state.get("show_clinical_report", False):
        report_text = f"""================================================================================
MINDBLOOM COGNITIVE TELEMETRY REPORT • CLINICAL SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Protocol: SIH26003 AI-Based Cognitive Gaming & Memory Platform
================================================================================

1. PATIENT PROFILE
------------------
Name:                {selected_user['name']}
Patient ID:          MB-{selected_user['id']:04d}
Age:                 {selected_user.get('age', 72)}
Preferred Language:  {selected_user.get('language', 'English')}
Active Difficulty:   {selected_user.get('difficulty', 'Easy')}
Daily Goal:          {selected_user.get('daily_goal', 3)} sessions/day

2. LONGITUDINAL TELEMETRY SUMMARY
---------------------------------
Total Game Sessions: {total_games}
Mean Accuracy:       {avg_accuracy}%
Mean Session Score:  {avg_score} pts
Habit Streak:        {streak} consecutive days
Daily Reminder:      {reminder.get('reminder_time', 'N/A') if reminder and reminder['enabled'] else 'Disabled'}
Last Activity:       {last_activity}

3. COGNITIVE DOMAIN BREAKDOWN
-----------------------------
"""
        try:
            by_game_dict = df.groupby("game_name").agg({"accuracy": "mean", "score": "mean", "response_time": "mean"}).to_dict("index")
            for g_name, metrics in by_game_dict.items():
                report_text += f"- {g_name:<20}: Mean Accuracy {metrics['accuracy']:.1f}% | Avg Score {metrics['score']:.1f} | Avg Reaction {metrics.get('response_time', 0):.1f}s\n"
        except Exception:
            report_text += "- Telemetry data aggregated across standard cognitive exercises.\n"

        report_text += f"""
4. CLINICAL OBSERVATIONS & CARE RECOMMENDATIONS
-----------------------------------------------
- Adherence Index:    {'High (Active daily engagement)' if streak >= 3 else 'Moderate (Encourage daily routine)'}
- Retention Profile:  {'Consistent high recall across sessions' if avg_accuracy >= 75 else 'Mild variance observed in complex patterns'}
- Recommendation:     Continue regular multi-sensory stimulation sessions (Word Recall + Memory Match).
                      Maintain gentle daily routine reminders at {reminder.get('reminder_time', '09:00') if reminder else '09:00'}.

================================================================================
Confidential Medical Telemetry • For Educational/Prototype Evaluation Purposes
================================================================================
"""
        st.text_area("Report Preview", report_text, height=280)
        st.download_button(
            label="📥 Download Clinical Report (.txt)",
            data=report_text,
            file_name=f"MindBloom_Cognitive_Report_{selected_user['name'].replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True,
            key="btn_download_report_txt"
        )
    st.markdown('</div>', unsafe_allow_html=True)


# =======================================================================
# MAIN ROUTER
# =======================================================================

def main():
    if st.session_state.user_id is None:
        render_auth_page()
        return

    # Apply logged-in app theming
    utils.apply_custom_style(
        font_size=st.session_state.font_size,
        high_contrast=st.session_state.high_contrast,
    )

    user = db.get_user(st.session_state.user_id)
    if user is None:
        # Safety net: stored user id no longer exists in the database
        st.session_state.user_id = None
        st.rerun()
        return

    render_sidebar(user)

    page = st.session_state.page
    if page == "Home":
        render_home(user)
    elif page == "Play":
        render_play_page(user)
    elif page == "Progress":
        render_progress(user)
    elif page == "Reminders":
        render_reminders(user)
    elif page == "Settings":
        render_settings(user)
    elif page == "Caregiver":
        render_caregiver(user)
    else:
        render_home(user)


if __name__ == "__main__":
    main()
