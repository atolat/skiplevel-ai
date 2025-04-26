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

        # Send initial "thinking" message
        thinking = await cl.Message(content="🔎 Analyzing your reflection...").send()

        # Create initial DAG state
        initial_state = AgentState(
            messages=[HumanMessage(content=reflection_text)],
            reflection_text=reflection_text,
            evaluation_result=None,
            growth_advice=None
        )

        final_state = None

        async for chunk in compiled_dag.astream(initial_state):
            final_state = chunk

        if final_state and isinstance(final_state, dict):
            end_state = final_state.get("__end__", {})
            evaluation = end_state.get("evaluation_result")

            if evaluation:
                print("✅ Evaluation found in final state")
                print(f"📝 Evaluation content: {evaluation[:100]}...")
                
                # Update the thinking message
                thinking.content = "✅ Reflection evaluated! Here's your feedback:"
                await thinking.update()
                
                # Send formatted evaluation
                await cl.Message(content=evaluation, author="Skiplevel AI").send()
            else:
                thinking.content = "❌ No evaluation was produced. Please try again."
                await thinking.update()
        else:
            thinking.content = "❌ No final evaluation was produced. Please try again."
            await thinking.update()

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        await cl.Message(
            content=f"⚠️ An unexpected error occurred:\n\n{str(e)}"
        ).send()


def format_evaluation(evaluation: dict) -> str:
    """Format the evaluation dictionary into Markdown."""
    if not evaluation:
        return "⚠️ No evaluation available."

    summary = evaluation.get("summary", "No summary provided.")
    strengths = evaluation.get("strengths", [])
    improvements = evaluation.get("areas_for_improvement", [])

    return f"""
# 📈 Overall Assessment
{summary}

# 💪 Key Strengths
{format_list(strengths)}

# 🚀 Areas for Improvement
{format_list(improvements)}
"""


def format_list(items):
    """Format a list into Markdown bullet points."""
    if not items:
        return "- None"
    return "\n".join([f"- {item}" for item in items])
