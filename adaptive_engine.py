"""
adaptive_engine.py
--------------------
A simple, explainable adaptive-difficulty engine for MindBloom.

This is NOT a medical or diagnostic assessment. It only adjusts how
challenging the cognitive games feel, based on recent scores,
accuracy, and response time - similar to difficulty systems used in
ordinary brain-training or puzzle apps.

Difficulty levels (in increasing order): "Easy", "Medium", "Hard"
"""

DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]

# Settings that games.py uses to actually build each difficulty level
DIFFICULTY_SETTINGS = {
    "Easy":   {"items": 4, "sequence_length": 3, "hints": 2, "time_limit": 30},
    "Medium": {"items": 6, "sequence_length": 4, "hints": 1, "time_limit": 20},
    "Hard":   {"items": 8, "sequence_length": 5, "hints": 0, "time_limit": 15},
}


def get_difficulty_settings(difficulty):
    """Return the game-building settings for a given difficulty label."""
    return DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS["Easy"])


def calculate_adaptive_difficulty(history, current_difficulty="Easy"):
    """
    Look at a user's recent game history and decide whether the
    difficulty should go up, down, or stay the same.

    Parameters
    ----------
    history : list of dicts
        Each dict should have at least 'accuracy' (0-100) and
        'response_time' (seconds). Most recent first.
    current_difficulty : str
        The user's current difficulty level.

    Returns
    -------
    dict with:
        - 'difficulty': the new difficulty label
        - 'explanation': a friendly, plain-language explanation
        - 'direction': 'up', 'down', or 'same'
    """
    if not history:
        return {
            "difficulty": current_difficulty,
            "explanation": "Let's start with a comfortable level and adjust as we go.",
            "direction": "same",
        }

    # Look at the last 3 games only (recent performance matters most)
    recent = history[:3]
    accuracies = [g.get("accuracy", 0) or 0 for g in recent]
    times = [g.get("response_time", 0) or 0 for g in recent]

    avg_accuracy = sum(accuracies) / len(accuracies)
    avg_time = sum(times) / len(times) if times else 0

    current_index = DIFFICULTY_LEVELS.index(current_difficulty) if current_difficulty in DIFFICULTY_LEVELS else 0

    # Decide direction
    if avg_accuracy >= 80 and avg_time <= 8 and current_index < len(DIFFICULTY_LEVELS) - 1:
        new_index = current_index + 1
        direction = "up"
        explanation = "Your last few games were strong, so we increased the challenge slightly."
    elif avg_accuracy < 50 and current_index > 0:
        new_index = current_index - 1
        direction = "down"
        explanation = "Let's make things a little easier and more relaxed for the next round."
    else:
        new_index = current_index
        direction = "same"
        explanation = "You're doing well at this level, so we'll keep the pace the same."

    return {
        "difficulty": DIFFICULTY_LEVELS[new_index],
        "explanation": explanation,
        "direction": direction,
    }
