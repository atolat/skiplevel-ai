"""
Dual perspective content evaluation module.

This module provides evaluation functions from two different perspectives:
1. Engineering Manager perspective - focusing on leadership, growth frameworks, process, and team efficiency
2. Staff/Principal Engineer perspective - focusing on technical depth, architecture, and engineering excellence
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
import openai
import time

logger = logging.getLogger(__name__)

def safe_float_convert(value, default=1.0):
    """Safely convert value to float with a default fallback."""
    try:
        if isinstance(value, str) and value.strip() == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def evaluate_as_engineering_manager(url: str, meta_data: Optional[Dict] = None) -> Dict:
    """
    Evaluate content from an Engineering Manager's perspective.
    
    This focuses on leadership aspects, team growth frameworks, processes,
    and how the content helps with people management.
    
    Args:
        url: The URL to evaluate
        meta_data: Optional metadata about the content
        
    Returns:
        Dictionary with evaluation results
    """
    try:
        # Set up OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Manager-specific evaluation criteria
        evaluation_criteria = [
            ("leadership_frameworks", "Does the content provide useful frameworks or strategies for engineering leadership?", 0.3),
            ("team_growth", "How well does the content address team development and growth?", 0.25),
            ("process_improvement", "Does the content offer valuable insights on process improvement?", 0.2),
            ("people_management", "How effective is the content for addressing people management challenges?", 0.15),
            ("practical_application", "How easily can the concepts be applied in real engineering teams?", 0.1),
        ]
        
        # Engineering Manager evaluation prompt
        system_prompt = """You are an experienced Engineering Manager evaluating content to determine its value 
for other engineering leaders.

Your task is to quickly evaluate a web resource WITHOUT spending excessive time reading the full content. 
Use the title, headings, initial paragraphs, and any visible frameworks or models to make your assessment.

Focus on leadership value: how useful is this for managing engineering teams, developing engineers' careers, 
improving processes, resolving team conflicts, or making strategic technical decisions?"""
        
        user_prompt = f"""Please evaluate this URL from an Engineering Manager's perspective: {url}

Format your response as a JSON object with this exact structure:
{{
  "scores": {{
    "leadership_frameworks": {{
      "score": [numeric 1-10],
      "explanation": "[brief explanation]"
    }},
    "team_growth": {{
      "score": [numeric 1-10],
      "explanation": "[brief explanation]"
    }},
    "process_improvement": {{
      "score": [numeric 1-10],
      "explanation": "[brief explanation]"
    }},
    "people_management": {{
      "score": [numeric 1-10],
      "explanation": "[brief explanation]"
    }},
    "practical_application": {{
      "score": [numeric 1-10],
      "explanation": "[brief explanation]"
    }}
  }},
  "overall_score": [numeric 1-10],
  "summary": "[2-3 sentence summary of value to engineering managers]",
  "key_insights": ["[key insight 1]", "[key insight 2]", "[key insight 3]"]
}}

Keep your evaluation focused and brief. You don't need to read the entire content.
ALL scores MUST be numeric values between 1-10."""

        evaluation_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Get evaluation from OpenAI
        logger.info(f"Getting Engineering Manager evaluation for {url}")
        response = client.chat.completions.create(
            model="gpt-4o",  # Uses a faster model for quick evaluations
            messages=evaluation_messages,
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        # Extract the JSON response
        response_content = response.choices[0].message.content
        logger.info(f"Received Engineering Manager evaluation for {url}")
        
        if not response_content:
            logger.error(f"Empty response content for {url}")
            return {
                "url": url,
                "perspective": "engineering_manager",
                "overall_score": 1.0,
                "error": "Empty response content"
            }
        
        try:
            evaluation_data = json.loads(response_content)
            
            # Calculate weighted score
            weighted_score = 0
            total_weight = 0
            
            for criterion, _, weight in evaluation_criteria:
                if criterion in evaluation_data.get("scores", {}):
                    try:
                        score = safe_float_convert(evaluation_data["scores"][criterion]["score"])
                        weighted_score += score * weight
                        total_weight += weight
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error processing score for {criterion}: {str(e)}")
                        weighted_score += 1.0 * weight
                        total_weight += weight
            
            # Calculate final score
            if total_weight > 0:
                final_score = weighted_score / total_weight
            else:
                final_score = safe_float_convert(evaluation_data.get("overall_score", 1.0))
            
            # Format the final response
            result = {
                "url": url,
                "perspective": "engineering_manager",
                "overall_score": final_score,
                "score_details": evaluation_data.get("scores", {}),
                "summary": evaluation_data.get("summary", "No summary provided"),
                "insights": evaluation_data.get("key_insights", []),
                "source": meta_data.get("source", "web") if meta_data else "web",
                "title": meta_data.get("title", "") if meta_data else ""
            }
            
            logger.info(f"Engineering Manager evaluation complete for {url} with score: {final_score}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Engineering Manager evaluation JSON: {str(e)}")
            return {
                "url": url,
                "perspective": "engineering_manager",
                "overall_score": 1.0,
                "error": f"JSON parsing error: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Error in Engineering Manager evaluation: {str(e)}")
        return {
            "url": url,
            "perspective": "engineering_manager",
            "overall_score": 1.0,
            "error": str(e)
        }

def evaluate_as_staff_engineer(url: str, meta_data: Optional[Dict] = None) -> Dict:
    """
    Evaluate content from a Staff/Principal Engineer's perspective.
    
    This focuses on technical depth, architecture, systems thinking,
    and engineering excellence aspects of the content.
    
    Args:
        url: The URL to evaluate
        meta_data: Optional metadata about the content
        
    Returns:
        Dictionary with evaluation results
    """
    try:
        # Set up OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Staff Engineer-specific evaluation criteria
        evaluation_criteria = [
            ("technical_depth", "How technically deep and substantive is the content?", 0.3),
            ("architectural_insight", "Does the content provide valuable architectural insights or patterns?", 0.25),
            ("systems_thinking", "How well does the content address complex systems and their interactions?", 0.2),
            ("engineering_excellence", "Does the content promote engineering best practices and excellence?", 0.15),
            ("technical_applicability", "How readily can the technical concepts be applied?", 0.1),
        ]
        
        # Staff Engineer evaluation prompt
        system_prompt = """You are an experienced Staff/Principal Engineer evaluating content to determine 
its technical value for senior engineers.

Your task is to quickly evaluate a web resource WITHOUT spending excessive time reading the full content. 
Use the title, headings, initial paragraphs, code samples, diagrams, and technical depth to make your assessment.

Focus on technical excellence: how useful is this for understanding complex systems, making architectural decisions, 
improving code quality, addressing scalability, or deepening technical expertise?"""
        
        user_prompt = f"""Please evaluate this URL from a Staff/Principal Engineer's perspective: {url}

Format your response as a JSON object with this exact structure:
{{
  "scores": {{
    "technical_depth": {{
      "score": [numeric 1-10],
      "explanation": "[brief explanation]"
    }},
    "architectural_insight": {{
      "score": [numeric 1-10],
      "explanation": "[brief explanation]"
    }},
    "systems_thinking": {{
      "score": [numeric 1-10],
      "explanation": "[brief explanation]"
    }},
    "engineering_excellence": {{
      "score": [numeric 1-10],
      "explanation": "[brief explanation]"
    }},
    "technical_applicability": {{
      "score": [numeric 1-10],
      "explanation": "[brief explanation]"
    }}
  }},
  "overall_score": [numeric 1-10],
  "summary": "[2-3 sentence summary of value to staff engineers]",
  "key_insights": ["[key technical insight 1]", "[key technical insight 2]", "[key technical insight 3]"]
}}

Keep your evaluation focused and brief. You don't need to read the entire content.
ALL scores MUST be numeric values between 1-10."""

        evaluation_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Get evaluation from OpenAI
        logger.info(f"Getting Staff Engineer evaluation for {url}")
        response = client.chat.completions.create(
            model="gpt-4o",  # Uses a faster model for quick evaluations
            messages=evaluation_messages,
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        # Extract the JSON response
        response_content = response.choices[0].message.content
        logger.info(f"Received Staff Engineer evaluation for {url}")
        
        if not response_content:
            logger.error(f"Empty response content for {url}")
            return {
                "url": url,
                "perspective": "staff_engineer",
                "overall_score": 1.0,
                "error": "Empty response content"
            }
        
        try:
            evaluation_data = json.loads(response_content)
            
            # Calculate weighted score
            weighted_score = 0
            total_weight = 0
            
            for criterion, _, weight in evaluation_criteria:
                if criterion in evaluation_data.get("scores", {}):
                    try:
                        score = safe_float_convert(evaluation_data["scores"][criterion]["score"])
                        weighted_score += score * weight
                        total_weight += weight
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error processing score for {criterion}: {str(e)}")
                        weighted_score += 1.0 * weight
                        total_weight += weight
            
            # Calculate final score
            if total_weight > 0:
                final_score = weighted_score / total_weight
            else:
                final_score = safe_float_convert(evaluation_data.get("overall_score", 1.0))
            
            # Format the final response
            result = {
                "url": url,
                "perspective": "staff_engineer",
                "overall_score": final_score,
                "score_details": evaluation_data.get("scores", {}),
                "summary": evaluation_data.get("summary", "No summary provided"),
                "insights": evaluation_data.get("key_insights", []),
                "source": meta_data.get("source", "web") if meta_data else "web",
                "title": meta_data.get("title", "") if meta_data else ""
            }
            
            logger.info(f"Staff Engineer evaluation complete for {url} with score: {final_score}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Staff Engineer evaluation JSON: {str(e)}")
            return {
                "url": url,
                "perspective": "staff_engineer",
                "overall_score": 1.0,
                "error": f"JSON parsing error: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Error in Staff Engineer evaluation: {str(e)}")
        return {
            "url": url,
            "perspective": "staff_engineer",
            "overall_score": 1.0,
            "error": str(e)
        }

def dual_perspective_evaluation(url: str, meta_data: Optional[Dict] = None) -> Dict:
    """
    Evaluate content from both Engineering Manager and Staff Engineer perspectives.
    
    Args:
        url: The URL to evaluate
        meta_data: Optional metadata about the content
        
    Returns:
        Dictionary with combined evaluation results
    """
    # Get evaluations from both perspectives
    manager_eval = evaluate_as_engineering_manager(url, meta_data)
    
    # Add small delay to avoid rate limiting
    time.sleep(1)
    
    staff_eval = evaluate_as_staff_engineer(url, meta_data)
    
    # Combine the results
    result = {
        "url": url,
        "title": meta_data.get("title", "") if meta_data else "",
        "source": meta_data.get("source", "web") if meta_data else "web",
        "manager_score": manager_eval.get("overall_score", 1.0),
        "staff_score": staff_eval.get("overall_score", 1.0),
        "avg_score": (manager_eval.get("overall_score", 1.0) + staff_eval.get("overall_score", 1.0)) / 2,
        "manager_evaluation": {
            "summary": manager_eval.get("summary", ""),
            "insights": manager_eval.get("insights", []),
            "scores": manager_eval.get("score_details", {})
        },
        "staff_evaluation": {
            "summary": staff_eval.get("summary", ""),
            "insights": staff_eval.get("insights", []),
            "scores": staff_eval.get("score_details", {})
        }
    }
    
    return result

def batch_evaluate_urls(urls: List[Dict]) -> List[Dict]:
    """
    Evaluate a batch of URLs from dual perspectives.
    
    Args:
        urls: List of URL dictionaries with at least a 'url' key
        
    Returns:
        List of dictionaries with evaluation results
    """
    results = []
    
    for item in urls:
        url = item["url"]
        # Add delay to avoid rate limiting
        time.sleep(1)
        
        # Pass meta data if available
        meta_data = item.get('meta', {})
        if not meta_data:
            meta_data = {
                "title": item.get("title", ""),
                "source": item.get("source", "web")
            }
        
        try:
            result = dual_perspective_evaluation(url, meta_data)
            
            # Add any additional metadata from the original item
            for key, value in item.items():
                if key not in result and key != "url" and key != "meta":
                    result[key] = value
                    
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error evaluating {url}: {str(e)}")
            # Return a minimal result with error information
            results.append({
                "url": url,
                "title": meta_data.get("title", ""),
                "source": meta_data.get("source", "web"),
                "manager_score": 1.0,
                "staff_score": 1.0,
                "avg_score": 1.0,
                "error": str(e)
            })
    
    return results 