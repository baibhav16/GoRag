import logging
import os

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ✅ COLLECTION NAME MUST BE DEFINED GLOBALLY
COLLECTION_NAME = "visrag_multimodal"

qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if not qdrant_url:
    logger.warning("QDRANT_URL is not set. Defaulting to local instance, which may fail on Render.")

# ✅ Connect to Qdrant Cloud (or Local)
client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
)


def setup_collection():
    """
    ✅ Ensure collection exists + payload indexes exist safely
    """
    try:
        collections = client.get_collections().collections
        existing = [c.name for c in collections]

        # ✅ Create collection if missing
        if COLLECTION_NAME not in existing:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=512,
                    distance=Distance.COSINE
                )
            )
            logger.info("Qdrant collection '%s' created", COLLECTION_NAME)
        else:
            logger.info("Collection '%s' already exists", COLLECTION_NAME)

        # ✅ Payload Indexes (safely ignore if already created)
        for field_name, field_schema in [
            ("doc_id", "keyword"),
            ("page", "integer"),
            ("type", "keyword"),
        ]:
            try:
                client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field_name,
                    field_schema=field_schema,
                )
            except Exception as idx_err:
                logger.debug("Payload index '%s' already exists or skipped: %s", field_name, idx_err)

        logger.info("Payload indexes verified: doc_id, page, type")

    except Exception as e:
        logger.error("Failed to setup Qdrant collection: %s", e)
        raise

