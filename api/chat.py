#!/usr/bin/env python3
"""
Vercel Python function for Emreq AI Engineering Manager
Handles streaming chat responses using agent_factory
"""

import json
import os
import sys
from typing import Optional, Dict, Any, Iterator
from http.server import BaseHTTPRequestHandler
import traceback

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

try:
    from agent_factory.agent import BaseAgent
    from agent_factory.config import load_config
    print("✅ Successfully imported agent_factory")
except ImportError as e:
    print(f"❌ Failed to import agent_factory: {e}")
    BaseAgent = None
    load_config = None

# Global agent instance (will be initialized on first request)
emreq_agent = None

def initialize_agent():
    """Initialize the Emreq agent if not already loaded"""
    global emreq_agent
    
    if emreq_agent is not None:
        return emreq_agent
    
    print("🔄 Initializing Emreq agent...")
    
    if BaseAgent is None or load_config is None:
        print("⚠️ agent_factory not available")
        return None
    
    try:
        # Load the Emreq agent configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "configs", "engineering_manager_emreq.yaml")
        print(f"Loading config from: {config_path}")
        
        if os.path.exists(config_path):
            config = load_config(config_path)
            if config:
                emreq_agent = BaseAgent(config)
                print(f"✅ Loaded Emreq agent successfully")
                return emreq_agent
            else:
                print(f"❌ Failed to load config from {config_path}")
        else:
            print(f"⚠️ Config file not found at {config_path}")
    except Exception as e:
        print(f"❌ Error loading agent: {e}")
        traceback.print_exc()
    
    return None

def generate_streaming_response(message: str, user_context: Optional[Dict[str, Any]] = None) -> Iterator[str]:
    """Generate streaming response from the agent"""
    try:
        agent = initialize_agent()
        
        if agent is None:
            yield "I'm currently in fallback mode. The Emreq agent is not available."
            return
        
        # Inject user profile data if available
        if user_context and user_context.get('profile'):
            profile = user_context['profile']
            if profile.get('profile_completed'):
                print(f"Injecting profile data for user: {profile.get('name', 'Unknown')}")
                
                # Use the agent's built-in profile injection method if it exists
                if hasattr(agent, '_inject_profile_data'):
                    agent._inject_profile_data(profile)
                
                # Store the profile for context generation
                agent.user_profile = profile
                print(f"Profile injected successfully. Name: {profile.get('name')}, Role: {profile.get('title')}")
        
        # Generate response using the agent
        if hasattr(agent, 'chat_stream'):
            print("Using agent chat_stream method")
            for chunk in agent.chat_stream(message):
                if chunk.strip():
                    yield chunk
        else:
            print("Using fallback word-by-word streaming")
            response = agent.chat(message)
            
            # Split into words and yield gradually for better UX
            words = response.split(' ')
            for i, word in enumerate(words):
                chunk = word + (' ' if i < len(words) - 1 else '')
                yield chunk
                
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"Stream error: {error_msg}")
        yield error_msg

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for chat streaming"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Parse JSON request
            try:
                request_data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                self.send_error(400, f"Invalid JSON: {e}")
                return
            
            message = request_data.get('message', '')
            user_context = request_data.get('user_context')
            
            print(f"Processing message: {message}")
            if user_context:
                print(f"User context: {user_context.get('email', 'anonymous')}")
                if user_context.get('profile'):
                    profile = user_context['profile']
                    print(f"Profile: {profile.get('name', 'N/A')} - {profile.get('title', 'N/A')}")
            
            # Set response headers for streaming
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            
            # Generate and stream response
            for chunk in generate_streaming_response(message, user_context):
                if chunk:
                    self.wfile.write(chunk.encode('utf-8'))
                    self.wfile.flush()
            
        except Exception as e:
            print(f"Error in handler: {e}")
            traceback.print_exc()
            try:
                self.send_error(500, f"Internal server error: {e}")
            except:
                pass
    
    def do_GET(self):
        """Handle GET requests for health check"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "Emreq agent running on Vercel",
            "agent_loaded": emreq_agent is not None,
            "version": "1.0.0"
        }
        
        self.wfile.write(json.dumps(response).encode('utf-8')) 