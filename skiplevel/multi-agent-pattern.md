# Multi-Agent Systems with LangGraph: Core Concepts

## 1. The Multi-Agent Supervisor Pattern

The multi-agent supervisor pattern is a powerful architectural approach where a group of specialized tools or agents work together under the coordination of a supervisor. Key aspects include:

### Components
- **Supervisor**: An agent responsible for:
  - Task delegation to appropriate team members
  - Monitoring progress
  - Coordinating between different agents
  - Deciding when a task is complete

### Team Structure
- **Specialized Agents**: Each team member has specific capabilities and tools
- **Clear Roles**: Agents are designed for particular tasks (e.g., research, writing, editing)
- **Coordinated Workflow**: Agents work together through supervisor orchestration

### Example Implementation
```python
supervisor_agent = create_team_supervisor(
    llm,
    "You are a supervisor tasked with managing a conversation between the following workers...",
    ["Worker1", "Worker2", "Worker3"],
)
```

## 2. Connecting Multiple Teams with LCEL

LangChain Expression Language (LCEL) enables the composition of multiple agent teams into larger systems:

### Key Features
- **Graph-Based Structure**: Teams are represented as nodes in a larger workflow
- **Hierarchical Organization**: Multiple levels of supervision possible
- **Message Passing**: Teams can communicate through standardized interfaces
- **State Management**: Each team maintains its own state while contributing to the overall system

### Implementation Pattern
```python
# Example structure
super_graph = StateGraph(State)
super_graph.add_node("Team1", team1_chain)
super_graph.add_node("Team2", team2_chain)
super_graph.add_node("supervisor", supervisor_node)
```

## 3. Reusable Utility Functions

Several utility functions make implementing multi-agent systems easier:

### Agent Creation and Management
- `create_agent()`: Creates function-calling agents with specific tools and prompts
- `agent_node()`: Wraps agents into graph nodes
- `create_team_supervisor()`: Generates supervisor agents for team coordination

### State Management
- `prelude()`: Manages working directory and file state
- `get_last_message()`: Extracts recent messages from state
- `join_graph()`: Combines messages from different graph components

### Key Wrapper Functions

#### Team Supervisor Creation
```python
def create_team_supervisor(llm: ChatOpenAI, system_prompt: str, members: List[str]) -> Runnable:
    """Creates a supervisor agent that manages team member selection.
    
    Args:
        llm: The language model to use
        system_prompt: Instructions for the supervisor
        members: List of team member names
    """
    options = ["FINISH"] + members
    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [
                        {"enum": options},
                    ],
                },
            },
            "required": ["next"],
        },
    }
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Given the conversation above, who should act next?"
            " Or should we FINISH? Select one of: {options}"
        ),
    ]).partial(options=str(options), team_members=", ".join(members))
    
    return (
        prompt
        | llm.bind_functions(functions=[function_def], function_call="route")
        | JsonOutputFunctionsParser()
    )

```

#### Agent Creation
```python
def create_agent(
    llm: ChatOpenAI,
    tools: List[BaseTool],
    system_prompt: str,
) -> AgentExecutor:
    """Create a function-calling agent with specific tools and prompt.
    
    Args:
        llm: The language model to use
        tools: List of tools the agent can use
        system_prompt: Instructions for the agent
    """
    system_prompt += (
        "\nWork autonomously according to your specialty, using the tools available to you."
        " Do not ask for clarification."
        " Your other team members (and other teams) will collaborate with you with their own specialties."
        " You are chosen for a reason! You are one of the following team members: {team_members}."
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = create_openai_functions_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools)
    return executor
```

#### Agent Node Creation
```python
def agent_node(state: dict, agent: AgentExecutor, name: str) -> dict:
    """Wraps an agent into a graph node.
    
    Args:
        state: Current state dictionary
        agent: The agent executor to wrap
        name: Name for the agent in messages
    """
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}
```

#### State Management
```python
def get_last_message(state: State) -> str:
    """Extracts the last message from state."""
    return state["messages"][-1].content

def join_graph(response: dict) -> dict:
    """Combines messages from different graph components."""
    return {"messages": [response["messages"][-1]]}

def prelude(state: dict) -> dict:
    """Manages working directory and file state."""
    written_files = []
    if not WORKING_DIRECTORY.exists():
        WORKING_DIRECTORY.mkdir()
    try:
        written_files = [
            f.relative_to(WORKING_DIRECTORY) for f in WORKING_DIRECTORY.rglob("*")
        ]
    except:
        pass
    if not written_files:
        return {**state, "current_files": "No files written."}
    return {
        **state,
        "current_files": "\nBelow are files your team has written to the directory:\n"
        + "\n".join([f" - {f}" for f in written_files]),
    }
```

## Best Practices

1. **Clear Role Definition**: Each agent should have well-defined responsibilities
2. **Proper Tool Assignment**: Agents should only have access to tools they need
3. **State Management**: Maintain clear state transitions between agents
4. **Error Handling**: Implement proper fallbacks and error recovery
5. **Message Standardization**: Use consistent message formats between agents

## Practical Applications

- Research Teams: Combining search and analysis capabilities
- Content Creation: Coordinating writers, editors, and reviewers
- Data Processing: Orchestrating data collection, analysis, and reporting
- Quality Assurance: Managing multiple validation and verification steps

This pattern enables complex workflows while maintaining modularity and scalability in AI systems. 