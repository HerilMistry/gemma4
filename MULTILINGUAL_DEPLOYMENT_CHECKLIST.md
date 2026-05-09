# Deployment Checklist: Multilingual & Feedback Features

## Pre-Deployment

- [ ] Install dependencies: `pip install -r backend/requirements.txt`
- [ ] Review `MULTILINGUAL_GUIDE.md` for configuration options
- [ ] Set environment variables in `.env`:
  ```bash
  SANCTUARY_LLM_MULTILINGUAL=false
  SANCTUARY_TRANSLATION_SERVICE=disabled  # Keep disabled for privacy/performance
  SANCTUARY_WHISPER_AUTO_LANG=true
  SANCTUARY_ENABLE_FEEDBACK=true
  SANCTUARY_FEEDBACK_STORAGE=vault
  ```
- [ ] Run validation: `python backend/validate_multilingual.py`
- [ ] Run tests: `pytest backend/test_multilingual.py -v`

## Code Changes Summary

### New Files
- ✅ `backend/lang_utils.py` — Language detection & translation utilities
- ✅ `backend/test_multilingual.py` — Comprehensive test suite
- ✅ `MULTILINGUAL_GUIDE.md` — Full documentation
- ✅ `backend/validate_multilingual.py` — Validation script
- ✅ `MULTILINGUAL_DEPLOYMENT_CHECKLIST.md` — This file

### Modified Files
- ✅ `backend/requirements.txt` — Added `langdetect==1.0.9`
- ✅ `backend/config.py` — Added multilingual & feedback settings
- ✅ `backend/audio_processing.py` — Added `language` parameter to `transcribe_audio()`
- ✅ `backend/database.py` — Extended vault with `feedback` table & methods
- ✅ `backend/server.py` — Updated `/analyze` endpoint + new `/feedback` endpoint

## API Changes

### `/analyze` Endpoint

**New Request Parameters**:
- `language` (optional, string) — ISO 639-1 language code override (e.g., "es", "fr")

**New Response Fields**:
- `language` (string | null) — Detected language code
- `language_name` (string | null) — Language name (e.g., "spanish")
- `translated` (boolean) — Whether text was translated for LLM

**Example**:
```bash
curl -X POST http://localhost:8000/analyze \
  -F "text=Me siento ansioso" \
  -F "typing={}" \
  -F "language=es"
```

### New `/feedback` Endpoint

**Request**:
```http
POST /feedback
Content-Type: application/json

{
    "log_id": 123,
    "rating": 5,
    "feedback_text": "Helpful response!"
}
```

**Response**:
```json
{
    "status": "success",
    "message": "Thank you for your feedback. Your input helps us improve."
}
```

## Frontend Integration

### 1. Update `/analyze` Call

```javascript
// Pass detected language from user profile (optional)
const response = await fetch("/analyze", {
    method: "POST",
    body: formData,  // Includes text, typing, audio, and optionally language
});

const data = await response.json();

// Display language metadata (optional UI enhancement)
console.log(`Language: ${data.language} (${data.language_name})`);
if (data.translated) {
    console.log("Note: Response was translated for processing");
}
```

### 2. Add Feedback UI

```javascript
// Example: Show 5-star rating after response
const rating = await showRatingDialog();  // User selects 1-5 stars
const comment = await showFeedbackDialog();  // Optional comment

await fetch("/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        log_id: data.log_id,  // From /analyze response (if tracking)
        rating,
        feedback_text: comment
    })
});
```

## Backward Compatibility

- ✅ Existing `/analyze` calls without `language` parameter still work (auto-detect)
- ✅ Feedback collection is optional (disable via `SANCTUARY_ENABLE_FEEDBACK=false`)
- ✅ No breaking changes to existing response structure (new fields are additive)
- ✅ All new features are privacy-preserving (encrypted storage, optional translation disabled by default)

## Monitoring & Logging

### Enable Debug Logs

```bash
export SANCTUARY_DEBUG=true
```

### Check Language Detection

```bash
# Tail logs for language detection
tail -f /var/log/sanctuary.log | grep "language"
```

### Monitor Feedback Collection

```python
from database import SecureVault

vault = SecureVault()
feedback = vault.retrieve_and_decrypt_feedback()
print(f"Total feedback entries: {len(feedback)}")

# Analyze feedback
ratings = [f["rating"] for f in feedback if f["rating"]]
if ratings:
    avg_rating = sum(ratings) / len(ratings)
    print(f"Average rating: {avg_rating:.1f}/5")
```

## Performance Considerations

### With Translation Disabled (Recommended)
- **Additional latency**: ~50ms per request (language detection only)
- **Memory overhead**: Minimal (~10MB for language detection models)
- **Privacy**: ✅ No external calls

### With Translation Enabled (Local M2M100)
- **Additional latency**: 5-30 seconds per non-English request (on CPU)
- **Memory overhead**: ~2GB during translation
- **Privacy**: ✅ Fully offline (but slow)
- **Recommendation**: Only enable if absolutely necessary; consider GPU deployment

## Rollback Plan

If issues occur post-deployment:

1. **Disable new features without code rollback**:
   ```bash
   SANCTUARY_ENABLE_FEEDBACK=false
   SANCTUARY_TRANSLATION_SERVICE=disabled
   SANCTUARY_WHISPER_AUTO_LANG=false  # Revert to no language param
   ```

2. **Restore full compatibility**:
   - Revert to previous version of `server.py` if needed
   - Database migrations are backward-compatible (feedback table is independent)

3. **Data preservation**:
   - All encrypted logs and feedback remain safe in vault
   - Can re-process later after fixes

## Testing Checklist

Run before deploying to production:

```bash
# 1. Unit tests
pytest backend/test_multilingual.py -v

# 2. Validation script
python backend/validate_multilingual.py

# 3. Manual endpoint tests
curl -X POST http://localhost:8000/analyze \
  -F "text=Hola mundo" \
  -F "typing={}"

curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"rating": 5, "feedback_text": "Great!"}'

# 4. Language detection accuracy
python -c "from lang_utils import detect_language; print(detect_language('Hola'))"

# 5. Feedback retrieval
python -c "from database import SecureVault; v = SecureVault(); print(len(v.retrieve_and_decrypt_feedback()))"
```

## Post-Deployment

- [ ] Monitor error logs for language detection failures
- [ ] Track feedback submission rates (expect 10-30% of users to provide feedback)
- [ ] Validate that multilingual users experience improved accuracy
- [ ] Set up alerting for feedback collection errors
- [ ] Plan for feedback analytics dashboard (future sprint)

## Support Documentation

For users/developers:
- **Installation**: See `backend/README.md`
- **API Reference**: See `MULTILINGUAL_GUIDE.md`
- **Troubleshooting**: See `MULTILINGUAL_GUIDE.md` section 12
- **Architecture**: See `backend/server.py` docstrings

## Questions?

Refer to:
1. `MULTILINGUAL_GUIDE.md` — Comprehensive feature guide
2. `backend/test_multilingual.py` — Working code examples
3. `backend/validate_multilingual.py` — Validation & diagnostics
4. Source code comments in `backend/lang_utils.py`, `backend/server.py`
