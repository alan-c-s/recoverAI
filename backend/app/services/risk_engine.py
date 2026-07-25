from typing import Tuple

CRITICAL_KEYWORDS = [
    "suicide", "end my life", "kill myself", "overdose", "want to die",
    "can't live anymore", "self harm", "cutting myself"
]

HIGH_RISK_KEYWORDS = [
    "relapse", "buying drugs", "bought alcohol", "tempted to drink",
    "can't stop craving", "giving up", "hopeless", "buying pills"
]

MEDIUM_RISK_KEYWORDS = [
    "stressed", "anxious", "overwhelmed", "lonely", "exhausted",
    "angry", "headache", "hard day"
]

def evaluate_risk(mood_score: int = None, craving_level: int = None, journal_text: str = None) -> Tuple[str, float, str]:
    """
    Evaluates risk tier (Low, Medium, High, Critical), numeric score (0.0 to 1.0), and trigger reason.
    """
    text_lower = (journal_text or "").lower()
    
    # 1. Critical Check (Self-harm / Suicide intent)
    for kw in CRITICAL_KEYWORDS:
        if kw in text_lower:
            return "Critical", 1.0, f"Critical crisis keyword detected: '{kw}'"
            
    # 2. High Risk Check (Craving >= 8 or High Risk Keywords)
    if craving_level is not None and craving_level >= 8:
        return "High", 0.85, f"Severe craving level reported ({craving_level}/10)"
        
    for kw in HIGH_RISK_KEYWORDS:
        if kw in text_lower:
            return "High", 0.75, f"High risk relapse indicator detected: '{kw}'"
            
    # 3. Medium Risk Check (Mood <= 3 or Craving >= 5 or Medium Keywords)
    if mood_score is not None and mood_score <= 3:
        return "Medium", 0.55, f"Low mood score reported ({mood_score}/10)"
        
    if craving_level is not None and craving_level >= 5:
        return "Medium", 0.50, f"Moderate craving level reported ({craving_level}/10)"
        
    for kw in MEDIUM_RISK_KEYWORDS:
        if kw in text_lower:
            return "Medium", 0.40, f"Stress/anxiety indicator detected: '{kw}'"
            
    # 4. Low Risk (Default)
    return "Low", 0.10, "Routine reflection; stable state."
