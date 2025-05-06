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
from .modules.content_cache import content_cache
from .modules.resource_discovery import discover_resources
from .modules.resource_processor import process_resources, get_resource_text
from .modules import medium_api

def run_content_pipeline(query: str, evaluation_method: str = "standard", use_cache: bool = True, 
                         include_books: bool = True) -> Dict:
    """
    Run the full pipeline from query to evaluation.
    
    Args:
        query: The search query
        evaluation_method: The method to use for evaluating content ("standard" or "openai_browsing")
        use_cache: Whether to use the caching system to skip already processed URLs
        include_books: Whether to include curated books and papers
    
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
    
    # Step 2: Discover high-quality books and resources if enabled
    urls_from_discovery = []
    if include_books:
        logger.info(f"Starting resource discovery for query: {query}")
        discovered_resources = discover_resources(query)
        # Process the discovered resources to extract content
        processed_resources = process_resources(discovered_resources)
        
        # Format them as URL dictionaries for the pipeline
        for resource in processed_resources:
            if "is_processed" in resource and resource.get("is_processed", False):
                urls_from_discovery.append({
                    "url": resource.get("url", ""),
                    "title": resource.get("title", ""),
                    "source": resource.get("source", "discovered"),
                    "meta": {
                        **resource.get("meta", {}),
                        "resource_content": resource.get("text", ""),
                        "is_discovered_resource": True,
                        "content_type": resource.get("content_type", "unknown"),
                    }
                })
                
        logger.info(f"Found {len(urls_from_discovery)} curated resources")
    
    # Combine all URL sources
    all_urls = urls_from_tavily + urls_from_reddit + urls_from_discovery
    logger.info(f"Total URLs found: {len(all_urls)}")
    
    # Step 3: Apply cache and filter out already processed URLs if enabled
    if use_cache:
        # Filter URLs to exclude ones already in the cache
        filtered_urls = []
        cached_results = []
        
        for url_data in all_urls:
            url = url_data["url"]
            if content_cache.has_url(url):
                # Get cached metadata which might include evaluation results
                metadata = content_cache.get_url_metadata(url)
                if metadata and "evaluation" in metadata:
                    logger.info(f"Using cached evaluation for {url}")
                    cached_results.append(metadata["evaluation"])
                else:
                    logger.info(f"URL {url} in cache but no evaluation found")
            else:
                filtered_urls.append(url_data)
        
        logger.info(f"After cache filtering: {len(filtered_urls)} URLs to process, {len(cached_results)} from cache")
        all_urls = filtered_urls
    else:
        logger.info("Cache system disabled, processing all URLs")
        cached_results = []
    
    # Step 4: Evaluate content (using parallel processing for web-based methods)
    new_results = []
    
    if not all_urls:
        logger.warning("No new URLs found to evaluate")
    elif evaluation_method == "standard":
        # Standard approach: extract and evaluate content sequentially
        for url_data in all_urls:
            url = url_data["url"]
            try:
                # Check if this is a discovered resource with content already available
                if url_data.get("meta", {}).get("is_discovered_resource", False):
                    # Use the content from the resource discovery process
                    logger.info(f"Using pre-extracted content for discovered resource: {url}")
                    resource_content = url_data.get("meta", {}).get("resource_content", "")
                    if not resource_content and "resource" in url_data.get("meta", {}):
                        # Get the text content using the helper function
                        resource = url_data.get("meta", {}).get("resource", {})
                        resource_content = get_resource_text(resource)
                        
                    if resource_content:
                        # Discovered resources are pre-vetted, so give them a high baseline score
                        source_quality = url_data.get("meta", {}).get("source_quality", 7)
                        evaluation = {
                            "url": url,
                            "title": url_data.get("title", ""),
                            "source": url_data.get("source", "discovered"),
                            "overall_score": source_quality,  # Pre-vetted resources get a high score
                            "content_type": url_data.get("meta", {}).get("content_type", "unknown"),
                            "is_discovered_resource": True,
                            "summary": url_data.get("meta", {}).get("summary", ""),
                            "evaluation_method": "direct"
                        }
                        new_results.append(evaluation)
                        
                        # Cache the URL with its metadata including evaluation
                        if use_cache:
                            content_cache.add_url(url, {"evaluation": evaluation, "source": url_data.get("source", "web")})
                    else:
                        logger.warning(f"No content available for discovered resource: {url}")
                else:
                    # Regular web content extraction and evaluation
                    content = content_extraction.scrape_url_content(url)
                    if content and not content.get("error"):
                        # Check content cache before evaluation
                        content_text = content.get("text", "")
                        cached_content_result = content_cache.get_content_result(content_text) if use_cache else None
                        
                        if cached_content_result:
                            logger.info(f"Using cached content evaluation for {url}")
                            evaluation = cached_content_result
                        else:
                            evaluation = content_evaluation.evaluate_content(content["text"], url)
                            # Cache the evaluation result
                            if use_cache and content_text:
                                content_cache.add_content(content_text, evaluation)
                        
                        # Add to results
                        new_results.append(evaluation)
                        
                        # Cache the URL with its metadata including evaluation
                        if use_cache:
                            content_cache.add_url(url, {"evaluation": evaluation, "source": url_data.get("source", "web")})
                    else:
                        logger.warning(f"Failed to extract content from {url}")
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
    else:
        # Check if we have any discovered resources to bypass web evaluation
        direct_resources = []
        web_resources = []
        
        for url_data in all_urls:
            if url_data.get("meta", {}).get("is_discovered_resource", False):
                direct_resources.append(url_data)
            else:
                web_resources.append(url_data)
        
        # Process discovered resources directly
        for resource in direct_resources:
            try:
                url = resource["url"]
                
                # Skip invalid Medium URLs (profiles or publications)
                if "medium.com" in url and not medium_api.is_valid_article_url(url):
                    logger.warning(f"Skipping invalid Medium URL during direct evaluation: {url}")
                    continue
                
                logger.info(f"Direct evaluation of discovered resource: {url}")
                
                # Get content from the resource or its related text file
                content_text = resource.get("meta", {}).get("resource_content", "")
                if not content_text and "resource" in resource.get("meta", {}):
                    # Get the text content using the helper function
                    resource_obj = resource.get("meta", {}).get("resource", {})
                    content_text = get_resource_text(resource_obj)
                    
                if content_text:
                    # Discovered resources are pre-vetted, so give them a high baseline score
                    source_quality = resource.get("meta", {}).get("source_quality", 7)
                    evaluation = {
                        "url": url,
                        "title": resource.get("title", ""),
                        "source": resource.get("source", "discovered"),
                        "overall_score": source_quality,  # Pre-vetted resources get a high score
                        "content_type": resource.get("meta", {}).get("content_type", "unknown"),
                        "is_discovered_resource": True,
                        "summary": resource.get("meta", {}).get("summary", ""),
                        "evaluation_method": "direct"
                    }
                    new_results.append(evaluation)
                    
                    # Cache the URL with its metadata including evaluation
                    if use_cache:
                        content_cache.add_url(url, {"evaluation": evaluation, "source": resource.get("source", "web")})
                else:
                    logger.warning(f"No content available for discovered resource: {url}")
            except Exception as e:
                logger.error(f"Error processing discovered resource {resource.get('url')}: {str(e)}")
        
        # Use parallel processing for regular web resources
        if web_resources:
            logger.info(f"Using parallel processing with {evaluation_method} for {len(web_resources)} URLs")
            web_results = web_evaluation.batch_evaluate_urls(web_resources, query, evaluation_method)
            
            # Cache the evaluation results
            if use_cache:
                for result in web_results:
                    url = result.get("url", "")
                    if url:
                        content_cache.add_url(url, {"evaluation": result, "source": result.get("source", "web")})
            
            new_results.extend(web_results)
    
    # Combine new results with cached results
    results = new_results + cached_results
    
    # Step 5: Filter and rank results
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
    
    # Step 6: Prepare final output
    pipeline_results = {
        "query": query,
        "evaluation_method": evaluation_method,
        "total_urls": len(all_urls) + len(cached_results),
        "evaluated_urls": len(results),
        "new_urls_processed": len(new_results),
        "cached_urls_used": len(cached_results),
        "discovered_resources": len(urls_from_discovery),
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