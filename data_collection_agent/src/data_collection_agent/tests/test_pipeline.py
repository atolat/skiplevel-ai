"""Test the data collection pipeline by chaining tools together."""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from ..tools.source_selector import SourceSelectorTool
from ..tools.content_fetcher import ContentFetcherTool
from ..tools.rubric_chunker import RubricChunkerTool

def test_pipeline():
    """Test the complete data collection pipeline."""
    # Load environment variables
    load_dotenv()
    
    # Initialize tools
    source_selector = SourceSelectorTool()
    content_fetcher = ContentFetcherTool()
    rubric_chunker = RubricChunkerTool()
    
    # Step 1: Select sources
    source_input = {
        "collection_goal": "Collect engineering career framework data for L5-L6 levels focusing on technical skills and leadership"
    }
    source_result = source_selector.run(source_input)
    print("\nSelected Sources:")
    for source in source_result["selected_sources"]:
        print(f"- {source['company']}: {source['url']}")
    
    # Step 2: Fetch content
    content_result = content_fetcher.run({"sources": source_result["selected_sources"]})
    print("\nFetched Content:")
    for content in content_result["fetched_content"]:
        print(f"- {content['company']}: {len(content['content'])} characters")
    
    if content_result["errors"]:
        print("\nErrors encountered:")
        for error in content_result["errors"]:
            print(f"- {error['url']}: {error['error']}")
    
    # Step 3: Chunk content
    chunk_result = rubric_chunker.run({
        "content": content_result["fetched_content"],
        "chunk_size": 1000,
        "chunk_overlap": 200
    })
    
    print("\nChunking Results:")
    print(f"Total chunks created: {chunk_result['metadata']['total_chunks']}")
    print(f"Average chunks per source: {chunk_result['metadata']['total_chunks'] / len(content_result['fetched_content']):.1f}")
    
    # Print sample chunk
    if chunk_result["chunks"]:
        print("\nSample Chunk:")
        sample = chunk_result["chunks"][0]
        print(f"Source: {sample['company']}")
        print(f"Chunk {sample['chunk_index'] + 1} of {sample['total_chunks']}")
        print("Content preview:", sample["content"][:200] + "...")

if __name__ == "__main__":
    test_pipeline() 