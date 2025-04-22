# Usage Guide

This section provides information on how to use the Data Collection Agent.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/data-collection-agent.git
cd data-collection-agent
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Basic Usage

```python
from data_collection_agent import DataCollectionAgent

# Create agent
agent = DataCollectionAgent()

# Run pipeline
goal = "Collect IC4–IC6 rubric fragments for the Execution dimension."
results = await agent.arun(goal)
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `TAVILY_API_KEY`: Your Tavily API key
- `QDRANT_URL`: Qdrant server URL
- `QDRANT_API_KEY`: Qdrant API key

### Pipeline Configuration

You can customize the pipeline by modifying the steps:

```python
# Custom pipeline configuration
pipeline = (
    RunnablePassthrough()
    | select_sources_step
    | {"content": fetch_content_step}
    | {"chunks": generate_chunks_step}
    | store_chunks_step
)
```

## Examples

### Basic Collection

```python
from data_collection_agent import DataCollectionAgent

agent = DataCollectionAgent()
results = await agent.arun(
    "Collect IC4–IC6 rubric fragments for the Execution dimension."
)
```

### Custom Source Selection

```python
from data_collection_agent.tools import select_sources

sources = select_sources.invoke({
    "level": "IC4",
    "dimension": "Execution"
})
```

## Error Handling

The agent provides comprehensive error handling:

```python
try:
    results = await agent.arun(goal)
except ToolError as e:
    print(f"Tool error: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Related Documentation

- [Architecture](./../architecture/README.md)
- [Implementation](./../implementation/README.md)
- [API Reference](./../api/README.md) 