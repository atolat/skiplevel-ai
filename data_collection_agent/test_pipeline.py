"""Test script for running the data collection pipeline."""

from dotenv import load_dotenv
from data_collection_agent.graph import DataCollectionAgent
import json

def main():
    """Run the data collection pipeline with a sample goal."""
    # Load environment variables
    load_dotenv()
    
    # Create the agent
    agent = DataCollectionAgent()
    
    # Define the goal
    goal = "Collect IC4–IC6 rubric fragments for the Execution dimension."
    
    # Run the agent
    print(f"Running data collection with goal: {goal}")
    results = agent.run(goal)
    
    # Print results
    print("\nResults:")
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

if __name__ == "__main__":
    main() 