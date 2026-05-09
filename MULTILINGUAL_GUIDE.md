# Sanctuary 3.0 — Multilingual & Feedback Implementation Guide

## Overview

This document describes the newly implemented multilingual support and user feedback collection features for Sanctuary 3.0.

---

## 1. Multilingual Text Support

### Feature: Language Detection

**Module**: `backend/lang_utils.py`

The system now automatically detects the language of user input text using the `langdetect` library.

#### API

```python
from lang_utils import detect_language, detect_language_with_probs

# Basic detection (returns language code and confidence)
lang_code, confidence = detect_language("Hola, ¿cómo estás?")
# Returns: ("es", 0.9)

# Get full probability distribution
lang_code, prob_dict = detect_language_with_probs("Bonjour le monde")
# Returns: ("fr", {"fr": 0.95, "en": 0.05})
```

#### Supported Languages

The system supports 28+ languages via `langdetect`. Key ones mapped to Whisper:

| ISO 639-1 | Language | Whisper Name |
|-----------|----------|--------------|
| en | English | english |
| es | Spanish | spanish |
| fr | French | french |
| de | German | german |
| it | Italian | italian |
| pt | Portuguese | portuguese |
| zh | Chinese | chinese |
| ja | Japanese | japanese |
| ko | Korean | korean |
| ar | Arabic | arabic |
| ru | Russian | russian |

(See `lang_utils.py::WHISPER_LANGUAGE_MAP` for full list)

#### Configuration

Add to `.env`:

```bash
# Language detection confidence threshold (0-1)
# Set to 0.5 to only accept confident detections
# SANCTUARY_LANG_DETECTION_THRESHOLD=0.5

# LLM multilingual support
# Set to "true" if your LLM model is multilingual
SANCTUARY_LLM_MULTILINGUAL=false

# Translation service: "disabled", "local", or "cloud" (cloud not implemented)
SANCTUARY_TRANSLATION_SERVICE=disabled

# Auto-detect language for Whisper
SANCTUARY_WHISPER_AUTO_LANG=true
```

---

## 2. Multilingual Speech Processing

### Feature: Whisper Language Parameter

**Module**: `backend/audio_processing.py`

Updated to accept and pass the detected language code to Whisper for improved transcription accuracy.

#### API

```python
from audio_processing import transcribe_audio

# Auto-detect language (Whisper default)
result = transcribe_audio("user_audio.wav")

# Specify language explicitly
result = transcribe_audio("user_audio.wav", language="es")

# Result structure:
# {
#     "text": "Transcribed text",
#     "language": "es",  # Detected or specified language
#     "confidence": None  # Whisper doesn't expose confidence
# }
```

#### Integration with Text Detection

The `/analyze` endpoint flow:

```
1. User sends text + optional audio
2. System detects language from text input
3. If audio provided:
   - Pass detected language to Whisper (improves accuracy)
   - Update detected language from Whisper result if more reliable
4. If audio language differs from text, prefer audio (more reliable)
5. Pass final detected language to LLM / RAG
```

---

## 3. Optional Translation Pipeline

### Feature: Text Translation

**Module**: `backend/lang_utils.py`

Translation is configurable and defaults to **disabled** for privacy. When enabled, translates non-English text to English before LLM processing if the LLM is English-only.

#### API

```python
from lang_utils import translate_text, should_translate_for_llm

# Check if translation is needed
needs_translation = should_translate_for_llm("es")  # True if LLM is English-only

# Translate text
translated_text, success = translate_text(
    text="Hola mundo",
    source_lang="es",
    target_lang="en"
)
# Returns: ("Hello world", True)
```

#### Translation Services

##### Disabled (Default)
```python
# In config.py:
TRANSLATION_SERVICE = "disabled"

# translate_text() returns original text, success=False
```

**Recommendation**: Keep this as the default for privacy and performance.

##### Local (M2M100 Model)
```python
# In config.py:
TRANSLATION_SERVICE = "local"

# First run: Downloads facebook/m2m100_418M (~800MB)
# Slow on CPU (5-30 seconds per 100 tokens)
# Runs entirely offline after download
```

**Requirements**:
```bash
pip install transformers torch
```

**Tradeoffs**:
- ✅ Privacy: No external API calls
- ❌ Slow: 5-30s per request on CPU
- ❌ Large model: ~800MB disk
- ❌ Memory intensive: ~2GB RAM during inference

##### Cloud (Placeholder)
```python
# In config.py:
TRANSLATION_SERVICE = "cloud"

# Not yet implemented
# Would require API keys (e.g., Google Translate, DeepL)
# Network latency and telemetry concerns
```

#### Decision Tree for Translation

```
User sends non-English text (e.g., Spanish)
            |
            v
Is LLM multilingual? (Config.LLM_MULTILINGUAL_SUPPORT)
      /                                    \
    Yes                                    No
      |                                     |
      |                                     v
      |                        Is Spanish in SUPPORTED_LLM_LANGUAGES?
      |                                /              \
      |                              Yes               No
      |                               |                 |
      |                               |                 v
      |                               |       Should translate? (Config.TRANSLATION_SERVICE)
      |                               |         /         |         \
      |                               |      local     disabled     cloud
      |                               |        |           |          |
      v                               v        v           v          v
   Use Spanish → LLM         Use Spanish → LLM  Download  Original   API call
                                                 M2M100    text → LLM  → LLM
```

---

## 4. User Feedback Collection

### Feature: Feedback Storage & `/feedback` Endpoint

**Modules**:
- `backend/database.py` — Vault extension with `feedback` table
- `backend/server.py` — `/feedback` POST endpoint

#### Database Schema

Two new tables in encrypted vault:

```sql
-- Existing table (unchanged)
encrypted_logs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    nonce BLOB,
    ciphertext BLOB
)

-- New feedback table
feedback (
    id INTEGER PRIMARY KEY,
    log_id INTEGER,                  -- Reference to original analysis
    timestamp TEXT,
    rating INTEGER,                  -- e.g., 1-5 stars
    feedback_text TEXT,              -- Free-form user comment
    nonce BLOB,                      -- AES-256 GCM nonce
    ciphertext BLOB                  -- Encrypted [log_id, rating, feedback_text]
)
```

All feedback is encrypted at rest (AES-256 GCM), same as analysis logs.

#### API

##### Store Feedback

```http
POST /feedback
Content-Type: application/json

{
    "log_id": 123,
    "rating": 5,
    "feedback_text": "This response really helped me reframe my thoughts!"
}
```

**Response**:
```json
{
    "status": "success",
    "message": "Thank you for your feedback. Your input helps us improve."
}
```

**Optional Fields**: All fields in the request are optional.
- `log_id=null`: Feedback not tied to a specific response
- `rating=null`: Qualitative-only feedback
- `feedback_text=null`: Quantitative-only rating

#### Frontend Integration

```javascript
// 1. Capture response ID from /analyze
const analyzeResponse = await fetch("/analyze", { ... });
const { response, log_id } = await analyzeResponse.json();

// Display response to user...

// 2. User rates response (e.g., thumbs up/down, star rating)
const userRating = 5;
const userComment = "Really helpful!";

// 3. Send feedback
await fetch("/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        log_id,
        rating: userRating,
        feedback_text: userComment
    })
});
```

#### Configuration

```bash
# Enable/disable feedback collection
SANCTUARY_ENABLE_FEEDBACK=true

# Storage backend (currently only "vault" is supported)
SANCTUARY_FEEDBACK_STORAGE=vault
```

#### Analytics & Retrieval

```python
from database import SecureVault

vault = SecureVault()

# Retrieve all encrypted feedback
feedback_list = vault.retrieve_and_decrypt_feedback()

for entry in feedback_list:
    print(f"Log ID: {entry['log_id']}")
    print(f"Rating: {entry['rating']}")
    print(f"Comment: {entry['feedback_text']}")
    print(f"Timestamp: {entry['timestamp']}")
    print("---")
```

---

## 5. Updated `/analyze` Endpoint

### New Parameters

```http
POST /analyze
Content-Type: multipart/form-data

text=I feel anxious
typing={"avg_interval": 420}
audio=@user_audio.wav
language=es  # OPTIONAL: user-specified language override
```

### Response Enhancements

```json
{
    "response": "Sanctuary: It sounds like...",
    "route_used": "heavy_core",
    "language": "es",              // NEW: detected language code
    "language_name": "spanish",    // NEW: language name
    "translated": false,           // NEW: whether text was translated for LLM
    "telemetry": "Encrypted via AES-256 GCM"
}
```

### Vault Storage

The `encrypt_and_store()` call now preserves both original and processed text:

```python
vault_data = {
    "original_text": "Me siento ansioso",              # Original input
    "processed_text": "I feel anxious",                 # After translation (if any)
    "detected_language": "es",
    "was_translated": True,
    "audio_features": {...},
    "typing_features": {...},
    "route": "heavy_core",
    "response": "Sanctuary: ..."
}
vault.encrypt_and_store(vault_data)
```

---

## 6. Configuration Summary

Add to `backend/.env`:

```bash
# --- Multilingual & Translation ---
SANCTUARY_LLM_MULTILINGUAL=false
SANCTUARY_TRANSLATION_SERVICE=disabled
SANCTUARY_WHISPER_AUTO_LANG=true

# --- Feedback ---
SANCTUARY_ENABLE_FEEDBACK=true
SANCTUARY_FEEDBACK_STORAGE=vault
```

---

## 7. Dependencies

Add to `backend/requirements.txt`:

```
langdetect==1.0.9
```

**Optional** (for local translation):
```
transformers>=4.30.0
torch>=2.0.0
```

---

## 8. Testing

Run the test suite:

```bash
cd backend
pytest test_multilingual.py -v
```

### Test Coverage

- Language detection (EN, ES, FR, etc.)
- Language mapping (ISO codes ↔ Whisper names)
- Translation routing (when to translate)
- Feedback storage & retrieval
- `/feedback` endpoint validation
- `/analyze` multilingual integration

---

## 9. Implementation Checklist

- [x] `backend/lang_utils.py` — language detection + translation utilities
- [x] `backend/audio_processing.py` — expose language parameter for Whisper
- [x] `backend/database.py` — feedback table & methods
- [x] `backend/server.py` — `/analyze` multilingual flow + `/feedback` endpoint
- [x] `backend/config.py` — multilingual configuration options
- [x] `backend/test_multilingual.py` — unit & integration tests
- [x] `backend/requirements.txt` — add `langdetect`
- [x] Documentation (this file)

---

## 10. Next Steps & Future Enhancements

### Short-term

1. **Collect feedback data**: Enable `/feedback` in production and gather user ratings.
2. **Monitor translation quality**: If local translation is enabled, track accuracy via feedback.
3. **Expand RAG content**: Add multilingual clinical protocols to ChromaDB.

### Medium-term

1. **Multilingual LLM**: If you deploy a multilingual LLM, set `LLM_MULTILINGUAL_SUPPORT=true` to skip translation.
2. **Feedback analytics**: Build a dashboard to visualize feedback ratings by language, route, distortion type.
3. **A/B testing**: Use feedback + language metadata to optimize response styles per language.

### Long-term

1. **Lightweight RL**: Integrate feedback into a contextual bandit (see `rl_agent.py` plan) to personalize response styles by user language & feedback history.
2. **Cloud translation**: Implement cloud translation API (DeepL, Google Translate) for low-latency multilingual support.
3. **Clinician dashboard**: Export feedback + language metadata for clinical review and validation.

---

## 11. Security & Privacy Notes

- ✅ All feedback is encrypted at rest (AES-256 GCM)
- ✅ Translation (if enabled locally) happens entirely offline
- ✅ No external telemetry or cloud calls (unless cloud translation is enabled)
- ⚠️ If using cloud translation, ensure compliance with HIPAA/GDPR
- ⚠️ User language data is stored; ensure privacy policy disclosure

---

## 12. Troubleshooting

### Language Detection Failing

**Symptom**: `detect_language()` returns `("en", 0.0)` for non-English text.

**Solution**:
1. Ensure text is long enough (>= 3 characters).
2. Try `detect_language_with_probs()` to see all candidates.
3. Manually specify language in `/analyze` request.

### Whisper Not Using Language Parameter

**Symptom**: Whisper still mis-transcribes even with language specified.

**Solution**:
1. Verify `audio_processing.py` is passing `language=` kwarg.
2. Check Whisper model size (`Config.WHISPER_MODEL_NAME`). Tiny/base models may ignore hints; use small/medium.
3. Ensure audio quality is sufficient (clear speech, minimal noise).

### Translation Slow

**Symptom**: Requests hang for 5-30 seconds with `TRANSLATION_SERVICE=local`.

**Solution**:
1. Disable local translation: `TRANSLATION_SERVICE=disabled` (recommended).
2. Deploy on GPU to speed up M2M100 (10-100x faster).
3. Use cloud translation if privacy allows: `TRANSLATION_SERVICE=cloud` (not yet implemented).

### Feedback Not Storing

**Symptom**: `/feedback` returns success but data doesn't persist.

**Solution**:
1. Verify `SANCTUARY_ENABLE_FEEDBACK=true`.
2. Check database permissions on `Config.DB_PATH`.
3. Inspect logs for encryption errors.
4. Manually call `vault.retrieve_and_decrypt_feedback()` to verify data.

---

## 13. Example: Multilingual User Journey

### Spanish User, No Audio

```
1. Frontend sends:
   POST /analyze
   text="Me siento ansioso y deprimido"
   typing="{...}"
   language=null (user didn't specify)

2. Backend processes:
   - detect_language("Me siento ansioso y deprimido") → ("es", 0.9)
   - No audio provided; skip transcription
   - Check: should_translate_for_llm("es") → True (LLM is English-only)
   - translate_text(..., "es", "en") → "I feel anxious and depressed"
   - Retrieve RAG context (in English)
   - Route: "heavy_core"
   - Generate response (in English or translated back)

3. Response:
   {
       "response": "Sanctuary: I hear you. It sounds like...",
       "route_used": "heavy_core",
       "language": "es",
       "language_name": "spanish",
       "translated": true
   }

4. Frontend displays response + "This response was helpful" buttons
5. User clicks ⭐⭐⭐⭐⭐
6. Frontend sends:
   POST /feedback
   log_id=42
   rating=5
   feedback_text="Muy útil!"
```

### French User, With Audio

```
1. Frontend sends:
   POST /analyze
   text="Je me sens déprimé"
   typing="{...}"
   audio=@user_voice.wav
   language="fr" (user specified)

2. Backend processes:
   - detect_language("Je me sens déprimé") → ("fr", 0.95)
   - Audio provided; transcribe with language="fr"
   - transcribe_audio(..., language="fr") → "J'ai pensé que j'échouerais"
   - Combine texts: "Je me sens déprimé J'ai pensé que j'échouerais"
   - should_translate_for_llm("fr") → True (LLM English-only)
   - translate_text(..., "fr", "en") → "I feel depressed. I thought I would fail."
   - Generate response in English
   - Store: original_text, processed_text, language="fr", was_translated=True

3. Response:
   {
       "response": "Sanctuary: I hear that you're feeling down...",
       "language": "fr",
       "language_name": "french",
       "translated": true
   }
```

---

**End of Documentation**

For questions or issues, refer to the test file (`test_multilingual.py`) for integration examples.
