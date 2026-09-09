"""
games.py
---------
Content generators for MindBloom's five cognitive games.

Each function takes a difficulty settings dict (from adaptive_engine.
get_difficulty_settings) and returns everything needed to render and
score that round of the game. No Streamlit code lives here - this
file only builds game data, keeping logic separate from the UI.
"""

import random

# A friendly, simple emoji symbol set used by Memory Match and Word Recall
SYMBOL_POOL = ["🍎", "🐶", "🌻", "⭐", "🎈", "🍊", "🐦", "🌙", "☂️", "🎁",
               "🐱", "🍇", "🌈", "🔔", "🚗", "🍓"]

WORD_POOL = ["Apple", "Chair", "River", "Garden", "Bread", "Window",
             "Music", "Flower", "Table", "Clock", "Bridge", "Letter",
             "Candle", "Mountain", "Basket", "Umbrella"]


# ---------------------------------------------------------------------
# GAME 1 - MEMORY MATCH
# ---------------------------------------------------------------------

def generate_memory_match(settings):
    """
    Pick a set of symbols to show, then a mixed set of options
    (correct symbols + distractors) to ask about afterward.
    """
    n = settings["items"]
    n = min(n, len(SYMBOL_POOL))
    shown = random.sample(SYMBOL_POOL, n)

    # Build an options list: shown symbols + a few distractors, shuffled
    distractor_pool = [s for s in SYMBOL_POOL if s not in shown]
    distractors = random.sample(distractor_pool, min(4, len(distractor_pool)))
    options = shown + distractors
    random.shuffle(options)

    return {
        "shown": shown,
        "options": options,
        "correct": set(shown),
    }


def score_memory_match(game_data, selected):
    """Score the Memory Match round. selected is a list of chosen symbols."""
    selected_set = set(selected)
    correct_set = game_data["correct"]
    correct_hits = len(selected_set & correct_set)
    wrong_picks = len(selected_set - correct_set)
    total = len(correct_set)
    accuracy = max(0, (correct_hits - wrong_picks) / total * 100) if total else 0
    score = int(accuracy)
    return score, round(accuracy, 1)


# ---------------------------------------------------------------------
# GAME 2 - NUMBER MEMORY
# ---------------------------------------------------------------------

def generate_number_memory(settings):
    """Generate a random sequence of digits for the user to memorize."""
    length = settings["sequence_length"]
    sequence = [random.randint(0, 9) for _ in range(length)]
    return {"sequence": sequence}


def score_number_memory(game_data, user_sequence):
    """Score Number Memory by comparing position-by-position."""
    correct = game_data["sequence"]
    total = len(correct)
    matches = sum(1 for a, b in zip(correct, user_sequence) if a == b)
    accuracy = (matches / total) * 100 if total else 0
    score = int(accuracy)
    return score, round(accuracy, 1)


# ---------------------------------------------------------------------
# GAME 3 - WORD RECALL
# ---------------------------------------------------------------------

def generate_word_recall(settings):
    """Pick a set of simple words to show, then build an option list."""
    n = settings["items"]
    n = min(n, len(WORD_POOL))
    shown = random.sample(WORD_POOL, n)

    distractor_pool = [w for w in WORD_POOL if w not in shown]
    distractors = random.sample(distractor_pool, min(4, len(distractor_pool)))
    options = shown + distractors
    random.shuffle(options)

    return {
        "shown": shown,
        "options": options,
        "correct": set(shown),
    }


def score_word_recall(game_data, selected):
    """Score Word Recall the same way as Memory Match."""
    return score_memory_match(game_data, selected)


# ---------------------------------------------------------------------
# GAME 4 - PATTERN RECOGNITION
# ---------------------------------------------------------------------

def generate_pattern(settings):
    """
    Build a simple arithmetic number pattern (e.g. +2 each step) and
    ask what comes next. Difficulty affects how many numbers are shown
    and the size of the step.
    """
    length = max(3, settings["sequence_length"])
    step = random.choice([1, 2, 3]) if settings["items"] <= 6 else random.choice([2, 3, 4, 5])
    start = random.randint(1, 10)
    sequence = [start + step * i for i in range(length)]
    answer = start + step * length

    # Build multiple-choice options
    options = {answer}
    while len(options) < 4:
        fake = answer + random.choice([-3, -2, -1, 1, 2, 3])
        if fake > 0:
            options.add(fake)
    options = list(options)
    random.shuffle(options)

    return {
        "sequence": sequence,
        "answer": answer,
        "options": options,
    }


def score_pattern(game_data, selected_answer):
    """Score Pattern Recognition - it's simply right or wrong."""
    correct = selected_answer == game_data["answer"]
    accuracy = 100.0 if correct else 0.0
    score = 100 if correct else 0
    return score, accuracy


# ---------------------------------------------------------------------
# GAME 5 - DAILY QUIZ
# ---------------------------------------------------------------------

QUIZ_BANK = [
    {"q": "Which of these is a fruit?", "options": ["Apple", "Chair", "Cloud", "Pencil"], "answer": "Apple"},
    {"q": "Which color is the sky on a clear day?", "options": ["Green", "Blue", "Purple", "Brown"], "answer": "Blue"},
    {"q": "How many days are in a week?", "options": ["5", "6", "7", "8"], "answer": "7"},
    {"q": "Which of these is a day of the week?", "options": ["Monday", "January", "Summer", "Morning"], "answer": "Monday"},
    {"q": "Which of these is a month?", "options": ["Tuesday", "April", "Winter", "Noon"], "answer": "April"},
    {"q": "What do we use to tell time?", "options": ["Clock", "Spoon", "Mirror", "Pillow"], "answer": "Clock"},
    {"q": "Which of these is a common morning activity?", "options": ["Brushing teeth", "Sleeping all day", "Swimming in a lake", "Driving a train"], "answer": "Brushing teeth"},
    {"q": "Which number comes after 9?", "options": ["8", "10", "11", "7"], "answer": "10"},
    {"q": "Which of these is used to drink water?", "options": ["Glass", "Shoe", "Book", "Hat"], "answer": "Glass"},
    {"q": "Which season usually comes after winter?", "options": ["Summer", "Spring", "Autumn", "Monsoon"], "answer": "Spring"},
]


def generate_quiz(settings):
    """Pick a small set of everyday-knowledge questions."""
    n = min(3 if settings["items"] <= 6 else 5, len(QUIZ_BANK))
    questions = random.sample(QUIZ_BANK, n)
    return {"questions": questions}


def score_quiz(game_data, user_answers):
    """Score the Daily Quiz. user_answers is a list matching questions order."""
    questions = game_data["questions"]
    total = len(questions)
    correct_count = sum(
        1 for q, a in zip(questions, user_answers) if a == q["answer"]
    )
    accuracy = (correct_count / total) * 100 if total else 0
    score = int(accuracy)
    return score, round(accuracy, 1)


# ---------------------------------------------------------------------
# ENCOURAGING FEEDBACK (never negative or frightening)
# ---------------------------------------------------------------------

ENCOURAGEMENT_MESSAGES = [
    "Good try!",
    "Let's try another one.",
    "You're doing great!",
    "Keep going!",
]


def get_encouragement(accuracy):
    """
    Return a warm, encouraging message based on accuracy.
    Never uses negative or frightening language, even for low scores.
    """
    if accuracy >= 80:
        return "You're doing great!"
    elif accuracy >= 50:
        return "Keep going!"
    else:
        return random.choice(["Good try!", "Let's try another one."])
