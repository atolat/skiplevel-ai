"""Main graph implementation for the data collection agent."""

from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import Graph
from langchain_core.messages import HumanMessage
import json

from .tools.source_selector import select_sources
from .tools.content_fetcher import fetch_content
from .tools.rubric_chunker import chunk_rubric
from .tools.qdrant_writer import store_chunks

class GraphState(TypedDict):
    """State type for the data collection graph."""
    level: str
    dimension: str
    sources: Dict[str, Dict[str, str]]
    content: Dict[str, str]
    chunks: List[Dict[str, Any]]
    result: str

class DataCollectionAgent:
    """Agent for collecting and ingesting engineering career rubrics."""
    
    def __init__(self):
        # Define the graph
        self.graph = self._create_graph()
    
    def _create_graph(self) -> Graph:
        """Create the data collection graph."""
        
        def select_sources_node(state: GraphState) -> GraphState:
            """Select appropriate sources based on the goal."""
            level = state["level"]
            dimension = state["dimension"]
            
            print(f"\nSelecting sources for level {level} and dimension {dimension}")
            sources = select_sources.invoke({"level": level, "dimension": dimension})
            print(f"Selected sources: {sources}")
            
            return {
                **state,
                "sources": sources
            }
        
        def fetch_content_node(state: GraphState) -> GraphState:
            """Fetch content from selected sources."""
            sources = state["sources"]
            content = {}
            
            print(f"\nFetching content from {len(sources)} sources")
            for source_name, source_info in sources.items():
                print(f"Fetching from {source_name}...")
                content[source_name] = fetch_content.invoke({"source_info": source_info})
                print(f"Content length: {len(content[source_name])} characters")
            
            return {
                **state,
                "content": content
            }
        
        def chunk_content_node(state: GraphState) -> GraphState:
            """Chunk and annotate the content."""
            content = state["content"]
            sources = state["sources"]
            level = state["level"]
            dimension = state["dimension"]
            
            print(f"\nChunking content for level {level} and dimension {dimension}")
            chunks = []
            for source_name, source_content in content.items():
                source_info = sources[source_name]
                print(f"Chunking content from {source_name}...")
                source_chunks = chunk_rubric.invoke({
                    "content": source_content,
                    "level": level,
                    "dimension": dimension,
                    "company": source_info["company"]
                })
                print(f"Generated {len(source_chunks)} chunks")
                chunks.extend(source_chunks)
            
            return {
                **state,
                "chunks": chunks
            }
        
        def store_chunks_node(state: GraphState) -> GraphState:
            """Store chunks in Qdrant."""
            chunks = state["chunks"]
            print(f"\nStoring {len(chunks)} chunks in Qdrant")
            result = store_chunks.invoke(json.dumps(chunks))
            print(f"Storage result: {result}")
            return {
                **state,
                "result": result
            }
        
        # Create the graph
        graph = Graph()
        
        # Add nodes
        graph.add_node("select_sources", select_sources_node)
        graph.add_node("fetch_content", fetch_content_node)
        graph.add_node("chunk_content", chunk_content_node)
        graph.add_node("store_chunks", store_chunks_node)
        
        # Add edges
        graph.add_edge("select_sources", "fetch_content")
        graph.add_edge("fetch_content", "chunk_content")
        graph.add_edge("chunk_content", "store_chunks")
        
        # Set entry and end points
        graph.set_entry_point("select_sources")
        graph.set_finish_point("store_chunks")
        
        # Compile the graph
        return graph.compile()
    
    def run(self, goal: str) -> Dict[str, Any]:
        """Run the data collection agent with the given goal."""
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
        
        # Run the graph for each level
        results = {}
        for level in levels:
            print(f"\nProcessing level {level}...")
            state: GraphState = {
                "level": level,
                "dimension": dimension_part,
                "sources": {},
                "content": {},
                "chunks": [],
                "result": ""
            }
            final_state = self.graph.invoke(state)
            results[level] = {
                "sources": final_state["sources"],
                "content": {k: len(v) for k, v in final_state["content"].items()},
                "chunks": len(final_state["chunks"]),
                "result": final_state["result"]
            }
        
        return results 