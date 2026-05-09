"""
Sanctuary 3.0 — Language Detection & Translation Utilities
Multilingual support for text and speech journaling.

Features:
- Language detection for text via langdetect
- Whisper language parameter mapping
- Optional translation fallback (text-only, user-configurable)
- Language-aware RAG context retrieval
"""

import logging
from langdetect import detect, DetectorFactory, LangDetectException
from config import Config

logger = logging.getLogger(__name__)

# Seed for reproducibility in language detection
DetectorFactory.seed = 0

# Mapping from ISO 639-1 codes to Whisper language names
WHISPER_LANGUAGE_MAP = {
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "de": "german",
    "it": "italian",
    "pt": "portuguese",
    "nl": "dutch",
    "ru": "russian",
    "zh": "chinese",
    "ja": "japanese",
    "ko": "korean",
    "ar": "arabic",
    "hi": "hindi",
    "tr": "turkish",
    "pl": "polish",
    "uk": "ukrainian",
    "el": "greek",
    "hu": "hungarian",
    "cs": "czech",
    "sv": "swedish",
    "no": "norwegian",
    "da": "danish",
    "fi": "finnish",
    "ro": "romanian",
    "th": "thai",
    "vi": "vietnamese",
}

# ISO 639-1 codes that the LLM model likely supports (defaults to English if not in this list)
SUPPORTED_LLM_LANGUAGES = {"en", "es", "fr", "de"}  # Expand based on your model's training


def detect_language(text: str, confidence_threshold: float = 0.5) -> tuple[str, float]:
    """
    Detect the language of the input text using langdetect.

    Args:
        text: The input text to detect language for.
        confidence_threshold: Minimum confidence (0-1) to return a language. If below, returns 'unknown'.

    Returns:
        Tuple of (language_code, confidence):
        - language_code: ISO 639-1 code (e.g., 'en', 'es') or 'unknown' if detection fails.
        - confidence: Confidence score (0-1) or 0.0 if unknown.
    """
    if not text or len(text.strip()) < 3:
        logger.debug("Text too short for language detection, defaulting to 'en'")
        return "en", 0.0

    try:
        lang_code = detect(text)
        # langdetect doesn't return confidence directly; we assume successful detection = high confidence
        confidence = 0.9  # Placeholder; langdetect does return probabilities in detect_langs()
        
        if confidence >= confidence_threshold:
            logger.info("Detected language: %s (confidence: %.2f)", lang_code, confidence)
            return lang_code, confidence
        else:
            logger.warning(
                "Language detection confidence %.2f below threshold %.2f, defaulting to 'en'",
                confidence,
                confidence_threshold,
            )
            return "en", 0.0

    except LangDetectException as e:
        logger.warning("Language detection failed: %s. Defaulting to 'en'", e)
        return "en", 0.0


def detect_language_with_probs(text: str) -> tuple[str, dict[str, float]]:
    """
    Detect language and return all detected probabilities (advanced).

    Args:
        text: The input text.

    Returns:
        Tuple of (primary_lang_code, {lang_code: probability, ...})
    """
    if not text or len(text.strip()) < 3:
        return "en", {"en": 1.0}

    try:
        from langdetect import detect_langs
        probs = detect_langs(text)
        prob_dict = {p.lang: p.prob for p in probs}
        primary_lang = max(prob_dict, key=prob_dict.get)
        logger.debug("Language probabilities: %s", prob_dict)
        return primary_lang, prob_dict
    except Exception as e:
        logger.warning("Language detection with probs failed: %s. Defaulting to 'en'", e)
        return "en", {"en": 1.0}


def get_whisper_language(lang_code: str) -> str | None:
    """
    Map ISO 639-1 code to Whisper language name.

    Args:
        lang_code: ISO 639-1 code (e.g., 'en', 'es').

    Returns:
        Whisper language name (e.g., 'english', 'spanish') or None if not mapped.
    """
    whisper_lang = WHISPER_LANGUAGE_MAP.get(lang_code)
    if whisper_lang:
        logger.debug("Mapped %s to Whisper language: %s", lang_code, whisper_lang)
    else:
        logger.warning("No Whisper mapping for language code: %s. Will use auto-detect.", lang_code)
    return whisper_lang


def is_llm_multilingual() -> bool:
    """
    Check if the LLM model supports multiple languages natively.

    Returns:
        True if multilingual support is enabled in config, False if English-only.
    """
    return Config.LLM_MULTILINGUAL_SUPPORT


def should_translate_for_llm(lang_code: str) -> bool:
    """
    Determine if text in the given language should be translated to English before LLM processing.

    Args:
        lang_code: ISO 639-1 code.

    Returns:
        True if translation is needed, False if LLM can handle the language natively.
    """
    if is_llm_multilingual():
        return False  # No translation needed if LLM is multilingual
    
    if lang_code in SUPPORTED_LLM_LANGUAGES:
        return False  # Language is explicitly supported
    
    return True  # Translation needed


def translate_text(text: str, source_lang: str, target_lang: str = "en") -> tuple[str, bool]:
    """
    Translate text from source_lang to target_lang.
    
    This is a placeholder that respects Config.TRANSLATION_SERVICE setting.
    - If 'local': Uses a local M2M100 model (requires transformers + torch, heavy).
    - If 'disabled': Returns original text (no translation).
    - If 'cloud': Currently unsupported (requires API keys and network).

    Args:
        text: The text to translate.
        source_lang: ISO 639-1 source language code.
        target_lang: ISO 639-1 target language code (default: 'en').

    Returns:
        Tuple of (translated_text, success_bool):
        - translated_text: The translated text or original if translation disabled/failed.
        - success_bool: True if translation was successful, False otherwise.
    """
    if source_lang == target_lang:
        logger.debug("Source and target languages are the same, skipping translation")
        return text, True

    service = Config.TRANSLATION_SERVICE

    if service == "disabled":
        logger.debug("Translation disabled in config. Returning original text.")
        return text, False

    if service == "cloud":
        logger.warning("Cloud translation not yet implemented. Returning original text.")
        return text, False

    if service == "local":
        try:
            logger.info("Translating %s -> %s using local M2M100 model...", source_lang, target_lang)
            from transformers import M2M100ForConditionalGeneration, AutoTokenizer

            # This loads a large model (~800MB) and will be slow on first run
            model_name = "facebook/m2m100_418M"
            tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=False)
            model = M2M100ForConditionalGeneration.from_pretrained(model_name)

            # Set source language for tokenizer
            tokenizer.src_lang = source_lang

            # Encode, generate, decode
            encoded = tokenizer(text, return_tensors="pt")
            generated_tokens = model.generate(
                **encoded,
                forced_bos_token_id=tokenizer.get_lang_id(target_lang),
                max_length=512,
            )
            translated = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

            logger.info("Translation successful: %s", translated[:100])
            return translated, True

        except ImportError:
            logger.error(
                "Local translation requested but transformers/torch not installed. "
                "Install: pip install transformers torch"
            )
            return text, False
        except Exception as e:
            logger.error("Local translation failed: %s. Returning original text.", e)
            return text, False

    logger.warning("Unknown translation service: %s", service)
    return text, False


def format_multilingual_context(text: str, lang_code: str, translated_text: str | None = None) -> dict:
    """
    Format text with language metadata for logging/RAG/display.

    Args:
        text: Original text.
        lang_code: Detected language code.
        translated_text: Optional translated text (if translation was performed).

    Returns:
        Dict with keys: original, language, language_name, translated (optional).
    """
    lang_name = WHISPER_LANGUAGE_MAP.get(lang_code, "unknown")
    result = {
        "original": text,
        "language": lang_code,
        "language_name": lang_name,
    }
    if translated_text:
        result["translated"] = translated_text
    return result
