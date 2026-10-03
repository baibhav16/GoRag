import logging
import uuid
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from ingestion.embedder import embed_text, embed_image
from storage.qdrant_client import client, COLLECTION_NAME

logger = logging.getLogger(__name__)


def upload_to_qdrant(blocks, doc_id: str):
    """
    ✅ Upload multimodal blocks into ONE Qdrant collection

    Stores:
    ✅ text
    ✅ tables
    ✅ images (figures)
    """

    logger.info("Uploading '%s' into Qdrant collection = %s", doc_id, COLLECTION_NAME)

    # ✅ Re-uploading a doc_id replaces its old points instead of duplicating them
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
    )

    points = []

    for block in blocks:

        block_type = block["type"]
        point_id = str(uuid.uuid4())

        # -----------------------------
        # ✅ TEXT
        # -----------------------------
        if block_type == "text":
            vector = embed_text(block["content"])

            payload = {
                "doc_id": doc_id,
                "type": "text",
                "page": block["page"],
                "content": block["content"],
            }

        # -----------------------------
        # ✅ TABLE
        # -----------------------------
        elif block_type == "table":
            table_data = block.get("table_data", [])

            vector = embed_text(str(table_data))

            payload = {
                "doc_id": doc_id,
                "type": "table",
                "page": block["page"],
                "caption": block.get("caption", "Extracted Table"),
                "table_data": table_data,
            }

        # -----------------------------
        # ✅ IMAGE / FIGURE
        # -----------------------------
        elif block_type == "image":
            file_path = block.get("file_path")
            if not file_path:
                continue

            vector = embed_image(file_path)

            payload = {
                "doc_id": doc_id,
                "type": "image",
                "page": block["page"],
                "caption": block.get("caption", "Extracted Figure"),
                "file_path": file_path,
            }

        else:
            continue

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
        )

    # ✅ Upload ALL points into ONE collection
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    logger.info("Uploaded %d multimodal points successfully!", len(points))
