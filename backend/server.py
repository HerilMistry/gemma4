"""
Sanctuary 3.0 — FastAPI Server
The main orchestrator that wires together all engines.

Senior SDE Hardening (v3.1):
- Modular structure (Logic moved to core/)
- Async-safe database operations (anyio.to_thread)
- Centralized constants and prompts
- Robust crisis detection
- Integrated Positive Reframer (v3.1.1)
- SSE Streaming Support (v3.2)
"""

import json
import os
import logging
import tempfile
import anyio

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from config import Config
from core.constants import (
    SYSTEM_INSTRUCTION, 
    FEW_SHOT_EXAMPLES, 
    FALLBACK_RESPONSE, 
    CRISIS_RESPONSE, 
    EMPTY_INPUT_RESPONSE
)
from core.crisis import is_crisis, is_severe
from reframer import Reframer

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
    logger.info("=== Sanctuary 3.2 Starting (Streaming + Hardened) ===")

    # Pre-load LLM (Modular Provider)
    from llm_engine import get_inference_orchestrator
    try:
        get_inference_orchestrator()._ensure_model_loaded()
    except Exception as e:
        logger.warning("LLM not loaded: %s", e)

    # Pre-load RAG
    from rag_engine import get_collection
    try:
        get_collection()
    except Exception as e:
        logger.warning("RAG engine failed to initialize: %s", e)

    logger.info("=== Sanctuary 3.2 Ready ===")
    yield
    logger.info("=== Sanctuary 3.2 Shutting Down ===")


# --- App Setup ---
app = FastAPI(
    title="Sanctuary",
    description="Zero-telemetry CBT reasoning engine powered by Gemma",
    version="3.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
from database import SecureVault
vault = SecureVault()
reframer = Reframer()


# --- Response Models ---
class HealthResponse(BaseModel):
    status: str
    engine: str
    version: str


class AnalyzeResponse(BaseModel):
    response: str
    route_used: str
    language: str | None = None
    language_name: str | None = None
    translated: bool = False
    distortions: list[dict] | None = None
    telemetry: str = "Encrypted via AES-256 GCM"


class FeedbackRequest(BaseModel):
    log_id: int | None = None
    rating: int | None = None
    feedback_text: str | None = None


class FeedbackResponse(BaseModel):
    status: str
    message: str


# --- Endpoints ---
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", engine="llama-cpp-python", version="3.2.0")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    text: str = Form(""),
    typing: str = Form("{}"),
    audio: UploadFile | None = File(None),
    language: str | None = Form(None),
    history: str = Form("[]"),
):
    """Main analysis endpoint (Synchronous - Backward Compatible)."""
    from lang_utils import detect_language, translate_text, should_translate_for_llm
    
    # 1. Parse typing features
    try:
        typing_features = json.loads(typing)
    except:
        typing_features = {}

    audio_features = None
    detected_language = None
    was_translated = False
    language_name = None

    # 2. Detect language
    if text.strip():
        detected_language, _ = detect_language(text)
    
    # 3. Process audio
    if audio and audio.filename:
        from audio_processing import transcribe_audio
        from acoustic import extract_acoustic_features

        suffix = os.path.splitext(audio.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name

        try:
            whisper_lang = language or detected_language
            transcription_result = transcribe_audio(tmp_path, language=whisper_lang)
            transcribed_text = transcription_result.get("text", "")
            
            if transcribed_text:
                text = f"{text} {transcribed_text}".strip()
                if transcription_result.get("language"):
                    detected_language = transcription_result.get("language")
            
            audio_features = extract_acoustic_features(tmp_path)
        except Exception as e:
            logger.error("Audio processing failed: %s", e)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # 4. Input validation
    if not text.strip():
        return AnalyzeResponse(
            response=EMPTY_INPUT_RESPONSE,
            route_used="none",
            language=detected_language,
        )

    # 5. Translation
    original_text = text
    if detected_language and should_translate_for_llm(detected_language):
        translated_text, success = translate_text(text, detected_language, "en")
        if success:
            text = translated_text
            was_translated = True

    if detected_language:
        from lang_utils import WHISPER_LANGUAGE_MAP
        language_name = WHISPER_LANGUAGE_MAP.get(detected_language, "unknown")

    # 6. Crisis Check (Hardened)
    if is_crisis(text):
        return AnalyzeResponse(
            response=CRISIS_RESPONSE,
            route_used="crisis",
            language=detected_language,
            language_name=language_name,
        )

    # 7. Reframer: Detect cognitive distortions
    detected_distortions = reframer.detect_distortions(text)
    reframing_instructions = reframer.get_reframing_instructions(detected_distortions)

    # 8. RAG & Routing
    from rag_engine import retrieve_context
    clinical_context = retrieve_context(text)

    from router import CactusEdgeRouter
    route = CactusEdgeRouter.route_task(text, audio_features, typing_features)

    # 9. Prompt Building
    try:
        history_list = json.loads(history)
    except:
        history_list = []
        
    prompt = _build_prompt(text, clinical_context, typing_features, route, reframing_instructions, history_list)

    # 10. Generation (Sync)
    from llm_engine import generate_response
    try:
        llm_response = generate_response(prompt)
    except Exception as e:
        logger.error("LLM generation failed: %s", e)
        llm_response = FALLBACK_RESPONSE

    # 11. Secure Storage
    try:
        vault_data = {
            "original_text": original_text,
            "processed_text": text,
            "detected_language": detected_language,
            "was_translated": was_translated,
            "audio_features": audio_features,
            "typing_features": typing_features,
            "route": route,
            "distortions": detected_distortions,
            "response": llm_response,
            "streamed": False
        }
        await anyio.to_thread.run_sync(vault.encrypt_and_store, vault_data)
    except Exception as e:
        logger.error("Vault storage failed: %s", e)

    return AnalyzeResponse(
        response=llm_response,
        route_used=route,
        language=detected_language,
        language_name=language_name,
        translated=was_translated,
        distortions=detected_distortions,
    )


@app.post("/analyze/stream")
async def analyze_stream(
    text: str = Form(""),
    typing: str = Form("{}"),
    audio: UploadFile | None = File(None),
    language: str | None = Form(None),
    history: str = Form("[]"),
):
    """
    Industry-grade SSE streaming endpoint.
    Strictly enforces Safety Hierarchy: Triage (Crisis/RAG) happens BEFORE the stream begins.
    """
    from lang_utils import detect_language, translate_text, should_translate_for_llm
    from llm_engine import get_inference_orchestrator
    
    # --- 1. Triage & Safety Hierarchy (Blocking) ---
    try:
        typing_features = json.loads(typing)
    except:
        typing_features = {}

    audio_features = None
    detected_language = None
    
    if text.strip():
        detected_language, _ = detect_language(text)

    # Audio Processing
    if audio and audio.filename:
        from audio_processing import transcribe_audio
        from acoustic import extract_acoustic_features
        suffix = os.path.splitext(audio.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name
        try:
            res = transcribe_audio(tmp_path, language=language or detected_language)
            if res.get("text"):
                text = f"{text} {res['text']}".strip()
                detected_language = res.get("language") or detected_language
            audio_features = extract_acoustic_features(tmp_path)
        finally:
            if os.path.exists(tmp_path): os.unlink(tmp_path)

    # Validation & Crisis Gate
    if not text.strip():
        return {"response": EMPTY_INPUT_RESPONSE}
    
    if is_crisis(text):
        return {"response": CRISIS_RESPONSE, "route": "crisis"}

    # RAG & Routing
    from rag_engine import retrieve_context
    from router import CactusEdgeRouter
    clinical_context = retrieve_context(text)
    route = CactusEdgeRouter.route_task(text, audio_features, typing_features)
    
    detected_distortions = reframer.detect_distortions(text)
    reframing_instructions = reframer.get_reframing_instructions(detected_distortions)

    try:
        history_list = json.loads(history)
    except:
        history_list = []

    prompt = _build_prompt(text, clinical_context, typing_features, route, reframing_instructions, history_list)

    # --- 2. Streaming Delivery (Async) ---
    async def event_generator():
        orchestrator = get_inference_orchestrator()
        full_response = ""
        
        # Initial metadata packet
        yield f"data: {json.dumps({'type': 'metadata', 'route': route, 'distortions': detected_distortions})}\n\n"
        
        # Token stream
        for token in orchestrator.generate_stream(prompt):
            full_response += token
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
            await anyio.sleep(0.01)

        # Final storage packet
        vault_data = {
            "original_text": text,
            "detected_language": detected_language,
            "route": route,
            "distortions": detected_distortions,
            "response": full_response,
            "streamed": True
        }
        await anyio.to_thread.run_sync(vault.encrypt_and_store, vault_data)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _build_prompt(text: str, clinical_context: str, typing_features: dict, route: str, reframing_instructions: str, history: list = []) -> str:
    """Build the structured prompt for Gemma."""
    prompt = (
        "<start_of_turn>user\n"
        f"INSTRUCTIONS: {SYSTEM_INSTRUCTION}\n\n"
        f"CURRENT STRATEGY: {reframing_instructions}<end_of_turn>\n"
        "<start_of_turn>model\n"
        "Understood. I will act as Sanctuary, providing empathetic Socratic guidance.<end_of_turn>\n"
    )
    
    prompt += f"{FEW_SHOT_EXAMPLES}\n"
    
    for msg in history[-4:]:
        role = "user" if msg.get("role") == "user" else "model"
        content = msg.get("text", "")
        prompt += f"<start_of_turn>{role}\n{content}<end_of_turn>\n"
    
    prompt += "<start_of_turn>user\n"
    if is_severe(text, typing_features, Config.TYPING_INTERVAL_STRESS_THRESHOLD):
        if "Crisis" not in clinical_context or is_crisis(text):
            prompt += f"[Clinical Context: {clinical_context}]\n"
        
    prompt += f"{text}<end_of_turn>\n"
    prompt += "<start_of_turn>model\n"
    return prompt


@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """Store user feedback."""
    if not Config.ENABLE_USER_FEEDBACK:
        return FeedbackResponse(status="disabled", message="Feedback disabled.")

    try:
        await anyio.to_thread.run_sync(
            vault.store_feedback, 
            feedback.log_id, 
            feedback.rating, 
            feedback.feedback_text
        )
        return FeedbackResponse(status="success", message="Thank you for your feedback.")
    except Exception as e:
        logger.error("Feedback storage failed: %s", e)
        return FeedbackResponse(status="error", message="Failed to store feedback.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=Config.HOST, port=Config.PORT, reload=Config.DEBUG)
