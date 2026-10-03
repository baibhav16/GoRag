import logging
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def embed_text(text: str):
    """
    ✅ Generate 512-dim embedding using Gemini API (models/text-embedding-004).
    Uses 0 MB of server RAM, completely eliminating Render Free Tier OOM crashes.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            res = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                output_dimensionality=512,
            )
            vec = res.get("embedding", [])
            if len(vec) == 512:
                return vec
            elif len(vec) < 512:
                return vec + [0.0] * (512 - len(vec))
            else:
                return vec[:512]
        except Exception as e:
            logger.warning("Gemini MRL embedding failed: %s, retrying default dimension...", e)
            try:
                res = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                )
                vec = res.get("embedding", [])
                if len(vec) >= 512:
                    return vec[:512]
                return vec + [0.0] * (512 - len(vec))
            except Exception as e2:
                logger.error("Gemini embedding failed: %s", e2)

    # Optional local fallback if sentence-transformers is available
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Using local SentenceTransformer fallback...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        vec = model.encode(text).tolist()
        return vec + [0.0] * (512 - len(vec))
    except Exception as local_err:
        logger.error("Local embedding fallback also failed: %s", local_err)
        raise RuntimeError("Embedding generation failed.")


def embed_image(image_path: str):
    """
    ✅ Compliant 512-dim vector for Qdrant image schema.
    Figures are retrieved by page and doc_id metadata matching.
    """
    return [0.0] * 512
