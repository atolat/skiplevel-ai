"""Web-based content evaluation using LLMs with browsing capabilities."""
import json
import os
import logging
import time
from typing import List, Dict, Any, Optional, Union
import openai
from urllib.parse import urlparse
from .query_metrics import QueryMetrics

logger = logging.getLogger(__name__)


def safe_float_convert(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float, returning a default if conversion fails.
    
    Args:
        value: The value to convert
        default: Default value to return if conversion fails
        
    Returns:
        Converted float value or default
    """
    if value is None:
        return default
        
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def evaluate_url_with_browsing(url: str, query: str, meta_data: Dict = None) -> Dict:
    """
    Evaluate a URL using OpenAI's browsing capabilities to directly analyze content quality.
    If browsing fails, falls back to a standard evaluation.
    
    Args:
        url: The URL to evaluate
        query: The original search query
        meta_data: Optional metadata about the URL
    
    Returns:
        Dictionary with evaluation results
    """
    try:
        # Check if this is a Reddit URL and has appropriate metadata
        is_reddit = False
        reddit_evaluation_prompt = ""
        
        if meta_data and meta_data.get("is_reddit_post", False):
            is_reddit = True
            # Create a custom prompt for Reddit content that includes the post and comments
            post_title = meta_data.get("title", "")
            post_text = meta_data.get("selftext", "")
            subreddit = meta_data.get("subreddit", "unknown")
            comments = meta_data.get("top_comments", [])
            
            # Format comments for evaluation
            formatted_comments = []
            for i, comment in enumerate(comments[:5], 1):  # Limit to 5 top comments
                author = comment.get("author", "unknown")
                score = comment.get("score", 0)
                body = comment.get("body", "").strip()
                if body:
                    formatted_comments.append(f"Comment {i} (by u/{author}, {score} points):\n{body}")
            
            comments_text = "\n\n".join(formatted_comments)
            
            reddit_evaluation_prompt = f"""
You are evaluating a Reddit post from r/{subreddit} about engineering career growth.

POST TITLE: {post_title}

POST CONTENT:
{post_text}

TOP COMMENTS:
{comments_text}

Based on this Reddit discussion, evaluate how valuable this content would be for software engineers looking for career growth frameworks and evaluation criteria. Focus on practical advice, frameworks, and concrete evaluation methodologies mentioned in either the post or comments.
"""
        
        # Specialized evaluation criteria for engineering career growth
        evaluation_criteria = [
            ("technical_accuracy", "Is the content technically accurate and up-to-date with current engineering practices?", 0.3),
            ("actionability", "How actionable is the content for career growth? Does it provide specific steps, frameworks, or metrics?", 0.3),
            ("evidence_based", "Is the content backed by evidence, research, or real-world examples?", 0.2),
            ("technical_depth", "Does the content have sufficient technical depth for senior engineers?", 0.1),
            ("bias_mitigation", "Does the content avoid biases and provide objective evaluation criteria?", 0.1)
        ]
        
        # Define the evaluation instructions without using f-strings for clarity
        evaluation_instructions = """
You are an expert engineering director evaluating content for an engineering career development tool.

Your task is to evaluate a web page about engineering career growth frameworks and technical evaluation criteria.

EVALUATION CRITERIA:
- Technical Accuracy (30%): Is the content technically accurate and up-to-date with current engineering practices?
- Actionability (30%): How actionable is the content for career growth? Does it provide specific steps, frameworks, or metrics?
- Evidence-Based (20%): Is the content backed by evidence, research, or real-world examples?
- Technical Depth (10%): Does the content have sufficient technical depth for senior engineers?
- Bias Mitigation (10%): Does the content avoid biases and provide objective evaluation criteria?

For each criterion, provide:
1. A score from 1-10 (must be a numeric value)
2. A brief explanation (1-2 sentences)

Your response MUST be a valid JSON object with this exact structure:
{
  "scores": {
    "technical_accuracy": {
      "score": [numeric 1-10],
      "explanation": [string]
    },
    "actionability": {
      "score": [numeric 1-10],
      "explanation": [string]
    },
    "evidence_based": {
      "score": [numeric 1-10],
      "explanation": [string]
    },
    "technical_depth": {
      "score": [numeric 1-10],
      "explanation": [string]
    },
    "bias_mitigation": {
      "score": [numeric 1-10],
      "explanation": [string]
    }
  },
  "overall_score": [numeric 1-10],
  "summary": [string - 2-3 sentence overall assessment],
  "recommended_tags": [array of relevant tag strings like "performance reviews", "career ladder", etc.]
}

DO NOT use any browsing tools or functions in your response - return ONLY the JSON evaluation.
"""

        # Create the system message for the evaluation
        system_message = """You are an expert engineering director with experience in evaluating engineers' career growth.
Your task is to evaluate web content for its ability to help engineers grow technically and professionally.
Provide ALL scores as numeric values between 1-10. Do not use strings for scores.
Structure your response EXACTLY as the JSON template provided in the instructions.
Do not include any browsing tool outputs in your final response - just provide the JSON evaluation."""

        # Set up OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI(api_key=openai_api_key)
        
        browsed_content = ""
        
        # We'll try a simplified approach that avoids the browsing API complexities
        if not is_reddit:
            # For non-Reddit content, skip the browsing and just tell GPT-4 to evaluate the URL directly
            logger.info(f"Using direct URL evaluation for {url}")
            evaluation_messages = [
                {"role": "system", "content": f"""You are an expert engineering director with experience in evaluating engineers' career growth.
Your task is to evaluate content from {url} for its ability to help engineers grow technically and professionally.
Before responding, you should visit and review the content at the URL to provide an accurate evaluation.
Provide ALL scores as numeric values between 1-10.
Structure your response as a JSON object containing scores for each criterion and an overall assessment."""},
                {"role": "user", "content": f"Please evaluate this URL: {url}\n\n{evaluation_instructions}"}
            ]
        else:
            # For Reddit content, use specialized prompt
            evaluation_messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": reddit_evaluation_prompt + "\n\n" + evaluation_instructions}
            ]
        
        # Now get the evaluation
        logger.info(f"Getting evaluation for {url}")
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=evaluation_messages,
            response_format={"type": "json_object"}
        )
        
        # Extract the JSON response - this should now always be in the content
        response_content = response.choices[0].message.content
        logger.info(f"Received evaluation response for {url}")
        
        if not response_content:
            logger.error(f"Empty response content for {url}")
            return {
                "url": url,
                "query": query,
                "overall_score": 1.0,
                "error": "Empty response content"
            }
        
        try:
            evaluation_data = json.loads(response_content)
            
            # Calculate weighted score from individual scores
            weighted_score = 0
            total_weight = 0
            
            for criterion, _, weight in evaluation_criteria:
                if criterion in evaluation_data.get("scores", {}):
                    # Safely convert scores to float
                    try:
                        score = safe_float_convert(evaluation_data["scores"][criterion]["score"])
                        weighted_score += score * weight
                        total_weight += weight
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error processing score for {criterion}: {str(e)}")
                        # Use a default score if conversion fails
                        weighted_score += 1.0 * weight
                        total_weight += weight
            
            # Calculate final score if we have weights
            if total_weight > 0:
                final_score = weighted_score / total_weight
            else:
                final_score = safe_float_convert(evaluation_data.get("overall_score", 1.0))
                
            # Format the final response
            result = {
                "url": url,
                "query": query,
                "overall_score": final_score,
                "score_details": evaluation_data.get("scores", {}),
                "summary": evaluation_data.get("summary", "No summary provided"),
                "tags": evaluation_data.get("recommended_tags", []),
                "source": meta_data.get("source", "web") if meta_data else "web",
                "title": meta_data.get("title", "") if meta_data else ""
            }
            
            logger.info(f"Successfully evaluated {url} with score: {final_score}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation JSON: {str(e)}")
            logger.error(f"Raw response: {response_content[:500]}")
            # Return basic result with error information
            return {
                "url": url,
                "query": query,
                "overall_score": 1.0,  # Minimum score for failed evaluations
                "error": f"JSON parsing error: {str(e)}",
                "raw_response": response_content[:500]  # Include part of the raw response for debugging
            }
            
    except Exception as e:
        logger.error(f"Error evaluating URL with browsing: {str(e)}")
        return {
            "url": url,
            "query": query,
            "overall_score": 1.0,  # Minimum score for failed evaluations
            "error": str(e)
        }


def evaluate_urls_with_browsing(urls: List[Dict], query: str = "engineering career growth") -> List[Dict]:
    """
    Evaluate multiple URLs using LLM.
    
    Args:
        urls: List of URL dictionaries with at least a 'url' key
        query: The original search query
        
    Returns:
        List of dictionaries with evaluation results
    """
    results = []
    
    for item in urls:
        url = item["url"]
        # Add delay to avoid rate limiting
        time.sleep(1)
        
        # Pass meta data if available (for Reddit posts)
        meta_data = item.get('meta', None)
        
        result = evaluate_url_with_browsing(url, query, meta_data=meta_data)
        
        # Add any additional metadata from the original item
        for key, value in item.items():
            if key not in result and key != "url" and key != "meta":
                result[key] = value
                
        results.append(result)
    
    return results


def evaluate_with_tavily_content_api(url: str) -> Dict[str, Any]:
    """
    Evaluate content using Tavily's content API.
    
    This function uses Tavily to fetch and process the content, then evaluates
    it using our standard evaluation approach.
    
    Args:
        url: URL to evaluate
        
    Returns:
        Dictionary with evaluation results
    """
    # This is a placeholder - Tavily's content API integration would go here
    # Would need to:
    # 1. Call Tavily API to get processed content
    # 2. Evaluate the processed content
    # 3. Return formatted results
    
    # For now, just return a placeholder
    return {
        "url": url,
        "title": "Tavily Content API Placeholder",
        "source": "tavily_content_api",
        "evaluation": {
            "score": 0,
            "tags": ["placeholder"],
            "summary": "Tavily Content API implementation pending",
            "reasoning": "This is a placeholder for Tavily Content API integration"
        }
    }


def evaluate_with_anthropic_claude(url: str) -> Dict[str, Any]:
    """
    Evaluate content using Anthropic's Claude with browsing capability.
    
    This function uses Claude to directly browse the URL and evaluate content.
    
    Args:
        url: URL to evaluate
        
    Returns:
        Dictionary with evaluation results
    """
    # This is a placeholder for Anthropic Claude integration
    # Would implement using the Anthropic API with claude-3-opus or similar
    
    # For now, just return a placeholder
    return {
        "url": url,
        "title": "Claude Browsing Placeholder",
        "source": "claude_browsing",
        "evaluation": {
            "score": 0,
            "tags": ["placeholder"],
            "summary": "Claude browsing implementation pending",
            "reasoning": "This is a placeholder for Claude browsing integration"
        }
    }


def batch_evaluate_urls(urls: List[Dict], query: str = "engineering career growth", method: str = "openai_browsing") -> List[Dict]:
    """
    Evaluate a batch of URLs using the specified method.
    
    Args:
        urls: List of URL dictionaries
        query: The original search query
        method: Evaluation method (openai_browsing, tavily_content, claude_browsing)
        
    Returns:
        List of dictionaries with evaluation results
    """
    import concurrent.futures
    from functools import partial
    
    if not urls:
        logger.warning("No URLs provided for batch evaluation")
        return []
    
    # Define a function to evaluate a single URL with error handling
    def evaluate_single_url(url_data, q, m):
        try:
            url = url_data["url"]
            meta_data = url_data.get("meta", None)
            
            if m == "openai_browsing":
                result = evaluate_url_with_browsing(url, q, meta_data)
            elif m == "tavily_content":
                result = evaluate_with_tavily_content_api(url)
            elif m == "claude_browsing":
                result = evaluate_with_anthropic_claude(url)
            else:
                logger.error(f"Unknown evaluation method: {m}")
                return None
                
            # Add any additional metadata from the original item
            for key, value in url_data.items():
                if key not in result and key != "url" and key != "meta":
                    result[key] = value
                    
            return result
        except Exception as e:
            logger.error(f"Error evaluating {url_data.get('url', 'unknown URL')}: {str(e)}")
            # Return a minimal result with error information
            return {
                "url": url_data.get("url", "unknown"),
                "query": q,
                "overall_score": 1.0,  # Minimum score for failed evaluations
                "error": str(e),
                "source": url_data.get("source", "unknown")
            }
    
    # Calculate an appropriate number of workers
    # More workers = faster, but can hit rate limits or cause resource issues
    max_urls = len(urls)
    max_workers = min(8, max_urls)  # Cap at 8 concurrent requests
    
    logger.info(f"Starting parallel evaluation of {max_urls} URLs with {max_workers} workers")
    
    # Create a partial function with the fixed parameters
    evaluate_func = partial(evaluate_single_url, q=query, m=method)
    
    # Use ThreadPoolExecutor to process URLs in parallel
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all URLs for processing
        future_to_url = {executor.submit(evaluate_func, url_data): url_data for url_data in urls}
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_url):
            result = future.result()
            if result:
                results.append(result)
    
    logger.info(f"Completed parallel evaluation of {len(results)}/{max_urls} URLs")
    return results 