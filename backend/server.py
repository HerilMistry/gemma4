"""
Sanctuary 3.0 — FastAPI Server
The main orchestrator that wires together all engines:
  Input → Audio Transcription → Acoustic Biomarkers → RAG Grounding → Edge Router → LLM → Encrypt → Respond

Replaces the old Flask app.py with:
- Proper request validation via Pydantic
- Async file handling with tempfile (no leaked uploads)
- Auto-generated API docs at /docs
- Health check endpoint
- Multilingual support (text + speech)
- User feedback collection
"""

import json
import os
import logging
import tempfile

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("sanctuary")


# --- Lifespan: Pre-load heavy models on startup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models into memory once at startup, not on first request."""
    logger.info("=== Sanctuary 3.0 Starting ===")

    # Pre-load LLM (this takes 10-30s on CPU)
    from llm_engine import get_llm
    try:
        get_llm()
    except FileNotFoundError as e:
        logger.warning("LLM not loaded: %s", e)
        logger.warning("The /analyze endpoint will return fallback responses.")

    # Pre-load RAG (downloads embedding model on first run, ~80MB)
    from rag_engine import get_collection
    try:
        get_collection()
    except Exception as e:
        logger.warning("RAG engine failed to initialize: %s", e)

    logger.info("=== Sanctuary 3.0 Ready ===")
    yield
    logger.info("=== Sanctuary 3.0 Shutting Down ===")


# --- App Setup ---
app = FastAPI(
    title="Sanctuary",
    description="Zero-telemetry CBT reasoning engine powered by Gemma",
    version="3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, lock this to your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-init the vault (no side effects until first use)
from database import SecureVault
vault = SecureVault()


# --- Response Models ---
class HealthResponse(BaseModel):
    status: str
    engine: str
    version: str


class AnalyzeResponse(BaseModel):
    response: str
    route_used: str
    language: str | None = None  # Detected language code
    language_name: str | None = None  # Language name (e.g., "spanish")
    translated: bool = False  # Whether translation was performed
    telemetry: str = "Encrypted via AES-256 GCM"


class FeedbackRequest(BaseModel):
    log_id: int | None = None  # Reference to the original analysis log
    rating: int | None = None  # Numeric rating (1-5, etc.)
    feedback_text: str | None = None  # Free-form feedback


class FeedbackResponse(BaseModel):
    status: str
    message: str


# --- Endpoints ---
@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint for deployment verification."""
    return HealthResponse(status="ok", engine="llama-cpp-python", version="3.0")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    text: str = Form(""),
    typing: str = Form("{}"),
    audio: UploadFile | None = File(None),
    language: str | None = Form(None),  # Optional: user-specified language code
):
    """
    Main analysis endpoint. Accepts multimodal input:
    - text: The user's journal entry
    - typing: JSON string with avg_interval in ms
    - audio: Optional WAV file for transcription + acoustic analysis
    - language: Optional ISO 639-1 language code for Whisper (e.g., 'en', 'es', 'fr')
    """
    from lang_utils import detect_language, translate_text, should_translate_for_llm, get_whisper_language
    
    # 1. Parse typing features
    try:
        typing_features = json.loads(typing)
    except (json.JSONDecodeError, TypeError):
        typing_features = {}

    audio_features = None
    detected_language = None
    was_translated = False
    language_name = None

    # 2. Detect language from text input
    if text.strip():
        detected_language, _ = detect_language(text)
        logger.info("Detected text language: %s", detected_language)
    
    # 3. Process audio (if provided)
    if audio and audio.filename:
        from audio_processing import transcribe_audio
        from acoustic import extract_acoustic_features

        # Write to a temp file that auto-cleans (no leaked uploads)
        suffix = os.path.splitext(audio.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Use detected language or user-specified language for Whisper
            whisper_lang = language or detected_language
            
            transcription_result = transcribe_audio(tmp_path, language=whisper_lang)
            transcribed_text = transcription_result.get("text", "")
            audio_detected_language = transcription_result.get("language")
            
            if transcribed_text:
                text = f"{text} {transcribed_text}".strip()
                # Update detected_language from audio if more reliable
                if audio_detected_language:
                    detected_language = audio_detected_language
                    logger.info("Updated language from audio: %s", detected_language)
            
            audio_features = extract_acoustic_features(tmp_path)
        except Exception as e:
            logger.error("Audio processing failed: %s", e)
        finally:
            # Always clean up, even if processing crashes
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # 4. Validate we have something to analyze
    if not text.strip():
        return AnalyzeResponse(
            response="Please share what's on your mind. I'm here to listen.",
            route_used="none",
            language=detected_language,
        )

    # 5. Optional: Translate text if LLM doesn't support the detected language
    original_text = text
    if detected_language and should_translate_for_llm(detected_language):
        logger.info("Translating from %s to English for LLM processing", detected_language)
        translated_text, translation_success = translate_text(text, detected_language, "en")
        if translation_success:
            text = translated_text
            was_translated = True
            logger.info("Translation successful")
        else:
            logger.warning("Translation failed; using original text")

    # 6. Retrieve language name for response
    if detected_language:
        from lang_utils import WHISPER_LANGUAGE_MAP
        language_name = WHISPER_LANGUAGE_MAP.get(detected_language, "unknown")

    # 7. RAG: Retrieve clinical grounding context
    from rag_engine import retrieve_context
    clinical_context = retrieve_context(text)

    # 8. Router: Determine analysis depth
    from router import CactusEdgeRouter
    route = CactusEdgeRouter.route_task(text, audio_features, typing_features)

    # 9. Build the Gemma prompt with clinical grounding
    prompt = _build_prompt(text, clinical_context, typing_features, audio_features, route)

    # 10. Generate LLM response
    from llm_engine import generate_response
    try:
        if _is_crisis(text):
            llm_response = (
                "I hear you, and your safety is the most important thing right now. "
                "I am an AI, not a crisis professional. Please reach out to a safe resource like the "
                "988 Suicide & Crisis Lifeline (call/text 988) or go to the nearest emergency room. "
                "You don't have to carry this alone."
            )
        else:
            llm_response = generate_response(prompt)
    except Exception as e:
        logger.error("LLM generation failed: %s", e)
        llm_response = (
            "I hear you, and I want to help. I'm experiencing a temporary issue "
            "processing your thoughts right now. Could you try sharing again?"
        )

    # 11. Encrypt and store (zero telemetry) with language metadata
    log_entry_id = None
    try:
        # Store data and track the log ID for feedback reference
        vault_data = {
            "original_text": original_text,
            "processed_text": text,
            "detected_language": detected_language,
            "was_translated": was_translated,
            "audio_features": audio_features,
            "typing_features": typing_features,
            "route": route,
            "response": llm_response,
        }
        vault.encrypt_and_store(vault_data)
        logger.info("Vault entry stored with language: %s, translated: %s", detected_language, was_translated)
    except Exception as e:
        logger.error("Vault encryption failed: %s", e)

    return AnalyzeResponse(
        response=llm_response,
        route_used=route,
        language=detected_language,
        language_name=language_name,
        translated=was_translated,
    )


FEW_SHOT_EXAMPLES = """<start_of_turn>user
I feel like I'm failing at everything because I missed one deadline.<end_of_turn>
<start_of_turn>model
Sanctuary: It sounds like you're carrying a lot of weight from that one missed deadline. When we feel overwhelmed, it's easy to fall into "overgeneralization"—where one mistake feels like a total failure. If you look at your week as a whole, what are some tasks you completed successfully, even small ones?<end_of_turn>
<start_of_turn>user
My friend didn't text back, they probably hate me now.<end_of_turn>
<start_of_turn>model
Sanctuary: I can hear the anxiety in your thought; it's painful to feel ignored by someone you care about. However, jumping to the conclusion that they "hate" you might be "mind reading." What are three other possible reasons they haven't replied yet that have nothing to do with their feelings for you?<end_of_turn>"""




def _is_crisis(text: str) -> bool:
    """Detect if the user is in a crisis state (Self-harm, etc)."""
    crisis_keywords = [
        "suicide", "harm", "kill", "end it", "die", "hurt myself", 
        "stop forever", "want to die", "can't take the pressure", "don't want to live",
        "everything to stop"
    ]
    return any(kw in text.lower() for kw in crisis_keywords)


def _is_severe(text: str, typing_features: dict) -> bool:
    """Detect if the situation warrants RAG injection (High stress)."""
    stress_keywords = ["hate", "desperate", "angry", "crying", "alone", "failure"]
    keyword_match = any(kw in text.lower() for kw in stress_keywords)
    
    # Check typing cadence if available
    high_stress_typing = typing_features.get("avg_interval", 500) < Config.TYPING_INTERVAL_STRESS_THRESHOLD
    
    return keyword_match or high_stress_typing

def _build_prompt(
    text: str,
    clinical_context: str,
    typing_features: dict,
    audio_features: dict | None,
    route: str,
) -> str:
    """
    Build the full prompt string using proper multi-turn formatting.
    """
    # 1. System Instruction (Universal Persona)
    prompt = (
        "<start_of_turn>user\n"
        "You are Sanctuary, a Socratic CBT reasoning engine. Your role is to identify "
        "cognitive distortions and ask gentle, empathetic questions to help the user reframe. "
        "Never lecture; always guide. Respond in 2-3 sentences.<end_of_turn>\n"
    )
    
    # 2. History Primes (Properly tagged)
    prompt += f"{FEW_SHOT_EXAMPLES}\n"
    
    # 3. Current User Turn
    prompt += f"<start_of_turn>user\n"
    if _is_severe(text, typing_features):
        prompt += f"[Clinical Context: {clinical_context}]\n"
    prompt += f"{text}<end_of_turn>\n"
    
    # 4. Model Response Start
    prompt += "<start_of_turn>model\nSanctuary:"
    
    return prompt


# --- Feedback Endpoint ---
@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """
    Store user feedback on a previous response.
    
    This endpoint allows users to provide ratings and comments,
    which are encrypted and stored for analytics and future RL improvements.
    
    Args:
        feedback: FeedbackRequest with optional log_id, rating, feedback_text.
    
    Returns:
        FeedbackResponse confirming storage.
    """
    if not Config.ENABLE_USER_FEEDBACK:
        return FeedbackResponse(
            status="disabled",
            message="Feedback collection is currently disabled.",
        )

    try:
        vault.store_feedback(
            log_id=feedback.log_id,
            rating=feedback.rating,
            feedback_text=feedback.feedback_text,
        )
        logger.info(
            "Feedback stored: log_id=%s, rating=%s, text_len=%s",
            feedback.log_id,
            feedback.rating,
            len(feedback.feedback_text or "") if feedback.feedback_text else 0,
        )
        return FeedbackResponse(
            status="success",
            message="Thank you for your feedback. Your input helps us improve.",
        )
    except Exception as e:
        logger.error("Failed to store feedback: %s", e)
        return FeedbackResponse(
            status="error",
            message="We encountered an issue storing your feedback. Please try again later.",
        )


# --- Entry point ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=Config.HOST, port=Config.PORT, reload=Config.DEBUG)
