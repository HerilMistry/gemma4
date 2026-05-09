"""
Example: End-to-End Multilingual & Feedback Flow

This script demonstrates the complete flow of:
1. Multilingual text/audio input
2. Language detection
3. Optional translation
4. LLM processing
5. Feedback collection

Usage:
    python backend/examples_multilingual.py

(This is a reference/documentation file. Modify Config to enable features.)
"""

import json
from pathlib import Path

print(__doc__)

# ============================================================================
# Example 1: Multilingual Text Input
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 1: Multilingual Text Input")
print("=" * 70)

from lang_utils import detect_language, translate_text, should_translate_for_llm

test_sentences = {
    "English": "I feel anxious about my presentation at work.",
    "Spanish": "Me siento ansioso por mi presentación en el trabajo.",
    "French": "Je me sens anxieux face à ma présentation au travail.",
    "German": "Ich bin angespannt vor meiner Präsentation bei der Arbeit.",
    "Chinese": "我对工作中的演讲感到焦虑。",
}

print("\nLanguage Detection:")
for lang_name, text in test_sentences.items():
    detected, confidence = detect_language(text)
    print(f"  {lang_name:12} → {detected} (confidence: {confidence:.2f})")

# ============================================================================
# Example 2: Translation Routing
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 2: Translation Routing Decision")
print("=" * 70)

print("\nIf LLM is English-only, should we translate?")
for lang_name, text in test_sentences.items():
    detected, _ = detect_language(text)
    needs_translation = should_translate_for_llm(detected)
    print(f"  {lang_name:12} ({detected}) → Translate: {needs_translation}")

# ============================================================================
# Example 3: Translation Simulation (Translation disabled by default)
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 3: Translation (Disabled by Default)")
print("=" * 70)

print("\nWith TRANSLATION_SERVICE='disabled':")
spanish_text = "Me siento ansioso por mi presentación."
translated, success = translate_text(spanish_text, "es", "en")
print(f"  Original:   {spanish_text}")
print(f"  Translated: {translated}")
print(f"  Success:    {success}")

# ============================================================================
# Example 4: API Request/Response Simulation
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 4: API Request/Response Simulation")
print("=" * 70)

print("\nRequest to /analyze endpoint:")
analyze_request = {
    "text": "Me siento deprimido y sin esperanza.",
    "typing": json.dumps({"avg_interval": 450}),
    "audio": None,
    "language": None,  # Optional: user can override
}
print(json.dumps(analyze_request, indent=2, ensure_ascii=False))

print("\nExpected Response:")
analyze_response = {
    "response": "Sanctuary: I hear that you're feeling down and hopeless right now. "
                "Those feelings are real, and I want to help you examine them. "
                "When you say 'hopeless,' what specific situation makes you feel that way?",
    "route_used": "heavy_core",
    "language": "es",
    "language_name": "spanish",
    "translated": False,
    "telemetry": "Encrypted via AES-256 GCM",
}
print(json.dumps(analyze_response, indent=2, ensure_ascii=False))

# ============================================================================
# Example 5: Feedback Collection
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 5: Feedback Collection")
print("=" * 70)

print("\nUser provides feedback after reading response:")
feedback_request = {
    "log_id": 42,  # Reference to the /analyze response
    "rating": 5,
    "feedback_text": "This really helped me see a different perspective!",
}
print(json.dumps(feedback_request, indent=2, ensure_ascii=False))

print("\nFeedback is stored encrypted in vault.feedback table:")
print("  - Accessible only with encryption key")
print("  - Tied to original analysis via log_id (optional)")
print("  - Can be retrieved for analytics: vault.retrieve_and_decrypt_feedback()")

# ============================================================================
# Example 6: Database Operations
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 6: Database Operations (Simulated)")
print("=" * 70)

print("\nStore analysis + feedback in vault (automatically encrypted):")

vault_entry = {
    "original_text": "Me siento deprimido y sin esperanza.",
    "processed_text": "Me siento deprimido y sin esperanza.",  # Same (no translation)
    "detected_language": "es",
    "was_translated": False,
    "audio_features": None,
    "typing_features": {"avg_interval": 450},
    "route": "heavy_core",
    "response": "Sanctuary: I hear that you're feeling down...",
}

print("vault.encrypt_and_store({...})")
print(json.dumps(vault_entry, indent=2, ensure_ascii=False))

print("\nStore user feedback (automatically encrypted):")

feedback_entry = {
    "log_id": 42,
    "rating": 5,
    "feedback_text": "This really helped!",
}

print("vault.store_feedback(log_id=42, rating=5, feedback_text='This really helped!')")
print(json.dumps(feedback_entry, indent=2, ensure_ascii=False))

# ============================================================================
# Example 7: Retrieval & Analytics
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 7: Retrieval & Analytics")
print("=" * 70)

print("\nRetrieve and decrypt all feedback:")
print("""
from database import SecureVault

vault = SecureVault()
feedback_list = vault.retrieve_and_decrypt_feedback()

for entry in feedback_list:
    print(f"Log ID:     {entry['log_id']}")
    print(f"Rating:     {entry['rating']}")
    print(f"Comment:    {entry['feedback_text']}")
    print(f"Timestamp:  {entry['timestamp']}")
    print("---")
""")

print("\nCompute feedback analytics:")
print("""
ratings = [f['rating'] for f in feedback_list if f['rating']]
avg_rating = sum(ratings) / len(ratings) if ratings else 0

print(f"Total feedback: {len(feedback_list)}")
print(f"Average rating: {avg_rating:.1f}/5")
print(f"Response rate: {len(ratings)/len(feedback_list)*100:.1f}%")
""")

# ============================================================================
# Example 8: Whisper Audio with Language
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 8: Whisper Audio with Language Parameter")
print("=" * 70)

print("\nFlow for audio input:")
print("""
1. User sends audio file (e.g., Spanish speech)
2. System detects text language (if text also provided): "es"
3. Transcribe audio with language="es":
   result = transcribe_audio("user_audio.wav", language="es")
4. Result:
   {
       "text": "Me siento ansioso por la presentación",
       "language": "es",
       "confidence": None
   }
5. Append transcribed text to user's text input
6. Continue with language-aware RAG + LLM processing
""")

# ============================================================================
# Example 9: Configuration for Different Scenarios
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 9: Configuration Scenarios")
print("=" * 70)

scenarios = {
    "Privacy-First (Recommended)": {
        "LLM_MULTILINGUAL_SUPPORT": False,
        "TRANSLATION_SERVICE": "disabled",
        "ENABLE_USER_FEEDBACK": True,
        "WHISPER_AUTO_LANG": True,
        "pros": ["No external APIs", "Fast", "Privacy-preserving"],
        "cons": ["Non-English users get English responses", "No automatic translation"],
    },
    "Multilingual LLM": {
        "LLM_MULTILINGUAL_SUPPORT": True,
        "TRANSLATION_SERVICE": "disabled",
        "ENABLE_USER_FEEDBACK": True,
        "WHISPER_AUTO_LANG": True,
        "pros": ["Responses in user's language", "Privacy-preserving", "No translation latency"],
        "cons": ["Requires multilingual LLM model"],
    },
    "Full Translation (GPU recommended)": {
        "LLM_MULTILINGUAL_SUPPORT": False,
        "TRANSLATION_SERVICE": "local",
        "ENABLE_USER_FEEDBACK": True,
        "WHISPER_AUTO_LANG": True,
        "pros": ["All users get responses in English LLM's style", "Fully offline"],
        "cons": ["5-30s latency per non-English request", "~2GB memory", "CPU intensive"],
    },
}

for scenario, config in scenarios.items():
    print(f"\n{scenario}:")
    for key, value in config.items():
        if key not in ["pros", "cons"]:
            print(f"  {key}: {value}")
    print(f"  Pros:  {', '.join(config['pros'])}")
    print(f"  Cons:  {', '.join(config['cons'])}")

# ============================================================================
# Example 10: Error Handling
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 10: Error Handling")
print("=" * 70)

print("\nLanguage detection gracefully handles edge cases:")
print("""
# Empty text
lang, conf = detect_language("")  # → ("en", 0.0)

# Very short text
lang, conf = detect_language("hi")  # → ("en", 0.0)

# Unknown/mixed language
lang, conf = detect_language("asdfjkl xyz")  # → ("en", 0.0) or detected

# Malformed request
transcribe_audio("/nonexistent.wav")  # → {"text": "", "language": None}
""")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print("""
New Capabilities:
  ✅ Automatic language detection (28+ languages)
  ✅ Whisper language parameter for better transcription
  ✅ Optional translation pipeline (disabled by default)
  ✅ User feedback collection (encrypted)
  ✅ Multilingual response tracking
  ✅ Backward compatible with existing code

Key Files:
  - backend/lang_utils.py          — Language detection & translation
  - backend/server.py               — /analyze & /feedback endpoints
  - backend/database.py             — Feedback table
  - MULTILINGUAL_GUIDE.md           — Full documentation
  - backend/test_multilingual.py    — Test suite
  - backend/validate_multilingual.py — Validation

Configuration (.env):
  SANCTUARY_LLM_MULTILINGUAL=false
  SANCTUARY_TRANSLATION_SERVICE=disabled
  SANCTUARY_ENABLE_FEEDBACK=true

Next Steps:
  1. Review MULTILINGUAL_GUIDE.md for detailed API docs
  2. Run: pytest backend/test_multilingual.py -v
  3. Run: python backend/validate_multilingual.py
  4. Deploy and enable feedback collection!
""")

print("=" * 70)
print("\n✅ For detailed docs, see MULTILINGUAL_GUIDE.md\n")
