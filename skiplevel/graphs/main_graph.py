# TODO: Implement main agent graph

import functools
from typing import Dict, Any, List, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
import os

from agents.reflection_evaluator.agent import create_reflection_evaluator_agent
from core.agent_helpers import agent_node

# Import the AgentState from models.types
from models.types import AgentState

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4-turbo-preview")

# Create the Reflection Evaluation Agent
reflection_agent = create_reflection_evaluator_agent(llm)

# Create the Reflection Node
def run_reflection_agent(state: AgentState) -> AgentState:
    print("\n🧠 Entered run_reflection_agent node")
    print(f"📝 Initial state: {state}")
    
    # Pass the AgentState directly to agent_node
    # The agent_node function handles both dict and AgentState objects
    result = agent_node(state, reflection_agent, "reflection_evaluator")
    
    print(f"📝 Result from agent_node: {result}")
    
    # Convert result back to AgentState
    return AgentState(
        messages=result.get("messages", []),
        reflection_text=result.get("reflection_text", ""),
        evaluation_result=result.get("reflection_evaluator", None),
        growth_advice=result.get("growth_advice", None)
    )

# Initialize the graph with AgentState
dag = StateGraph(AgentState)

# Add the ReflectionEvaluator node
dag.add_node("evaluate_reflection", run_reflection_agent)

# Set entry point to ReflectionEvaluator
dag.set_entry_point("evaluate_reflection")

# Add conditional edge from reflection_evaluator to END
dag.add_edge("evaluate_reflection", END)

# Compile the graph
compiled_dag = dag.compile()

# Print the raw graph structure
print("\nRaw Graph Structure:")
print("===================")
print(f"Nodes: {list(compiled_dag.get_graph().nodes)}")
print(f"Edges: {list(compiled_dag.get_graph().edges)}")
print("===================\n")

# Visualize the graph
def visualize_graph():
    """Generate and save a visualization of the DAG."""
    try:
        # Get the graph structure
        graph = compiled_dag.get_graph()
        
        # Print the raw graph structure for debugging
        print("\nRaw Graph Structure:")
        print("===================")
        print(f"Nodes: {list(graph.nodes)}")
        print(f"Edges: {list(graph.edges)}")
        print("===================\n")
        
        # Print a simple text representation of our graph
        print("\nGraph Structure:")
        print("===============")
        print("Entry Point: evaluate_reflection")
        print("Nodes:")
        print("- evaluate_reflection (Entry Point)")
        print("- END")
        print("\nEdges:")
        print("evaluate_reflection -> END (via FINISH)")
        print("===============\n")
        print(graph.draw_ascii())
        
    except Exception as e:
        print(f"❌ Error generating graph visualization: {str(e)}")
        print(f"Error details: {str(e.__cause__) if hasattr(e, '__cause__') else 'No additional details'}")

# Generate the visualization when this module is imported
visualize_graph()
