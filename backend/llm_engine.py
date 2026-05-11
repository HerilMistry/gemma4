"""
Sanctuary 3.0 — Modular LLM Engine
Implements the InferenceProvider pattern to decouple the API from the specific LLM implementation.
Supports both synchronous and streaming generation with hardware-aware thread allocation.
"""

import logging
from pathlib import Path
from typing import Generator, Protocol
from llama_cpp import Llama

from config import Config
from cache_utils import LRUCache

logger = logging.getLogger(__name__)

# In-memory LRU cache for LLM outputs (process-local)
_llm_cache = LRUCache(capacity=Config.CACHE_SIZE_LLM)

class InferenceProvider(Protocol):
    """Protocol defining the interface for LLM inference engines."""
    def generate(self, prompt: str, max_tokens: int | None = None) -> str: ...
    def generate_stream(self, prompt: str, max_tokens: int | None = None) -> Generator[str, None, None]: ...


class LlamaCppProvider:
    """
    In-process GGUF inference via llama-cpp-python.
    Optimized for local CPU/GPU execution with thread awareness.
    """
    def __init__(self):
        self._llm: Llama | None = None
        self._model_path = Path(Config.MODEL_PATH)
        
    def _ensure_model_loaded(self):
        if self._llm is not None:
            return

        if not self._model_path.exists():
            raise FileNotFoundError(f"GGUF model not found at {self._model_path}")

        logger.info(
            "Loading Sanctuary Core (%s) with %d threads...", 
            self._model_path.name, 
            Config.N_THREADS
        )
        
        self._llm = Llama(
            model_path=str(self._model_path),
            n_threads=Config.N_THREADS,
            n_ctx=Config.N_CTX,
            n_gpu_layers=Config.N_GPU_LAYERS,
            verbose=False
        )
        logger.info("Sanctuary Core loaded successfully.")

    def generate(self, prompt: str, max_tokens: int | None = None) -> str:
        """Synchronous generation for backward compatibility."""
        self._ensure_model_loaded()
        # Try cache first (cache key includes prompt and generation params)
        cache_key = (prompt, max_tokens)
        cached = _llm_cache.get(cache_key)
        if cached is not None:
            logger.debug("LLM cache hit for prompt")
            return cached

        output = self._llm(
            prompt,
            max_tokens=max_tokens or Config.MAX_TOKENS,
            temperature=0.7,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["User:", "\n\n", "<end_of_turn>", "<eos>"]
        )
        result = output["choices"][0]["text"].strip()
        _llm_cache.set(cache_key, result)
        return result

    def generate_stream(self, prompt: str, max_tokens: int | None = None) -> Generator[str, None, None]:
        """Streaming generation (yields tokens) for snappy UX."""
        self._ensure_model_loaded()
        cache_key = (prompt, max_tokens)
        cached = _llm_cache.get(cache_key)
        if cached is not None:
            logger.debug("LLM stream cache hit for prompt; replaying cached output")
            # Yield the cached final output as a single chunk to replay quickly
            yield cached
            return

        stream = self._llm(
            prompt,
            max_tokens=max_tokens or Config.MAX_TOKENS,
            temperature=0.7,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["User:", "\n\n", "<end_of_turn>", "<eos>"],
            stream=True
        )
        collected = []
        for chunk in stream:
            token = chunk["choices"][0]["text"]
            if token:
                collected.append(token)
                yield token

        # Cache the final combined output for future fast responses
        final = "".join(collected).strip()
        if final:
            _llm_cache.set(cache_key, final)

# Global Singleton Orchestrator
_provider: LlamaCppProvider | None = None

def get_inference_orchestrator() -> LlamaCppProvider:
    """Entry point to get the active inference provider."""
    global _provider
    if _provider is None:
        _provider = LlamaCppProvider()
    return _provider

# Backward compatible helper
def generate_response(prompt: str, max_tokens: int | None = None) -> str:
    return get_inference_orchestrator().generate(prompt, max_tokens)

def get_llm():
    """Legacy helper for lifespan loading."""
    orchestrator = get_inference_orchestrator()
    orchestrator._ensure_model_loaded()
    return orchestrator._llm
