#!/usr/bin/env python3

from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        logger.info("Connected to Qdrant")

        # Get collection info
        collection_info = qdrant_client.get_collection("rubrics")
        logger.info(f"Collection 'rubrics' contains {collection_info.points_count} points")

        # Scroll through the collection
        results = qdrant_client.scroll(
            collection_name="rubrics",
            with_payload=True,
            limit=100
        )

        # Print each rubric
        logger.info("\nFirst 100 rubrics in collection:")
        for i, point in enumerate(results[0], 1):
            payload = point.payload
            logger.info(f"\n{i}. Level: {payload.get('level')}, Dimension: {payload.get('dimension')}")
            logger.info(f"Text: {payload.get('text')}")
            logger.info(f"Source: {payload.get('source')}")

    except Exception as e:
        logger.error(f"Error inspecting rubrics: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 