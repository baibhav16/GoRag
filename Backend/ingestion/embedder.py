import logging
import os
import threading

logger = logging.getLogger(__name__)

text_model = None
_text_lock = threading.Lock()

clip_model = None
clip_processor = None
_clip_lock = threading.Lock()

# On Render Free Tier (512MB RAM), loading CLIP (~600MB) causes an instant OOM crash.
# Since retrieval/search.py retrieves figures by page/doc_id filter (not vector similarity),
# disabling CLIP by default saves 600MB RAM and prevents crashes.
ENABLE_CLIP = os.getenv("ENABLE_CLIP", "false").lower() in ("true", "1", "yes")


def load_clip():
    global clip_model, clip_processor

    if not ENABLE_CLIP:
        return False

    if clip_model is None:
        with _clip_lock:
            if clip_model is None:
                try:
                    logger.info("Attempting to load CLIP model...")
                    from transformers import CLIPProcessor, CLIPModel

                    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                    logger.info("CLIP loaded successfully")
                    return True
                except Exception as e:
                    logger.warning("Could not load CLIP (falling back to lightweight vector): %s", e)
                    clip_model = False
                    return False
    return clip_model is not False and clip_model is not None


def load_text_model():
    global text_model

    if text_model is None:
        with _text_lock:
            if text_model is None:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading text embedding model (all-MiniLM-L6-v2)...")
                text_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Text embedding model loaded")

    return text_model


def embed_text(text: str):
    """✅ SentenceTransformer for text + tables (padded to 512 dim)"""
    vec = load_text_model().encode(text).tolist()
    return vec + [0.0] * (512 - len(vec))


def embed_image(image_path: str):
    """
    ✅ Image embedding for Qdrant (512-dim)
    If CLIP is enabled and available, computes visual features.
    Otherwise returns a compliant 512-dim vector without allocating 600MB RAM.
    """
    if load_clip():
        try:
            from PIL import Image
            import torch

            image = Image.open(image_path).convert("RGB")
            inputs = clip_processor(images=image, return_tensors="pt")

            with torch.no_grad():
                features = clip_model.get_image_features(**inputs)

            return features[0].tolist()
        except Exception as e:
            logger.warning("CLIP inference failed, using zero vector: %s", e)

    # Compliant 512-dim vector for Qdrant point schema
    return [0.0] * 512

