"""Content analysis functions for high-quality content."""
import json
import os
from typing import List, Dict
import openai


def analyze_high_quality_content(high_quality_results: List[Dict]) -> Dict:
    """Analyze high-quality content to identify patterns and successful elements."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Build content analysis string using text if available, summary if not
    content_items = []
    for doc in high_quality_results:
        title = doc.get('title', 'Untitled')
        
        # Use text field if available, otherwise use summary from evaluation
        if 'text' in doc:
            content = doc['text'][:1000]  # Limit to first 1000 chars
        else:
            # For web evaluation results that don't have text field
            eval_data = doc.get('evaluation', {})
            raw_eval = doc.get('raw_evaluation', {})
            
            # Build content from available fields
            content_parts = []
            if eval_data.get('summary'):
                content_parts.append(f"Summary: {eval_data['summary']}")
            
            if raw_eval.get('key_terms'):
                content_parts.append(f"Key terms: {', '.join(raw_eval['key_terms'])}")
                
            if eval_data.get('reasoning'):
                content_parts.append(f"Key points: {eval_data['reasoning']}")
                
            if raw_eval.get('scores'):
                scores_text = "; ".join([f"{k}: {v.get('score', 'N/A')}" for k, v in raw_eval['scores'].items()])
                content_parts.append(f"Scores: {scores_text}")
                
            content = "\n".join(content_parts)
            
        content_items.append(f"Title: {title}\nContent: {content}")
    
    content_analysis = "\n\n".join(content_items)
    
    prompt = f"""
Analyze the following high-quality content to identify patterns and successful elements:

{content_analysis}

Identify and return a JSON object with:
1. common_themes: List of main themes/topics
2. source_types: Types of sources that produced good content
3. content_structure: Common elements in the content structure
4. key_terminology: Important terms and concepts
5. content_depth: Level of detail and depth
"""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    
    return json.loads(response.choices[0].message.content) 