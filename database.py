"""
database.py
------------
Handles all SQLite database operations for MindBloom.

This file automatically creates the database and tables on first
launch, and provides simple helper functions used by the rest of
the app (app.py, games.py, adaptive_engine.py).

IMPORTANT: This prototype does NOT store any medical information.
Only simple activity/game data is stored to power progress tracking.
"""

import hashlib
import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mindbloom.db")


def get_connection():
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt for security."""
    salt = "mindbloom_liquid_glass_salt"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Check if password matches hash."""
    return hash_password(password) == hashed


def init_db():
    """
    Create the database file and all required tables if they do not
    already exist. Safe to call every time the app starts.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT,
            age INTEGER,
            language TEXT DEFAULT 'English',
            difficulty TEXT DEFAULT 'Easy',
            daily_goal INTEGER DEFAULT 3,
            created_at TEXT
        )
    """)

    # Non-destructive migrations for existing DB instances
    try:
        cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    except sqlite3.OperationalError:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_name TEXT,
            score INTEGER,
            accuracy REAL,
            response_time REAL,
            difficulty TEXT,
            played_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reminder_time TEXT DEFAULT '09:00',
            enabled INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement TEXT,
            earned_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# USER & AUTHENTICATION FUNCTIONS
# ---------------------------------------------------------------------

def get_user_by_email(email):
    """Return user by email address (case-insensitive) or None."""
    if not email:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email.strip().lower(),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def register_user(email, password, name=None, age=70, language="English", difficulty="Easy", daily_goal=3):
    """Register a new user with Email + Password."""
    cleaned_email = email.strip().lower()
    if not name or name.strip() == "":
        name = cleaned_email.split("@")[0].capitalize()
    
    pwd_hash = hash_password(password)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, email, password_hash, age, language, difficulty, daily_goal, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name.strip(), cleaned_email, pwd_hash, age, language, difficulty, daily_goal, datetime.now().isoformat()))
    conn.commit()
    user_id = cur.lastrowid
    
    # Create default reminder row
    cur.execute("""
        INSERT INTO reminders (user_id, reminder_time, enabled)
        VALUES (?, ?, ?)
    """, (user_id, "09:00", 0))
    conn.commit()
    conn.close()
    return user_id


def authenticate_user(email, password):
    """Authenticate a user using Email and Password. Returns user dict or None."""
    if not email or not password:
        return None
    user = get_user_by_email(email)
    if not user or not user.get("password_hash"):
        return None
    if verify_password(password, user["password_hash"]):
        return user
    return None


def create_user(name, age, language="English", difficulty="Easy", daily_goal=3):
    """Add a new user profile and return the new user's id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, age, language, difficulty, daily_goal, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, age, language, difficulty, daily_goal, datetime.now().isoformat()))
    conn.commit()
    user_id = cur.lastrowid
    # Create a default (disabled) reminder row for the new user
    cur.execute("""
        INSERT INTO reminders (user_id, reminder_time, enabled)
        VALUES (?, ?, ?)
    """, (user_id, "09:00", 0))
    conn.commit()
    conn.close()
    return user_id


def get_all_users():
    """Return a list of all user profiles."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user(user_id):
    """Return a single user's profile as a dict, or None if not found."""
    if user_id is None:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_settings(user_id, language=None, difficulty=None, daily_goal=None):
    """Update selected settings for a user."""
    user = get_user(user_id)
    if not user:
        return
    language = language if language is not None else user["language"]
    difficulty = difficulty if difficulty is not None else user["difficulty"]
    daily_goal = daily_goal if daily_goal is not None else user["daily_goal"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users SET language = ?, difficulty = ?, daily_goal = ?
        WHERE id = ?
    """, (language, difficulty, daily_goal, user_id))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# GAME RESULT FUNCTIONS
# ---------------------------------------------------------------------

def save_game_result(user_id, game_name, score, accuracy, response_time, difficulty):
    """Save the result of a completed game round."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO game_results (user_id, game_name, score, accuracy, response_time, difficulty, played_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, game_name, score, accuracy, response_time, difficulty, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_game_history(user_id, limit=100):
    """Return recent game results for a user, most recent first."""
    if user_id is None:
        return []
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM game_results
        WHERE user_id = ?
        ORDER BY played_at DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# REMINDER FUNCTIONS
# ---------------------------------------------------------------------

def get_reminder(user_id):
    """Return the reminder settings for a user (creates a default if missing)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reminders WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row is None:
        cur.execute("""
            INSERT INTO reminders (user_id, reminder_time, enabled) VALUES (?, ?, ?)
        """, (user_id, "09:00", 0))
        conn.commit()
        cur.execute("SELECT * FROM reminders WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_reminder(user_id, reminder_time, enabled):
    """Update (or create) a user's reminder settings."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM reminders WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row:
        cur.execute("""
            UPDATE reminders SET reminder_time = ?, enabled = ? WHERE user_id = ?
        """, (reminder_time, int(enabled), user_id))
    else:
        cur.execute("""
            INSERT INTO reminders (user_id, reminder_time, enabled) VALUES (?, ?, ?)
        """, (user_id, reminder_time, int(enabled)))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# ACHIEVEMENT FUNCTIONS
# ---------------------------------------------------------------------

def add_achievement(user_id, achievement):
    """Record a new achievement for a user if they don't already have it."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM achievements WHERE user_id = ? AND achievement = ?
    """, (user_id, achievement))
    if cur.fetchone() is None:
        cur.execute("""
            INSERT INTO achievements (user_id, achievement, earned_at) VALUES (?, ?, ?)
        """, (user_id, achievement, datetime.now().isoformat()))
        conn.commit()
    conn.close()


def get_achievements(user_id):
    """Return all achievements earned by a user."""
    if user_id is None:
        return []
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM achievements WHERE user_id = ? ORDER BY earned_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------
# DEMO DATA
# ---------------------------------------------------------------------

def load_demo_data(user_id):
    """
    Generate realistic-looking fake activity data for a user so the
    Caregiver Dashboard and Progress page have meaningful charts to
    show during the SIH demonstration. Clearly a DEMO-ONLY helper.
    """
    game_names = ["Memory Match", "Number Memory", "Word Recall", "Pattern Recognition", "Daily Quiz"]
    difficulties = ["Easy", "Medium", "Hard"]

    conn = get_connection()
    cur = conn.cursor()

    for day_offset in range(13, -1, -1):
        played_date = datetime.now() - timedelta(days=day_offset)
        # 1 to 3 games played that day
        for _ in range(random.randint(1, 3)):
            game = random.choice(game_names)
            accuracy = round(random.uniform(55, 98), 1)
            score = int(accuracy)
            response_time = round(random.uniform(2.5, 9.0), 1)
            difficulty = random.choice(difficulties)
            played_at = played_date.replace(
                hour=random.randint(8, 20), minute=random.randint(0, 59)
            ).isoformat()
            cur.execute("""
                INSERT INTO game_results (user_id, game_name, score, accuracy, response_time, difficulty, played_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, game, score, accuracy, response_time, difficulty, played_at))

    conn.commit()
    conn.close()

    # Award a couple of demo achievements too
    add_achievement(user_id, "First Game")
    add_achievement(user_id, "3 Day Streak")
    add_achievement(user_id, "10 Games")
