# Quick Start: Multilingual & Feedback

## 1-Minute Setup

```bash
# 1. Install langdetect
pip install langdetect

# 2. Add to .env
echo "SANCTUARY_ENABLE_FEEDBACK=true" >> backend/.env
echo "SANCTUARY_TRANSLATION_SERVICE=disabled" >> backend/.env

# 3. Restart server
# (Database migration happens automatically on first run)

# 4. Test it
curl -X POST http://localhost:8000/analyze \
  -F "text=Me siento ansioso" \
  -F "typing={}"
```

**Expected Response**:
```json
{
    "response": "Sanctuary: I hear you...",
    "route_used": "heavy_core",
    "language": "es",
    "language_name": "spanish",
    "translated": false,
    "telemetry": "Encrypted via AES-256 GCM"
}
```

---

## Feature Overview

### 1. Automatic Language Detection

Any input text automatically detected (EN, ES, FR, DE, ZH, JA, etc.). Language code in response.

### 2. Whisper Audio Accuracy

If user sends audio, system passes detected language to Whisper for better transcription.

### 3. User Feedback Collection

Users can rate responses (1-5 stars) and leave comments. Stored encrypted.

```bash
# Send feedback
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "log_id": 123,
    "rating": 5,
    "feedback_text": "Really helpful!"
  }'
```

---

## What Changed?

| Component | Change | Impact |
|-----------|--------|--------|
| `/analyze` endpoint | +3 response fields | Backward compatible |
| `/analyze` request | +1 optional param | Backward compatible |
| Database | +1 feedback table | Auto-created, safe |
| Response time | ~50ms slower | Language detection only |

---

## Configuration (Optional)

```bash
# Enable/disable features
SANCTUARY_ENABLE_FEEDBACK=true          # Collect user ratings
SANCTUARY_TRANSLATION_SERVICE=disabled  # "disabled" or "local" (local = slow)
SANCTUARY_LLM_MULTILINGUAL=false        # "true" if LLM speaks multiple languages
```

---

## Testing

```bash
# Run all tests
pytest backend/test_multilingual.py -v

# Or validate without pytest
python backend/validate_multilingual.py
```

---

## Frontend Example

```javascript
// 1. Call /analyze with optional language override
const response = await fetch("/analyze", {
    method: "POST",
    body: new FormData({
        text: "Me siento ansioso",
        typing: "{}",
        language: "es"  // Optional
    })
});

const data = await response.json();
console.log(`Response in ${data.language_name}`);

// 2. User rates response
const userRating = 5;
await fetch("/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        log_id: data.log_id,
        rating: userRating,
        feedback_text: "Helpful!"
    })
});
```

---

## Monitoring

```bash
# Check feedback collection
python -c "
from database import SecureVault
v = SecureVault()
feedback = v.retrieve_and_decrypt_feedback()
print(f'Total feedback: {len(feedback)}')
ratings = [f['rating'] for f in feedback if f['rating']]
print(f'Avg rating: {sum(ratings)/len(ratings):.1f}/5' if ratings else 'No ratings')
"
```

---

## Documentation

- **Full Guide**: `MULTILINGUAL_GUIDE.md`
- **API Docs**: `MULTILINGUAL_GUIDE.md` section 2-5
- **Deployment**: `MULTILINGUAL_DEPLOYMENT_CHECKLIST.md`
- **Troubleshooting**: `MULTILINGUAL_GUIDE.md` section 12

---

## What's Next?

### Short-term (1-2 weeks)
- Collect feedback data
- Monitor language detection accuracy
- Expand multilingual RAG content

### Medium-term (1-2 months)
- Add feedback analytics dashboard
- Deploy multilingual LLM (if available)
- A/B test response styles by language

### Long-term (2-3 months)
- Integrate lightweight RL using feedback
- Implement contextual bandits for personalization
- Add clinician dashboard for feedback review

---

**Questions?** See `MULTILINGUAL_GUIDE.md` or run `python backend/validate_multilingual.py` for diagnostics.
