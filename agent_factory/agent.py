"""Simple agent implementation for Agent Factory."""

import os
from typing import Optional
from dotenv import load_dotenv

from .config import AgentConfig
from .llm import BaseLLM, get_llm
from .tools import get_tool


class BaseAgent:
    """Base agent class that provides simple chat functionality."""
    
    def __init__(self, config: AgentConfig, llm: Optional[BaseLLM] = None):
        """Initialize the agent with configuration.
        
        Args:
            config: Validated agent configuration
            llm: Optional LLM instance, will create one if not provided
        """
        self.config = config
        self.llm = llm
        
        # Load available tools
        self.available_tools = {}
        tool_names = getattr(config, 'tools', [])
        for tool_name in tool_names:
            tool = get_tool(tool_name)
            if tool:
                self.available_tools[tool_name] = tool
            else:
                print(f"Warning: Tool '{tool_name}' not found")
        
        # Create LLM if not provided
        if self.llm is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.llm = get_llm(
                    provider=config.llm.provider,
                    api_key=api_key,
                    model_name=config.llm.model_name
                )
    
    def chat(self, message: str) -> str:
        """Chat with the agent.
        
        Args:
            message: User message to respond to
            
        Returns:
            Agent response string
        """
        # Use LLM if available
        if self.llm:
            description = self.config.description or "a helpful assistant"
            
            # Build prompt with tools information
            prompt = f"You are {self.config.name}. {description}\n\n"
            
            # Add tools information if available
            if self.available_tools:
                tool_names = list(self.available_tools.keys())
                tool_descriptions = []
                for name, tool in self.available_tools.items():
                    tool_descriptions.append(f"{name}: {tool.description}")
                prompt += f"Available tools: {', '.join(tool_names)}\n"
                prompt += "Tool descriptions:\n" + "\n".join(tool_descriptions) + "\n\n"
                prompt += "If you need to use a tool, respond with TOOL: tool_name INPUT: input_data\n\n"
            
            prompt += f"User: {message}\nAgent:"
            
            response = self.llm.generate(
                prompt=prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # Check if response contains tool usage
            if "TOOL:" in response:
                lines = response.split('\n')
                for line in lines:
                    if line.strip().startswith("TOOL:"):
                        try:
                            # Extract tool name and input
                            tool_part = line.split("TOOL:")[1].strip()
                            if "INPUT:" in tool_part:
                                tool_name = tool_part.split("INPUT:")[0].strip()
                                tool_input = tool_part.split("INPUT:")[1].strip()
                            else:
                                tool_name = tool_part
                                tool_input = ""
                            
                            # Execute tool
                            tool_result = self.use_tool(tool_name, tool_input)
                            
                            # Append tool result to response
                            response += f"\n\nTool Result: {tool_result}"
                            
                        except Exception as e:
                            response += f"\n\nTool Error: {str(e)}"
            
            return response
        
        # Fallback to original behavior if no LLM
        return f"Hello! I'm {self.config.name}. You said: {message}"
    
    def use_tool(self, tool_name: str, input_data: str) -> str:
        """Use a tool with the given input data.
        
        Args:
            tool_name: Name of the tool to use
            input_data: Input data for the tool
            
        Returns:
            Tool execution result or error message
        """
        if tool_name not in self.available_tools:
            return f"Error: Tool '{tool_name}' is not available. Available tools: {list(self.available_tools.keys())}"
        
        tool = self.available_tools[tool_name]
        return tool.execute(input_data)
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"BaseAgent(name='{self.config.name}', id='{self.config.agent_id}')"


def create_agent(config: AgentConfig) -> BaseAgent:
    """Create an agent instance from configuration.
    
    Args:
        config: Validated agent configuration
        
    Returns:
        BaseAgent instance
    """
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Create LLM if API key is available
    llm = None
    if api_key:
        llm = get_llm(
            provider=config.llm.provider,
            api_key=api_key,
            model_name=config.llm.model_name
        )
    
    return BaseAgent(config, llm) 