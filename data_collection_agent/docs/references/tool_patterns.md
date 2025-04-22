# LangChain Tool Patterns

This document provides reference examples of different tool patterns using the `@tool` decorator.

## Basic Tool Pattern

```python
from typing import Dict
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Optional: Define input schema for validation
class MyToolInput(BaseModel):
    param1: str = Field(..., description="Description of param1")
    param2: int = Field(..., description="Description of param2")

# Basic tool with schema
@tool("my_tool", args_schema=MyToolInput)
def my_tool(param1: str, param2: int) -> Dict[str, str]:
    """Tool description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Dictionary with results
    """
    # Tool implementation
    return {"result": f"Processed {param1} with {param2}"}

# Basic tool without schema
@tool("simple_tool")
def simple_tool(input: str) -> str:
    """Simple tool that takes a string and returns a string."""
    return f"Processed: {input}"
```

## Tool with State Management (Graph Node)

```python
from typing import Dict, Any
from langgraph.graph import Graph

# The tool itself remains simple
@tool("state_aware_tool")
def state_aware_tool(value: str) -> Dict[str, str]:
    """Tool that will be used in a stateful context."""
    return {"processed": value}

# The graph node handles state
def state_aware_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node that manages state for the tool."""
    # 1. Read from state
    input_value = state["input"]
    
    # 2. Call the tool
    result = state_aware_tool(input_value)
    
    # 3. Update state
    return {**state, "output": result}

# Example graph setup
graph = Graph()
graph.add_node("process", state_aware_node)
```

## Tool with Message Handling

```python
from typing import Dict, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool

@tool("message_tool")
def message_tool(messages: List[Dict]) -> str:
    """Tool that processes a list of messages."""
    # Process messages
    return "Response based on messages"

# Example usage in a chain
messages = [
    HumanMessage(content="Hello"),
    AIMessage(content="Hi there!")
]
result = message_tool(messages)
```

## Tool with Error Handling

```python
from typing import Dict, Optional
from langchain_core.tools import tool

@tool("error_handling_tool")
def error_handling_tool(input: str) -> Dict[str, Optional[str]]:
    """Tool with error handling."""
    try:
        # Tool implementation
        result = f"Processed: {input}"
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

## Tool Composition

```python
from typing import Dict
from langchain_core.tools import tool

@tool("first_tool")
def first_tool(input: str) -> str:
    """First tool in the chain."""
    return f"First: {input}"

@tool("second_tool")
def second_tool(input: str) -> str:
    """Second tool in the chain."""
    return f"Second: {input}"

# Example composition
def composed_tools(input: str) -> str:
    """Example of tool composition."""
    result1 = first_tool(input)
    result2 = second_tool(result1)
    return result2
```

## Notes

1. Tools should be focused and do one thing well
2. State management belongs in graph nodes, not tools
3. Tools can be composed to build more complex functionality
4. Always include good documentation and type hints
5. Consider error handling in your tools
6. Use Pydantic models for input validation when needed 