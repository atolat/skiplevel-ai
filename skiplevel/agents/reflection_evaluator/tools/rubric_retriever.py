#!/usr/bin/env python3

# File: skiplevel/agents/reflection_evaluator/tools/rubric_retriever.py

from typing import Dict, List
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_core.tools import tool

# Load environment variables
load_dotenv()

# Constants
COLLECTION_NAME = "rubrics"
TOP_K = 5

@tool
def rubric_retriever(reflection: str) -> List[Dict]:
    """
    Retrieves relevant rubric chunks for a given reflection using semantic search.
    
    Args:
        reflection: The engineer's self-reflection text
        
    Returns:
        List[Dict]: List of relevant rubric chunks with their similarity scores
    """
    try:
        print("\n🔎 RubricRetrieverTool invoked")
        print(f"📝 Reflection: {reflection[:100]}...")
        
        # Initialize clients
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        print("✅ Connected to Qdrant")
        
        embeddings = OpenAIEmbeddings()
        print("✅ Initialized OpenAI embeddings")
        
        # Get embedding for the reflection
        reflection_embedding = embeddings.embed_query(reflection)
        print(f"📊 Embedding shape: {len(reflection_embedding)} dimensions")
        
        # Search Qdrant
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=reflection_embedding,
            limit=TOP_K,
            with_payload=True,
            with_vectors=False
        )
        
        if not search_results:
            print("⚠️ Warning: No matching rubrics found!")
            return []
            
        print(f"✅ Found {len(search_results)} matching rubrics")
        
        # Format results
        results = []
        for i, result in enumerate(search_results, 1):
            rubric = {
                "text": result.payload["text"],
                "score": result.score,
                "level": result.payload.get("level"),
                "dimension": result.payload.get("dimension")
            }
            results.append(rubric)
            
            # Print top 3 results in detail
            if i <= 3:
                print(f"\n🏆 Top {i} Match:")
                print(f"   Score: {rubric['score']:.2f}")
                print(f"   Level: {rubric['level']}")
                print(f"   Dimension: {rubric['dimension']}")
                print(f"   Text: {rubric['text'][:100]}...")
            
        return results
        
    except Exception as e:
        print(f"❌ Error retrieving rubrics: {str(e)}")
        return []
