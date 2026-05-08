"""
Sanctuary 3.0 — LLM Engine
Loads the fine-tuned GGUF model directly into process memory via llama-cpp-python.
No external server dependency (no Ollama, no HTTP calls, no timeouts).
"""

import logging
from pathlib import Path
from llama_cpp import Llama

from config import Config

logger = logging.getLogger(__name__)

_llm: Llama | None = None


def get_llm() -> Llama:
    """Lazy-load the GGUF model. Keeps it in RAM for the lifetime of the server."""
    global _llm
    if _llm is not None:
        return _llm

    model_path = Path(Config.MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(
            f"GGUF model not found at {model_path}. "
            f"Place your sanctuary_cbt_final.gguf file in backend/models/"
        )

    logger.info("Loading GGUF model from %s (this may take 10-30 seconds)...", model_path)
  #  _llm = Llama(
  #       model_path=str(model_path),
  #       n_ctx=Config.N_CTX,
  #       n_gpu_layers=Config.N_GPU_LAYERS,
  #       verbose=False,
  #   )
    logger.info("Loading GGUF model from %s (this may take 10-30 seconds)...", model_path)
    
    # The updated, multi-threaded CPU engine
    _llm = Llama(
        model_path=str(model_path), # Uses the dynamic path so it doesn't break
        n_threads=8,                # Forces 8 CPU cores for speed
        n_ctx=2048,                 # Context window
        verbose=False               # Keeps your terminal from getting messy
    )
    logger.info("Model loaded successfully.")
    return _llm


def generate_response(prompt: str, max_tokens: int | None = None) -> str:
    """
    Generate a response from the loaded GGUF model.

    Args:
        prompt: The full prompt string (including clinical grounding context).
        max_tokens: Override the default max_tokens from Config.

    Returns:
        The model's generated text, stripped of whitespace.
    """
    llm = get_llm()
    tokens = max_tokens or Config.MAX_TOKENS

    try:
        # Update your generation parameters to these exact values:
        output = llm(
            prompt,
            max_tokens=256,        # Generous limit for multi-sentence reframes
            temperature=0.7,       # Industry standard for balanced creativity
            top_p=0.9,             # Nucleus sampling for coherence
            repeat_penalty=1.1,    # Subtle loop prevention
            stop=["User:", "\n\n", "<end_of_turn>", "<eos>"] 
        )
        return output["choices"][0]["text"].strip()




    except Exception as e:
        logger.error("LLM generation failed: %s", e)
        return "I'm having trouble processing that right now. Could you try rephrasing?"
