from typing import List, Dict, Any

def process_resources(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of resources in parallel.
    
    Args:
        resources: List of resource dictionaries
        
    Returns:
        List of processed resources
    """
    import concurrent.futures
    from functools import partial
    
    logger.info(f"Processing {len(resources)} resources")
    
    if not resources:
        return []
    
    # Use parallel processing to handle multiple resources simultaneously
    max_workers = min(len(resources), 8)  # Cap at 8 concurrent workers
    
    processed_resources = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all resources for processing
        future_to_resource = {executor.submit(process_resource, resource): resource for resource in resources}
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_resource):
            try:
                processed_resource = future.result()
                processed_resources.append(processed_resource)
            except Exception as e:
                resource = future_to_resource[future]
                logger.error(f"Error processing resource {resource.get('title', 'Unknown')}: {str(e)}")
                resource["process_error"] = str(e)
                processed_resources.append(resource)
    
    logger.info(f"Processed {len(processed_resources)} resources")
    return processed_resources 