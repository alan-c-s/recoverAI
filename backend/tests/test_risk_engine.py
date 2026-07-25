import pytest
from app.services.risk_engine import evaluate_risk

def test_risk_evaluation_low():
    tier, score, reason = evaluate_risk(mood_score=8, craving_level=1, journal_text="Went for a walk and had a peaceful day.")
    assert tier == "Low"
    assert score < 0.3

def test_risk_evaluation_high():
    tier, score, reason = evaluate_risk(mood_score=3, craving_level=8, journal_text="Craving alcohol strongly after late evening argument.")
    assert tier in ["High", "Critical"]
    assert score >= 0.6

def test_risk_evaluation_critical_self_harm():
    tier, score, reason = evaluate_risk(journal_text="I feel hopeless and want to end my life right now.")
    assert tier == "Critical"
    assert score >= 0.95
    assert "Critical crisis keyword detected" in reason
