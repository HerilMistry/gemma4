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
            import shutil
            logger.info("GGUF model not found locally at %s. Initiating automatic self-healing download...", self._model_path)
            self._model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Default to public/private weights from user's huggingface repository
            default_url = "https://huggingface.co/HerilMistry/gemma4/resolve/main/sanctuary_cbt_final.gguf"
            url = os.getenv("SANCTUARY_MODEL_URL", default_url)
            # Extract HF repository name and filename if downloading from huggingface.co
            hf_repo = None
            hf_filename = None
            if "huggingface.co" in url and "/resolve/" in url:
                try:
                    parts = url.split("huggingface.co/", 1)[1].split("/")
                    if len(parts) >= 5 and parts[2] == "resolve":
                        hf_repo = f"{parts[0]}/{parts[1]}"
                        hf_filename = "/".join(parts[4:])
                except Exception as ex:
                    logger.warning("Could not parse Hugging Face repo structure from URL: %s", ex)

            hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
            downloaded = False

            # Option A: Try standard huggingface_hub API if available
            if hf_repo and hf_filename:
                try:
                    import huggingface_hub
                    logger.info("Attempting secure download via huggingface_hub for repo '%s', file '%s'...", hf_repo, hf_filename)
                    downloaded_path = huggingface_hub.hf_hub_download(
                        repo_id=hf_repo,
                        filename=hf_filename,
                        token=hf_token,
                        local_dir=str(self._model_path.parent),
                        local_dir_use_symlinks=False
                    )
                    downloaded_file = Path(downloaded_path)
                    if downloaded_file.resolve() != self._model_path.resolve():
                        shutil.copy2(downloaded_path, str(self._model_path))
                    logger.info("Model download via huggingface_hub completed successfully!")
                    downloaded = True
                except ImportError:
                    logger.info("huggingface_hub library not found. Falling back to HTTP request...")
                except Exception as he:
                    logger.warning("huggingface_hub download attempt failed: %s. Falling back to HTTP request...", he)

            # Option B: Stream download using urllib with authorization headers and chunked writing
            if not downloaded:
                try:
                    import urllib.request
                    logger.info("Downloading quantized Gemma 4 model from %s...", url)
                    
                    headers = {
                        "User-Agent": "SanctuaryDownloader/3.2"
                    }
                    if hf_token:
                        headers["Authorization"] = f"Bearer {hf_token}"
                        logger.info("Authenticated download request initiated using HF_TOKEN.")
                    
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req) as response:
                        total_size = int(response.info().get('Content-Length', 0))
                        chunk_size = 4 * 1024 * 1024  # 4MB chunks for fast I/O
                        bytes_downloaded = 0
                        
                        # Write atomically to a temporary file first
                        temp_path = self._model_path.with_suffix(".tmp")
                        logger.info("Downloading to temporary path: %s", temp_path.name)
                        
                        last_reported = 0
                        with open(temp_path, "wb") as f:
                            while True:
                                chunk = response.read(chunk_size)
                                if not chunk:
                                    break
                                f.write(chunk)
                                bytes_downloaded += len(chunk)
                                
                                # Limit progress logging to prevent spam
                                if total_size > 0:
                                    percent = (bytes_downloaded / total_size) * 100
                                    if percent - last_reported >= 5.0 or bytes_downloaded == total_size:
                                        logger.info("Download progress: %.1f%% (%d/%d MB)", percent, bytes_downloaded // (1024 * 1024), total_size // (1024 * 1024))
                                        last_reported = percent
                                else:
                                    if bytes_downloaded - last_reported >= 50 * 1024 * 1024:
                                        logger.info("Downloaded %d MB", bytes_downloaded // (1024 * 1024))
                                        last_reported = bytes_downloaded
                                        
                        # Move to target model path atomically
                        temp_path.rename(self._model_path)
                    logger.info("Download completed successfully!")
                except Exception as e:
                    raise FileNotFoundError(
                        f"GGUF model not found at {self._model_path} and automatic download from {url} failed: {e}. "
                        "Please verify your HF_TOKEN is correctly configured in your environment, or place sanctuary_cbt_final.gguf manually in the models/ directory."
                    )

        logger.info("Loading Sanctuary Core (%s)...", self._model_path.name)
        
        self._llm = Llama(
            model_path=str(self._model_path),
            n_threads=Config.N_THREADS,
            n_ctx=Config.N_CTX,
            n_batch=512,
            n_ubatch=256,
            n_gpu_layers=Config.N_GPU_LAYERS,
            offload_kqv=(Config.N_GPU_LAYERS > 0),
            flash_attn=(Config.N_GPU_LAYERS > 0),
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
                    elif len(buffer) >= 20:
                        # Confidently flush if prefix is absent
                        yield buffer
                        prefix_skipped = True
                else:
                    yield token

        # Flush any remaining buffer if it was never flushed (short response case)
        if not prefix_skipped and buffer:
            clean_buf = _extract_sanctuary_response(buffer)
            if clean_buf:
                yield clean_buf

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
