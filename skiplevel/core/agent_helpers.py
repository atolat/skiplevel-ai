from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable
import functools

def create_agent(llm: ChatOpenAI, tools: List[Any], system_prompt: str) -> AgentExecutor:
    """
    Creates a LangChain agent with the specified LLM and tools.
    
    Args:
        llm: The language model to use
        tools: List of tools available to the agent
        system_prompt: Base system prompt for the agent
        
    Returns:
        AgentExecutor: Configured agent executor
    """
    # Append autonomy instruction to system prompt
    full_system_prompt = f"{system_prompt}\n\nWork autonomously according to your specialty, using the tools available to you. Do not ask for clarification. Your other team members will collaborate based on their own specialties."
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", full_system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    
    # Return agent executor
    return AgentExecutor(agent=agent, tools=tools)

def agent_node(state: Dict[str, Any], agent: AgentExecutor, name: str) -> Dict[str, Any]:
    """Invoke agent and wrap output in expected format."""
    print(f"📝 Input state: {state}")
    
    # Convert state to dict if it's an AgentState object
    if hasattr(state, '__dict__'):
        state_dict = state.__dict__
    else:
        state_dict = state

    result = agent.invoke(state_dict)
    print(f"📝 Agent result: {result}")

    # Update state with the result
    if isinstance(result, dict):
        # If there's an output field, use it as the reflection_evaluator
        if 'output' in result:
            updated_state = {**state_dict, "reflection_evaluator": result['output']}
        else:
            # Merge the result with the current state
            updated_state = {**state_dict, **result}
    else:
        # Add the result to the state
        updated_state = {**state_dict, "reflection_evaluator": result}
    
    print(f"📝 Updated state: {updated_state}")
    return updated_state

def create_team_supervisor(llm: ChatOpenAI, system_prompt: str, members: List[str]) -> Runnable:
    """
    Creates a router agent for team supervision.
    
    Args:
        llm: The language model to use
        system_prompt: System prompt for the supervisor
        members: List of team member names
        
    Returns:
        Runnable: Configured router agent
    """
    # Create enum for routing options
    options = ["FINISH"] + members
    options_str = " | ".join(f'"{opt}"' for opt in options)
    
    # Create function schema for routing
    function_schema = {
        "name": "route",
        "description": "Select next team member to handle the task or finish",
        "parameters": {
            "type": "object",
            "properties": {
                "next": {
                    "type": "string",
                    "enum": options,
                    "description": "Next team member to handle the task, or FINISH if complete"
                }
            },
            "required": ["next"]
        }
    }
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    # Create and return the chain
    return (
        prompt
        | llm.bind(functions=[function_schema])
        | JsonOutputParser()
    ) 