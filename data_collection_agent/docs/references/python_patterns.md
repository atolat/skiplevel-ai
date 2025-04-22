# Python Patterns Reference

This document provides reference examples and explanations of useful Python patterns.

## Dictionary Unpacking (`**` operator)

The `**` operator (double star) is used for dictionary unpacking. It's particularly useful for state management and function arguments.

### Basic Examples

```python
# Example 1: Basic dictionary unpacking
person = {"name": "Alice", "age": 30}
print(**person)  # Equivalent to print(name="Alice", age=30)

# Example 2: Merging dictionaries
default_config = {"timeout": 30, "retries": 3}
user_config = {"timeout": 60}
final_config = {**default_config, **user_config}
# Result: {"timeout": 60, "retries": 3}
```

### State Management Example

```python
class GraphState(TypedDict):
    level: str
    dimension: str
    sources: Dict[str, Dict[str, str]]
    content: Dict[str, str]
    chunks: List[Dict[str, Any]]
    result: str

def select_sources_node(state: GraphState) -> GraphState:
    # state contains all fields
    return {
        **state,  # Unpacks all existing state
        "sources": new_sources  # Updates only what changed
    }
    
    # Equivalent to:
    # return {
    #     "level": state["level"],
    #     "dimension": state["dimension"],
    #     "sources": new_sources,
    #     "content": state["content"],
    #     "chunks": state["chunks"],
    #     "result": state["result"]
    # }
```

### Function Arguments

```python
def greet(name, age):
    print(f"Hello {name}, you are {age} years old")

person = {"name": "Bob", "age": 25}
greet(**person)  # Equivalent to greet(name="Bob", age=25)
```

### Combining with List Unpacking (`*`)

```python
def example(a, b, c, d):
    print(a, b, c, d)

args = [1, 2]
kwargs = {"c": 3, "d": 4}
example(*args, **kwargs)  # Equivalent to example(1, 2, c=3, d=4)
```

## Best Practices

1. **State Management:**
   - Use `**state` to maintain all existing state
   - Only specify fields that need updating
   - Helps prevent accidentally dropping state fields

2. **Function Arguments:**
   - Use `**kwargs` for flexible function parameters
   - Great for configuration objects
   - Makes function calls more readable

3. **Dictionary Merging:**
   - Later dictionaries override earlier ones
   - Useful for default configurations
   - Clean way to combine multiple configs 