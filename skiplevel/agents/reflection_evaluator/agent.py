# TODO: Implement reflection evaluator agent

from typing import List
from langchain_openai import ChatOpenAI
from core.agent_helpers import create_agent
from .tools.reflection_evaluator import reflection_evaluator
from .tools.rubric_retriever import rubric_retriever

def create_reflection_evaluator_agent(llm: ChatOpenAI):
    """
    Creates an agent that evaluates engineer reflections against role-specific rubrics.
    
    The agent follows a two-step process:
    1. Retrieves relevant rubric chunks using semantic search
    2. Evaluates the reflection against the retrieved rubrics
    
    Args:
        llm: The language model to use for the agent
        
    Returns:
        An agent that can evaluate reflections
    """
    # Define the system prompt
    system_prompt = """You are an AI performance review assistant. Your task is to evaluate an engineer's self-reflection against relevant role expectations.

Follow these steps:
1. First, use the rubric_retriever tool to find relevant rubric chunks that match the reflection's content
2. Then, use the reflection_evaluator tool to evaluate the reflection against the retrieved rubrics

The rubric_retriever will return a list of relevant rubric chunks with similarity scores.
The reflection_evaluator will help you analyze the reflection against these rubrics.

Your final evaluation should be comprehensive and actionable, focusing on:
- Overall assessment of growth and impact
- Key strengths demonstrated
- Areas for improvement
- Specific recommendations based on the rubric expectations

Be specific and provide concrete examples from the reflection where possible."""

    # Create the agent with both tools
    agent = create_agent(
        llm=llm,
        tools=[rubric_retriever, reflection_evaluator],
        system_prompt=system_prompt
    )
    
    return agent
