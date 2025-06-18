#!/usr/bin/env python3
"""
Simple FastAPI server to expose agent_factory via HTTP API
This allows the Next.js app to communicate with your Python agents
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import os
import sys
from typing import Optional

# Add the current directory to Python path to import agent_factory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agent_factory.agent import BaseAgent
    from agent_factory.config import load_config  # Use load_config instead of AgentConfig.from_yaml
except ImportError as e:
    print(f"Warning: Could not import agent_factory: {e}")
    print("Make sure you're running this from the skip-level-ai directory")
    BaseAgent = None
    load_config = None

# Global agent instance
emreq_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the Emreq agent on startup"""
    global emreq_agent
    
    print("🔄 Initializing Emreq agent...")
    
    if BaseAgent is None or load_config is None:
        print("⚠️  agent_factory not available, API will return mock responses")
    else:
        try:
            # Load the Emreq agent configuration using the correct function
            config_path = "configs/engineering_manager_emreq.yaml"
            if os.path.exists(config_path):
                config = load_config(config_path)  # Use load_config function
                if config:
                    emreq_agent = BaseAgent(config)
                    print(f"✅ Loaded Emreq agent from {config_path}")
                else:
                    print(f"❌ Failed to load config from {config_path}")
            else:
                print(f"⚠️  Config file not found at {config_path}")
        except Exception as e:
            print(f"❌ Error loading agent: {e}")
            import traceback
            traceback.print_exc()
    
    yield  # Server runs here
    
    print("🔄 Shutting down...")

app = FastAPI(title="Agent Factory API", version="1.0.0", lifespan=lifespan)

# Enable CORS for Next.js app
allowed_origins = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000",
    "https://skiplevel-ai.vercel.app",  # Add Vercel production domain
]

# Add production origins if available
frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

# Add Railway preview URLs
railway_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
if railway_url:
    allowed_origins.extend([
        f"https://{railway_url}",
        f"http://{railway_url}"
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"
    agent_name: str = "engineering_manager_emreq"
    user_context: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    agent_name: str
    timestamp: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "Agent Factory API is running",
        "agent_loaded": emreq_agent is not None,
        "timestamp": "2024-06-18T10:00:00Z"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "agent_factory_available": BaseAgent is not None,
        "emreq_agent_loaded": emreq_agent is not None,
        "version": "1.0.0"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint that communicates with the agent"""
    
    if emreq_agent is None:
        # Fallback response if agent is not loaded
        return ChatResponse(
            response=f"I received your message: '{request.message}'\n\nHowever, I'm currently running in fallback mode. The full Emreq agent is not connected yet.\n\nTo enable full functionality, make sure:\n• agent_factory is properly installed\n• engineering_manager_emreq.yaml config exists\n• All dependencies are available",
            agent_name=request.agent_name,
            timestamp="2024-06-18T10:00:00Z"
        )
    
    try:
        # Inject user profile data into the agent if available
        if request.user_context and request.user_context.get('profile'):
            profile = request.user_context['profile']
            if profile.get('profile_completed'):
                print(f"Injecting profile data for user: {profile.get('name', 'Unknown')}")
                # Use the agent's built-in profile injection method
                emreq_agent._inject_profile_data(profile)
                
                # Also store the profile for context generation
                emreq_agent.user_profile = profile
                print(f"Profile injected successfully. Name: {profile.get('name')}, Role: {profile.get('title')}")
        
        # Use the real agent to process the message
        response = emreq_agent.chat(request.message)  # This should be sync, not async
        
        return ChatResponse(
            response=response,
            agent_name=request.agent_name,
            timestamp="2024-06-18T10:00:00Z"
        )
        
    except Exception as e:
        print(f"Error processing chat request: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing request: {str(e)}"
        )

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming endpoint that yields response chunks"""
    def generate():
        try:
            print(f"Starting stream for message: {request.message}")
            if request.user_context:
                print(f"User context: {request.user_context.get('email', 'anonymous')}")
                if request.user_context.get('profile'):
                    profile = request.user_context['profile']
                    print(f"Profile: {profile.get('name', 'N/A')} - {profile.get('title', 'N/A')}")
                    print(f"Profile completed: {profile.get('profile_completed', 'N/A')}")
                    print(f"Full profile keys: {list(profile.keys()) if profile else 'None'}")
                else:
                    print("No profile data in user context")
            
            if emreq_agent is None:
                response = "I'm currently in fallback mode. Please check agent configuration."
                print(f"Fallback response: {response}")
                yield response
                return
            
            # Inject user profile data into the agent if available
            if request.user_context and request.user_context.get('profile'):
                profile = request.user_context['profile']
                if profile.get('profile_completed'):
                    print(f"Injecting profile data for user: {profile.get('name', 'Unknown')}")
                    # Use the agent's built-in profile injection method
                    emreq_agent._inject_profile_data(profile)
                    
                    # Also store the profile for context generation
                    emreq_agent.user_profile = profile
                    print(f"Profile injected successfully. Name: {profile.get('name')}, Role: {profile.get('title')}")
            
            # If agent supports streaming
            if hasattr(emreq_agent, 'chat_stream'):
                print("Using agent chat_stream method")
                for chunk in emreq_agent.chat_stream(request.message):
                    print(f"Yielding chunk: {chunk[:50]}...")
                    yield chunk
            else:
                # Fallback: simulate streaming by yielding full response
                print("Using fallback word-by-word streaming")
                response = emreq_agent.chat(request.message)
                print(f"Full response length: {len(response)} chars")
                
                # Split into words and yield gradually for better UX
                words = response.split(' ')
                for i, word in enumerate(words):
                    chunk = word + (' ' if i < len(words) - 1 else '')
                    print(f"Yielding word {i+1}/{len(words)}: {word}")
                    yield chunk
                    
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"Stream error: {error_msg}")
            yield error_msg
    
    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/agents")
async def list_agents():
    """List available agents"""
    return {
        "available_agents": ["engineering_manager_emreq"],
        "loaded_agents": ["engineering_manager_emreq"] if emreq_agent else []
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    is_production = os.environ.get("RAILWAY_ENVIRONMENT") is not None
    
    if is_production:
        print("🚀 Starting Agent Factory API server in PRODUCTION mode...")
        print(f"📡 Server will run on port: {port}")
        print("🔗 Production deployment ready!")
    else:
        print("🚀 Starting Agent Factory API server in DEVELOPMENT mode...")
        print("📡 This will expose your agent_factory via HTTP API")
        print(f"🔗 Next.js app can connect to: http://localhost:{port}")
    
    uvicorn.run(
        "api_server:app", 
        host="0.0.0.0", 
        port=port,
        reload=not is_production  # Disable reload in production
    ) 