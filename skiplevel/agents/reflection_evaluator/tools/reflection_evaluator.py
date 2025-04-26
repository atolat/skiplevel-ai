#!/usr/bin/env python3

# TODO: Implement reflection evaluator tool

from typing import Dict, List
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

@tool
def reflection_evaluator(reflection: str, rubrics: List[Dict]) -> str:
    """
    Evaluates an engineer's reflection against role-specific rubrics.
    
    Args:
        reflection: The engineer's self-reflection text
        rubrics: List of rubric dictionaries containing evaluation criteria
        
    Returns:
        str: A JSON string containing evaluation results with fields:
            - summary: Overall assessment
            - strengths: Key strengths identified
            - areas_for_improvement: Areas needing development
    """
    print("\n🧠 ReflectionEvaluatorTool invoked")
    print(f"📝 Reflection: {reflection[:100]}...")
    print(f"📚 Received {len(rubrics)} rubric chunks")
    
    if not rubrics:
        print("⚠️ Warning: No rubric context provided")
        return json.dumps({
            "summary": "No rubric context provided.",
            "strengths": [],
            "areas_for_improvement": []
        })
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    print("✅ Initialized GPT-4")
    
    # Construct system prompt
    system_prompt = """You are a performance review AI. Given an engineer's reflection and a set of role-specific rubrics, evaluate their growth and impact.
    
Return a structured JSON with the following fields:
- summary: A concise overall assessment
- strengths: List of key strengths identified
- areas_for_improvement: List of areas needing development

Be specific and actionable in your feedback, grounding it in the provided rubrics."""
    
    # Format rubrics into context
    rubric_context = "\n".join([f"- {rubric.get('text', '')}" for rubric in rubrics])
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Engineer's Reflection:\n{reflection}\n\nRubric Context:\n{rubric_context}")
    ])
    
    try:
        # Format and invoke
        messages = prompt.format_messages(
            reflection=reflection,
            rubric_context=rubric_context
        )
        
        print("\n📤 Sending prompt to GPT-4...")
        print("System prompt:")
        print(system_prompt)
        print("\nUser prompt:")
        print(f"Engineer's Reflection:\n{reflection}\n")
        print("Rubric Context:")
        print(rubric_context)
        
        response = llm.invoke(messages)
        print("\n📥 Received response from GPT-4")
        print("Raw response:")
        print(response.content)
        
        # Try to parse as JSON to validate
        parsed_response = json.loads(response.content)
        print("\n✅ Successfully parsed JSON response")
        return response.content
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to parse JSON response: {str(e)}")
        print("Raw response that failed to parse:")
        print(response.content)
        return json.dumps({
            "error": f"Failed to parse JSON response: {str(e)}",
            "raw_response": response.content if 'response' in locals() else None
        })
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return json.dumps({
            "error": f"Unexpected error: {str(e)}",
            "raw_response": response.content if 'response' in locals() else None
        })
