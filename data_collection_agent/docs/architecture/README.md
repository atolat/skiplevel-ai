# Architecture

This document describes the architecture of the Data Collection Agent.

## Overview

The Data Collection Agent is designed to collect and process engineering career rubrics. It uses a pipeline architecture to process data in stages, with each stage implemented as a tool.

## Components

### Data Collection Agent

The main class that orchestrates the data collection process. It uses LangChain Expression Language (LCEL) to compose a pipeline of tools.

### Tools

#### Source Selection

The `select_sources` tool selects relevant sources based on level and dimension. It uses a language model to understand the context and select appropriate sources.

#### Content Fetching

The `fetch_content` tool fetches content from sources using Tavily. It handles both web pages and PDFs, and includes built-in retries and error handling.

#### Content Chunking

The `chunk_rubric` tool generates chunks from content using a language model. It takes content, level, and dimension as input and returns a list of chunks with metadata.

#### Chunk Storage

The `store_chunks` tool stores chunks in Qdrant with embeddings. It uses OpenAI's embeddings to generate embeddings for chunks and stores them in Qdrant.

## Data Flow

1. **Source Selection**: The agent selects relevant sources based on the level and dimension.
2. **Content Fetching**: The agent fetches content from the selected sources.
3. **Content Chunking**: The agent generates chunks from the fetched content.
4. **Chunk Storage**: The agent stores the chunks in Qdrant with embeddings.

## State Management

The pipeline uses LangChain's state management to pass data between steps. Each step receives the state from the previous step and returns updated state.

## Error Handling

The pipeline includes error handling at each step:

- **Source Selection**: Handles invalid levels and dimensions
- **Content Fetching**: Handles network errors and invalid URLs
- **Content Chunking**: Handles invalid content and chunking errors
- **Chunk Storage**: Handles storage errors and invalid chunks

## Configuration

The pipeline can be configured using environment variables:

- `OPENAI_API_KEY`: OpenAI API key for language models and embeddings
- `TAVILY_API_KEY`: Tavily API key for content fetching
- `QDRANT_URL`: Qdrant URL for chunk storage
- `QDRANT_API_KEY`: Qdrant API key for chunk storage

## Related Documentation

- [Implementation](./../implementation/README.md)
- [API Reference](./../api/README.md)
- [Usage Guide](./../usage/README.md) 