# API Reference

This section provides detailed documentation for the Data Collection Agent's API.

## DataCollectionAgent

The main class for running the data collection pipeline.

### Methods

#### `__init__(self)`
Initialize the Data Collection Agent.

#### `arun(self, goal: str) -> Dict[str, Any]`
Run the data collection pipeline asynchronously.

**Parameters:**
- `goal` (str): The goal describing what data to collect (e.g., "Collect IC4–IC6 rubric fragments for the Execution dimension")

**Returns:**
- `Dict[str, Any]`: Results containing collected data and metadata

**Example:**
```python
agent = DataCollectionAgent()
results = await agent.arun("Collect IC4–IC6 rubric fragments for the Execution dimension")
```

## Tools

### select_sources

Selects relevant sources based on level and dimension.

**Parameters:**
- `level` (str): The career level (e.g., "IC4")
- `dimension` (str): The dimension to collect data for (e.g., "Execution")

**Returns:**
- `List[Dict[str, str]]`: List of selected sources with metadata

**Example:**
```python
sources = select_sources.invoke({
    "level": "IC4",
    "dimension": "Execution"
})
```

### fetch_content

Fetches content from a source asynchronously.

**Parameters:**
- `source` (Dict[str, str]): Source metadata including URL and type

**Returns:**
- `str`: Fetched content

**Example:**
```python
content = await fetch_content.ainvoke({
    "url": "https://example.com/rubric",
    "type": "web"
})
```

### chunk_rubric

Generates chunks from content asynchronously.

**Parameters:**
- `content` (str): The content to chunk
- `level` (str): The career level
- `dimension` (str): The dimension

**Returns:**
- `List[Dict[str, Any]]`: List of chunks with metadata

**Example:**
```python
chunks = await chunk_rubric.ainvoke({
    "content": "Rubric content...",
    "level": "IC4",
    "dimension": "Execution"
})
```

### store_chunks

Stores chunks in Qdrant with embeddings.

**Parameters:**
- `chunks` (List[Dict[str, Any]]): List of chunks to store

**Returns:**
- `Dict[str, Any]`: Storage operation results

**Example:**
```python
result = store_chunks.invoke([
    {
        "content": "Chunk content...",
        "metadata": {
            "level": "IC4",
            "dimension": "Execution"
        }
    }
])
```

## Types

### Chunk
```python
class Chunk(TypedDict):
    content: str
    metadata: Dict[str, Any]
```

### Source
```python
class Source(TypedDict):
    url: str
    type: str
    metadata: Dict[str, Any]
```

## Related Documentation

- [Architecture](./../architecture/README.md)
- [Implementation](./../implementation/README.md)
- [Usage Guide](./../usage/README.md) 