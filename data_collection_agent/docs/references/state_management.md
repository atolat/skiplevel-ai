# State Management in LangGraph

This document provides reference examples and explanations of different state management patterns in LangGraph.

## State Flow Diagram

Here's a visualization of how state flows through our data collection pipeline:

```
Initial State
┌─────────────────────────────────────────────┐
│ level: "IC4"                                │
│ dimension: "Execution"                      │
│ sources: []                                 │
│ content: []                                 │
│ chunks: []                                  │
│ result: ""                                  │
└─────────────────────────────────────────────┘
        │
        ▼
select_sources_node
┌─────────────────────────────────────────────┐
│ sources: [{source1: {...}, source2: {...}}] │
└─────────────────────────────────────────────┘
        │
        ▼
fetch_content_node
┌─────────────────────────────────────────────┐
│ content: [{source1: "content1", ...}]       │
└─────────────────────────────────────────────┘
        │
        ▼
chunk_content_node
┌─────────────────────────────────────────────┐
│ chunks: [{chunk1: {...}, chunk2: {...}}]    │
└─────────────────────────────────────────────┘
        │
        ▼
store_chunks_node
┌─────────────────────────────────────────────┐
│ result: "success"                           │
└─────────────────────────────────────────────┘

Final State
┌─────────────────────────────────────────────┐
│ level: "IC4"                                │
│ dimension: "Execution"                      │
│ sources: [{source1: {...}, source2: {...}}] │
│ content: [{source1: "content1", ...}]       │
│ chunks: [{chunk1: {...}, chunk2: {...}}]    │
│ result: "success"                           │
└─────────────────────────────────────────────┘
```

Key points about the state flow:
- Each node only returns the new state it creates
- Previous state is automatically maintained
- Lists (sources, content, chunks) are appended
- Single values (result) are replaced
- The final state contains the complete history

## Basic State Pattern

```python
from typing import TypedDict, Dict, Any

class BasicState(TypedDict):
    input: str
    output: str

def basic_node(state: BasicState) -> BasicState:
    """Node that manually manages state."""
    # Process input
    result = process(state["input"])
    
    # Return new state with all fields
    return {
        "input": state["input"],  # Maintain previous state
        "output": result          # Add new state
    }
```

## Annotated State Pattern (Recommended)

```python
from typing import TypedDict, Annotated, List

class AnnotatedState(TypedDict):
    messages: Annotated[List[str], "append"]  # Will append new messages
    count: Annotated[int, "add"]              # Will add to existing count
    current: str                              # Will replace current value

def annotated_node(state: AnnotatedState) -> Dict[str, Any]:
    """Node that returns only new state values."""
    # Only return new values, LangGraph handles state management
    return {
        "messages": ["new message"],
        "count": 1
    }
```

## State Management Strategies

1. **Append** (`Annotated[List[T], "append"]`):
   - Adds new items to a list
   - Example: Chat history, processing steps
   ```python
   class ChatState(TypedDict):
       messages: Annotated[List[Dict[str, str]], "append"]
   
   def chat_node(state: ChatState) -> Dict[str, List[Dict[str, str]]]:
       return {"messages": [{"role": "user", "content": "Hello"}]}
   ```

2. **Add** (`Annotated[int, "add"]`):
   - Adds to numeric values
   - Example: Counters, totals
   ```python
   class CounterState(TypedDict):
       total: Annotated[int, "add"]
   
   def counter_node(state: CounterState) -> Dict[str, int]:
       return {"total": 1}
   ```

3. **Replace** (default behavior):
   - Replaces existing values
   - Example: Current status, latest result
   ```python
   class StatusState(TypedDict):
       current_status: str
   
   def status_node(state: StatusState) -> Dict[str, str]:
       return {"current_status": "processing"}
   ```

## State Access Patterns

1. **Accessing Latest State**:
   ```python
   # For lists
   latest_message = state["messages"][-1]
   
   # For counters
   current_count = state["total"]
   
   # For single values
   current_status = state["status"]
   ```

2. **Initial State Setup**:
   ```python
   initial_state: GraphState = {
       "messages": [],      # Initialize lists as empty
       "total": 0,         # Initialize counters as 0
       "status": "ready"   # Initialize single values
   }
   ```

3. **Result Processing**:
   ```python
   results = {
       "latest_message": state["messages"][-1] if state["messages"] else None,
       "total_count": state["total"],
       "final_status": state["status"]
   }
   ```

## Best Practices

1. **State Definition**:
   - Use `TypedDict` for type safety
   - Use `Annotated` for list/counter fields
   - Document state structure clearly

2. **Node Implementation**:
   - Return only new values
   - Let LangGraph handle state management
   - Access latest state with `[-1]` for lists

3. **State Access**:
   - Always check if lists are empty before accessing
   - Use type hints for better IDE support
   - Document state access patterns

4. **Error Handling**:
   - Handle missing state gracefully
   - Provide default values where appropriate
   - Validate state before processing

## Example: Data Collection Pipeline

```python
class GraphState(TypedDict):
    level: str
    dimension: str
    sources: Annotated[List[Dict[str, Dict[str, str]]], "append"]
    content: Annotated[List[Dict[str, str]], "append"]
    chunks: Annotated[List[Dict[str, Any]], "append"]
    result: str

def select_sources_node(state: GraphState) -> Dict[str, List[Dict[str, Dict[str, str]]]]:
    """Node that selects sources."""
    # Only return new sources
    return {"sources": [new_sources]}

def fetch_content_node(state: GraphState) -> Dict[str, List[Dict[str, str]]]:
    """Node that fetches content."""
    # Access latest sources
    sources = state["sources"][-1]
    # Return new content
    return {"content": [new_content]}
``` 