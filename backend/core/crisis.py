"""
Sanctuary 3.0 — Crisis Detection Engine
Improved logic to identify users in distress or crisis.
"""

import re
import logging
from core.constants import CRISIS_KEYWORDS, STRESS_KEYWORDS

logger = logging.getLogger(__name__)

def is_crisis(text: str) -> bool:
    """
    Detect if the user is in a crisis state (Self-harm, etc).
    Uses a combination of keyword matching and regex for better coverage.
    """
    if not text:
        return False
        
    text_lower = text.lower()
    
    # 1. Direct keyword match
    if any(kw in text_lower for kw in CRISIS_KEYWORDS):
        return True
        
    # 2. Pattern matching (e.g., "I want to [action] myself")
    patterns = [
        r"i (want|plan|need) to (kill|hurt|harm|end) (myself|my life)",
        r"better off (dead|if i wasn't here)",
        r"nothing (matters|worth living for)",
        r"can't (go on|take it) anymore",
    ]
    
    for pattern in patterns:
        if re.search(pattern, text_lower):
            logger.warning("Crisis pattern detected: %s", pattern)
            return True
            
    return False

def is_severe(text: str, typing_features: dict, stress_threshold: int = 400) -> bool:
    """
    Detect if the situation warrants RAG injection (High stress).
    """
    if not text:
        return False
        
    text_lower = text.lower()
    keyword_match = any(kw in text_lower for kw in STRESS_KEYWORDS)
    
    # Check typing cadence if available
    avg_interval = typing_features.get("avg_interval", 1000)
    high_stress_typing = 0 < avg_interval < stress_threshold
    
    if high_stress_typing:
        logger.info("High stress typing detected: %sms", avg_interval)
        
    return keyword_match or high_stress_typing
