"""Data collection pipeline using LangChain Expression Language."""

from typing import Dict, Any, List
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import json
import asyncio

from .tools.source_selector import select_sources
from .tools.content_fetcher import fetch_content
from .tools.rubric_chunker import chunk_rubric
from .tools.qdrant_writer import store_chunks

async def process_sources(sources: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """Process sources to fetch content asynchronously."""
    content = {}
    tasks = []
    for source_name, source_info in sources.items():
        tasks.append(fetch_content.ainvoke({"source_info": source_info}))
    
    # Run all fetch operations concurrently
    results = await asyncio.gather(*tasks)
    for source_name, result in zip(sources.keys(), results):
        content[source_name] = result
    return content

async def process_content(content: Dict[str, str], sources: Dict[str, Dict[str, str]], 
                   level: str, dimension: str) -> List[Dict[str, Any]]:
    """Process content to generate chunks asynchronously."""
    chunks = []
    tasks = []
    for source_name, source_content in content.items():
        source_info = sources[source_name]
        tasks.append(chunk_rubric.ainvoke({
            "content": source_content,
            "level": level,
            "dimension": dimension,
            "company": source_info["company"]
        }))
    
    # Run all chunking operations concurrently
    results = await asyncio.gather(*tasks)
    for result in results:
        chunks.extend(result)
    return chunks

def create_pipeline() -> Dict[str, Any]:
    """Create the data collection pipeline using LCEL."""
    
    # Define the pipeline steps
    select_sources_step = RunnableLambda(
        lambda x: {
            **x,  # Preserve existing state
            "sources": select_sources.invoke({
                "level": x["level"],
                "dimension": x["dimension"]
            })
        }
    )
    
    async def fetch_content_async(x: Dict[str, Any]) -> Dict[str, Any]:
        content = await process_sources(x["sources"])
        return {**x, "content": content}
    
    async def generate_chunks_async(x: Dict[str, Any]) -> Dict[str, Any]:
        chunks = await process_content(
            x["content"],
            x["sources"],
            x["level"],
            x["dimension"]
        )
        return {**x, "chunks": chunks}
    
    fetch_content_step = RunnableLambda(fetch_content_async)
    generate_chunks_step = RunnableLambda(generate_chunks_async)
    
    store_chunks_step = RunnableLambda(
        lambda x: {
            **x,  # Preserve existing state
            "result": store_chunks.invoke(json.dumps(x["chunks"]))
        }
    )
    
    # Compose the pipeline using the | operator
    pipeline = (
        RunnablePassthrough()
        | select_sources_step
        | fetch_content_step
        | generate_chunks_step
        | store_chunks_step
    )
    
    return pipeline

class DataCollectionAgent:
    """Agent for collecting and ingesting engineering career rubrics."""
    
    def __init__(self):
        self.pipeline = create_pipeline()
    
    async def arun(self, goal: str) -> Dict[str, Any]:
        """Run the data collection agent asynchronously with the given goal."""
        # Parse the goal to extract level and dimension
        parts = goal.split("for the")
        level_part = parts[0].strip().replace("Collect", "").strip()
        dimension_part = parts[1].strip().replace("dimension.", "").strip()
        
        # Extract level range
        if "–" in level_part:
            start_level, end_level = level_part.split("–")
            start_level = start_level.strip().replace("IC", "")
            end_level = end_level.strip().split()[0].replace("IC", "")
            levels = [f"IC{i}" for i in range(int(start_level), int(end_level) + 1)]
        else:
            level = level_part.strip().split()[0]
            levels = [level]
        
        # Run the pipeline for each level
        results = {}
        for level in levels:
            print(f"\nProcessing level {level}...")
            state = {
                "level": level,
                "dimension": dimension_part
            }
            final_state = await self.pipeline.ainvoke(state)
            results[level] = {
                "sources": final_state["sources"],
                "content": {k: len(v) for k, v in final_state["content"].items()},
                "chunks": len(final_state["chunks"]),
                "result": final_state["result"]
            }
        
        return results
    
    def run(self, goal: str) -> Dict[str, Any]:
        """Synchronous wrapper for the async run method."""
        return asyncio.run(self.arun(goal)) 