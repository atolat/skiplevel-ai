"""Core pipeline module that orchestrates the content curation and evaluation process."""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Literal
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urlparse

from .content_curation import curate_urls, curate_urls_from_reddit
from .content_extraction import extract_and_clean
from .content_evaluation import evaluate_content, calculate_query_metrics
from .content_analysis import analyze_high_quality_content
from .query_metrics import QueryMetrics

# Import web evaluation functions but don't use by default
from .web_evaluation import batch_evaluate_urls

logger = logging.getLogger(__name__)


def run_content_pipeline(
    query: str, 
    evaluation_method: Optional[Literal["standard", "openai_browsing", "tavily_content", "claude_browsing"]] = "standard"
) -> Tuple[List[Dict], QueryMetrics]:
    """
    Run the content curation and evaluation pipeline.
    
    Args:
        query: The search query to use
        evaluation_method: Method for evaluating content
            - "standard": Traditional scraping and evaluation
            - "openai_browsing": OpenAI with browsing capabilities
            - "tavily_content": Tavily content API
            - "claude_browsing": Claude with browsing capabilities
    
    Returns:
        Tuple of (results, query metrics)
    """
    try:
        logger.info(f"Starting content pipeline with query: {query}")
        logger.info(f"Using evaluation method: {evaluation_method}")
        
        # Check for required API keys
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY is required to run the pipeline")
        
        # Get URLs from multiple sources
        logger.info("Fetching content from sources...")
        
        # Get URLs from Tavily
        tavily_urls = curate_urls(query)
        logger.info(f"Found {len(tavily_urls)} URLs from Tavily")
        
        # Get URLs from Reddit
        reddit_urls = curate_urls_from_reddit(query)
        logger.info(f"Found {len(reddit_urls)} URLs from Reddit")
        
        # Combine results
        urls = tavily_urls + reddit_urls
        logger.info(f"Total: {len(urls)} URLs from all sources")
        
        # Check if we have any URLs
        if not urls:
            logger.warning("No URLs found from any source. Check API keys and query.")
            # Return empty results with zero metrics
            return [], QueryMetrics(
                query=query,
                avg_score=0.0,
                high_quality_count=0,
                source_domains=set(),
                total_results=0
            )
        
        # Evaluate content based on selected method
        if evaluation_method == "standard":
            # Standard approach: Extract and then evaluate
            logger.info("Extracting and cleaning content...")
            cleaned = extract_and_clean(urls)
            logger.info(f"Successfully processed {len(cleaned)} URLs")
            
            if not cleaned:
                logger.warning("No content was successfully extracted. Check network connectivity.")
                # Return empty results with zero metrics
                return [], QueryMetrics(
                    query=query,
                    avg_score=0.0,
                    high_quality_count=0,
                    source_domains=set(),
                    total_results=0
                )
            
            logger.info("Evaluating content...")
            evaluated = evaluate_content(cleaned)
            
            # Calculate metrics for standard evaluation
            metrics = calculate_query_metrics(query, evaluated)
            
            # Log metrics
            logger.info("\nResults Summary:")
            logger.info(f"Average Score: {metrics.avg_score:.2f}")
            logger.info(f"High Quality Results: {metrics.high_quality_count}/{metrics.total_results}")
            logger.info(f"Quality Ratio: {metrics.quality_ratio:.2%}")
            logger.info(f"Unique Domains: {len(metrics.source_domains)}")
            
            # Analyze high-quality content for standard evaluation
            high_quality = [doc for doc in evaluated if doc["evaluation"]["score"] >= 4]
            
            if high_quality:
                logger.info(f"Analyzing {len(high_quality)} high-quality results...")
                analysis = analyze_high_quality_content(high_quality)
                
                # Log analysis insights
                logger.info("\nContent Analysis:")
                logger.info(f"Common themes: {', '.join(analysis.get('common_themes', []))}")
                logger.info(f"Source types: {', '.join(analysis.get('source_types', []))}")
                logger.info(f"Content depth: {analysis.get('content_depth', 'N/A')}")
                logger.info(f"Key terminology: {', '.join(analysis.get('key_terminology', []))}")
            else:
                logger.info("No high-quality results found for analysis.")
                
            return evaluated, metrics
        else:
            # Web-based evaluation: Skip extraction and evaluate directly from URLs
            logger.info(f"Using web-based evaluation method: {evaluation_method}")
            web_results = batch_evaluate_urls(urls, query=query, method=evaluation_method)
            logger.info(f"Successfully evaluated {len(web_results)} URLs")
            
            # Calculate metrics for web-based evaluation
            # Web results have a different structure than standard results
            if web_results:
                # Extract domains for metrics
                domains = set()
                for result in web_results:
                    if "url" in result:
                        try:
                            parsed_url = urlparse(result["url"])
                            domains.add(parsed_url.netloc)
                        except:
                            pass
                            
                # Calculate average score
                avg_score = sum(result.get("overall_score", 0) for result in web_results) / len(web_results)
                
                # Define high-quality based on score threshold (over 7.0)
                high_quality = [r for r in web_results if r.get("overall_score", 0) >= 7.0]
                high_quality_count = len(high_quality)
                
                # Create metrics object
                web_metrics = QueryMetrics(
                    query=query,
                    avg_score=avg_score,
                    high_quality_count=high_quality_count,
                    source_domains=domains,
                    total_results=len(web_results)
                )
                
                # Log metrics
                logger.info("\nResults Summary:")
                logger.info(f"Average Score: {web_metrics.avg_score:.2f}")
                logger.info(f"High Quality Results: {web_metrics.high_quality_count}/{web_metrics.total_results}")
                logger.info(f"Quality Ratio: {web_metrics.quality_ratio:.2%}")
                logger.info(f"Unique Domains: {len(web_metrics.source_domains)}")
                
                # Convert web results to standard format for easier processing downstream
                standardized_results = []
                for result in web_results:
                    # Create a standardized structure
                    standardized = {
                        "url": result.get("url", ""),
                        "title": result.get("title", ""),
                        "source": result.get("source", "web"),
                        "text": result.get("summary", ""),  # Use summary as text
                        "evaluation": {
                            "score": result.get("overall_score", 0),
                            "tags": result.get("tags", []),
                            "summary": result.get("summary", ""),
                            "reasoning": ""  # No detailed reasoning in web results
                        },
                        "score_details": result.get("score_details", {})
                    }
                    standardized_results.append(standardized)
                
                return standardized_results, web_metrics
            else:
                logger.warning("No web evaluation results found.")
                # Return empty results
                return [], QueryMetrics(
                    query=query,
                    avg_score=0.0,
                    high_quality_count=0,
                    source_domains=set(),
                    total_results=0
                )
        
    except Exception as e:
        logger.error(f"Error in content pipeline: {str(e)}")
        # Return empty results with error
        return [], QueryMetrics(
            query=query,
            avg_score=0.0,
            high_quality_count=0,
            source_domains=set(),
            total_results=0
        )


def main(
    query: str = "engineering technical growth metrics and objective performance evaluation",
    evaluation_method: str = "standard"
) -> None:
    """
    Main pipeline function.
    
    Args:
        query: The search query
        evaluation_method: Method for evaluating content (standard, openai_browsing, tavily_content, claude_browsing)
    """
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pipeline.log'),
                logging.StreamHandler()
            ]
        )
        
        # Try to load from different possible .env locations
        root_env = Path(".env")
        subdir_env = Path("non-agentic-pipeline/.env")
        
        if subdir_env.exists():
            logger.info(f"Loading environment from {subdir_env}")
            load_dotenv(subdir_env)
        elif root_env.exists():
            logger.info(f"Loading environment from {root_env}")
            load_dotenv(root_env)
        else:
            logger.info("No .env file found. Using environment variables directly.")
        
        # Validate API keys and show clear messages
        missing_keys = []
        if not os.getenv("OPENAI_API_KEY"):
            missing_keys.append("OPENAI_API_KEY")
        if evaluation_method == "standard" and not os.getenv("TAVILY_API_KEY"):
            missing_keys.append("TAVILY_API_KEY")
        if missing_keys:
            logger.error(f"Missing required API keys: {', '.join(missing_keys)}")
            logger.error("Please set these environment variables in your .env file")
            return
            
        start_time = datetime.now()
        logger.info(f"Pipeline started at {start_time}")
        
        os.makedirs("data", exist_ok=True)
        
        logger.info(f"Processing query: {query}")
        all_results, metrics = run_content_pipeline(query, evaluation_method=evaluation_method)
        
        if not all_results:
            logger.warning("No results found. Pipeline completed with empty results.")
            return
            
        # Save results
        logger.info("Saving results...")
        
        # Create a timestamp to include in filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save all results including evaluations
        with open(f"data/all_results_{timestamp}.json", "w") as f:
            json.dump(all_results, f, indent=2)
        
        # Save full text content for chunking (if available)
        logger.info("Saving content...")
        full_content = []
        
        for doc in all_results:
            # Handle different formats (standard vs web-based)
            if "evaluation" in doc:
                # Standard format with evaluation dictionary
                content_item = {
                    "url": doc["url"],
                    "title": doc.get("title", ""),
                    "text": doc.get("full_text", doc.get("text", "")),  # Use full text if available
                    "source": doc.get("source", ""),
                    "quality_score": doc["evaluation"].get("score", 0)
                }
            else:
                # Web-based format with overall_score at top level
                content_item = {
                    "url": doc["url"],
                    "title": doc.get("title", ""),
                    "text": doc.get("summary", ""),  # Use summary as text for web evaluation
                    "source": doc.get("source", "web"),
                    "quality_score": doc.get("overall_score", 0)
                }
            
            full_content.append(content_item)
        
        with open(f"data/full_content_{timestamp}.json", "w") as f:
            json.dump(full_content, f, indent=2)
        
        # Convert set to list for JSON serialization
        metric_dict = vars(metrics)
        metric_dict['source_domains'] = list(metric_dict['source_domains'])
        
        with open(f"data/query_metrics_{timestamp}.json", "w") as f:
            json.dump(metric_dict, f, indent=2)
        
        # Also save just the high-quality content
        # Define high-quality based on evaluation method
        if evaluation_method == "standard":
            high_quality = [doc for doc in all_results if doc["evaluation"]["score"] >= 4]
        else:
            # For web-based evaluation, use higher threshold as the scale is 1-10
            high_quality = [doc for doc in all_results if doc.get("evaluation", {}).get("score", 0) >= 7]
        
        with open(f"data/high_quality_content_{timestamp}.json", "w") as f:
            json.dump(high_quality, f, indent=2)
        
        # Make copies without timestamps for easy access
        with open("data/all_results.json", "w") as f:
            json.dump(all_results, f, indent=2)
            
        with open("data/full_content.json", "w") as f:
            json.dump(full_content, f, indent=2)
            
        with open("data/query_metrics.json", "w") as f:
            json.dump(metric_dict, f, indent=2)
            
        with open("data/high_quality_content.json", "w") as f:
            json.dump(high_quality, f, indent=2)
        
        # Log final summary
        logger.info("\nFinal Results Summary:")
        logger.info(f"Query: {metrics.query}")
        logger.info(f"Average Score: {metrics.avg_score:.2f}")
        logger.info(f"High Quality Results: {metrics.high_quality_count}/{metrics.total_results}")
        logger.info(f"Quality Ratio: {metrics.quality_ratio:.2%}")
        logger.info(f"Unique Domains: {len(metrics.source_domains)}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"\nPipeline completed in {duration}")
        logger.info("Check the data directory for results and pipeline.log for detailed logs.")
    
    except Exception as e:
        logger.error(f"Error running pipeline: {str(e)}")
        logger.exception("Stack trace:") 