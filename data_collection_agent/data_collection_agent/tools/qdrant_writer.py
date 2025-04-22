"""Tool for storing rubric chunks in Qdrant."""

from typing import List, Dict, Any, Type
from langchain.tools import BaseTool
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models
from pydantic import BaseModel, Field, PrivateAttr

from ..constants import QDRANT_CONFIG

class QdrantWriterInput(BaseModel):
    """Input model for the QdrantWriterTool."""
    chunks: List[Dict[str, Any]] = Field(..., description="List of rubric chunks with metadata")

class QdrantWriterTool(BaseTool):
    """Tool for storing rubric chunks in Qdrant."""
    
    name: str = "qdrant_writer"
    description: str = "Stores rubric chunks in Qdrant vector database"
    args_schema: Type[BaseModel] = QdrantWriterInput
    
    _embeddings: OpenAIEmbeddings = PrivateAttr()
    _client: QdrantClient = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._embeddings = OpenAIEmbeddings()
        self._client = QdrantClient(":memory:")
        
        # Create collection if it doesn't exist
        try:
            self._client.get_collection(QDRANT_CONFIG["collection_name"])
        except:
            self._client.create_collection(
                collection_name=QDRANT_CONFIG["collection_name"],
                vectors_config=models.VectorParams(
                    size=QDRANT_CONFIG["vector_size"],
                    distance=models.Distance.COSINE
                )
            )

    def _run(self, chunks: List[Dict[str, Any]]) -> str:
        """Store rubric chunks in Qdrant."""
        try:
            # Prepare points for batch upload
            points = []
            for i, chunk in enumerate(chunks):
                # Generate embedding for the text
                embedding = self._embeddings.embed_query(chunk["text"])
                
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
            self._client.upsert(
                collection_name=QDRANT_CONFIG["collection_name"],
                points=points
            )
            
            return f"Successfully stored {len(chunks)} chunks in Qdrant"
            
        except Exception as e:
            return f"Error storing chunks in Qdrant: {str(e)}"

    async def _arun(self, chunks: List[Dict[str, Any]]) -> str:
        """Async implementation of Qdrant writing."""
        return self._run(chunks) 