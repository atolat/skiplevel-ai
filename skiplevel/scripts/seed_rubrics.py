#!/usr/bin/env python3

import json
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import openai
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Constants
BATCH_SIZE = 100
EMBEDDING_MODEL = "text-embedding-ada-002"
COLLECTION_NAME = "rubrics"
VECTOR_SIZE = 1536

def get_rubrics_from_jsonl(file_path: Path) -> List[Dict]:
    """Read rubrics from a JSONL file."""
    rubrics = []
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    rubric = json.loads(line.strip())
                    if not rubric or "chunk" not in rubric:
                        print(f"Warning: Skipping invalid rubric in {file_path.name} at line {line_num}")
                        continue
                        
                    rubrics.append({
                        "text": rubric["chunk"],
                        "level": rubric.get("level"),
                        "dimension": rubric.get("dimension"),
                        "source": file_path.name
                    })
                except json.JSONDecodeError:
                    print(f"Warning: Invalid JSON in {file_path.name} at line {line_num}")
                    continue
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return []
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return []
        
    return rubrics

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings for a batch of texts."""
    response = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]

def main():
    # Initialize clients
    qdrant_client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    
    # Create collection if it doesn't exist
    collections = qdrant_client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    if COLLECTION_NAME not in collection_names:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE
            )
        )
        print(f"Created collection '{COLLECTION_NAME}'")
    
    # Read all JSONL files
    rubrics_dir = Path("data/rubrics")
    all_rubrics = []
    
    if not rubrics_dir.exists():
        print(f"Error: Directory not found: {rubrics_dir}")
        return
        
    jsonl_files = list(rubrics_dir.glob("*.jsonl"))
    if not jsonl_files:
        print(f"Warning: No JSONL files found in {rubrics_dir}")
        return
    
    for jsonl_file in jsonl_files:
        rubrics = get_rubrics_from_jsonl(jsonl_file)
        if rubrics:
            all_rubrics.extend(rubrics)
            print(f"Loaded {len(rubrics)} rubrics from {jsonl_file.name}")
    
    if not all_rubrics:
        print("No valid rubrics found to process")
        return
        
    print(f"\nFound {len(all_rubrics)} valid rubrics in {len(jsonl_files)} files")
    
    # Process in batches
    total_processed = 0
    for i in tqdm(range(0, len(all_rubrics), BATCH_SIZE)):
        batch = all_rubrics[i:i + BATCH_SIZE]
        texts = [rubric["text"] for rubric in batch]
        
        # Get embeddings
        embeddings = get_embeddings(texts)
        
        # Prepare points for upsert
        points = []
        for j, (rubric, embedding) in enumerate(zip(batch, embeddings)):
            points.append(models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": rubric["text"],
                    "source": rubric["source"],
                    "level": rubric["level"],
                    "dimension": rubric["dimension"]
                }
            ))
        
        # Upsert batch
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        total_processed += len(batch)
    
    print(f"\nSuccessfully processed {total_processed} rubrics")
    print(f"Collection '{COLLECTION_NAME}' now contains {qdrant_client.count(COLLECTION_NAME).count} points")

if __name__ == "__main__":
    main() 