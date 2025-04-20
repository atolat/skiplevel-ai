from graph.agent import create_agent
import json
import os
from dotenv import load_dotenv
from load_data import load_data
from tools.rubric_retriever import set_qdrant_client

def main():
    """Run the agent with a sample reflection."""
    # Load environment variables
    load_dotenv()
    
    # Verify LangSmith API key is set
    if not os.getenv("LANGCHAIN_API_KEY"):
        print("Warning: LANGCHAIN_API_KEY not set. Tracing will be disabled.")
    
    # Load synthetic data into Qdrant
    qdrant_client = load_data()
    
    # Set the Qdrant client for the RubricRetrieverTool
    set_qdrant_client(qdrant_client)
    
    # Initialize the agent
    agent = create_agent()
    
    # Visualize the agent
    agent.display()
    
    # Sample reflection
    reflection = """
    I've been leading a team of 3 engineers for the past year. We've successfully 
    delivered 2 major features that increased user engagement by 40%. I've also 
    mentored 2 junior engineers who have grown significantly in their roles. 
    However, I sometimes struggle with technical decision-making and could improve 
    my system design skills.
    """
    
    # Run the agent
    result = agent.invoke({"reflection": reflection})
    
    # Print results
    print("\nEvaluation Results:")
    print(json.dumps(json.loads(result["evaluation"]), indent=2))
    
    print("\nGrowth Advice:")
    print(json.dumps(json.loads(result["advice"]), indent=2))
    
    print("\nRetrieved Rubrics:")
    for i, rubric in enumerate(result["rubrics"], 1):
        print(f"\nChunk {i} (Score: {rubric['score']:.2f}):")
        print(rubric["text"])

if __name__ == "__main__":
    main() 