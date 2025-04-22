"""Tool for storing rubric chunks in Qdrant."""

from typing import List, Dict, Any
from langchain.tools import tool
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models
import json
import os

from ..constants import QDRANT_CONFIG

# Initialize Qdrant client
_client = QdrantClient(":memory:")

# Create collection if it doesn't exist
try:
    _client.get_collection(QDRANT_CONFIG["collection_name"])
except:
    _client.create_collection(
        collection_name=QDRANT_CONFIG["collection_name"],
        vectors_config=models.VectorParams(
            size=QDRANT_CONFIG["vector_size"],
            distance=models.Distance.COSINE
        )
    )

@tool
def store_chunks(chunks_json: str) -> str:
    """Store rubric chunks in Qdrant.
    
    Args:
        chunks_json: JSON string containing a list of dictionaries with:
            - text: The chunk text
            - metadata: Dictionary containing:
                - level: Target level (e.g., IC4, IC5)
                - dimension: Target dimension (e.g., Execution, Leadership)
                - company: Company name
                - rubric_type: Type of rubric (e.g., career_level)
    
    Returns:
        str: Success message with number of chunks stored
    """
    try:
        # Parse the JSON string
        chunks = json.loads(chunks_json)
        
        # Initialize embeddings inside the function
        embeddings = OpenAIEmbeddings()
        
        # Prepare points for batch upload
        points = []
        for i, chunk in enumerate(chunks):
            # Generate embedding for the text
            embedding = embeddings.embed_query(chunk["text"])
            
            # Create point with embedding and metadata
            point = models.PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    **chunk["metadata"]
                }
            )
            points.append(point)
        
        # Upload points to Qdrant
        _client.upsert(
            collection_name=QDRANT_CONFIG["collection_name"],
            points=points
        )
        
        return f"Successfully stored {len(chunks)} chunks in Qdrant"
        
    except Exception as e:
        return f"Error storing chunks in Qdrant: {str(e)}" 