import logging
import os

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ✅ COLLECTION NAME MUST BE DEFINED GLOBALLY
COLLECTION_NAME = "visrag_multimodal"



# ✅ Connect to Qdrant Cloud (or Local)
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    
)


def setup_collection():
    """
    ✅ Ensure collection exists + indexes exist
    """

    existing = [c.name for c in client.get_collections().collections]

    # ✅ Create collection if missing
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=512,
                distance=Distance.COSINE
            )
        )
        logger.info("Qdrant collection created")
    else:
        logger.info("Collection already exists")

    # ✅ Payload Indexes
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="doc_id",
        field_schema="keyword"
    )

    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="page",
        field_schema="integer"
    )

    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="type",
        field_schema="keyword"
    )

    logger.info("Payload indexes created: doc_id, page, type")
