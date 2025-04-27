# File: skiplevel/chainlit_app.py
#!/usr/bin/env python3

import chainlit as cl
import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from graphs.main_graph import compiled_dag
from models.types import AgentState

load_dotenv()
print("Environment loaded successfully")


@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content="👋 Welcome to Skiplevel! Please submit your reflection to begin."
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    try:
        reflection_text = message.content
        preview = reflection_text[:100] + "..." if len(reflection_text) > 100 else reflection_text
        print(f"📥 Received reflection: {preview}")

        thinking = await cl.Message(content="🔎 Analyzing your reflection...").send()

        initial_state = AgentState(
            messages=[HumanMessage(content=reflection_text)],
            reflection_text=reflection_text,
            evaluation_result=None,
            growth_advice=None,
            next=None
        )

        final_state = None
        evaluation = None

        async for chunk in compiled_dag.astream(initial_state):
            final_state = chunk
            print(f"📦 State update: {list(chunk.keys())}")
            
            # Check for evaluation in reflection_evaluator field
            if "reflection_evaluator" in chunk and chunk["reflection_evaluator"]:
                evaluation = chunk["reflection_evaluator"]
                print("✅ Found evaluation in reflection_evaluator")

            # Log supervisor decisions
            if "next" in chunk:
                print(f"🧠 Supervisor decision: {chunk['next']}")

        if evaluation and "evaluation_result" in evaluation:
            print("✅ Evaluation ready!")
            
            thinking.content = "✅ Reflection evaluated! Here's your feedback:"
            await thinking.update()

            await cl.Message(content=evaluation["evaluation_result"], author="Skiplevel AI").send()
        else:
            print("❌ No evaluation found!")
            thinking.content = "❌ No evaluation was produced. Please try again."
            await thinking.update()

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        await cl.Message(
            content=f"⚠️ An unexpected error occurred:\n\n{str(e)}"
        ).send()


def format_evaluation(evaluation: dict) -> str:
    """Format the evaluation dictionary into a readable string."""
    if not evaluation:
        return "No evaluation available."
    
    try:
        # If evaluation is already a string, return it
        if isinstance(evaluation, str):
            return evaluation
            
        # If evaluation is a dictionary, format it
        if isinstance(evaluation, dict):
            sections = []
            if "overall_assessment" in evaluation:
                sections.append(f"### Overall Assessment\n\n{evaluation['overall_assessment']}")
            if "key_strengths" in evaluation:
                sections.append(f"### Key Strengths\n\n{evaluation['key_strengths']}")
            if "areas_for_improvement" in evaluation:
                sections.append(f"### Areas for Improvement\n\n{evaluation['areas_for_improvement']}")
            if "recommendations" in evaluation:
                sections.append(f"### Recommendations\n\n{evaluation['recommendations']}")
            return "\n\n".join(sections)
            
        return str(evaluation)
    except Exception as e:
        print(f"⚠️ Error formatting evaluation: {str(e)}")
        return str(evaluation)
