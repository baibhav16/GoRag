from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


def embed_image(image_path: str):
    """
    ✅ CLIP image embedding
    Output: 512-dim vector
    """

    image = Image.open(image_path).convert("RGB")
    inputs = clip_processor(images=image, return_tensors="pt")

    with torch.no_grad():
        features = clip_model.get_image_features(**inputs)

    return features[0].tolist()
