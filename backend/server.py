"""
Sanctuary 3.0 — FastAPI Server
Industry Standard (v3.2.8): Full Endpoint Suite
"""

import json
import os
import logging
import tempfile
import anyio
import gc
import uuid
from pathlib import Path
from pydantic import BaseModel

from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
from core.sanitizer import PIISanitizer
from memory import retrieve_past_memories, summarize_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("sanctuary")
inference_semaphore = anyio.Semaphore(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from vad import SileroVAD
        SileroVAD()._init_session()
    except ImportError: pass
    except Exception: pass
    
    try: 
        from llm_engine import get_inference_orchestrator
        get_inference_orchestrator()._ensure_model_loaded()
    except Exception: pass
    
    try: 
        from rag_engine import get_collection
        get_collection()
    except Exception: pass
    yield

app = FastAPI(title="Sanctuary", version="3.2.8", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

from database import SecureVault
vault = SecureVault()
reframer = Reframer()

class FeedbackRequest(BaseModel):
    log_id: int | None = None
    rating: int
    feedback_text: str | None = None

class AnalyzeResponse(BaseModel):
    response: str
    language: str | None = None
    language_name: str | None = None
    translated: bool | None = None
    route_used: str | None = None
    route: str | None = None
    distortions: list[str] | None = None
    session_id: str | None = None

class FeedbackResponse(BaseModel):
    status: str
    message: str | None = None

# --- Endpoints ---

@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.2.8", "mode": "industry-grade"}

@app.get("/sessions")
async def list_sessions():
    try: return await anyio.to_thread.run_sync(vault.list_sessions)
    except: return []

@app.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    try: return await anyio.to_thread.run_sync(vault.retrieve_session_history, session_id)
    except: raise HTTPException(status_code=404, detail="Session not found")

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    text: str = Form(""),
    typing: str = Form("{}"),
    language: str | None = Form(None),
    history: str = Form("[]"),
    session_id: str | None = Form(None),
):
    from lang_utils import detect_language
    from llm_engine import get_inference_orchestrator
    from rag_engine import retrieve_context
    from router import CactusEdgeRouter

    active_session_id = session_id or str(uuid.uuid4())
    try: typing_features = json.loads(typing)
    except: typing_features = {}
    
    detected_lang = language
    if text.strip() and not detected_lang:
        detected_lang, _ = detect_language(text)

    text = PIISanitizer.sanitize(text)
    if not text.strip(): return {"response": EMPTY_INPUT_RESPONSE, "language": detected_lang}
    if is_crisis(text): return {"response": CRISIS_RESPONSE, "language": detected_lang, "route": "crisis"}

    orchestrator = get_inference_orchestrator()
    async with inference_semaphore:
        is_severe_state = is_severe(text, typing_features)
        hypothetical_doc = None
        if is_severe_state:
            hypothetical_doc = await anyio.to_thread.run_sync(orchestrator.generate_hyde, text)
        
        clinical_context = await anyio.to_thread.run_sync(retrieve_context, text, 2, hypothetical_doc)
        route = await anyio.to_thread.run_sync(CactusEdgeRouter.route_task, text, None, typing_features)
        detected_distortions = reframer.detect_distortions(text)
        reframing_instructions = reframer.get_reframing_instructions(detected_distortions)
        user_state = CactusEdgeRouter.get_user_state_summary(None, typing_features)
        past_memories = await anyio.to_thread.run_sync(retrieve_past_memories, text)

        try: history_list = json.loads(history)
        except: history_list = []
        messages = _build_messages(text, clinical_context, user_state, route, reframing_instructions, past_memories, history_list)
        
        response_text = await anyio.to_thread.run_sync(orchestrator.generate, messages)
        try:
            await anyio.to_thread.run_sync(vault.encrypt_and_store, {
                "original_text": text, "route": route, "distortions": detected_distortions, "response": response_text, "streamed": False
            }, active_session_id)
        except: pass

        return {"response": response_text, "language": detected_lang, "route": route, "distortions": detected_distortions, "session_id": active_session_id}

@app.post("/analyze/stream")
async def analyze_stream(
    request: Request,
    text: str = Form(""),
    typing: str = Form("{}"),
    audio: UploadFile | None = File(None),
    language: str | None = Form(None),
    history: str = Form("[]"),
    session_id: str | None = Form(None),
):
    from lang_utils import detect_language
    from llm_engine import get_inference_orchestrator
    from rag_engine import retrieve_context
    from router import CactusEdgeRouter
    
    active_session_id = session_id or str(uuid.uuid4())
    try: typing_features = json.loads(typing)
    except: typing_features = {}

    audio_features = None
    detected_language = language
    if text.strip() and not detected_language: 
        detected_language, _ = detect_language(text)

    if audio and audio.filename:
        from audio_processing import transcribe_audio
        from acoustic import extract_acoustic_features
        suffix = os.path.splitext(audio.filename)[1] or ".wav"
        async def _process_audio(data, sfx):
            with tempfile.NamedTemporaryFile(suffix=sfx, delete=False) as tmpf:
                tmpf.write(data)
                p = tmpf.name
            try:
                res = transcribe_audio(p, language or detected_language)
                feat = extract_acoustic_features(p)
                return res, feat
            finally:
                if os.path.exists(p): os.unlink(p)
        try:
            res, audio_features = await anyio.to_thread.run_sync(_process_audio, await audio.read(), suffix)
            if res.get("text"):
                text = f"{text} {res['text']}".strip()
                detected_language = res.get("language") or detected_language
        except: pass

    text = PIISanitizer.sanitize(text)
    typing_features = PIISanitizer.sanitize_biometrics(typing_features)

    if not text.strip(): return StreamingResponse(_single_token_gen(EMPTY_INPUT_RESPONSE), media_type="text/event-stream")
    if is_crisis(text): return StreamingResponse(_single_token_gen(CRISIS_RESPONSE, route="crisis"), media_type="text/event-stream")

    orchestrator = get_inference_orchestrator()
    async with inference_semaphore:
        is_severe_state = is_severe(text, typing_features)
        hypothetical_doc = None
        if is_severe_state:
            hypothetical_doc = await anyio.to_thread.run_sync(orchestrator.generate_hyde, text)
        
        clinical_context = await anyio.to_thread.run_sync(retrieve_context, text, 2, hypothetical_doc)
        route = await anyio.to_thread.run_sync(CactusEdgeRouter.route_task, text, audio_features, typing_features)
        detected_distortions = reframer.detect_distortions(text)
        reframing_instructions = reframer.get_reframing_instructions(detected_distortions)
        user_state = CactusEdgeRouter.get_user_state_summary(audio_features, typing_features)
        past_memories = await anyio.to_thread.run_sync(retrieve_past_memories, text)

        try: history_list = json.loads(history)
        except: history_list = []
        messages = _build_messages(text, clinical_context, user_state, route, reframing_instructions, past_memories, history_list)

        async def event_generator():
            full_response = ""
            yield f"data: {json.dumps({'type': 'metadata', 'route': route, 'distortions': detected_distortions, 'session_id': active_session_id})}\n\n"
            try:
                for token in orchestrator.generate_stream(messages):
                    if await request.is_disconnected(): break
                    full_response += token
                    yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
            except: yield f"data: {json.dumps({'type': 'token', 'text': ' [Core Error]'})}\n\n"
            try:
                await anyio.to_thread.run_sync(vault.encrypt_and_store, {
                    "original_text": text, "route": route, "distortions": detected_distortions, "response": full_response, "streamed": True
                }, active_session_id)
            except: pass
            yield "data: [DONE]\n\n"
            gc.collect()

        return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/sessions/{session_id}/summarize")
async def trigger_summarize(session_id: str):
    history = await anyio.to_thread.run_sync(vault.retrieve_session_history, session_id)
    if not history:
        raise HTTPException(status_code=404, detail="No history found for this session")
    summary = await anyio.to_thread.run_sync(summarize_session, session_id, history)
    return {"status": "success", "summary": summary}

@app.post("/feedback", response_model=FeedbackResponse)
async def store_feedback(feedback: FeedbackRequest):
    if not Config.ENABLE_USER_FEEDBACK: return {"status": "disabled"}
    try:
        await anyio.to_thread.run_sync(vault.store_feedback, feedback.log_id, feedback.rating, feedback.feedback_text)
        return {"status": "success"}
    except: raise HTTPException(status_code=500, detail="Database error")

async def _single_token_gen(text: str, route: str = "fallback"):
    yield f"data: {json.dumps({'type': 'metadata', 'route': route, 'distortions': [], 'session_id': 'none'})}\n\n"
    yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"
    yield "data: [DONE]\n\n"

def _build_messages(text: str, clinical_context: str, user_state: str, route: str, reframing_instructions: str, past_memories: str = "", history: list = []) -> list:
    messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    if reframing_instructions: 
        messages[0]["content"] += f"\n\nSTRATEGY: {reframing_instructions}"
    if user_state:
        messages[0]["content"] += f"\n\nUSER EMOTIONAL STATE (via Biometrics): {user_state}. Adjust your tone accordingly (e.g., be more grounding if high stress detected)."
    if past_memories:
        messages[0]["content"] += f"\n\nLONG-TERM MEMORY (Relevant Past Themes):\n{past_memories}\nUse this for continuity."
    
    messages.extend(FEW_SHOT_EXAMPLES)
    for msg in history[-6:]:
        role = "user" if msg.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": msg.get("text", "")})
    
    user_content = ""
    if clinical_context: 
        user_content += f"[Clinical Grounding: {clinical_context}]\n"
    user_content += text
    messages.append({"role": "user", "content": user_content})
    return messages

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=Config.HOST, port=Config.PORT, reload=Config.DEBUG)
