import logging
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not set. Gemini generation will fail until key is configured.")

try:
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    logger.error("Failed to initialize Gemini model %s: %s", MODEL_NAME, e)
    model = None


def generate_answer(query, context, citations):
    """
    Generate grounded answer with Gemini.
    Includes page citations.
    """
    global model

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    if model is None:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))

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
        logger.exception("Gemini answer generation failed: %s", e)
        # If the configured model failed, try gemini-1.5-flash fallback
        if MODEL_NAME != "gemini-1.5-flash":
            logger.info("Retrying with gemini-1.5-flash fallback...")
            fallback_model = genai.GenerativeModel("gemini-1.5-flash")
            response = fallback_model.generate_content(prompt)
            return response.text
        raise

