import pytest
from core.sanitizer import PIISanitizer
from core.crisis import is_crisis

def test_pii_sanitization():
    raw_text = "My name is John Doe and my phone number is 123-456-7890."
    sanitized = PIISanitizer.sanitize(raw_text)
    assert "John Doe" not in sanitized
    assert "123-456-7890" not in sanitized
    assert "[NAME]" in sanitized or "[PII]" in sanitized or "John" not in sanitized

def test_crisis_detection():
    normal_text = "I am feeling a bit stressed about work."
    crisis_text = "I want to end my life, I have no hope."
    
    assert is_crisis(normal_text) is False
    assert is_crisis(crisis_text) is True

def test_message_building():
    from server import _build_messages
    text = "Hello"
    messages = _build_messages(text, "Clinical context", {}, "normal", "Reframing")
    
    assert messages[0]["role"] == "system"
    assert "Reframing" in messages[0]["content"]
    assert messages[-1]["role"] == "user"
    assert "Hello" in messages[-1]["content"]
