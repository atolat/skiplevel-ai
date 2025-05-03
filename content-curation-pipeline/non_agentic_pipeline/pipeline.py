def run_pipeline(query: str, evaluation_method: str = "standard") -> Dict:
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
    urls_from_tavily = content_curation.curate_urls_from_tavily(query)
    logger.info(f"Found {len(urls_from_tavily)} URLs from Tavily")
    
    urls_from_reddit = content_curation.curate_urls_from_reddit(query)
    logger.info(f"Found {len(urls_from_reddit)} URLs from Reddit")
    
    all_urls = urls_from_tavily + urls_from_reddit
    logger.info(f"Total URLs found: {len(all_urls)}")
    
    # Step 2: Extract and evaluate content
    results = []
    
    for url_data in all_urls:
        url = url_data["url"]
        meta_data = url_data.get("meta", {})
        
        logger.info(f"Processing URL: {url}")
        
        try:
            if evaluation_method == "standard":
                # Standard approach: extract content, then evaluate
                content = content_extraction.extract_content_from_url(url)
                if content:
                    evaluation = content_evaluation.evaluate_content(content, url)
                    results.append(evaluation)
                else:
                    logger.warning(f"Failed to extract content from {url}")
            
            elif evaluation_method == "openai_browsing":
                # Direct evaluation using browser capability
                evaluation = web_evaluation.evaluate_url_with_browsing(url, query, meta_data)
                results.append(evaluation)
                
            else:
                logger.error(f"Unknown evaluation method: {evaluation_method}")
                
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
    
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