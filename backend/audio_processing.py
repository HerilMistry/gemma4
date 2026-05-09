import whisper
import os

from config import Config

# Load the base model locally. 
# In a real environment, this will download the model weights to ~/.cache/whisper on the first run.
# 'base' or 'tiny' are good for edge devices.
MODEL_NAME = Config.WHISPER_MODEL_NAME
model = None

def get_whisper_model():
    global model
    if model is None:
        try:
            model = whisper.load_model(MODEL_NAME)
        except Exception as e:
            print(f"Error loading whisper: {e}")
    return model

def transcribe_audio(audio_path, language: str | None = None):
    """
    Transcribes audio file to text using local Whisper model.
    
    Args:
        audio_path: Path to the audio file.
        language: Optional ISO 639-1 language code (e.g., 'en', 'es', 'fr').
                 If None, Whisper will auto-detect the language.
    
    Returns:
        Dict with keys:
        - 'text': Transcribed text
        - 'language': Detected language code (if available)
        - 'confidence': Language detection confidence (if available)
    """
    if not os.path.exists(audio_path):
        return {"text": "", "language": None, "confidence": None}
        
    whisper_model = get_whisper_model()
    if whisper_model is None:
        return {"text": "[Error: Whisper model not loaded]", "language": None, "confidence": None}
    
    try:
        # Build transcribe kwargs
        transcribe_kwargs = {"audio_path": audio_path}
        
        if language:
            # Map ISO 639-1 to Whisper language names if needed
            # Whisper accepts both codes and names; ISO 639-1 codes work directly
            transcribe_kwargs["language"] = language
        
        result = whisper_model.transcribe(**transcribe_kwargs)
        
        return {
            "text": result.get("text", ""),
            "language": result.get("language"),
            "confidence": None,  # Whisper doesn't expose confidence directly
        }
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return {"text": f"[Transcription error: {str(e)}]", "language": None, "confidence": None}

