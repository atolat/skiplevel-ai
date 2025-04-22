"""Test script for running the data collection pipeline.

Note: The previous graph-based implementation has been moved to the reference directory
(data_collection_agent/reference/graph.py) and can be used as a reference if needed.
"""

from dotenv import load_dotenv
from data_collection_agent.pipeline import DataCollectionAgent
import json
import asyncio

def print_results(results: dict, implementation: str):
    """Print the results in a formatted way."""
    print(f"\nResults from {implementation}:")
    for level, result in results.items():
        print(f"\nLevel {level}:")
        print("Sources:")
        for source_name, source_info in result["sources"].items():
            print(f"  - {source_name}:")
            print(f"    URL: {source_info['url']}")
            print(f"    Type: {source_info['type']}")
            print(f"    Company: {source_info['company']}")
        
        print("\nContent Lengths:")
        for source_name, length in result["content"].items():
            print(f"  - {source_name}: {length:,} characters")
        
        print(f"\nChunks Generated: {result['chunks']}")
        print(f"Storage Result: {result['result']}")
        print("-" * 80)

async def main():
    """Run the data collection pipeline with a sample goal."""
    # Load environment variables
    load_dotenv()
    
    # Define the goal
    goal = "Collect IC4–IC6 rubric fragments for the Execution dimension."
    print(f"Running data collection with goal: {goal}")
    
    # Run the LCEL-based implementation
    print("\nRunning LCEL-based implementation...")
    agent = DataCollectionAgent()
    results = await agent.arun(goal)
    print_results(results, "LCEL Implementation")

if __name__ == "__main__":
    asyncio.run(main()) 