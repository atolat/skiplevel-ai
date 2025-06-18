#!/usr/bin/env python3
"""Demonstration of intelligent web search capabilities in the engineering manager agent."""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agent_factory.config import load_config
from agent_factory.agent import create_agent

def main():
    """Demonstrate web search capabilities with Sam - Senior Engineering Manager."""
    
    print("🏭 Agent Factory - Web Search Demo")
    print("=" * 50)
    print("Demonstrating Sam's intelligent research capabilities")
    print("Sam can now research current industry best practices to provide evidence-based recommendations!")
    print()
    
    # Load and create the engineering manager agent
    try:
        config = load_config("configs/engineering_manager_sam.yaml")
        sam = create_agent(config)
        print(f"✅ {sam.config.name} loaded successfully")
        print(f"🧠 Using {sam.llm.model_name} with web search capabilities")
        print()
    except Exception as e:
        print(f"❌ Error loading agent: {e}")
        return
    
    # Demonstration scenarios
    scenarios = [
        {
            "title": "Performance Review Research",
            "question": "Research the latest best practices for conducting performance reviews for senior engineers in 2024"
        },
        {
            "title": "Team Scaling Insights", 
            "question": "What are the current industry trends in engineering team scaling? Research and provide recommendations."
        },
        {
            "title": "1:1 Meeting Best Practices",
            "question": "Research effective 1:1 meeting frameworks for engineering managers and share insights"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"📋 Scenario {i}: {scenario['title']}")
        print("-" * 40)
        print(f"Question: {scenario['question']}")
        print()
        
        try:
            # Get Sam's research-driven response
            response = sam.chat(scenario['question'])
            
            # Display response with formatting
            print("Sam's Research-Driven Response:")
            print("=" * 40)
            
            # Show if web search was used
            if "TOOL: web_search" in response:
                print("🔍 [Web search automatically triggered]")
                print()
            
            # Display the response (truncated for demo)
            if len(response) > 800:
                print(response[:800] + "...")
                print("\n[Response truncated for demo - full response would continue with detailed recommendations and sources]")
            else:
                print(response)
            
            print("\n" + "="*60 + "\n")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
    
    print("🎯 Key Features Demonstrated:")
    print("• Automatic research trigger when discussing management topics")
    print("• Intelligent search query generation using GPT-4-turbo")
    print("• Synthesis of findings from authoritative engineering sources")
    print("• Evidence-based recommendations with proper citations")
    print("• Integration with 8+ years of management experience")
    print()
    print("💡 Try chatting with Sam about any engineering management topic!")
    print("   He'll automatically research current best practices to give you the most up-to-date advice.")

if __name__ == "__main__":
    main() 