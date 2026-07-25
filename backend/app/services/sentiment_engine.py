from typing import Dict, Any

POSITIVE_WORDS = [
    "good",
    "great",
    "happy",
    "hopeful",
    "proud",
    "walked",
    "walking",
    "calm",
    "sober",
    "strong",
    "better",
    "clear",
    "family",
    "daughter",
    "grateful",
    "spent quality time",
    "exercised",
    "gym",
    "accomplished",
    "peaceful",
    "loved",
    "optimistic",
    "relaxed",
]

NEGATIVE_WORDS = [
    "bad",
    "sad",
    "craving",
    "tempted",
    "cravings",
    "drink",
    "drinking",
    "alcohol",
    "stress",
    "stressed",
    "anxious",
    "anxiety",
    "exhausted",
    "tired",
    "alone",
    "lonely",
    "argument",
    "fight",
    "frustrated",
    "hard",
    "difficult",
    "struggling",
]

CRITICAL_WORDS = [
    "suicide",
    "kill myself",
    "end my life",
    "hopeless",
    "giving up",
    "relapse",
]


def analyze_log_sentiment(text: str) -> Dict[str, Any]:
    """
    Automated sentiment analysis for patient logs.
    Returns:
      - sentiment_label: Positive | Neutral | Negative | Distressed
      - sentiment_score: float from -1.0 to +1.0
      - emotional_tone: Descriptive tone summary
    """
    if not text or not text.strip():
        return {
            "sentiment_label": "Neutral",
            "sentiment_score": 0.0,
            "emotional_tone": "Neutral / Unspecified",
        }

    lower_text = text.lower()

    # Check for critical distress
    for kw in CRITICAL_WORDS:
        if kw in lower_text:
            return {
                "sentiment_label": "Distressed",
                "sentiment_score": -0.95,
                "emotional_tone": "High Distress / Crisis Indicator",
            }

    pos_count = sum(1 for w in POSITIVE_WORDS if w in lower_text)
    neg_count = sum(1 for w in NEGATIVE_WORDS if w in lower_text)

    score = 0.0
    if pos_count + neg_count > 0:
        score = round((pos_count - neg_count) / max(1, pos_count + neg_count), 2)
    else:
        score = 0.05 if len(lower_text) > 10 else 0.0

    if score >= 0.3:
        label = "Positive"
        tone = (
            "Hopeful & Resilient"
            if "daughter" in lower_text or "family" in lower_text
            else "Positive & Grounded"
        )
    elif score <= -0.3:
        label = "Negative"
        tone = (
            "Stressed / Elevated Cravings"
            if "craving" in lower_text or "drink" in lower_text
            else "Anxious / Exhausted"
        )
    else:
        label = "Neutral"
        tone = "Calm & Reflective"

    return {"sentiment_label": label, "sentiment_score": score, "emotional_tone": tone}
