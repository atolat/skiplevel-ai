#!/usr/bin/env python3
"""Test script to debug agent creation."""

from agent_factory.config import load_config
from agent_factory.agent import create_agent

print("Loading config...")
config = load_config("configs/math_helper.yaml")

if config:
    print(f"✓ Loaded agent: {config.name}")
    print(f"Tools: {config.tools}")
    print(f"Tools type: {type(config.tools)}")
    
    print("\nCreating agent...")
    try:
        agent = create_agent(config)
        print(f"✓ Created agent: {agent}")
        print(f"Available tools: {list(agent.available_tools.keys())}")
        
        print("\nTesting chat...")
        response = agent.chat("What is 2 + 2?")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("✗ Failed to load config") 