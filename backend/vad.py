"""
Sanctuary 3.0 — Silero VAD (Voice Activity Detection)
Uses ONNX Runtime for high-performance, local-only speech detection.
Ensures that the transcription engine only processes segments containing actual speech,
reducing noise and improving PII privacy.
"""

import numpy as np
import onnxruntime as ort
import librosa
import logging
from pathlib import Path

from config import Config

logger = logging.getLogger(__name__)

class SileroVAD:
    def __init__(self, model_path: str | None = None):
        if model_path is None:
            model_path = str(Path(Config.BASE_DIR) / "models" / "silero_vad.onnx")
        
        self.model_path = model_path
        self._session = None
        self._h = np.zeros((2, 1, 64)).astype('float32')
        self._c = np.zeros((2, 1, 64)).astype('float32')
        self._sample_rate = 16000

    def _init_session(self):
        if self._session is None:
            if not Path(self.model_path).exists():
                logger.warning("Silero VAD model not found at %s. VAD will be skipped.", self.model_path)
                return False
            self._session = ort.InferenceSession(self.model_path)
        return True

    def is_speech(self, audio_path: str, threshold: float = 0.5) -> bool:
        """
        Quickly check if the audio file contains any speech.
        """
        # Reset RNN states for every fresh audio stream check to avoid multi-request state leakage
        self._h = np.zeros((2, 1, 64)).astype('float32')
        self._c = np.zeros((2, 1, 64)).astype('float32')

        if not self._init_session():
            return True # Fallback to transcription if VAD unavailable
            
        try:
            # Load audio at 16kHz (Silero requirement)
            audio, _ = librosa.load(audio_path, sr=self._sample_rate)
            
            # Use only a portion if it's very long (first 3 seconds is usually enough for VAD)
            chunk_size = 512
            for i in range(0, len(audio), chunk_size):
                chunk = audio[i:i+chunk_size]
                if len(chunk) < chunk_size:
                    break
                    
                input_data = {
                    'input': chunk.reshape(1, -1).astype('float32'),
                    'sr': np.array([self._sample_rate], dtype='int64'),
                    'h': self._h,
                    'c': self._c
                }
                
                out, h, c = self._session.run(None, input_data)
                self._h, self._c = h, c
                
                if out > threshold:
                    return True
            return False
        except Exception as e:
            logger.error("VAD processing error: %s", e)
            return True

_vad_instance = None

def has_speech(audio_path: str) -> bool:
    global _vad_instance
    if _vad_instance is None:
        _vad_instance = SileroVAD()
    return _vad_instance.is_speech(audio_path)
