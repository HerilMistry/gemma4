# File Reference: Multilingual & Feedback Implementation

## Core Implementation Files

### Backend Modules

#### `backend/lang_utils.py` (NEW, 290 lines)
**Purpose**: Language detection and translation utilities  
**Key Functions**:
- `detect_language(text)` → `(lang_code, confidence)`
- `detect_language_with_probs(text)` → `(lang_code, {lang: prob})`
- `get_whisper_language(lang_code)` → Whisper language name
- `should_translate_for_llm(lang_code)` → bool
- `translate_text(text, source_lang, target_lang)` → `(translated_text, success)`
- `format_multilingual_context()` → metadata dict

**Constants**:
- `WHISPER_LANGUAGE_MAP` — ISO 639-1 to Whisper names (28+ languages)
- `SUPPORTED_LLM_LANGUAGES` — Languages LLM natively supports

**Usage**:
```python
from lang_utils import detect_language
lang, conf = detect_language("Hola mundo")
# → ("es", 0.9)
```

---

#### `backend/audio_processing.py` (UPDATED, +30 lines)
**Purpose**: Whisper-based audio transcription with language support  
**Changes**:
- Added `language` parameter to `transcribe_audio(audio_path, language=None)`
- Returns dict instead of string: `{text, language, confidence}`
- Passes language to Whisper for improved accuracy

**Updated Function**:
```python
def transcribe_audio(audio_path, language=None):
    """
    Args:
        audio_path: Path to WAV file
        language: Optional ISO 639-1 language code
    
    Returns:
        {"text": "...", "language": "...", "confidence": ...}
    """
```

---

#### `backend/database.py` (UPDATED, +70 lines)
**Purpose**: Extended vault with feedback storage  
**New Methods**:
- `store_feedback(log_id, rating, feedback_text)` → None
- `retrieve_and_decrypt_feedback()` → list[dict]

**New Table**:
```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY,
    log_id INTEGER,
    timestamp TEXT,
    rating INTEGER,
    feedback_text TEXT,
    nonce BLOB,
    ciphertext BLOB
)
```

**Usage**:
```python
from database import SecureVault
vault = SecureVault()
vault.store_feedback(log_id=123, rating=5, feedback_text="Great!")
feedback = vault.retrieve_and_decrypt_feedback()
```

---

#### `backend/server.py` (UPDATED, +100 lines)
**Purpose**: FastAPI endpoints with multilingual support  
**New Request Parameters** (on `/analyze`):
- `language` (optional) — User-specified ISO 639-1 code

**New Response Fields** (from `/analyze`):
- `language` (str | None) — Detected language code
- `language_name` (str | None) — Language name
- `translated` (bool) — Whether translation was performed

**New Endpoint**:
- `POST /feedback` — User feedback submission
  - Request: `FeedbackRequest` (log_id, rating, feedback_text)
  - Response: `FeedbackResponse` (status, message)

**Updated Workflow**:
1. Detect language from text
2. If audio: transcribe with detected language
3. Optional: translate if needed
4. Process with RAG + LLM
5. Store with language metadata
6. Accept feedback via `/feedback`

**Updated Imports**:
- Added `from lang_utils import ...`
- Added response models: `AnalyzeResponse`, `FeedbackRequest`, `FeedbackResponse`

---

#### `backend/config.py` (UPDATED, +6 settings)
**Purpose**: Configuration for multilingual features  
**New Settings**:
- `LLM_MULTILINGUAL_SUPPORT` (bool, env: `SANCTUARY_LLM_MULTILINGUAL`)
- `TRANSLATION_SERVICE` (str, env: `SANCTUARY_TRANSLATION_SERVICE`)
- `WHISPER_LANGUAGE_AUTO_DETECT` (bool, env: `SANCTUARY_WHISPER_AUTO_LANG`)
- `ENABLE_USER_FEEDBACK` (bool, env: `SANCTUARY_ENABLE_FEEDBACK`)
- `FEEDBACK_STORAGE` (str, env: `SANCTUARY_FEEDBACK_STORAGE`)

**Usage**:
```bash
# In .env
SANCTUARY_LLM_MULTILINGUAL=false
SANCTUARY_TRANSLATION_SERVICE=disabled
SANCTUARY_ENABLE_FEEDBACK=true
```

---

#### `backend/requirements.txt` (UPDATED)
**Added Dependency**:
- `langdetect==1.0.9` — Language detection library

**Optional Dependencies** (for local translation):
- `transformers>=4.30.0`
- `torch>=2.0.0`

---

## Testing Files

#### `backend/test_multilingual.py` (NEW, 500+ lines)
**Purpose**: Comprehensive test suite  
**Test Classes**:
1. `TestLanguageDetection` — Language detection (EN, ES, FR, ZH, etc.)
2. `TestWhisperLanguageMapping` — ISO ↔ Whisper name mapping
3. `TestLLMMultilingualSupport` — Translation routing logic
4. `TestAudioProcessing` — Whisper with language parameter
5. `TestDatabaseFeedback` — Feedback storage/retrieval
6. `TestFeedbackEndpoint` — `/feedback` endpoint validation
7. `TestAnalyzeEndpointMultilingual` — `/analyze` integration

**Run**:
```bash
pytest backend/test_multilingual.py -v
pytest backend/test_multilingual.py::TestLanguageDetection -v
```

---

#### `backend/validate_multilingual.py` (NEW, 300+ lines)
**Purpose**: Validation and diagnostics script  
**Checks**:
- Module imports (all new modules can be imported)
- Configuration defaults (new settings exist and are sensible)
- Language detection (basic tests with multiple languages)
- Database schema (feedback table created correctly)
- Response models (Pydantic models have required fields)

**Run**:
```bash
python backend/validate_multilingual.py
```

**Output**: Summary with ✅/❌ for each check

---

#### `backend/examples_multilingual.py` (NEW, 250+ lines)
**Purpose**: Reference examples and documentation  
**Examples**:
1. Multilingual text input (EN, ES, FR, DE, ZH)
2. Translation routing decisions
3. Translation simulation
4. API request/response simulation
5. Feedback collection flow
6. Database operations
7. Retrieval & analytics
8. Whisper audio with language
9. Configuration scenarios
10. Error handling

**Run**:
```bash
python backend/examples_multilingual.py
```

**Output**: Detailed walkthrough of all features

---

## Documentation Files

#### `MULTILINGUAL_GUIDE.md` (NEW, 450+ lines)
**Purpose**: Comprehensive feature guide  
**Sections**:
1. Overview
2. Language Detection API
3. Speech Processing with Language
4. Translation Pipeline
5. User Feedback Collection
6. Updated `/analyze` Endpoint
7. Configuration Summary
8. Dependencies
9. Testing
10. Implementation Checklist
11. Next Steps & Enhancements
12. Security & Privacy
13. Troubleshooting

**Audience**: Developers, DevOps engineers

---

#### `MULTILINGUAL_QUICKSTART.md` (NEW, 150 lines)
**Purpose**: Quick reference and 1-minute setup  
**Sections**:
1. 1-Minute Setup
2. Feature Overview
3. What Changed?
4. Configuration (Optional)
5. Testing
6. Frontend Example
7. Monitoring
8. Documentation Links
9. What's Next?

**Audience**: Everyone (quick start)

---

#### `MULTILINGUAL_DEPLOYMENT_CHECKLIST.md` (NEW, 280 lines)
**Purpose**: Step-by-step deployment guide  
**Sections**:
1. Pre-Deployment
2. Code Changes Summary
3. API Changes
4. Frontend Integration
5. Backward Compatibility
6. Monitoring & Logging
7. Performance Considerations
8. Rollback Plan
9. Testing Checklist
10. Post-Deployment
11. Support Documentation

**Audience**: DevOps, QA, release managers

---

#### `IMPLEMENTATION_SUMMARY.md` (NEW, 350 lines)
**Purpose**: Executive summary of implementation  
**Sections**:
1. What Was Implemented (11 features)
2. Files Modified/Created (breakdown)
3. Feature Checklist (comprehensive)
4. Backward Compatibility
5. Performance Impact
6. Security & Privacy
7. Next Steps (for team)
8. Configuration Template
9. Testing Commands
10. Monitoring & Observability
11. Documentation Index
12. Summary

**Audience**: Project managers, team leads, developers

---

## Directory Structure

```
gemma4/
├── backend/
│   ├── lang_utils.py                    ✨ NEW
│   ├── audio_processing.py              🔄 UPDATED
│   ├── database.py                      🔄 UPDATED
│   ├── server.py                        🔄 UPDATED
│   ├── config.py                        🔄 UPDATED
│   ├── requirements.txt                 🔄 UPDATED
│   ├── test_multilingual.py             ✨ NEW
│   ├── validate_multilingual.py         ✨ NEW
│   ├── examples_multilingual.py         ✨ NEW
│   ├── (other existing files...)
│
├── MULTILINGUAL_GUIDE.md                ✨ NEW
├── MULTILINGUAL_QUICKSTART.md           ✨ NEW
├── MULTILINGUAL_DEPLOYMENT_CHECKLIST.md ✨ NEW
├── IMPLEMENTATION_SUMMARY.md            ✨ NEW
├── README.md                            (existing)
└── ...
```

**Legend**:
- ✨ NEW — Newly created files
- 🔄 UPDATED — Modified existing files

---

## Integration Points

### 1. Client → `/analyze` Endpoint
```
User sends:
  - text (multilingual)
  - typing (JSON)
  - audio (optional, any language)
  - language (optional override)

Server returns:
  - response (personalized therapy)
  - language (detected)
  - language_name (friendly name)
  - translated (if translation applied)
```

### 2. Client → `/feedback` Endpoint
```
User sends:
  - log_id (reference to analysis)
  - rating (1-5 stars)
  - feedback_text (comment)

Server returns:
  - status (success/disabled)
  - message (thank you message)
```

### 3. Backend Processing Flow
```
Input (multilingual text/audio)
  ↓
Language Detection (lang_utils.detect_language)
  ↓
Audio Transcription (audio_processing with language param)
  ↓
Translation Check (should_translate_for_llm)
  ↓
Optional Translation (lang_utils.translate_text)
  ↓
RAG + LLM Processing (existing pipeline)
  ↓
Response Generation
  ↓
Vault Storage (database.encrypt_and_store with language metadata)
  ↓
Feedback Collection (vault.store_feedback)
```

---

## Configuration Files

### Environment Variables (Add to `.env`)
```bash
# Language Detection & Translation
SANCTUARY_LLM_MULTILINGUAL=false
SANCTUARY_TRANSLATION_SERVICE=disabled
SANCTUARY_WHISPER_AUTO_LANG=true

# User Feedback
SANCTUARY_ENABLE_FEEDBACK=true
SANCTUARY_FEEDBACK_STORAGE=vault
```

### Default Values
All settings have sensible defaults; environment variables are optional.

---

## Dependencies Added

### Required
- `langdetect==1.0.9` — Language detection (28+ languages)

### Optional
- `transformers>=4.30.0` — For local translation (M2M100)
- `torch>=2.0.0` — For local translation (M2M100)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | May 9, 2026 | Initial implementation: Language detection, audio support, feedback collection |

---

## Quick Links

| Purpose | File |
|---------|------|
| Language detection API | `backend/lang_utils.py` |
| Whisper integration | `backend/audio_processing.py` |
| Feedback storage | `backend/database.py` |
| Endpoints | `backend/server.py` |
| Configuration | `backend/config.py` |
| Tests | `backend/test_multilingual.py` |
| Validation | `backend/validate_multilingual.py` |
| Examples | `backend/examples_multilingual.py` |
| **Full Guide** | `MULTILINGUAL_GUIDE.md` |
| **Quick Start** | `MULTILINGUAL_QUICKSTART.md` |
| **Deployment** | `MULTILINGUAL_DEPLOYMENT_CHECKLIST.md` |
| **Summary** | `IMPLEMENTATION_SUMMARY.md` |

---

**Total Implementation**:
- **New Files**: 8
- **Modified Files**: 5
- **New Lines of Code**: ~1,500
- **Test Coverage**: 7 test classes, 25+ test cases
- **Documentation**: 4 comprehensive guides
- **Status**: ✅ Ready for testing & deployment

---

*Last Updated: May 9, 2026*
