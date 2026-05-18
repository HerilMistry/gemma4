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

_llm_cache = LRUCache(capacity=Config.CACHE_SIZE_LLM)

class InferenceProvider(Protocol):
    def generate(self, messages: list, max_tokens: int | None = None) -> str: ...
    def generate_stream(self, messages: list, max_tokens: int | None = None) -> Generator[str, None, None]: ...


def _build_gemma_prompt(messages: list) -> str:
    """
    Format the message list into the official Gemma Instruct template:
    <start_of_turn>user
    {system_instruction}\n\nUser input: {user_input}<end_of_turn>
    <start_of_turn>model
    """
    system_content = ""
    turns = []
    
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "").strip()
        
        if role == "system":
            system_content = content
        elif role in ("user", "human"):
            turns.append(("user", content))
        elif role in ("assistant", "model"):
            turns.append(("model", content))
            
    prompt = ""
    first_turn = True
    for role, content in turns:
        # Inject system prompt into the first user turn if present
        if first_turn and role == "user" and system_content:
            content = f"{system_content}\n\nUser input: {content}"
        first_turn = False
            
        prompt += f"<start_of_turn>{role}\n{content}<end_of_turn>\n"
        
    prompt += "<start_of_turn>model\n"
    return prompt


def _extract_sanctuary_response(text: str) -> str:
    """Extracts the therapist's response from structural reasoning output if present."""
    if "Sanctuary Response:" in text:
        parts = text.split("Sanctuary Response:", 1)
        return parts[1].strip()
    return text.strip()


class LlamaCppProvider:
    def __init__(self):
        self._llm: Llama | None = None
        self._model_path = Path(Config.MODEL_PATH)
        
    def _ensure_model_loaded(self):
        if self._llm is not None:
            return

        if not self._model_path.exists():
            import os
            logger.info("GGUF model not found locally at %s. Initiating automatic self-healing download...", self._model_path)
            self._model_path.parent.mkdir(parents=True, exist_ok=True)
            # Default to public weights from user's huggingface repository
            default_url = "https://huggingface.co/HerilMistry/gemma4/resolve/main/sanctuary_cbt_final.gguf"
            url = os.getenv("SANCTUARY_MODEL_URL", default_url)
            try:
                import urllib.request
                logger.info("Downloading quantized Gemma 4 model from %s...", url)
                urllib.request.urlretrieve(url, str(self._model_path))
                logger.info("Download completed successfully!")
            except Exception as e:
                raise FileNotFoundError(
                    f"GGUF model not found at {self._model_path} and automatic download from {url} failed: {e}. "
                    "Please place sanctuary_cbt_final.gguf manually in the models/ directory."
                )

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

        prompt = _build_gemma_prompt(messages)
        
        # Min-P sampling (0.05 - 0.1)
        output = self._llm(
            prompt=prompt,
            max_tokens=max_tokens or Config.MAX_TOKENS,
            temperature=0.7,
            top_p=0.9,
            min_p=0.05,
            repeat_penalty=1.1,
            stop=["<end_of_turn>", "<eos>"]
        )
        result = output["choices"][0]["text"].strip()
        
        # Clean structural prefix if model outputs it
        clean_result = _extract_sanctuary_response(result)
        
        _llm_cache.set(cache_key, clean_result)
        return clean_result

    def generate_stream(self, messages: list, max_tokens: int | None = None) -> Generator[str, None, None]:
        self._ensure_model_loaded()
        cache_key = str(messages)
        cached = _llm_cache.get(cache_key)
        if cached is not None:
            yield cached
            return

        prompt = _build_gemma_prompt(messages)
        
        stream = self._llm(
            prompt=prompt,
            max_tokens=max_tokens or Config.MAX_TOKENS,
            temperature=0.7,
            top_p=0.9,
            min_p=0.05,
            repeat_penalty=1.1,
            stop=["<end_of_turn>", "<eos>"],
            stream=True
        )
        
        buffer = ""
        prefix_skipped = False
        collected = []
        
        for chunk in stream:
            if "choices" in chunk and len(chunk["choices"]) > 0:
                token = chunk["choices"][0]["text"]
                collected.append(token)
                
                if not prefix_skipped:
                    buffer += token
                    if "Sanctuary Response:" in buffer:
                        parts = buffer.split("Sanctuary Response:", 1)
                        content = parts[1].lstrip()
                        if content:
                            yield content
                        prefix_skipped = True
                    elif len(buffer) > 150:
                        # Fallback if structural header is absent, flush buffer
                        yield buffer
                        prefix_skipped = True
                else:
                    yield token

        final = "".join(collected).strip()
        if final:
            clean_final = _extract_sanctuary_response(final)
            _llm_cache.set(cache_key, clean_final)

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
