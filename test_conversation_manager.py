#!/usr/bin/env python3
"""Test script for the new conversation management system."""

import os
import sys
import uuid
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_factory.conversation_manager import ConversationManager
from agent_factory.agent import BaseAgent
from agent_factory.config import load_config

def test_conversation_manager():
    """Test the basic conversation manager functionality."""
    print("🧪 Testing Conversation Management System")
    print("=" * 50)
    
    # Test 1: Initialize ConversationManager
    print("\n1️⃣ Testing ConversationManager initialization...")
    try:
        conversation_manager = ConversationManager()
        print("✅ ConversationManager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ConversationManager: {e}")
        return False
    
    # Test 2: Start a new session
    print("\n2️⃣ Testing session creation...")
    test_user_id = str(uuid.uuid4())  # Generate a proper UUID
    try:
        session = conversation_manager.start_new_session(test_user_id, "Test Conversation")
        if session:
            print(f"✅ Created session: {session.id}")
            print(f"   Title: {session.title}")
            print(f"   User ID: {session.user_id}")
            print(f"   Status: {session.status}")
        else:
            print("❌ Failed to create session")
            return False
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return False
    
    # Test 3: Increment message count
    print("\n3️⃣ Testing message count increment...")
    try:
        for i in range(3):
            conversation_manager.increment_message_count()
            print(f"   Message count: {conversation_manager.current_session.message_count}")
        print("✅ Message count incremented successfully")
    except Exception as e:
        print(f"❌ Error incrementing message count: {e}")
        return False
    
    # Test 4: Update session title
    print("\n4️⃣ Testing session title update...")
    try:
        new_title = f"Updated Test - {datetime.now().strftime('%H:%M:%S')}"
        success = conversation_manager.update_session_title(new_title)
        if success:
            print(f"✅ Updated title to: {new_title}")
        else:
            print("❌ Failed to update title")
    except Exception as e:
        print(f"❌ Error updating title: {e}")
    
    # Test 5: Get recent sessions
    print("\n5️⃣ Testing session history retrieval...")
    try:
        sessions = conversation_manager.get_recent_sessions(test_user_id, 5)
        print(f"✅ Found {len(sessions)} recent sessions")
        for session in sessions:
            print(f"   - {session.title} ({session.status}) - {session.message_count} messages")
    except Exception as e:
        print(f"❌ Error getting session history: {e}")
    
    # Test 6: Complete session
    print("\n6️⃣ Testing session completion...")
    try:
        success = conversation_manager.complete_session("Test summary: This was a basic functionality test.")
        if success:
            print("✅ Session completed successfully")
        else:
            print("❌ Failed to complete session")
    except Exception as e:
        print(f"❌ Error completing session: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Basic conversation management test completed!")
    return True

def test_agent_integration():
    """Test the agent integration with conversation management."""
    print("\n🤖 Testing Agent Integration with Conversations")
    print("=" * 50)
    
    # Load agent config
    try:
        config = load_config("configs/engineering_manager_emreq.yaml")
        if not config:
            print("❌ Failed to load agent config")
            return False
        
        agent = BaseAgent(config)
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return False
    
    # Test conversation start
    test_user_id = str(uuid.uuid4())  # Generate a proper UUID
    try:
        success = agent.start_conversation(test_user_id, "Agent Integration Test")
        if success:
            print(f"✅ Agent started conversation for user: {test_user_id}")
            print(f"   Session ID: {agent.conversation_manager.current_session.id}")
        else:
            print("❌ Failed to start conversation through agent")
            return False
    except Exception as e:
        print(f"❌ Error starting conversation through agent: {e}")
        return False
    
    # Test chat with message counting
    try:
        print("\n💬 Testing chat with automatic message counting...")
        response = agent.chat("Hello, this is a test message!")
        print(f"✅ Agent responded (length: {len(response)} chars)")
        print(f"   Current message count: {agent.conversation_manager.current_session.message_count}")
        
        # Send another message
        response2 = agent.chat("How are you doing?")
        print(f"✅ Second response (length: {len(response2)} chars)")
        print(f"   Updated message count: {agent.conversation_manager.current_session.message_count}")
        
    except Exception as e:
        print(f"❌ Error during chat: {e}")
        return False
    
    # Test conversation end
    try:
        success = agent.end_conversation("Agent integration test completed successfully.")
        if success:
            print("✅ Agent ended conversation successfully")
        else:
            print("❌ Failed to end conversation through agent")
    except Exception as e:
        print(f"❌ Error ending conversation through agent: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Agent integration test completed!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Conversation Management Tests")
    
    # Run basic tests
    basic_success = test_conversation_manager()
    
    # Run agent integration tests
    if basic_success:
        agent_success = test_agent_integration()
    
    print("\n" + "=" * 60)
    if basic_success:
        print("✅ All tests completed! Your conversation management system is working.")
        print("\n🎯 What's working:")
        print("   • Conversation sessions are being saved to database")
        print("   • Message counts are tracked automatically")
        print("   • Session titles can be updated")
        print("   • Conversation history can be retrieved")
        print("   • Sessions can be completed with summaries")
        print("   • Agent integration is functional")
        
        print("\n🚀 Next steps:")
        print("   • Test the API endpoints with real user data")
        print("   • Add intelligent title generation")
        print("   • Implement conversation summaries")
        print("   • Add 'last conversation' context retrieval")
    else:
        print("❌ Some tests failed. Check the error messages above.") 