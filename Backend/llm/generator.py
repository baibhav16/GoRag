import logging
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_model_instance = None


def get_model():
    global _model_instance

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    if _model_instance is not None:
        return _model_instance

    genai.configure(api_key=api_key)

    configured_model = os.getenv("GEMINI_MODEL")
    candidates = []
    if configured_model:
        candidates.append(configured_model)
        if not configured_model.startswith("models/"):
            candidates.append(f"models/{configured_model}")

    candidates.extend([
        "gemini-1.5-flash",
        "models/gemini-1.5-flash",
        "gemini-1.5-pro",
        "models/gemini-1.5-pro",
        "gemini-pro",
        "models/gemini-pro",
    ])

    # Discover available models from the API
    try:
        api_models = [
            m.name for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        logger.info("Available generateContent models: %s", api_models)
        # Prepend available models matching 1.5-flash or any flash
        flash_models = [m for m in api_models if "flash" in m]
        if flash_models:
            candidates = flash_models + candidates
        else:
            candidates = api_models + candidates
    except Exception as list_err:
        logger.warning("Could not list models from API: %s", list_err)

    for cand in candidates:
        try:
            m = genai.GenerativeModel(cand)
            _model_instance = m
            logger.info("Successfully initialized Gemini model: %s", cand)
            return _model_instance
        except Exception:
            continue

    _model_instance = genai.GenerativeModel("gemini-1.5-flash")
    return _model_instance


def generate_answer(query, context, citations):
    """
    Generate grounded answer with Gemini.
    Includes page citations.
    """
    model = get_model()

    prompt = f"""
    You are an AI assistant answering from a PDF.

    Context (retrieved from PDF):
    {context}

    Question:
    {query}

    Rules:
    - Answer only from context
    - Mention page citations at end

    Citations: {citations}
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.exception("Gemini generation failed: %s", e)
        # Retry with dynamic discovery
        try:
            available = [
                m.name for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]
            for fallback_name in available:
                try:
                    logger.info("Retrying with discovered model %s...", fallback_name)
                    fb = genai.GenerativeModel(fallback_name)
                    response = fb.generate_content(prompt)
                    return response.text
                except Exception:
                    continue
        except Exception:
            pass
        raise
