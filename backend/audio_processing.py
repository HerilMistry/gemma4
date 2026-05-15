import whisper
import os
import logging

from config import Config
from vad import has_speech
from core.sanitizer import mask_text

logger = logging.getLogger(__name__)

# Load the base model locally. 
MODEL_NAME = Config.WHISPER_MODEL_NAME
model = None

def get_whisper_model():
    global model
    if model is None:
        try:
            model = whisper.load_model(MODEL_NAME)
        except Exception as e:
            logger.error(f"Error loading whisper: {e}")
    return model

def transcribe_audio(audio_path, language: str | None = None):
    """
    Transcribes audio file to text using local Whisper model.
    Pre-filters via Silero VAD to ensure privacy and save compute.
    """
    if not os.path.exists(audio_path):
        return {"text": "", "language": None, "confidence": None}

    # --- Premium Feature: Silero VAD ---
    try:
        if not has_speech(audio_path):
            logger.info("VAD: No speech detected in audio. Skipping transcription.")
            return {"text": "", "language": None, "confidence": None}
    except Exception as e:
        logger.warning(f"VAD failed: {e}. Proceeding with Whisper.")
        
    whisper_model = get_whisper_model()
    if whisper_model is None:
        return {"text": "[Error: Whisper model not loaded]", "language": None, "confidence": None}
    
    try:
        transcribe_kwargs = {}
        if language:
            transcribe_kwargs["language"] = language
        
        result = whisper_model.transcribe(audio_path, **transcribe_kwargs)
        raw_text = result.get("text", "").strip()
        
        # --- Premium Feature: PII Masking ---
        sanitized_text = mask_text(raw_text)
        
        return {
            "text": sanitized_text,
            "language": result.get("language"),
            "confidence": None,
        }
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return {"text": f"[Transcription error: {str(e)}]", "language": None, "confidence": None}
