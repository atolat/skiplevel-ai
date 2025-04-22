"""Main graph implementation for the data collection agent."""

from typing import Dict, Any, List
from langgraph.graph import Graph
from langchain_core.messages import HumanMessage

from .tools.source_selector import SourceSelectorTool
from .tools.content_fetcher import ContentFetcherTool
from .tools.rubric_chunker import RubricChunkerTool
from .tools.qdrant_writer import QdrantWriterTool

class DataCollectionAgent:
    """Agent for collecting and ingesting engineering career rubrics."""
    
    def __init__(self):
        self.source_selector = SourceSelectorTool()
        self.content_fetcher = ContentFetcherTool()
        self.rubric_chunker = RubricChunkerTool()
        self.qdrant_writer = QdrantWriterTool()
        
        # Define the graph
        self.graph = self._create_graph()
    
    def _create_graph(self) -> Graph:
        """Create the data collection graph."""
        
        def select_sources(state: Dict[str, Any]) -> Dict[str, Any]:
            """Select appropriate sources based on the goal."""
            level = state["level"]
            dimension = state["dimension"]
            
            print(f"\nSelecting sources for level {level} and dimension {dimension}")
            sources = self.source_selector._run(level, dimension)
            print(f"Selected sources: {sources}")
            
            return {**state, "sources": sources}
        
        def fetch_content(state: Dict[str, Any]) -> Dict[str, Any]:
            """Fetch content from selected sources."""
            sources = state["sources"]
            content = {}
            
            print(f"\nFetching content from {len(sources)} sources")
            for source_name, source_info in sources.items():
                print(f"Fetching from {source_name}...")
                content[source_name] = self.content_fetcher._run(source_info)
                print(f"Content length: {len(content[source_name])} characters")
            
            return {**state, "content": content}
        
        def chunk_content(state: Dict[str, Any]) -> Dict[str, Any]:
            """Chunk and annotate the content."""
            content = state["content"]
            level = state["level"]
            dimension = state["dimension"]
            chunks = []
            
            print(f"\nChunking content for level {level} and dimension {dimension}")
            for source_name, source_content in content.items():
                source_info = state["sources"][source_name]
                print(f"Chunking content from {source_name}...")
                source_chunks = self.rubric_chunker._run(
                    content=source_content,
                    level=level,
                    dimension=dimension,
                    company=source_info["company"]
                )
                print(f"Generated {len(source_chunks)} chunks")
                chunks.extend(source_chunks)
            
            return {**state, "chunks": chunks}
        
        def store_chunks(state: Dict[str, Any]) -> Dict[str, Any]:
            """Store chunks in Qdrant."""
            chunks = state["chunks"]
            
            print(f"\nStoring {len(chunks)} chunks in Qdrant")
            result = self.qdrant_writer._run(chunks)
            print(f"Storage result: {result}")
            
            return {**state, "result": result}
        
        # Create the graph
        graph = Graph()
        
        # Add nodes
        graph.add_node("select_sources", select_sources)
        graph.add_node("fetch_content", fetch_content)
        graph.add_node("chunk_content", chunk_content)
        graph.add_node("store_chunks", store_chunks)
        
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
        # Example: "Collect IC4–IC6 rubric fragments for the Execution dimension."
        parts = goal.split("for the")
        level_part = parts[0].strip().replace("Collect", "").strip()
        dimension_part = parts[1].strip().replace("dimension.", "").strip()
        
        # Extract level range
        if "–" in level_part:
            # Split on the en dash and take only the level parts
            start_level, end_level = level_part.split("–")
            start_level = start_level.strip().replace("IC", "")
            end_level = end_level.strip().split()[0].replace("IC", "")  # Take only the level number
            levels = [f"IC{i}" for i in range(
                int(start_level),
                int(end_level) + 1
            )]
        else:
            # Handle single level case
            level = level_part.strip().split()[0]  # Take only the level part
            levels = [level]
        
        # Run the graph for each level
        results = {}
        for level in levels:
            print(f"\nProcessing level {level}...")
            state = {
                "level": level,
                "dimension": dimension_part
            }
            final_state = self.graph.invoke(state)
            results[level] = {
                "sources": final_state.get("sources", {}),
                "content": {k: len(v) for k, v in final_state.get("content", {}).items()},
                "chunks": len(final_state.get("chunks", [])),
                "result": final_state.get("result", "")
            }
        
        return results 