"""
Content curation pipeline implementation.
"""

import logging
import time
import os
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from .interfaces import ContentItem, ContentSource, ContentProcessor
from .sources.substack import SubstackSource, SubstackProcessor
from .sources.medium import MediumSource, MediumProcessor
from .sources.youtube import YouTubeSource, YouTubeProcessor
from .sources.papers import TechnicalPapersSource, PapersProcessor
from .sources.reddit import RedditSource, RedditProcessor
from .visualizers.markdown import MarkdownTableVisualizer
from .config import load_config, get_default_config, ConfigSchema
from .modules.content_evaluation import evaluate_content, calculate_query_metrics
from .modules.web_evaluation import batch_evaluate_urls, evaluate_urls_with_browsing
from .modules.dual_perspective_evaluation import dual_perspective_evaluation, batch_evaluate_urls as dual_batch_evaluate

logger = logging.getLogger(__name__)

class ContentPipeline:
    """Main content curation pipeline."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None, data_dir: Optional[Path] = None):
        """
        Initialize the pipeline.
        
        Args:
            config_path: Path to configuration file (optional)
            data_dir: Base directory for data storage (overrides config)
        """
        # Load configuration
        if config_path:
            self.config = load_config(config_path)
        else:
            self.config = get_default_config()
        
        # Override data_dir if provided
        self.data_dir = data_dir or Path(self.config.data_dir)
        
        # Set up directory structure
        self.cache_dir = self.data_dir / "cache"
        self.content_dir = self.data_dir / "content"
        self.exports_dir = self.data_dir / "output" if "output" in str(self.data_dir) else self.data_dir / "exports"
        self.stats_dir = self.data_dir / "stats"
        
        for directory in [self.cache_dir, self.content_dir, self.exports_dir, self.stats_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize sources based on configuration
        self.sources: Dict[str, ContentSource] = {}
        self._initialize_sources()
        
        # Initialize processors based on configuration
        self.processors: Dict[str, ContentProcessor] = {}
        self._initialize_processors()
        
        # Initialize visualizer
        self.visualizer = MarkdownTableVisualizer(self.data_dir)
    
    def _initialize_sources(self):
        """Initialize content sources based on configuration."""
        for source_id, source_config in self.config.sources.items():
            if not source_config.enabled:
                logger.info(f"Skipping disabled source: {source_id}")
                continue
                
            try:
                source_type = source_config.type
                source_cache_dir = self.cache_dir / source_id
                source_output_dir = self.content_dir / source_id
                
                # Ensure directories exist
                source_cache_dir.mkdir(parents=True, exist_ok=True)
                source_output_dir.mkdir(parents=True, exist_ok=True)
                
                # Create appropriate source
                if source_type == "substack":
                    # Extract curated newsletters from config
                    newsletters = source_config.source_params.get("curated_newsletters", [])
                    
                    self.sources[source_id] = SubstackSource(
                        cache_dir=source_cache_dir,
                        output_dir=source_output_dir
                    )
                    # Update newsletters from config if provided
                    if newsletters:
                        self.sources[source_id].curated_newsletters = newsletters
                        
                elif source_type == "medium":
                    # Extract tags from config
                    tags = source_config.source_params.get("tags", [])
                    
                    self.sources[source_id] = MediumSource(
                        cache_dir=source_cache_dir,
                        output_dir=source_output_dir
                    )
                    # Update tags from config if provided
                    if tags:
                        self.sources[source_id].topics = tags
                        
                elif source_type == "youtube":
                    self.sources[source_id] = YouTubeSource(
                        cache_dir=source_cache_dir,
                        output_dir=source_output_dir
                    )
                    
                elif source_type == "papers":
                    self.sources[source_id] = TechnicalPapersSource(
                        cache_dir=source_cache_dir,
                        output_dir=source_output_dir
                    )
                    
                elif source_type == "reddit":
                    # Extract recommended subreddits from config
                    subreddits = source_config.source_params.get("recommended_subreddits", [])
                    
                    self.sources[source_id] = RedditSource(
                        cache_dir=source_cache_dir,
                        output_dir=source_output_dir
                    )
                    # Update subreddits from config if provided
                    if subreddits:
                        self.sources[source_id].recommended_subreddits = subreddits
                    
                else:
                    logger.warning(f"Unknown source type: {source_type}")
                    continue
                    
                logger.info(f"Initialized source: {source_id} ({source_type})")
                    
            except Exception as e:
                logger.error(f"Error initializing source {source_id}: {str(e)}")
    
    def _initialize_processors(self):
        """Initialize content processors based on configuration."""
        for processor_id, processor_config in self.config.processors.items():
            if not processor_config.enabled:
                logger.info(f"Skipping disabled processor: {processor_id}")
                continue
                
            try:
                processor_type = processor_config.type
                processor_output_dir = self.content_dir / processor_id
                
                # Ensure directory exists
                processor_output_dir.mkdir(parents=True, exist_ok=True)
                
                # Create appropriate processor
                if processor_type == "substack":
                    self.processors[processor_id] = SubstackProcessor(
                        output_dir=processor_output_dir
                    )
                elif processor_type == "medium":
                    self.processors[processor_id] = MediumProcessor(
                        output_dir=processor_output_dir
                    )
                elif processor_type == "youtube":
                    self.processors[processor_id] = YouTubeProcessor(
                        output_dir=processor_output_dir
                    )
                elif processor_type == "papers":
                    self.processors[processor_id] = PapersProcessor(
                        output_dir=processor_output_dir
                    )
                elif processor_type == "reddit":
                    self.processors[processor_id] = RedditProcessor(
                        output_dir=processor_output_dir
                    )
                else:
                    logger.warning(f"Unknown processor type: {processor_type}")
                    continue
                    
                logger.info(f"Initialized processor: {processor_id} ({processor_type})")
                    
            except Exception as e:
                logger.error(f"Error initializing processor {processor_id}: {str(e)}")
    
    def discover_content(self, query: Optional[str] = None, limit_per_source: Optional[int] = None) -> List[ContentItem]:
        """
        Discover content from all sources.
        
        Args:
            query: Search query (overrides config queries)
            limit_per_source: Maximum items per source (overrides config limits)
        
        Returns:
            List of discovered content items
        """
        discovered_items = []
        
        for source_id, source in self.sources.items():
            try:
                source_config = self.config.sources[source_id]
                
                # Use provided query or get from config
                if query:
                    queries = [query]
                else:
                    queries = source_config.seed_queries
                
                # Use provided limit or get from config
                source_limit = limit_per_source or source_config.limit
                
                # Process each query
                source_items = []
                for q in queries:
                    logger.info(f"Discovering content from {source_id} with query: {q}")
                    items = source.discover(q, source_limit)
                    source_items.extend(items)
                    logger.info(f"Found {len(items)} items from {source_id} for query: {q}")
                
                # Process custom URLs
                if source_config.custom_urls:
                    logger.info(f"Processing {len(source_config.custom_urls)} custom URLs for {source_id}")
                    for url in source_config.custom_urls:
                        try:
                            if source.is_source_url(url):
                                item = source.process_url(url)
                                if item:
                                    source_items.append(item)
                        except Exception as e:
                            logger.error(f"Error processing custom URL {url}: {str(e)}")
                
                # Add to discovered items
                discovered_items.extend(source_items)
                logger.info(f"Total items from {source_id}: {len(source_items)}")
                
            except Exception as e:
                logger.error(f"Error discovering content from {source_id}: {str(e)}")
        
        return discovered_items
    
    def discover_content_parallel(self, query: Optional[str] = None, limit_per_source: Optional[int] = None) -> List[ContentItem]:
        """
        Discover content from all sources in parallel.
        
        This method executes content discovery across all sources simultaneously using ThreadPoolExecutor,
        which significantly improves performance for I/O-bound operations like API calls.
        
        Args:
            query: Optional query string to use for all sources. If None, uses the source's seed queries.
            limit_per_source: Optional limit on the number of items to retrieve from each source.
            
        Returns:
            A list of ContentItem objects discovered from all sources.
        """
        all_items = []
        
        def process_source(source_name, source):
            try:
                items = []
                source_config = self.config.sources[source_name]
                
                # Use provided query or get from config
                if query:
                    queries = [query]
                else:
                    queries = source_config.seed_queries
                
                # Use provided limit or get from config
                source_limit = limit_per_source or source_config.limit
                
                # Process each query
                for q in queries:
                    logger.info(f"Discovering content from {source_name} with query: {q}")
                    found_items = source.discover(q, source_limit)
                    logger.info(f"Found {len(found_items)} items from {source_name} for query: {q}")
                    items.extend(found_items)
                
                # Process custom URLs if available
                custom_urls = source_config.custom_urls
                if custom_urls:
                    logger.info(f"Processing {len(custom_urls)} custom URLs for {source_name}")
                    for url in custom_urls:
                        try:
                            if source.is_source_url(url):
                                item = source.process_url(url)
                                if item:
                                    items.append(item)
                        except Exception as e:
                            logger.error(f"Error processing URL {url}: {str(e)}")
                
                logger.info(f"Total items from {source_name}: {len(items)}")
                return items
                
            except Exception as e:
                logger.error(f"Error discovering content from {source_name}: {str(e)}")
                return []
        
        # Execute all sources in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_source = {
                executor.submit(process_source, source_name, source): source_name 
                for source_name, source in self.sources.items()
            }
            
            for future in concurrent.futures.as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    items = future.result()
                    all_items.extend(items)
                except Exception as e:
                    logger.error(f"Error processing source {source_name}: {str(e)}")
        
        return all_items
    
    def process_content(self, items: List[ContentItem]) -> Dict[str, Any]:
        """
        Process discovered content items.
        
        Args:
            items: List of content items to process
            
        Returns:
            Processing statistics
        """
        stats = {
            "processed_items": 0,
            "failed_items": 0,
            "source_stats": {}
        }
        
        # Initialize source stats
        for source_id in self.sources.keys():
            stats["source_stats"][source_id] = {
                "processed_count": 0,
                "error_count": 0,
                "total_words": 0,
                "average_words": 0
            }
        
        # Process each item
        for item in items:
            try:
                source_type = item.metadata.source_type
                
                # Get appropriate processor
                processor = None
                if source_type == "substack" and "substack" in self.processors:
                    processor = self.processors["substack"]
                elif source_type == "medium" and "medium" in self.processors:
                    processor = self.processors["medium"]
                elif source_type == "youtube" and "youtube" in self.processors:
                    processor = self.processors["youtube"]
                elif source_type == "technical_paper" and "papers" in self.processors:
                    processor = self.processors["papers"]
                
                # Process item if processor exists
                processed_data = {}
                if processor:
                    processed_data = processor.process(item)
                else:
                    # Default processing
                    processed_data = {
                        "id": item.id,
                        "title": item.title,
                        "url": item.url
                    }
                
                # Update source-specific stats
                source_stats = stats["source_stats"].get(source_type, {
                    "processed_count": 0,
                    "error_count": 0,
                    "total_words": 0,
                    "average_words": 0
                })
                
                source_stats["processed_count"] += 1
                
                # Update word count
                word_count = 0
                if isinstance(processed_data, dict) and "word_count" in processed_data:
                    word_count = processed_data["word_count"]
                elif hasattr(processed_data, "word_count"):
                    word_count = processed_data.word_count
                elif item.description:
                    word_count = len(item.description.split())
                
                source_stats["total_words"] += word_count
                if source_stats["processed_count"] > 0:
                    source_stats["average_words"] = source_stats["total_words"] / source_stats["processed_count"]
                
                # Update source stats
                stats["source_stats"][source_type] = source_stats
                stats["processed_items"] += 1
                
            except Exception as e:
                logger.error(f"Error processing item {item.id}: {str(e)}")
                stats["failed_items"] += 1
                if source_type in stats["source_stats"]:
                    stats["source_stats"][source_type]["error_count"] += 1
        
        return stats
    
    def _read_text_file(self, file_path: str) -> str:
        """
        Read text from a file, trying multiple encodings if necessary.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            File contents as string, or empty string on error
        """
        encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {str(e)}")
                return ""
        
        # If none of the encodings worked, try binary mode
        try:
            with open(file_path, 'rb') as f:
                return str(f.read())
        except Exception as e:
            logger.error(f"Error reading binary file {file_path}: {str(e)}")
            return ""

    def evaluate_content(self, items: List[ContentItem]) -> List[Dict]:
        """
        Evaluate content quality.
        
        Args:
            items: List of content items to evaluate
            
        Returns:
            List of evaluation results
        """
        if not self.config.evaluation.enabled:
            logger.info("Content evaluation disabled in config")
            return []
            
        try:
            # Prepare items for evaluation
            eval_items = []
            for item in items:
                # Get text content from file if available
                text_content = ""
                if item.text_path and os.path.exists(item.text_path):
                    text_content = self._read_text_file(item.text_path)
                    if not text_content:
                        text_content = item.description
                else:
                    text_content = item.description
                
                eval_items.append({
                    "url": item.url,
                    "title": item.title,
                    "text": text_content[:25000],  # Limit to avoid token limits
                    "source": item.metadata.source_type
                })
            
            # Choose evaluation method based on configuration
            method = self.config.evaluation.method
            
            if method == "dual_perspective":
                # Use dual perspective evaluation (engineering manager and staff engineer perspectives)
                logger.info(f"Using dual perspective evaluation for {len(eval_items)} items")
                # Transform items for dual perspective evaluation
                dual_eval_items = [
                    {
                        "url": item["url"],
                        "title": item["title"],
                        "source": item["source"],
                        "meta": {
                            "title": item["title"],
                            "source": item["source"]
                        }
                    }
                    for item in eval_items
                ]
                
                # Use parallel processing for batch evaluation
                results = self._parallel_dual_perspective_evaluation(dual_eval_items)
                
                # Transform results to match expected format
                transformed_results = []
                for result in results:
                    transformed_results.append({
                        "url": result["url"],
                        "title": result["title"],
                        "text": "",  # We don't need to pass text back
                        "source": result["source"],
                        "evaluation": {
                            "score": result["avg_score"],
                            "tags": [],  # Add tags based on scores if needed
                            "summary": f"Manager: {result['manager_evaluation']['summary']} | Staff: {result['staff_evaluation']['summary']}",
                            "reasoning": f"Manager score: {result['manager_score']:.1f}/10, Staff score: {result['staff_score']:.1f}/10"
                        },
                        "raw_evaluation": result
                    })
                
                return transformed_results
                
            elif method == "web" or method == "browsing":
                # Use web-based browsing evaluation
                logger.info(f"Using web-based evaluation for {len(eval_items)} items")
                results = batch_evaluate_urls([{"url": item["url"], "meta": item} for item in eval_items])
                
                # Transform results to match expected format
                transformed_results = []
                for result in results:
                    # Handle errors
                    if "error" in result:
                        logger.warning(f"Error evaluating {result['url']}: {result.get('error')}")
                        continue
                        
                    transformed_results.append({
                        "url": result["url"],
                        "title": result.get("title", ""),
                        "text": "",  # We don't need to pass text back
                        "source": result.get("source", "web"),
                        "evaluation": {
                            "score": result.get("overall_score", 1.0),
                            "tags": result.get("tags", []),
                            "summary": result.get("summary", "No summary available"),
                            "reasoning": ""  # Could extract from score details if needed
                        },
                        "raw_evaluation": result
                    })
                
                return transformed_results
                
            else:
                # Default to standard content evaluation
                logger.info(f"Using standard content evaluation for {len(eval_items)} items")
                return evaluate_content(eval_items)
                
        except Exception as e:
            logger.error(f"Error evaluating content: {str(e)}")
            return []

    def _parallel_dual_perspective_evaluation(self, items: List[Dict]) -> List[Dict]:
        """
        Perform dual perspective evaluation in parallel using ThreadPoolExecutor.
        
        Args:
            items: List of items to evaluate, each with a 'url' key
            
        Returns:
            List of evaluation results
        """
        from .modules.dual_perspective_evaluation import dual_perspective_evaluation
        
        results = []
        max_workers = min(8, len(items))  # Limit number of workers to avoid overloading API
        
        def evaluate_item(item):
            url = item["url"]
            meta_data = item.get("meta", {})
            try:
                logger.info(f"Evaluating: {url}")
                result = dual_perspective_evaluation(url, meta_data)
                
                # Add any additional metadata from the original item
                for key, value in item.items():
                    if key not in result and key != "url" and key != "meta":
                        result[key] = value
                        
                return result
            except Exception as e:
                logger.error(f"Error evaluating {url}: {str(e)}")
                # Return a minimal result with error information
                return {
                    "url": url,
                    "title": meta_data.get("title", ""),
                    "source": meta_data.get("source", "web"),
                    "manager_score": 1.0,
                    "staff_score": 1.0,
                    "avg_score": 1.0,
                    "error": str(e),
                    "manager_evaluation": {"summary": "", "insights": [], "scores": {}},
                    "staff_evaluation": {"summary": "", "insights": [], "scores": {}}
                }
        
        # Execute evaluations in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {executor.submit(evaluate_item, item): item for item in items}
            
            for future in concurrent.futures.as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Evaluation failed for {item.get('url')}: {str(e)}")
                    # Add a placeholder result for failed evaluations
                    results.append({
                        "url": item.get("url", "unknown"),
                        "title": item.get("title", ""),
                        "source": item.get("source", "web"),
                        "manager_score": 1.0,
                        "staff_score": 1.0,
                        "avg_score": 1.0,
                        "error": f"Executor error: {str(e)}",
                        "manager_evaluation": {"summary": "", "insights": [], "scores": {}},
                        "staff_evaluation": {"summary": "", "insights": [], "scores": {}}
                    })
        
        return results
    
    def run(self, query: Optional[str] = None, limit_per_source: Optional[int] = None, parallel: bool = False, parallel_eval: bool = False) -> Dict[str, Any]:
        """
        Run the complete pipeline.
        
        Args:
            query: Search query (optional, overrides config queries)
            limit_per_source: Maximum items per source (optional, overrides config limits)
            parallel: Whether to use parallel processing for content discovery
            parallel_eval: Whether to use parallel processing for content evaluation
            
        Returns:
            Pipeline results and statistics
        """
        start_time = time.time()
        results = {
            "query": query or "config-based-queries",
            "timestamp": time.time(),
            "items": [],
            "stats": {},
            "evaluations": []
        }
        
        try:
            # Discover content (parallel or sequential)
            if parallel:
                items = self.discover_content_parallel(query, limit_per_source)
            else:
                items = self.discover_content(query, limit_per_source)
                
            results["items"] = items
            
            # Process content
            processing_stats = self.process_content(items)
            results["stats"] = processing_stats
            
            # Evaluate content if enabled
            if self.config.evaluation.enabled:
                # Store original method to restore it later if needed
                original_method = self.config.evaluation.method
                
                # If using dual perspective and parallel evaluation is requested,
                # we will use our custom method instead of the batch one
                if parallel_eval and original_method == "dual_perspective":
                    # We will handle parallelization in the evaluate_content method
                    # No need to modify the method name
                    pass
                    
                evaluations = self.evaluate_content(items)
                results["evaluations"] = evaluations
                
                # Restore original method if it was changed
                if self.config.evaluation.method != original_method:
                    self.config.evaluation.method = original_method
            
            # Generate visualization
            if items:
                viz_path = self.visualizer.save_table(items)
                results["visualization_path"] = str(viz_path)
            
            # Add runtime stats
            results["runtime_seconds"] = time.time() - start_time
            
            return results
                
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            results["error"] = str(e)
            return results 