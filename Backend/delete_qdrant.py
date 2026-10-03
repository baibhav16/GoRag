import logging

from storage.qdrant_client import client, COLLECTION_NAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

client.delete_collection(COLLECTION_NAME)
logger.info("Deleted collection '%s'", COLLECTION_NAME)
