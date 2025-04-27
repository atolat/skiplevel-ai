# File: skiplevel/agents/reflection_evaluator/agent.py
# TODO: Implement reflection evaluator agent

from typing import List
from langchain_openai import ChatOpenAI
from core.agent_helpers import create_agent
from .tools.rubric_retriever import rubric_retriever
from .tools.reflection_evaluator import reflection_evaluator
from .tools.rubric_searcher import rubric_searcher

def create_reflection_evaluator_agent(llm: ChatOpenAI):
    """
    Creates a reflection evaluator agent that can analyze engineer reflections.
    
    The agent uses multiple tools to:
    1. First try to retrieve relevant rubrics from internal database
    2. If needed, search for additional rubrics using web search
    3. Evaluate reflections against the collected rubrics
    
    Args:
        llm: The language model to use for the agent
        
    Returns:
        AgentExecutor: The configured reflection evaluator agent
    """
    return create_agent(
        llm=llm,
        system_prompt="""You are an AI performance review assistant. Your task is to evaluate an engineer's self-reflection against role expectations.

Follow these steps:
1. First, use the rubric_retriever tool to find relevant rubric chunks that match the reflection's content.
2. If rubric_retriever returns no results or insufficient information, use the rubric_searcher tool to perform a web search for relevant role expectations.
3. Then, use the reflection_evaluator tool to evaluate the reflection against the retrieved or searched rubrics.

The rubric_retriever returns rubric snippets from an internal database.
The rubric_searcher queries external information sources via web search.

Your final evaluation must include:
- A concise overall assessment
- Key strengths demonstrated
- Areas for improvement
- Specific actionable recommendations

Be specific and tie feedback closely to the rubrics or search results wherever possible. Stay professional and structured in tone.""",
        tools=[rubric_retriever, reflection_evaluator, rubric_searcher]
    )
