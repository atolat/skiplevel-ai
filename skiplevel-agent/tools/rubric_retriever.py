from typing import List, Dict, Optional
from langchain.tools import BaseTool
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings

# Global variable to store the Qdrant client
_qdrant_client = None

def get_qdrant_client() -> QdrantClient:
    """Get the Qdrant client, creating it if necessary."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(":memory:")
    return _qdrant_client

def set_qdrant_client(client: QdrantClient) -> None:
    """Set the Qdrant client to use."""
    global _qdrant_client
    _qdrant_client = client

class RubricRetrieverTool(BaseTool):
    name: str = "rubric_retriever"
    description: str = "Retrieves relevant rubric chunks from the Qdrant collection based on similarity search"
    collection_name: Optional[str] = None
    client: Optional[QdrantClient] = None
    embeddings: Optional[OpenAIEmbeddings] = None
    
    def __init__(self, collection_name: str = "rubrics"):
        super().__init__(collection_name=collection_name)
        self.collection_name = collection_name
        self.client = get_qdrant_client()
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize collection if it doesn't exist
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536,  # OpenAI embedding dimension
                    distance=models.Distance.COSINE
                )
            )
    
    def _run(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve top k most relevant rubric chunks."""
        query_vector = self.embeddings.embed_query(query)
        
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k
        )
        
        return [
            {
                "text": hit.payload["text"],
                "score": hit.score,
                "metadata": hit.payload.get("metadata", {})
            }
            for hit in search_result
        ]
    
    async def _arun(self, query: str, top_k: int = 3) -> List[Dict]:
        """Async implementation of the tool."""
        return self._run(query, top_k) 