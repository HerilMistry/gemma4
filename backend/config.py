"""
Sanctuary 3.0 — Centralized Configuration
All paths are resolved relative to this file's directory.
Every value can be overridden via environment variables.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Central configuration for the Sanctuary 3.0 backend."""

    # --- Server ---
    HOST = os.getenv("SANCTUARY_HOST", "127.0.0.1")
    PORT = int(os.getenv("SANCTUARY_PORT", "8000"))
    DEBUG = os.getenv("SANCTUARY_DEBUG", "true").lower() == "true"

    # --- LLM Engine (llama-cpp-python) ---
    # Place your .gguf file at: backend/models/sanctuary_cbt_final.gguf
    MODEL_PATH = Path(
        os.getenv("SANCTUARY_MODEL_PATH", str(BASE_DIR / "models" / "sanctuary_cbt_final.gguf"))
    )
    N_CTX = int(os.getenv("SANCTUARY_N_CTX", "2048"))
    N_GPU_LAYERS = int(os.getenv("SANCTUARY_N_GPU_LAYERS", "0"))  # 0 = CPU only
    MAX_TOKENS = int(os.getenv("SANCTUARY_MAX_TOKENS", "512"))

    # --- RAG Engine (ChromaDB + sentence-transformers) ---
    CHROMA_DB_PATH = os.getenv("SANCTUARY_CHROMA_PATH", str(BASE_DIR / "data" / "chroma_db"))
    EMBEDDING_MODEL = os.getenv("SANCTUARY_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    KAGGLE_DATASET_PATH = os.getenv("SANCTUARY_KAGGLE_DATA", str(BASE_DIR / "data" / "mental_health_diagnosis_treatment_.csv"))


    # --- Security Vault (AES-256 GCM) ---
    DB_PATH = os.getenv("SANCTUARY_DB_PATH", str(BASE_DIR / "data" / "sanctuary.db"))
    KEY_FILE = os.getenv("SANCTUARY_KEY_FILE", str(BASE_DIR / "data" / "aes_key.bin"))

    # --- Audio Processing ---
    WHISPER_MODEL_NAME = os.getenv("SANCTUARY_WHISPER_MODEL", "small")
    UPLOAD_FOLDER = os.getenv("SANCTUARY_UPLOAD_FOLDER", str(BASE_DIR / "uploads"))

    # --- Cactus Edge Router Thresholds ---
    TYPING_INTERVAL_STRESS_THRESHOLD = int(
        os.getenv("SANCTUARY_TYPING_THRESHOLD", "400")
    )
    TEXT_COMPLEXITY_WORD_COUNT = int(
        os.getenv("SANCTUARY_COMPLEXITY_WORDS", "20")
    )

    # --- Multilingual Support ---
    LLM_MULTILINGUAL_SUPPORT = os.getenv("SANCTUARY_LLM_MULTILINGUAL", "false").lower() == "true"
    TRANSLATION_SERVICE = os.getenv("SANCTUARY_TRANSLATION_SERVICE", "disabled")
    # Options: "disabled" (no translation), "local" (M2M100 model, heavy), "cloud" (not implemented yet)
    WHISPER_LANGUAGE_AUTO_DETECT = os.getenv("SANCTUARY_WHISPER_AUTO_LANG", "true").lower() == "true"

    # --- Feedback & Analytics ---
    ENABLE_USER_FEEDBACK = os.getenv("SANCTUARY_ENABLE_FEEDBACK", "true").lower() == "true"
    FEEDBACK_STORAGE = os.getenv("SANCTUARY_FEEDBACK_STORAGE", "vault")  # "vault" or "separate_db"
