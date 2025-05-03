# Agentic Pipeline Reference Implementation

> **Note:** This is a reference implementation using a multi-agent approach. No further development will take place on this codebase. For the active project, see the `content-curation-pipeline` directory.

A pipeline for collecting and curating engineering growth resources using LangGraph and LangChain.

## Overview

This pipeline uses a multi-agent system to:
1. Search for relevant engineering growth resources using Tavily
2. Extract and process content from the discovered resources
3. Curate and organize the collected data

## Installation

```bash
# Install the package
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Usage

```python
from data_collection_pipeline import data_pipeline_chain

# Run the pipeline
test_query = "Find the latest public documents on engineering promotion rubrics at top tech companies"
for step in data_pipeline_chain.stream(test_query, {"recursion_limit": 100}):  
    if "__end__" not in step:
        print(step)
        print("---")
```

## Development

- Format code: `black .`
- Sort imports: `isort .`
- Type check: `mypy .`
- Lint: `ruff check .`
- Test: `pytest`

## License

MIT 