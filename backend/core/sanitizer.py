"""
Sanctuary 3.0 — PII Sanitizer & Masker
Strict compliance tool to prevent sensitive personal information from 
hitting the LLM or being stored in a way that could be reverse-engineered.
"""

import re
import logging

logger = logging.getLogger(__name__)

class PIISanitizer:
    # Industry-standard regex patterns for PII
    PATTERNS = {
        "email": r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
        "phone": r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "ipv4": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        "credit_card": r'\b(?:\d[ -]*?){13,16}\b',
    }

    @classmethod
    def sanitize(cls, text: str) -> str:
        """
        Mask PII in text using the defined patterns and heuristics.
        """
        sanitized = text
        for label, pattern in cls.PATTERNS.items():
            sanitized = re.sub(pattern, f"[{label.upper()}]", sanitized)
        
        # Simple Name Heuristic: Mask common introductions
        # Matches "My name is John Doe", "I am Jane", etc.
        # Restrict case-insensitivity to intro verbs, keeping the matched Name strictly capitalized
        intro_patterns = [
            r'(?i:(?:my name is|i am|this is|call me))\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ]
        blacklist = {"feeling", "stressed", "overwhelmed", "sad", "anxious", "depressed", "afraid", "scared", "worried", "happy", "angry", "tired", "down", "low", "going", "doing", "fine", "okay", "here", "there"}
        for pattern in intro_patterns:
            def _mask_name(match):
                full_match = match.group(0)
                name_part = match.group(1)
                # Skip masking if it is a common feeling or verb
                if name_part.lower() in blacklist:
                    return full_match
                intro = full_match.split(name_part)[0]
                return f"{intro}[NAME]"
            sanitized = re.sub(pattern, _mask_name, sanitized)

        return sanitized

    @classmethod
    def sanitize_biometrics(cls, features: dict) -> dict:
        """
        Anonymize behavioral biometrics by adding subtle jitter.
        """
        sanitized = features.copy()
        import random
        if "pitch" in sanitized:
            sanitized["pitch"] = round(sanitized["pitch"] * (1 + random.uniform(-0.05, 0.05)), 2)
        if "avg_interval" in sanitized:
            # avg_interval can be a number or a list
            if isinstance(sanitized["avg_interval"], (int, float)):
                sanitized["avg_interval"] = round(sanitized["avg_interval"] * (1 + random.uniform(-0.05, 0.05)), 2)
            
        return sanitized

def mask_text(text: str) -> str:
    return PIISanitizer.sanitize(text)
