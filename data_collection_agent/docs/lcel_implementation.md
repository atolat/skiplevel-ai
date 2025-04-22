# Data Collection Agent: LCEL Implementation

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture](#architecture)
   - [Pipeline Overview](#pipeline-overview)
   - [Component Design](#component-design)
3. [Core Components](#core-components)
   - [Source Selection](#source-selection)
   - [Content Fetching](#content-fetching)
   - [Content Chunking](#content-chunking)
   - [Chunk Storage](#chunk-storage)
4. [Implementation Details](#implementation-details)
   - [State Management](#state-management)
   - [Async Operations](#async-operations)
   - [Error Handling](#error-handling)
5. [Usage Guide](#usage-guide)
   - [Basic Usage](#basic-usage)
   - [Advanced Configuration](#advanced-configuration)
6. [Development](#development)
   - [Extending the Pipeline](#extending-the-pipeline)
   - [Testing](#testing)
7. [Reference](#reference)

## Introduction

The Data Collection Agent is a tool designed to collect and process engineering career rubrics. It uses LangChain Expression Language (LCEL) to create a declarative, asynchronous pipeline that efficiently handles the collection and processing of rubric data.

### Key Features

- **Declarative Pipeline**: Clear, readable pipeline definition using LCEL
- **Async Operations**: Concurrent processing for better performance
- **Type Safety**: Strong typing throughout the implementation
- **Extensible Design**: Easy to add or modify pipeline steps

## Architecture

### Pipeline Overview

The agent implements a four-step pipeline:

1. **Source Selection**: Identify relevant sources based on level and dimension
2. **Content Fetching**: Retrieve content from selected sources
3. **Content Chunking**: Process content into meaningful chunks
4. **Chunk Storage**: Store processed chunks in Qdrant

```python
pipeline = (
    RunnablePassthrough()
    | select_sources_step
    | fetch_content_step
    | generate_chunks_step
    | store_chunks_step
)
```

### Component Design

Each component in the pipeline is designed as a standalone tool with:
- Clear input/output interfaces
- Async support for concurrent operations
- Comprehensive error handling
- Type hints for better development experience

## Core Components

### Source Selection

**Tool**: `select_sources`

```python
@tool
def select_sources(level: str, dimension: str) -> Dict[str, Dict[str, str]]:
    """Select relevant sources based on level and dimension."""
    # Implementation details...
```

**Features**:
- Level and dimension-based source selection
- Predefined source list management
- Error handling for invalid inputs

### Content Fetching

**Tool**: `fetch_content`

```python
@tool
async def fetch_content(source_info: Dict[str, str]) -> str:
    """Fetch content from a source using Tavily."""
    # Implementation details...
```

**Features**:
- Tavily integration for content fetching
- Concurrent fetching of multiple sources
- Support for various content types (HTML, PDF)

### Content Chunking

**Tool**: `chunk_rubric`

```python
@tool
async def chunk_rubric(
    content: str,
    level: str,
    dimension: str,
    company: str
) -> List[Dict[str, Any]]:
    """Generate chunks from content using LLM."""
    # Implementation details...
```

**Features**:
- LLM-powered chunking
- Context-aware chunk generation
- Concurrent processing of multiple sources

### Chunk Storage

**Tool**: `store_chunks`

```python
@tool
def store_chunks(chunks: str) -> str:
    """Store chunks in Qdrant with embeddings."""
    # Implementation details...
```

**Features**:
- Qdrant integration
- Embedding generation
- Batch storage operations

## Implementation Details

### State Management

The pipeline maintains state throughout execution:

```python
state = {
    "level": level,
    "dimension": dimension,
    "sources": {...},
    "content": {...},
    "chunks": [...],
    "result": "..."
}
```

Each step preserves state using dictionary unpacking:
```python
async def process_sources(x: Dict[str, Any]) -> Dict[str, Any]:
    content = await process_sources(x["sources"])
    return {**x, "content": content}
```

### Async Operations

The implementation uses async operations for improved performance:

```python
async def process_sources(sources: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    content = {}
    tasks = []
    for source_name, source_info in sources.items():
        tasks.append(fetch_content.ainvoke({"source_info": source_info}))
    
    results = await asyncio.gather(*tasks)
    for source_name, result in zip(sources.keys(), results):
        content[source_name] = result
    return content
```

### Error Handling

Each component implements comprehensive error handling:

```python
@tool
async def fetch_content(source_info: Dict[str, str]) -> str:
    try:
        # Fetch content
        return content
    except NetworkError as e:
        raise ToolError(f"Failed to fetch content: {e}")
    except InvalidContentError as e:
        raise ToolError(f"Invalid content format: {e}")
```

## Usage Guide

### Basic Usage

```python
from data_collection_agent import DataCollectionAgent

# Create agent
agent = DataCollectionAgent()

# Run pipeline
goal = "Collect IC4–IC6 rubric fragments for the Execution dimension."
results = await agent.arun(goal)
```

### Advanced Configuration

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

## Development

### Extending the Pipeline

To add a new step to the pipeline:

1. Create a new tool:
```python
@tool
async def new_step(input_data: Dict[str, Any]) -> Dict[str, Any]:
    # Implementation
    return result
```

2. Add it to the pipeline:
```python
pipeline = (
    RunnablePassthrough()
    | existing_steps
    | new_step
)
```

### Testing

Run the test suite:
```bash
python -m pytest tests/
```

## Reference

- [LangChain Expression Language Documentation](https://python.langchain.com/docs/expression_language/)
- [Tavily API Documentation](https://tavily.com/docs)
- [Qdrant Documentation](https://qdrant.tech/documentation/) 