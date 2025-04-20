import chainlit as cl
from graph.agent import create_agent
import json
import os
from dotenv import load_dotenv
from load_data import load_data
from tools.rubric_retriever import set_qdrant_client

# Load environment variables
load_dotenv()

# Verify LangSmith API key is set
if not os.getenv("LANGCHAIN_API_KEY"):
    print("Warning: LANGCHAIN_API_KEY not set. Tracing will be disabled.")

# Load synthetic data into Qdrant
qdrant_client = load_data()

# Set the Qdrant client for the RubricRetrieverTool
set_qdrant_client(qdrant_client)

# Initialize the agent
agent = create_agent()

@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    await cl.Message(
        content="Welcome to SkipLevel! Share your reflection, and I'll help evaluate your growth and provide advice.",
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """Process user messages and return evaluation results."""
    # Create initial state
    state = {"reflection": message.content}
    
    # Run the agent
    result = agent.invoke(state)
    
    # Format the response
    evaluation = json.loads(result["evaluation"])
    advice = json.loads(result["advice"])
    
    # Create markdown response
    response = f"""## Evaluation Results

### Level Estimate: {evaluation['level']}
**Score:** {evaluation['score']}/100

### Reasoning
{evaluation['reasoning']}

### Key Strengths
{chr(10).join(f"- {s}" for s in evaluation['strengths'])}

### Areas for Improvement
{chr(10).join(f"- {a}" for a in evaluation['areas_for_improvement'])}

## Growth Advice

### Target Level: {advice['next_level']}
**Timeline:** {advice['timeline']}

### Focus Areas
{chr(10).join(f"- {area}" for area in advice['key_focus_areas'])}

### Action Items
{chr(10).join(f"- {item}" for item in advice['action_items'])}

### Recommended Resources
{chr(10).join(f"- {resource}" for resource in advice['resources'])}
"""
    
    # Send the response
    await cl.Message(content=response).send()
    
    # Show retrieved rubrics
    rubrics_text = "### Retrieved Rubrics\n\n"
    for i, rubric in enumerate(result["rubrics"], 1):
        rubrics_text += f"**Chunk {i}** (Score: {rubric['score']:.2f})\n{rubric['text']}\n\n"
    
    await cl.Message(content=rubrics_text).send() 