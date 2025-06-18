#!/usr/bin/env python3
"""Test script to verify profile integration works."""

import os
import sys
from agent_factory.supabase_client import SupabaseProfileClient
from agent_factory.config import load_config
from agent_factory.agent import BaseAgent

def test_profile_integration():
    """Test loading profile data and creating personalized agent."""
    
    # Test 1: Check if Supabase client can be initialized
    try:
        client = SupabaseProfileClient()
        print("✅ Supabase client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return False
    
    # Test 2: Test profile formatting with mock data
    mock_profile = {
        "id": "test-user-123",
        "name": "John Doe",
        "title": "Software Engineer",
        "level": "Senior",
        "specialization": "Backend Development",
        "years_experience": 5,
        "years_at_company": 2,
        "team": "Large (10+ people)",
        "tech_skills": ["Python", "JavaScript", "Docker"],
        "current_projects": ["API Migration", "Performance Optimization"],
        "career_goals": ["Tech Lead", "System Architecture"],
        "biggest_challenges": ["Team coordination", "Technical debt"],
        "strengths": ["Problem solving", "Mentoring"],
        "learning_goals": ["Kubernetes", "System Design"],
        "communication_style": "Direct",
        "feedback_frequency": "Weekly",
        "meeting_style": "Structured",
        "email": "john@company.com"
    }
    
    try:
        formatted_profile = client.format_profile_for_agent(mock_profile)
        print("✅ Profile formatting works")
        print(f"   Name: {formatted_profile.get('name')}")
        print(f"   Role: {formatted_profile.get('title')}")
        print(f"   Experience: {formatted_profile.get('years_experience')} years")
    except Exception as e:
        print(f"❌ Profile formatting failed: {e}")
        return False
    
    # Test 3: Test personalized context generation
    try:
        context = client.generate_personalized_context(formatted_profile)
        print("✅ Personalized context generation works")
        print(f"   Context preview: {context[:100]}...")
    except Exception as e:
        print(f"❌ Context generation failed: {e}")
        return False
    
    # Test 4: Test agent creation with profile
    try:
        config = load_config("configs/engineering_manager_emreq.yaml")
        if config:
            agent = BaseAgent(config, user_profile=formatted_profile)
            print("✅ Agent creation with profile works")
            
            # Test personalized context
            personalized_context = agent.get_personalized_context()
            print(f"   Agent context preview: {personalized_context[:100]}...")
        else:
            print("❌ Could not load agent config")
            return False
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False
    
    # Test 5: Test welcome message generation
    try:
        from app import generate_personalized_welcome
        welcome_msg = generate_personalized_welcome(formatted_profile)
        print("✅ Personalized welcome message generation works")
        print(f"   Welcome preview: {welcome_msg[:100]}...")
    except Exception as e:
        print(f"❌ Welcome message generation failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Profile integration is working correctly.")
    return True

if __name__ == "__main__":
    print("Testing Profile Integration...\n")
    
    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        print("⚠️  Warning: SUPABASE_URL and SUPABASE_ANON_KEY environment variables not set")
        print("   Some tests may fail, but others should still work\n")
    
    success = test_profile_integration()
    sys.exit(0 if success else 1) 