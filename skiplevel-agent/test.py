import os
from dotenv import load_dotenv
from load_data import load_data
from tools.rubric_retriever import set_qdrant_client, RubricRetrieverTool
from tools.reflection_evaluator import ReflectionEvaluatorTool
from tools.growth_advisor import GrowthAdvisorTool
from graph.agent import create_agent
import json

def test_tools():
    """Test each tool individually."""
    # Load environment variables
    load_dotenv()
    
    # Load synthetic data into Qdrant
    qdrant_client = load_data()
    
    # Set the Qdrant client for the RubricRetrieverTool
    set_qdrant_client(qdrant_client)
    
    # Sample reflection
    reflection = """
    I've been leading a team of 3 engineers for the past year. We've successfully 
    delivered 2 major features that increased user engagement by 40%. I've also 
    mentored 2 junior engineers who have grown significantly in their roles. 
    However, I sometimes struggle with technical decision-making and could improve 
    my system design skills.
    """
    
    # Test RubricRetrieverTool
    print("\n=== Testing RubricRetrieverTool ===")
    retriever = RubricRetrieverTool()
    rubrics = retriever._run(reflection)
    print(f"Retrieved {len(rubrics)} rubric chunks:")
    for i, rubric in enumerate(rubrics, 1):
        print(f"\nChunk {i} (Score: {rubric['score']:.2f}):")
        print(rubric["text"])
    
    # Test ReflectionEvaluatorTool
    print("\n=== Testing ReflectionEvaluatorTool ===")
    evaluator = ReflectionEvaluatorTool()
    evaluation = evaluator._run(reflection, rubrics)
    print("Evaluation:")
    print(json.dumps(json.loads(evaluation), indent=2))
    
    # Test GrowthAdvisorTool
    print("\n=== Testing GrowthAdvisorTool ===")
    advisor = GrowthAdvisorTool()
    advice = advisor._run(evaluation)
    print("Growth Advice:")
    print(json.dumps(json.loads(advice), indent=2))

def test_agent():
    """Test the compiled agent with a sample reflection."""
    # Load environment variables
    load_dotenv()
    
    # Load synthetic data into Qdrant
    qdrant_client = load_data()
    
    # Set the Qdrant client for the RubricRetrieverTool
    set_qdrant_client(qdrant_client)
    
    # Initialize the agent
    agent = create_agent()
    # Display ASCII representation of the graph in terminal
    print(agent.get_graph().draw_ascii())

    # Sample reflection
    reflection = """
    I've been leading a team of 3 engineers for the past year. We've successfully 
    delivered 2 major features that increased user engagement by 40%. I've also 
    mentored 2 junior engineers who have grown significantly in their roles. 
    However, I sometimes struggle with technical decision-making and could improve 
    my system design skills.
    """
    
    # Run the agent
    print("\n=== Testing Compiled Agent ===")
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
    print("Testing individual tools...")
    test_tools()
    print("\n" + "="*50 + "\n")
    print("Testing compiled agent...")
    test_agent() 