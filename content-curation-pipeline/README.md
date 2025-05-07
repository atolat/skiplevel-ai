# Content Curation Pipeline

A configurable content curation pipeline for discovering, processing, and evaluating technical content from various sources.

## Overview

This pipeline helps discover and curate high-quality technical content from multiple sources:

- **Substack** newsletters
- **Medium** articles 
- **YouTube** videos (with transcripts)
- **Technical Papers** (ArXiv)
- **Reddit** discussions and posts

It uses a configuration-based approach to customize content discovery, processing, and evaluation.

## Features

- **Configurable**: Use YAML configuration files to customize sources, processors, and evaluation
- **Multiple Sources**: Unified interface for different content sources
- **Content Processing**: Extract text, metadata, and perform analysis
- **Evaluation**: Rate content based on relevance, quality, and technical depth (optional)
- **Visualization**: Generate markdown reports of discovered content
- **Caching**: Efficient content discovery with cache support

## Directory Structure

```
content-curation-pipeline/
├── config.yaml                  # Main configuration file
├── data/                        # Data storage
│   ├── cache/                   # Cached API responses and results
│   ├── content/                 # Processed content by source type
│   ├── exports/                 # Output files and visualizations
│   ├── pdfs/                    # Downloaded technical papers
│   └── stats/                   # Processing statistics
├── run.py                       # Main entry point
├── scripts/                     # Utility scripts
│   ├── clean_cache.py           # Script to clean cached data
│   └── create_config.py         # Configuration file generator
└── src/                         # Source code
    └── pipeline/                # Pipeline components
        ├── config/              # Configuration handling
        ├── interfaces.py        # Core interfaces
        ├── modules/             # Shared utility modules
        ├── pipeline.py          # Main pipeline implementation
        ├── sources/             # Source implementations
        │   ├── medium/          # Medium source and processor
        │   ├── papers/          # Technical papers source and processor
        │   ├── substack/        # Substack source and processor
        │   └── youtube/         # YouTube source and processor
        ├── utils/               # Utility functions
        └── visualizers/         # Output visualizers
```

## Getting Started

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/content-curation-pipeline.git
   cd content-curation-pipeline
   ```

2. Set up a virtual environment:
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```sh
   pip install -e .
   ```

### Git Configuration

The repository includes a `.gitignore` file configured to:

- Ignore all data files in the `data/` directory to avoid committing cached data, PDFs, and generated content
- Preserve the directory structure with empty `.gitkeep` files
- Exclude development artifacts, virtual environments, and IDE-specific files

This ensures that data generated during pipeline execution won't be committed to version control, keeping the repository size manageable while still maintaining the required directory structure.

### Environment Setup

Create a `.env` file with the required API keys:

```
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
YOUTUBE_API_KEY=your_youtube_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=content_curation_pipeline:v1.0.0 (by /u/your_username)
```

### Configuration

The pipeline uses a YAML configuration file to customize behavior. Create a configuration file:

```sh
./scripts/create_config.py --name "my-project" --output config.yaml --enable-evaluation
```

Edit the generated `config.yaml` file to customize:
- Sources to use (Substack, Medium, YouTube, Papers)
- Query parameters and limits
- Evaluation settings
- Output formats

### Basic Usage

Run the pipeline with default settings:

```sh
python run.py
```

Run with a specific query:

```sh
python run.py --query "engineering career growth frameworks"
```

Run with a custom configuration:

```sh
python run.py --config custom_config.yaml
```

Clean the cache before running:

```sh
python run.py --config config.yaml --clean
```

Disable evaluation for faster runs:

```sh
python run.py --config config.yaml --no-eval
```

Enable parallel processing for better performance:

```sh
python run.py --config config.yaml --parallel
```

### Utilities

Clean all cached data:

```sh
./scripts/clean_cache.py
```

Clean cache but keep downloaded PDFs:

```sh
./scripts/clean_cache.py --keep-pdfs
```

## Configuration Reference

### Main Configuration Structure

```yaml
project_name: "engineering-career-growth-resources"
data_dir: "./data"
output_dir: "./output"
log_level: "INFO"

# Source configurations
sources:
  substack:
    name: "Substack Newsletters"
    type: "substack"
    enabled: true
    seed_queries:
      - "engineering management best practices"
    custom_urls:
      - "https://newsletter.pragmaticengineer.com/p/career-laddering"
    limit: 10
    source_params:
      curated_newsletters:
        - "pragmaticengineer"
        - "theengineeringmanager"

  medium:
    name: "Medium Articles"
    type: "medium"
    enabled: true
    # ...similar structure...

# Processor configurations
processors:
  substack:
    type: "substack"
    enabled: true
    # ...processor settings...

# Evaluation configuration
evaluation:
  enabled: true
  method: "standard"  # Options: standard, web, hybrid
  # ...evaluation settings...
```

### Source Configuration Options

Each source type (substack, medium, youtube, papers) supports these common options:

- `enabled`: Enable/disable the source (boolean)
- `limit`: Maximum items to retrieve per query (integer)
- `seed_queries`: List of queries to use for discovery (list of strings)
- `custom_urls`: Specific URLs to process (list of strings)

Plus source-specific parameters:

- **Substack**: `curated_newsletters` list
- **Medium**: `tags` list
- **YouTube**: `require_captions`, `language` options
- **Papers**: `repositories` list, `categories` list
- **Reddit**: `recommended_subreddits` list

## Extending the Pipeline

### Adding a New Source

1. Create a new directory in `src/pipeline/sources/`.
2. Implement a source class inheriting from `ContentSource`.
3. Implement a processor class inheriting from `ContentProcessor`.
4. Add source type to the configuration loader.

## Performance Optimization

### Parallel Processing

The pipeline supports parallel processing of content sources for improved performance:

- **Parallel Mode**: Use the `--parallel` flag to enable parallel content discovery
- **Performance Gains**: Significantly reduces runtime when using multiple content sources (up to 75% faster)
- **Implementation**: Uses Python's `concurrent.futures.ThreadPoolExecutor` for I/O-bound API calls
- **Best For**: Configurations with multiple sources and multiple queries per source

Examples of performance improvement:

```
Small run (limit=2):
  Sequential: 30.90 seconds
  Parallel:    8.96 seconds
  Improvement: 71%

Larger run (limit=5):
  Sequential: 61.06 seconds
  Parallel:   16.15 seconds
  Improvement: 74%
```

This is most effective with API-based sources that spend time waiting for external responses.

## Troubleshooting

### Common Issues

- **API Rate Limits**: Reduce concurrent requests or add delays.
- **Missing Content**: Check source parameters and query terms.
- **Slow Performance**: Use the `--no-eval` flag to skip evaluation.
- **Evaluation Errors**: Ensure OpenAI API key is valid and has sufficient credits.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Developed by Arpan Tolat (arpan@skiplevel.ai). 