"""
Sanctuary 3.0 — Modular LLM Engine
Optimized for local CPU/GPU execution with Min-P sampling and HyDE support.
"""

import logging
from pathlib import Path
from typing import Generator, Protocol
from llama_cpp import Llama

from config import Config
from cache_utils import LRUCache
from core.constants import HYDE_PROMPT

logger = logging.getLogger(__name__)

# In-memory LRU cache
_llm_cache = LRUCache(capacity=Config.CACHE_SIZE_LLM)

class InferenceProvider(Protocol):
    def generate(self, messages: list, max_tokens: int | None = None) -> str: ...
    def generate_stream(self, messages: list, max_tokens: int | None = None) -> Generator[str, None, None]: ...


class LlamaCppProvider:
    def __init__(self):
        self._llm: Llama | None = None
        self._model_path = Path(Config.MODEL_PATH)
        
    def _ensure_model_loaded(self):
        if self._llm is not None:
            return

        if not self._model_path.exists():
            raise FileNotFoundError(f"GGUF model not found at {self._model_path}")

        logger.info("Loading Sanctuary Core (%s)...", self._model_path.name)
        
        self._llm = Llama(
            model_path=str(self._model_path),
            n_threads=Config.N_THREADS,
            n_ctx=Config.N_CTX,
            n_batch=512,
            n_ubatch=256,
            n_gpu_layers=Config.N_GPU_LAYERS,
            offload_kqv=True,
            flash_attn=True,
            verbose=False
        )
        logger.info("Sanctuary Core loaded successfully.")

    def generate(self, messages: list, max_tokens: int | None = None) -> str:
        self._ensure_model_loaded()
        cache_key = str(messages)
        cached = _llm_cache.get(cache_key)
        if cached is not None:
            return cached

        # Industry standard: Min-P sampling (0.05 - 0.1)
        output = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens or Config.MAX_TOKENS,
            temperature=0.7, 
            top_p=0.9,
            min_p=0.05, 
            repeat_penalty=1.1,
        )
        result = output["choices"][0]["message"]["content"].strip()
        _llm_cache.set(cache_key, result)
        return result

    def generate_stream(self, messages: list, max_tokens: int | None = None) -> Generator[str, None, None]:
        self._ensure_model_loaded()
        cache_key = str(messages)
        cached = _llm_cache.get(cache_key)
        if cached is not None:
            yield cached
            return

        stream = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens or Config.MAX_TOKENS,
            temperature=0.7,
            top_p=0.9,
            min_p=0.05,
            repeat_penalty=1.1,
            stream=True
        )
        collected = []
        for chunk in stream:
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0]["delta"]
                if "content" in delta:
                    token = delta["content"]
                    collected.append(token)
                    yield token

        final = "".join(collected).strip()
        if final:
            _llm_cache.set(cache_key, final)

    def generate_hyde(self, query: str) -> str:
        """Generate a hypothetical clinical response for HyDE retrieval."""
        prompt = HYDE_PROMPT.format(query=query)
        messages = [{"role": "user", "content": prompt}]
        # Use low max_tokens and temp for HyDE
        return self.generate(messages, max_tokens=150)


# Global Singleton Orchestrator
_provider: LlamaCppProvider | None = None

def get_inference_orchestrator() -> LlamaCppProvider:
    global _provider
    if _provider is None:
        _provider = LlamaCppProvider()
    return _provider

def generate_response(messages: list, max_tokens: int | None = None) -> str:
    return get_inference_orchestrator().generate(messages, max_tokens)
