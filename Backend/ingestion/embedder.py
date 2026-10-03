import logging
import threading

from PIL import Image

logger = logging.getLogger(__name__)

text_model = None
_text_lock = threading.Lock()

clip_model = None
clip_processor = None
_clip_lock = threading.Lock()


def load_clip():
    global clip_model, clip_processor

    # ✅ Double-checked locking: embed_image() runs in a threadpool (see app.py),
    # so concurrent requests can call this from separate threads at once.
    if clip_model is None:
        with _clip_lock:
            if clip_model is None:
                logger.info("Loading CLIP...")
                from transformers import CLIPProcessor, CLIPModel

                clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                logger.info("CLIP loaded")


def load_text_model():
    global text_model

    if text_model is None:
        with _text_lock:
            if text_model is None:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading text embedding model...")
                text_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Text embedding model loaded")

    return text_model


def embed_text(text: str):
    """✅ ONLY SentenceTransformer for text + tables"""
    vec = load_text_model().encode(text).tolist()
    return vec + [0] * (512 - len(vec))


def embed_image(image_path: str):
    """✅ CLIP ONLY for images"""
    load_clip()
    import torch

    image = Image.open(image_path).convert("RGB")
    inputs = clip_processor(images=image, return_tensors="pt")

    with torch.no_grad():
        features = clip_model.get_image_features(**inputs)

    return features[0].tolist()
