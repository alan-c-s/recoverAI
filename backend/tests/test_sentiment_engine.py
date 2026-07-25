import pytest
from app.services.sentiment_engine import analyze_log_sentiment


def test_sentiment_analysis_positive():
    text = "Had a great productive day, went for a 20 minute walk outside and read a story with my daughter before bed."
    result = analyze_log_sentiment(text)
    assert result["sentiment_label"] == "Positive"
    assert result["sentiment_score"] > 0
    assert "Hopeful" in result["emotional_tone"]


def test_sentiment_analysis_negative():
    text = "Feeling hopeless and overwhelmed by intense cravings after a difficult meeting at work."
    result = analyze_log_sentiment(text)
    assert result["sentiment_label"] in ["Negative", "Distressed"]
    assert result["sentiment_score"] < 0


def test_sentiment_analysis_distressed_crisis():
    text = "I am in crisis and want to end everything right now, feeling completely hopeless."
    result = analyze_log_sentiment(text)
    assert result["sentiment_label"] == "Distressed"
    assert result["sentiment_score"] <= -0.8
