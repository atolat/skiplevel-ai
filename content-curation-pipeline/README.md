# Content Curation Pipeline

A data pipeline for discovering, curating, and evaluating high-quality content about engineering career development and performance feedback.

## Key Features

- **Multi-source content discovery** from both search engines and social platforms
- **Parallel URL processing** for significantly improved performance
- **Specialized Reddit content evaluation** with structured analysis of posts and comments
- **Medium API integration** for high-quality engineering articles
- **Enhanced web evaluation** using modern LLM capabilities
- **Robust error handling** for reliable operation
- **Structured output format** for downstream applications

## Current Implementation

### Pipeline Stages

1. **Query Evolution**
   - Starts with initial broad query
   - Runs up to 3 iterations
   - Each iteration:
     - Searches with current query
     - Evaluates results
     - Analyzes high-quality content
     - Generates improved queries

2. **Content Curation (Multiple Sources)**
   - **Tavily Search**
     - Uses Tavily's advanced search
     - Returns up to 10 results per query
     - Includes metadata like titles and relevance scores
   
   - **Medium API Integration**
     - Uses the Unofficial Medium API to fetch high-quality articles
     - Extracts full article content directly from the API
     - Searches based on relevant engineering topics
     - Includes metadata like claps, reading time, and authors
   
   - **Reddit Integration**
     - Searches relevant engineering and career subreddits
     - Extracts posts and their top comments
     - Prioritizes substantial content (longer posts/comments)
     - Searches across multiple relevant subreddits:
       - r/engineering, r/cscareerquestions, r/careerguidance
       - r/engineeringmanagers, r/programming, r/softwareengineering
       - r/developers, r/datascience, r/machinelearning
       - r/devops, r/techleadership

3. **Content Extraction**
   - Robust web scraping with retry logic
   - Specialized extraction for Reddit content
   - Handles 403 errors and other issues
   - Extracts main content using multiple strategies
   - Cleans and processes text

4. **Content Evaluation**
   - Uses LLM to evaluate content quality
   - Parallel processing of up to 8 URLs simultaneously
   - Specialized evaluation criteria for engineering career content:
     - Technical accuracy (30%)
     - Actionability (30%)
     - Evidence-based approach (20%)
     - Technical depth (10%)
     - Bias mitigation (10%)
   - Returns detailed evaluation with scores and reasoning

5. **Query Evolution Logic**
   - Analyzes high-quality content (score >= 4)
   - Identifies patterns in successful content
   - Generates new queries based on insights
   - Tracks query performance metrics

### Performance Optimizations

- **Parallel URL Processing**
  - Concurrent evaluation of up to 8 URLs
  - ThreadPoolExecutor for efficient processing
  - Significant reduction in total runtime
  - Automatic thread management and error isolation

- **Enhanced Error Handling**
  - Safe numeric conversion with fallbacks
  - Detailed error logging
  - Process isolation prevents cascading failures
  - Graceful degradation when services are unavailable

- **Type Safety**
  - Improved numeric processing for scores
  - Consistent error handling for API responses
  - Better JSON validation and parsing

### Quality Metrics

- Average Score (1-10)
- High Quality Count (score >= 4)
- Quality Ratio (high quality / total)
- Source Diversity (unique domains)
- Content Analysis (themes, sources, terminology)

### Data Output

1. **JSON Files**
   - `all_results.json`: All content found
   - `query_metrics.json`: Performance metrics for each query

2. **Logging**
   - Detailed pipeline.log with:
     - Timestamps
     - Iteration progress
     - Query evolution
     - Quality metrics
     - Analysis insights

## Key Learnings

1. **Query Strategy**
   - Broad queries often perform better than specific ones
   - Quality tends to decrease with increasing specificity
   - Initial query: "engineering performance feedback and growth" (3.20 avg, 70% quality)
   - Final query: "Case studies on career growth..." (2.00 avg, 30% quality)

2. **Content Quality**
   - High-quality content focuses on:
     - Practical development strategies
     - Performance feedback mechanisms
     - Career growth frameworks
     - Professional identity in engineering

3. **Source Quality**
   - Best sources are:
     - Professional engineering blogs
     - Industry publications
     - Engineering career development platforms

## Recent Improvements

- **Parallel Processing**: Implemented concurrent evaluation of URLs, reducing overall runtime by up to 8x
- **Project Reorganization**: Restructured into a proper Python package with clean separation of concerns
- **Enhanced Error Handling**: Added robust error handling with safe type conversion and better logging
- **Improved Scoring**: Refined scoring system with weighted criteria and more consistent numeric handling
- **Dotenv Integration**: Added automatic loading of environment variables from .env files
- **Type Safety**: Enhanced type safety throughout the codebase with proper type hints and conversions

## Future Improvements

### 1. Query Evolution Strategy

**Current Issue**: Sequential evolution leads to quality degradation

**Proposed Solutions**:
- Parallel query generation
  - Generate multiple queries in each iteration
  - Run searches concurrently
  - Select best performing queries
- Quality-based stopping conditions
  - Stop if average score drops below threshold
  - Stop if quality ratio drops significantly
- Hybrid approach
  - Mix broad and specific queries
  - Weight results based on source authority
  - Maintain quality rather than just evolving

### 2. Content Analysis Enhancement

**Current Issue**: Basic content analysis

**Proposed Solutions**:
- Implement topic modeling
  - Identify subtopics within content
  - Track topic coverage over iterations
- Add sentiment analysis
  - Evaluate content tone and perspective
  - Balance positive/negative viewpoints
- Source authority scoring
  - Weight results based on source reputation
  - Consider domain expertise

### 3. Performance Optimization

**Current Issue**: ~~Sequential processing~~ *Largely addressed with parallel processing*

**Proposed Solutions**:
- ~~Parallel processing~~ *Implemented*
- Caching
  - Cache successful queries
  - Store content analysis results
  - Implement result deduplication
- Distributed execution
  - AWS Lambda integration
  - Auto-scaling worker pools

### 4. Quality Metrics Enhancement

**Current Issue**: Basic quality metrics

**Proposed Solutions**:
- Add temporal metrics
  - Content freshness
  - Update frequency
- Add structural metrics
  - Content length
  - Section organization
  - Reference quality
- Add engagement metrics
  - Social shares
  - Comments/feedback
  - Citation count

### 5. Error Handling and Recovery

**Current Issue**: ~~Basic error handling~~ *Significantly improved*

**Proposed Solutions**:
- ~~Basic error isolation~~ *Implemented*
- Implement circuit breakers
  - Stop processing if error rate exceeds threshold
  - Automatic retry with backoff
- Add fallback strategies
  - Alternative content sources
  - Backup query generation
  - Content reconstruction

### 6. User Interface and Control

**Current Issue**: No user interaction

**Proposed Solutions**:
- Add interactive controls
  - Query adjustment
  - Quality threshold setting
  - Source filtering
- Add visualization
  - Quality trends
  - Topic coverage
  - Source distribution
- Add feedback mechanism
  - User rating of results
  - Query suggestion
  - Content tagging

### 7. Model Improvements
- **Current Issues**:
  - Using GPT-3.5-turbo for content analysis
  - Single model approach for all evaluation aspects
  - Limited technical depth understanding
  - Potential bias in scoring
  - Inconsistent evaluation across different content types

- **Proposed Solutions**:
  - Upgrade to GPT-4-turbo-preview for primary evaluation
  - Implement specialized models for different aspects:
    - Claude 3 Opus for technical depth evaluation
    - Claude 3 Sonnet for career relevance
    - GPT-4-turbo-preview for practical applicability
  - Use ensemble approach with weighted scoring
  - Implement consensus-based evaluation
  - Add model-specific configurations for optimal performance
  - Enhanced output structure with detailed feedback

- **Ensemble Approach with Consensus**:
  - **Model Configuration**:
    ```python
    model_config = {
        "primary": {
            "name": "gpt-4-turbo-preview",
            "temperature": 0.3,
            "max_tokens": 2000
        },
        "technical": {
            "name": "claude-3-opus",
            "temperature": 0.2,
            "max_tokens": 1500
        },
        "career": {
            "name": "claude-3-sonnet",
            "temperature": 0.3,
            "max_tokens": 1500
        }
    }
    ```

  - **Evaluation Framework**:
    ```python
    evaluation_criteria = {
        "technical_depth": {
            "model": "claude-3-opus",
            "weight": 0.25,
            "description": "Technical accuracy and depth of engineering concepts"
        },
        "practical_applicability": {
            "model": "gpt-4-turbo-preview",
            "weight": 0.25,
            "description": "Practical value and actionable insights"
        },
        "career_relevance": {
            "model": "claude-3-sonnet",
            "weight": 0.20,
            "description": "Relevance to engineering career development"
        },
        "originality": {
            "model": "gpt-4-turbo-preview",
            "weight": 0.15,
            "description": "Originality and uniqueness of insights"
        },
        "structure": {
            "model": "gpt-4-turbo-preview",
            "weight": 0.15,
            "description": "Clarity and organization of content"
        }
    }
    ```

  - **Consensus Scoring Process**:
    1. Each model evaluates content independently
    2. Scores are normalized across models
    3. Weighted average calculated based on model expertise
    4. Consensus level determined by score agreement
    5. Disagreements flagged for human review
    6. Final score adjusted based on consensus level

  - **Output Structure**:
    ```python
    {
        "scores": {
            "technical_depth": {
                "score": <number>,
                "reasoning": "<detailed reasoning>",
                "examples": ["<specific example>"],
                "improvements": ["<suggestion>"]
            },
            "practical_applicability": {...},
            "career_relevance": {...},
            "originality": {...},
            "structure": {...}
        },
        "overall_score": <weighted average>,
        "summary": "<overall assessment>",
        "key_strengths": ["<strength>"],
        "key_weaknesses": ["<weakness>"],
        "model_consensus": {
            "agreement_level": <percentage>,
            "disagreements": ["<area of disagreement>"]
        }
    }
    ```

- **Expected Benefits**:
  - More accurate and reliable evaluations
  - Better handling of technical content
  - More nuanced understanding of career implications
  - Reduced bias through consensus scoring
  - Detailed feedback for improvement
  - Better consistency across evaluations

## Usage

1. **Check Environment Variables**:
   
   Run the environment check script to ensure all required API keys are available:
   ```bash
   ./check_env.py
   ```
   
   This script will check for the following environment variables:
   - `OPENAI_API_KEY` (required)
   - `TAVILY_API_KEY` (required for standard evaluation)
   - `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` (optional, for Reddit content)
   - `MEDIUM_API_KEY` (optional, for Medium content)

2. **Set up environment variables**:
   
   Create a `.env` file in either:
   - The project root directory: `./.env`
   - OR the package directory: `./content-curation-pipeline/.env`
   
   ```
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USER_AGENT=python:content-curation-pipeline:v0.2.0 (by /u/your_username)
   MEDIUM_API_KEY=your_medium_api_key
   ```

   To obtain Medium API credentials:
   - Visit https://mediumapi.com/
   - Sign up for a RapidAPI account
   - Subscribe to the Medium API
   - Get your API key from the RapidAPI dashboard

3. **Install dependencies**:
   ```bash
   pip install -e .
   ```

4. **Run the pipeline**:
   ```bash
   # Standard evaluation (default)
   python run.py --query "your search query"
   
   # Using web-based evaluation with parallel processing
   python run.py --query "your search query" --evaluation-method openai_browsing
   ```

5. **Check results** in:
   - `data/` directory for JSON outputs
   - `pipeline.log` for detailed logs

## Project Structure

```
content-curation-pipeline/
├── src/
│   └── pipeline/           # Core package 
│       ├── __init__.py     # Package initialization
│       ├── pipeline.py     # Main pipeline implementation
│       └── modules/        # Pipeline modules
│           ├── content_curation.py    # URL discovery
│           ├── content_extraction.py  # Content scraping
│           ├── content_evaluation.py  # Content evaluation
│           ├── web_evaluation.py      # Direct URL evaluation 
│           └── ...
├── data/                   # Output data directory
├── run.py                  # CLI runner
├── pyproject.toml          # Project configuration
├── README.md               # Documentation
└── .env                    # Environment variables (create this)
```

## Deployment

For cloud deployment options, see the AWS deployment plan for serverless deployment with:
- AWS Lambda for compute
- Step Functions for orchestration
- S3 for storage
- ElastiCache for caching
- EventBridge for scheduling

## Command-line Options

```
usage: run.py [-h] [--query QUERY] [--evaluation-method {standard,openai_browsing,tavily_content,claude_browsing}]
              [--no-cache] [--output-file OUTPUT_FILE] [--no-books] [--github-token GITHUB_TOKEN] 
              [--medium-api-key MEDIUM_API_KEY] [--clean] [--clean-pdfs] [--clean-texts] [--clean-cache]

Run the content curation pipeline

options:
  -h, --help            show this help message and exit
  --query QUERY         Content query to search for
  --evaluation-method {standard,openai_browsing,tavily_content,claude_browsing}
                        Method for evaluating content
  --no-cache            Disable URL and content caching (forces reprocessing of all URLs)
  --output-file OUTPUT_FILE
                        Optional file to save results JSON
  --no-books            Disable discovery of books, papers and other curated resources
  --github-token GITHUB_TOKEN
                        GitHub API token for accessing repositories (optional)
  --medium-api-key MEDIUM_API_KEY
                        Medium API key from RapidAPI for accessing Medium content (optional)
  --clean               Clean data directories (pdfs, texts, cache) before running the pipeline
  --clean-pdfs          Clean only the PDFs directory before running
  --clean-texts         Clean only the texts directory before running
  --clean-cache         Clean only the cache directory before running
```

## Dependencies

- openai>=1.0.0
- requests>=2.31.0
- beautifulsoup4>=4.12.0
- python-dotenv>=1.0.0
- tavily-python>=0.2.0
- praw>=7.7.0 (for Reddit integration)
- arxiv>=1.4.7 (for academic papers)
- PyPDF2>=3.0.0 (for PDF processing)
- newspaper3k>=0.2.8 (for web content extraction) 