"""
Pipeline module for content curation and evaluation.
"""
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Setup logger
logger = logging.getLogger("pipeline")

# Import modules
from .modules import content_curation, content_extraction, content_evaluation, web_evaluation

def run_content_pipeline(query: str, evaluation_method: str = "standard") -> Dict:
    """
    Run the full pipeline from query to evaluation.
    
    Args:
        query: The search query
        evaluation_method: The method to use for evaluating content ("standard" or "openai_browsing")
    
    Returns:
        Dictionary with pipeline results
    """
    start_time = time.time()
    
    # Step 1: Curate URLs from various sources
    logger.info(f"Starting URL curation for query: {query}")
    urls_from_tavily = content_curation.curate_urls(query)
    logger.info(f"Found {len(urls_from_tavily)} URLs from Tavily")
    
    urls_from_reddit = content_curation.curate_urls_from_reddit(query)
    logger.info(f"Found {len(urls_from_reddit)} URLs from Reddit")
    
    all_urls = urls_from_tavily + urls_from_reddit
    logger.info(f"Total URLs found: {len(all_urls)}")
    
    # Step 2: Evaluate content (using parallel processing for web-based methods)
    results = []
    
    if not all_urls:
        logger.warning("No URLs found to evaluate")
    elif evaluation_method == "standard":
        # Standard approach: extract and evaluate content sequentially
        for url_data in all_urls:
            url = url_data["url"]
            try:
                content = content_extraction.scrape_url_content(url)
                if content and not content.get("error"):
                    evaluation = content_evaluation.evaluate_content(content["text"], url)
                    results.append(evaluation)
                else:
                    logger.warning(f"Failed to extract content from {url}")
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
    else:
        # Use parallel processing for web-based evaluation methods
        logger.info(f"Using parallel processing with {evaluation_method} for {len(all_urls)} URLs")
        results = web_evaluation.batch_evaluate_urls(all_urls, query, evaluation_method)
    
    # Step 3: Filter and rank results
    logger.info(f"Filtering and ranking {len(results)} results")
    
    # Calculate average score for normalization
    if results:
        avg_score = sum(result.get("overall_score", 0) for result in results) / len(results)
    else:
        avg_score = 0
    
    # Filter for high-quality results (score > 4 or top 25% if all scores are low)
    if results:
        scores = [result.get("overall_score", 0) for result in results]
        threshold = max(4.0, sorted(scores)[max(0, len(scores) - len(scores) // 4 - 1)])
        high_quality = [r for r in results if r.get("overall_score", 0) >= threshold]
    else:
        high_quality = []
    
    # Quality ratio calculation
    quality_ratio = len(high_quality) / len(results) * 100 if results else 0
    
    # Step 4: Prepare final output
    pipeline_results = {
        "query": query,
        "evaluation_method": evaluation_method,
        "total_urls": len(all_urls),
        "evaluated_urls": len(results),
        "high_quality_count": len(high_quality),
        "quality_ratio": quality_ratio,
        "average_score": avg_score,
        "results": sorted(results, key=lambda x: x.get("overall_score", 0), reverse=True),
        "timestamp": datetime.now().isoformat(),
        "runtime_seconds": time.time() - start_time
    }
    
    logger.info(f"Pipeline complete. Evaluated {len(results)} URLs with average score: {avg_score:.2f}")
    logger.info(f"Found {len(high_quality)}/{len(results)} high-quality results ({quality_ratio:.2f}%)")
    logger.info(f"Pipeline completed in {time.time() - start_time:.1f} seconds")
    
    return pipeline_results 