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

def transcribe_audio(audio_path):
    """Transcribes audio file to text using local Whisper model."""
    if not os.path.exists(audio_path):
        return ""
        
    whisper_model = get_whisper_model()
    if whisper_model is None:
        return "[Error: Whisper model not loaded]"
        
    result = whisper_model.transcribe(audio_path)
    return result["text"]
