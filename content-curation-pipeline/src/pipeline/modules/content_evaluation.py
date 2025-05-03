"""Content evaluation module using LLMs."""
import json
import os
import logging
from typing import List, Dict, Any
import openai
from statistics import mean
from urllib.parse import urlparse
from .query_metrics import QueryMetrics

logger = logging.getLogger(__name__)


def evaluate_content(content: List[Dict]) -> List[Dict]:
    """Evaluate content quality using GPT-4-turbo with specialized evaluation criteria for engineering career growth."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    results = []
    
    for item in content:
        try:
            # Define specialized evaluation criteria focused on engineering career growth
            evaluation_criteria = {
                "technical_accuracy": {
                    "description": "Precision of technical information and engineering concepts",
                    "weight": 0.25
                },
                "growth_actionability": {
                    "description": "Concrete actions engineers can take to advance their careers",
                    "weight": 0.30
                },
                "evidence_based": {
                    "description": "Uses empirical data, case studies, or clear reasoning rather than opinions",
                    "weight": 0.20
                },
                "technical_depth": {
                    "description": "Provides sufficient depth for senior engineers to gain value",
                    "weight": 0.15
                },
                "bias_mitigation": {
                    "description": "Avoids common biases in evaluation; focuses on objective measures of growth",
                    "weight": 0.10
                }
            }

            # Create evaluation prompts with engineering manager persona
            system_content = """You are an exceptionally skilled engineering director with 20+ years of experience growing technical talent across multiple tech companies.

You have a reputation for:
1. Evaluating engineers based purely on their technical merit and impact
2. Providing clear, actionable growth paths based on evidence
3. Identifying high-quality resources that genuinely advance engineering careers
4. Cutting through fluff and focusing on substantial career development concepts
5. Completely eliminating bias from your evaluations
                    
Your goal is to evaluate content for how well it would help an ambitious engineer advance their career without relying on a manager's subjective opinion."""

            # Build user content without using f-strings for the JSON example
            user_content = "I need your assessment of this engineering career content:\n\n"
            user_content += "---\n"
            user_content += item['text'] + "\n"
            user_content += "---\n\n"
            
            user_content += "Evaluate this content using these specific criteria:\n\n"
            
            user_content += "1. Technical Accuracy: " + evaluation_criteria['technical_accuracy']['description'] + "\n"
            user_content += "2. Growth Actionability: " + evaluation_criteria['growth_actionability']['description'] + "\n"
            user_content += "3. Evidence-Based: " + evaluation_criteria['evidence_based']['description'] + "\n"
            user_content += "4. Technical Depth: " + evaluation_criteria['technical_depth']['description'] + "\n"
            user_content += "5. Bias Mitigation: " + evaluation_criteria['bias_mitigation']['description'] + "\n\n"
            
            user_content += "For each criterion:\n"
            user_content += "- Score (1-5)\n"
            user_content += "- 2-3 sentences explaining your reasoning\n"
            user_content += "- Specific evidence from the content\n"
            user_content += "- What would make it more valuable for engineers\n\n"
            
            user_content += "Your evaluation should be rigorous - as if an engineer's career depends on this resource.\n\n"
            
            user_content += 'Format your response as a JSON object with this structure:\n'
            user_content += '```json\n'
            user_content += '{\n'
            user_content += '  "scores": {\n'
            user_content += '    "technical_accuracy": {\n'
            user_content += '      "score": 4,\n'
            user_content += '      "reasoning": "The content provides accurate information about engineering concepts.",\n'
            user_content += '      "evidence": "For example, the article correctly explains technical requirements.",\n'
            user_content += '      "improvement": "Could be improved by including more recent technical standards."\n'
            user_content += '    },\n'
            user_content += '    "growth_actionability": {\n'
            user_content += '      "score": 3,\n'
            user_content += '      "reasoning": "The content offers some actionable advice.",\n'
            user_content += '      "evidence": "It provides specific steps for career development.",\n'
            user_content += '      "improvement": "Could include more concrete examples of implementation."\n'
            user_content += '    },\n'
            user_content += '    "evidence_based": {\n'
            user_content += '      "score": 5,\n'
            user_content += '      "reasoning": "The content is well-supported by evidence.",\n'
            user_content += '      "evidence": "It cites multiple research studies and industry reports.",\n'
            user_content += '      "improvement": "No significant improvements needed in this area."\n'
            user_content += '    },\n'
            user_content += '    "technical_depth": {\n'
            user_content += '      "score": 2,\n'
            user_content += '      "reasoning": "The content lacks sufficient depth for senior engineers.",\n'
            user_content += '      "evidence": "Concepts are explained at a surface level only.",\n'
            user_content += '      "improvement": "Should include more complex technical scenarios."\n'
            user_content += '    },\n'
            user_content += '    "bias_mitigation": {\n'
            user_content += '      "score": 4,\n'
            user_content += '      "reasoning": "The content generally avoids biased perspectives.",\n'
            user_content += '      "evidence": "Uses inclusive language and diverse examples.",\n'
            user_content += '      "improvement": "Could address systemic barriers more directly."\n'
            user_content += '    }\n'
            user_content += '  },\n'
            user_content += '  "overall_score": 3.7,\n'
            user_content += '  "summary": "This content provides solid technical guidance on engineering career development.",\n'
            user_content += '  "key_value_points": [\n'
            user_content += '    "Offers clear metrics for measuring technical growth",\n'
            user_content += '    "Provides actionable feedback templates"\n'
            user_content += '  ],\n'
            user_content += '  "key_limitations": [\n'
            user_content += '    "Lacks specific examples for different engineering levels",\n'
            user_content += '    "Could provide more data-driven approaches"\n'
            user_content += '  ]\n'
            user_content += '}\n'
            user_content += '```'

            evaluation_prompts = [
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ]

            # Get evaluation from GPT-4-turbo
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=evaluation_prompts,
                temperature=0.2,  # Lower temperature for more consistent evaluations
                response_format={"type": "json_object"}
            )

            # Parse the evaluation
            evaluation = json.loads(response.choices[0].message.content)
            
            # Calculate weighted average score if not provided
            if "overall_score" not in evaluation:
                weighted_score = sum(
                    evaluation["scores"][criterion]["score"] * criteria["weight"]
                    for criterion, criteria in evaluation_criteria.items()
                )
                evaluation["overall_score"] = weighted_score

            # Add evaluated content to results
            results.append({
                "url": item["url"],
                "title": item["title"],
                "text": item["text"],
                "full_text": item.get("full_text", item["text"]),  # Preserve full text if available
                "source": item.get("source", "web"),
                "evaluation": {
                    "score": evaluation["overall_score"],
                    "tags": [k for k, v in evaluation["scores"].items() if v["score"] >= 4],
                    "summary": evaluation["summary"],
                    "reasoning": ", ".join(evaluation.get("key_value_points", [""])) if evaluation.get("key_value_points") else ""
                }
            })

            logger.info(f"Evaluated: {item['title'][:50]}... Score: {evaluation['overall_score']:.2f}")

        except Exception as e:
            logger.error(f"Error evaluating content: {str(e)}")
            results.append({
                "url": item["url"],
                "title": item["title"],
                "text": item["text"],
                "full_text": item.get("full_text", item["text"]),  # Preserve full text if available
                "source": item.get("source", "web"),
                "evaluation": {
                    "score": 1,
                    "tags": ["error"],
                    "summary": "Evaluation failed",
                    "reasoning": f"Error: {str(e)}"
                }
            })
    
    return results


def calculate_query_metrics(query: str, results: List[Dict]) -> QueryMetrics:
    """Calculate metrics for a query's results."""
    scores = [doc["evaluation"]["score"] for doc in results]
    high_quality = [doc for doc in results if doc["evaluation"]["score"] >= 4]
    domains = {urlparse(doc["url"]).netloc for doc in results}
    
    return QueryMetrics(
        query=query,
        avg_score=mean(scores) if scores else 0,
        high_quality_count=len(high_quality),
        source_domains=domains,
        total_results=len(results)
    ) 