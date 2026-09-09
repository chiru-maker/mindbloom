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
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def lang():
    """Return the current user's preferred language, defaulting to English."""
    user = db.get_user(st.session_state.user_id)
    return utils.safe_get(user, "language", "English")


# Apply theming for every page
utils.apply_custom_style(
    font_size=st.session_state.font_size,
    high_contrast=st.session_state.high_contrast,
)


# =======================================================================
# PROFILE / LOGIN SCREEN
# =======================================================================

def render_profile_selector():
    st.markdown(f"<h1 class='mb-center'>🌸 {_t('app_name')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='mb-center mb-muted'>{_t('tagline')}</p>", unsafe_allow_html=True)
    st.info("This is a hackathon prototype for education and engagement only. "
            "It does not diagnose or treat any medical condition.")

    users = db.get_all_users()

    if users:
        utils.card_start()
        st.subheader("👋 Select Your Profile")
        for u in users:
            if st.button(f"{u['name']}  (Age {u['age']})", key=f"select_user_{u['id']}", use_container_width=True):
                st.session_state.user_id = u["id"]
                st.session_state.page = "Home"
                st.rerun()
        utils.card_end()

    utils.card_start()
    st.subheader(f"✨ {_t('create_profile')}")
    with st.form("create_profile_form", clear_on_submit=True):
        name = st.text_input("Your Name")
        age = st.number_input("Your Age", min_value=40, max_value=110, value=70, step=1)
        language = st.selectbox("Preferred Language", ["English", "Hindi", "Kannada"])
        daily_goal = st.slider("Daily Goal (games per day)", 1, 5, 3)
        submitted = st.form_submit_button("🌸 Create My Profile", use_container_width=True)
        if submitted:
            if name.strip() == "":
                st.warning("Please enter your name to continue.")
            else:
                new_id = db.create_user(name.strip(), int(age), language, "Easy", daily_goal)
                st.session_state.user_id = new_id
                st.session_state.page = "Home"
                st.rerun()
    utils.card_end()


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
        if st.button("🔄 Switch Profile", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.active_game = None
            st.session_state.caregiver_unlocked = False
            st.rerun()


# =======================================================================
# HOME PAGE
# =======================================================================

def render_home(user):
    L = user["language"]
    st.markdown(f"<h1 class='mb-center'>🌸 {_t('app_name', L)}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='mb-center mb-muted'>{_t('tagline', L)}</p>", unsafe_allow_html=True)

    history = db.get_game_history(user["id"])
    streak = utils.calculate_streak(history)
    games_today = [
        g for g in history
        if g.get("played_at") and datetime.fromisoformat(g["played_at"]).date() == datetime.now().date()
    ]

    col1, col2 = st.columns(2)
    with col1:
        utils.card_start()
        st.markdown(f"<h3 class='mb-center'>🔥 {_t('current_streak', L)}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h1 class='mb-center'>{streak}</h1>", unsafe_allow_html=True)
        st.markdown("<p class='mb-center mb-muted'>days in a row</p>", unsafe_allow_html=True)
        utils.card_end()
    with col2:
        utils.card_start()
        st.markdown(f"<h3 class='mb-center'>🎯 {_t('todays_activity', L)}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h1 class='mb-center'>{len(games_today)}/{user['daily_goal']}</h1>", unsafe_allow_html=True)
        st.markdown("<p class='mb-center mb-muted'>games played today</p>", unsafe_allow_html=True)
        utils.card_end()

    st.write("")
    if st.button(f"▶️  {_t('start_game', L)}", use_container_width=True, key="home_start_game"):
        st.session_state.page = "Play"
        st.session_state.active_game = None
        st.rerun()

    st.write("")
    voice.read_aloud_button(
        f"{_t('welcome', L)}, {user['name']}. {_t('tagline', L)}",
        language=L,
        key="home_read_aloud",
    )

    st.write("")
    utils.card_start()
    st.markdown("**🧑‍⚕️ Caregiver?**")
    if st.button(f"{_t('caregiver_login', L)}", use_container_width=True, key="home_caregiver_login"):
        st.session_state.page = "Caregiver"
        st.rerun()
    utils.card_end()


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
    st.markdown(f"<h1 class='mb-center'>🎮 {_t('games', L)}</h1>", unsafe_allow_html=True)

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
    L = user["language"]
    st.markdown(f"<h1 class='mb-center'>📈 {_t('progress', L)}</h1>", unsafe_allow_html=True)

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
        fig.update_layout(font_size=16)
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
    L = user["language"]
    st.markdown(f"<h1 class='mb-center'>⏰ {_t('reminder', L)}</h1>", unsafe_allow_html=True)

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
    L = user["language"]
    st.markdown(f"<h1 class='mb-center'>⚙️ {_t('settings', L)}</h1>", unsafe_allow_html=True)

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
    st.markdown("<h1 class='mb-center'>🧑‍⚕️ Caregiver Dashboard</h1>", unsafe_allow_html=True)
    st.caption("This is a demo login for hackathon purposes only - not a secure production login system.")

    if not st.session_state.caregiver_unlocked:
        utils.card_start()
        pin = st.text_input("Enter Caregiver PIN (demo: 1234)", type="password")
        if st.button("🔓 Unlock Dashboard", use_container_width=True):
            if pin == "1234":
                st.session_state.caregiver_unlocked = True
                st.rerun()
            else:
                st.error("Incorrect PIN. Please try again.")
        utils.card_end()
        return

    users = db.get_all_users()
    if not users:
        st.info("No user profiles yet.")
        return

    names = [u["name"] for u in users]
    selected_name = st.selectbox("Select User", names, index=names.index(user["name"]) if user["name"] in names else 0)
    selected_user = next(u for u in users if u["name"] == selected_name)

    if st.button("🧪 Load Demo Data (for presentation)", use_container_width=True):
        db.load_demo_data(selected_user["id"])
        st.success("Demo data loaded! (Clearly marked as demo data for presentation purposes.)")
        st.rerun()

    history = db.get_game_history(selected_user["id"])

    if not history:
        st.info("No activity yet for this user. Use 'Load Demo Data' above for a presentation-ready view.")
        return

    total_games = len(history)
    avg_score = round(utils.safe_average([g["score"] for g in history]), 1)
    avg_accuracy = round(utils.safe_average([g["accuracy"] for g in history]), 1)
    streak = utils.calculate_streak(history)
    reminder = db.get_reminder(selected_user["id"])
    last_activity = history[0]["played_at"] if history else "N/A"

    col1, col2, col3 = st.columns(3)
    col1.metric("Games Completed", total_games)
    col2.metric("Average Score", avg_score)
    col3.metric("Accuracy", f"{avg_accuracy}%")

    col4, col5, col6 = st.columns(3)
    col4.metric("Current Streak", f"{streak} days")
    col5.metric("Difficulty Level", selected_user["difficulty"])
    col6.metric("Reminder", "On" if reminder and reminder["enabled"] else "Off")

    st.caption(f"Last activity: {last_activity}")

    try:
        df = pd.DataFrame(history)
        df["played_at"] = pd.to_datetime(df["played_at"])
        df["date"] = df["played_at"].dt.date

        st.markdown("#### Accuracy Over Time")
        fig1 = px.line(df.sort_values("played_at"), x="played_at", y="accuracy", markers=True)
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("#### Games Completed Per Day")
        daily_counts = df.groupby("date").size().reset_index(name="games")
        fig2 = px.bar(daily_counts, x="date", y="games")
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### Score by Game Type")
        by_game = df.groupby("game_name")["score"].mean().reset_index()
        fig3 = px.bar(by_game, x="game_name", y="score")
        st.plotly_chart(fig3, use_container_width=True)
    except Exception:
        st.info("Not enough data yet to render charts.")

    st.markdown("#### Recent Activity")
    recent_df = pd.DataFrame(history[:10])[["game_name", "score", "accuracy", "difficulty", "played_at"]]
    st.dataframe(recent_df, use_container_width=True, hide_index=True)


# =======================================================================
# MAIN ROUTER
# =======================================================================

def main():
    if st.session_state.user_id is None:
        render_profile_selector()
        return

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
