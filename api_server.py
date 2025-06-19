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
import time
from datetime import datetime, timedelta
from typing import Optional, List

# Add the current directory to Python path to import agent_factory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agent_factory.agent import SimpleLangGraphAgent
    from agent_factory.config import load_config
    from agent_factory.tools import get_tool, web_search_tool
    from agent_factory.llm import get_llm
except ImportError as e:
    print(f"Warning: Could not import agent_factory: {e}")
    print("Make sure you're running this from the skip-level-ai directory")
    SimpleLangGraphAgent = None
    load_config = None
    get_tool = None
    web_search_tool = None
    get_llm = None

# Global agent instance
emreq_agent = None

# Conversation-specific agent cache - one agent per conversation
conversation_agents = {}

def get_conversation_agent(conversation_id: str, user_id: str, user_profile: Optional[dict] = None):
    """Get or create a conversation-specific agent instance.
    
    This implements the recommended LangGraph pattern of one agent per conversation.
    Each conversation gets its own thread_id and agent instance for proper memory isolation.
    """
    if conversation_id not in conversation_agents:
        # Create new agent for this conversation
        config_path = "configs/engineering_manager_emreq.yaml"
        config = load_config(config_path)
        
        # Create agent with conversation-specific thread_id
        conversation_agent = SimpleLangGraphAgent(config, user_profile)
        
        # Set the thread_id to the conversation_id for LangGraph memory
        conversation_agent.thread_id = conversation_id
        
        # Start conversation session
        conversation_agent.start_conversation(user_id, "Chat with Emreq")
        
        # Cache the agent
        conversation_agents[conversation_id] = conversation_agent
        print(f"✅ Created new agent for conversation: {conversation_id} (user: {user_id})")
    else:
        # Update user profile if provided
        if user_profile and hasattr(conversation_agents[conversation_id], 'user_profile'):
            conversation_agents[conversation_id].user_profile = user_profile
    
    return conversation_agents[conversation_id]

def clear_conversation_agent(conversation_id: str):
    """Clear cached agent for a conversation when it ends."""
    if conversation_id in conversation_agents:
        del conversation_agents[conversation_id]
        print(f"🗑️ Cleared agent cache for conversation: {conversation_id}")

def get_user_agent(user_id: str, user_profile: Optional[dict] = None):
    """Legacy function - now redirects to conversation-based approach.
    
    For backward compatibility, we create a default conversation per user.
    """
    # Use user_id as conversation_id for legacy support
    default_conversation_id = f"user-{user_id}-default"
    return get_conversation_agent(default_conversation_id, user_id, user_profile)

def clear_user_agent(user_id: str):
    """Legacy function - clear default conversation for user."""
    default_conversation_id = f"user-{user_id}-default"
    clear_conversation_agent(default_conversation_id)

def cleanup_stale_conversations(temp_agent, user_id: str, sessions: list) -> list:
    """Clean up stale conversations that claim to be active but aren't resumable.
    
    Args:
        temp_agent: Agent instance with conversation manager
        user_id: User ID
        sessions: List of conversation sessions
        
    Returns:
        List of sessions with corrected status
    """
    corrected_sessions = []
    stale_conversation_ids = []
    
    for session in sessions:
        actual_status = session.status
        
        # If the session claims to be "active", verify it's actually resumable
        if session.status == "active":
            # Check if there's actually a running agent for this conversation
            is_truly_active = session.id in conversation_agents
            
            # Also check if the conversation was created more than 24 hours ago without completion
            if session.created_at:
                time_since_creation = datetime.now(session.created_at.tzinfo) - session.created_at
                is_stale = time_since_creation > timedelta(hours=24)
                
                # If not truly active OR stale, mark for cleanup
                if not is_truly_active or is_stale:
                    actual_status = "completed"
                    stale_conversation_ids.append(session.id)
        
        # Create corrected session
        corrected_session = session
        corrected_session.status = actual_status
        corrected_sessions.append(corrected_session)
    
    # Optional: Update stale conversations in database (uncomment if desired)
    if stale_conversation_ids and hasattr(temp_agent, 'conversation_manager'):
        try:
            for conv_id in stale_conversation_ids:
                # Update status in database
                update_data = {
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "summary": "Conversation auto-completed due to inactivity."
                }
                temp_agent.conversation_manager.client.table("conversation_sessions").update(update_data).eq("id", conv_id).execute()
            
            print(f"🧹 Auto-completed {len(stale_conversation_ids)} stale conversations for user {user_id}")
        except Exception as e:
            print(f"⚠️ Warning: Could not update stale conversations in database: {e}")
    
    return corrected_sessions

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the Emreq agent on startup"""
    global emreq_agent
    
    print("🔄 Initializing Emreq agent...")
    
    if SimpleLangGraphAgent is None or load_config is None:
        print("⚠️  agent_factory not available, API will return mock responses")
    else:
        try:
            # Load the Emreq agent configuration using the correct function
            config_path = "configs/engineering_manager_emreq.yaml"
            if os.path.exists(config_path):
                config = load_config(config_path)
                if config:
                    emreq_agent = SimpleLangGraphAgent(config)
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
    "https://skiplevel-ai.vercel.app",  # Production domain
    "https://skiplevel-6qds3ok8p-arpans-projects-21a46514.vercel.app",  # Current preview deployment
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
    allow_origins=allowed_origins + ["*"],  # Allow all origins for now to test
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"
    conversation_id: Optional[str] = None  # New: conversation ID for proper memory isolation
    agent_name: str = "engineering_manager_emreq"
    user_context: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    agent_name: str
    timestamp: str
    conversation_id: Optional[str] = None
    tools_used: Optional[List[str]] = None
    tool_execution_info: Optional[List[dict]] = None

class ToolRequest(BaseModel):
    input: str
    user_context: Optional[dict] = None

class ToolResponse(BaseModel):
    tool_name: str
    result: str
    success: bool
    timestamp: str
    execution_time_ms: int
    error: Optional[str] = None

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
    # Quick health check - just return basic status
    return {
        "status": "healthy",
        "port": os.environ.get("PORT", "8001"),
        "environment": "production" if os.environ.get("RAILWAY_ENVIRONMENT") else "development"
    }

@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check with agent status"""
    return {
        "status": "healthy",
        "agent_factory_available": SimpleLangGraphAgent is not None,
        "emreq_agent_loaded": emreq_agent is not None,
        "version": "1.0.0",
        "port": os.environ.get("PORT", "8001"),
        "environment": "production" if os.environ.get("RAILWAY_ENVIRONMENT") else "development"
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
        # Get user-specific profile if available
        user_profile = None
        if request.user_context and request.user_context.get('profile'):
            profile = request.user_context['profile']
            if profile.get('profile_completed'):
                user_profile = profile
                print(f"Using profile for user: {profile.get('name', 'Unknown')}")
        
        # Determine conversation ID - create new one if not provided
        conversation_id = request.conversation_id
        if not conversation_id:
            # Generate a new conversation ID
            import uuid
            conversation_id = str(uuid.uuid4())
            print(f"🆕 Starting new conversation: {conversation_id}")
        
        # Get or create conversation-specific agent (implements LangGraph best practices)
        conversation_agent = get_conversation_agent(conversation_id, request.user_id, user_profile)
        
        # Use the conversation-specific agent to process the message
        response = conversation_agent.chat(request.message)
        
        # Get tool usage information
        tools_used = []
        tool_execution_info = []
        if hasattr(conversation_agent, 'get_last_tool_usage'):
            tool_usage = conversation_agent.get_last_tool_usage()
            for tool_info in tool_usage:
                tools_used.append(tool_info.get("name", "unknown"))
                tool_execution_info.append({
                    "name": tool_info.get("name", "unknown"),
                    "args": tool_info.get("args", {}),
                    "id": tool_info.get("id", "")
                })
        
        return ChatResponse(
            response=response,
            agent_name=request.agent_name,
            timestamp="2024-06-18T10:00:00Z",
            conversation_id=conversation_id,
            tools_used=tools_used if tools_used else None,
            tool_execution_info=tool_execution_info if tool_execution_info else None
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
            
            # Get user-specific profile if available
            user_profile = None
            if request.user_context and request.user_context.get('profile'):
                profile = request.user_context['profile']
                if profile.get('profile_completed'):
                    user_profile = profile
                    print(f"Using profile for user: {profile.get('name', 'Unknown')}")
            
            # Determine conversation ID - create new one if not provided
            conversation_id = request.conversation_id
            if not conversation_id:
                # Generate a new conversation ID
                import uuid
                conversation_id = str(uuid.uuid4())
                print(f"🆕 Starting new conversation: {conversation_id}")
            
            # Get or create conversation-specific agent (implements LangGraph best practices)
            conversation_agent = get_conversation_agent(conversation_id, request.user_id, user_profile)
            
            # If agent supports streaming
            if hasattr(conversation_agent, 'chat_stream'):
                print("Using agent chat_stream method")
                for chunk in conversation_agent.chat_stream(request.message):
                    print(f"Yielding chunk: {chunk[:50]}...")
                    yield chunk
            else:
                # Fallback: simulate streaming by yielding full response
                print("Using fallback word-by-word streaming")
                response = conversation_agent.chat(request.message)
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

@app.get("/api/conversations/history")
async def get_conversation_history(user_id: str, limit: int = 5):
    """Get conversation history for a user"""
    if emreq_agent is None:
        raise HTTPException(status_code=503, detail="Agent not available")
    
    try:
        # Create a temporary agent instance to access conversation manager
        config_path = "configs/engineering_manager_emreq.yaml"
        config = load_config(config_path)
        temp_agent = SimpleLangGraphAgent(config)
        
        # Check if the agent has a conversation manager
        if hasattr(temp_agent, 'conversation_manager') and temp_agent.conversation_manager:
            sessions = temp_agent.conversation_manager.get_recent_sessions(user_id, limit)
            
            # Clean up stale conversations and correct their status
            corrected_sessions = cleanup_stale_conversations(temp_agent, user_id, sessions)
            
            # Convert to dict for JSON response
            session_data = []
            for session in corrected_sessions:
                session_data.append({
                    "id": session.id,
                    "title": session.title,
                    "summary": session.summary,
                    "summary_format": "markdown" if session.summary and session.summary.startswith("# ") else "text",
                    "status": session.status,  # Now using the corrected status
                    "message_count": session.message_count,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None
                })
            
            return {"sessions": session_data}
        else:
            # Fallback for SimpleLangGraphAgent without conversation manager
            return {"sessions": [], "message": "Conversation history not available with current agent"}
        
    except Exception as e:
        print(f"Error fetching conversation history: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

@app.post("/api/conversations/complete")
async def complete_conversation(user_id: str, conversation_id: Optional[str] = None, summary: Optional[str] = None):
    """Complete a conversation session"""
    if emreq_agent is None:
        raise HTTPException(status_code=503, detail="Agent not available")
    
    try:
        # If no conversation_id provided, use legacy user-based approach
        if not conversation_id:
            conversation_id = f"user-{user_id}-default"
        
        # Get the conversation's agent if it exists
        if conversation_id in conversation_agents:
            conversation_agent = conversation_agents[conversation_id]
            success = conversation_agent.end_conversation(summary)
            
            # Clear the conversation's agent cache
            clear_conversation_agent(conversation_id)
            
            if success:
                return {"message": "Conversation completed successfully", "conversation_id": conversation_id}
            else:
                return {"message": "No active conversation to complete"}
        else:
            return {"message": f"No active conversation found: {conversation_id}"}
            
    except Exception as e:
        print(f"Error completing conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error completing conversation: {str(e)}")

# ========== TOOLS API ENDPOINTS ==========

@app.get("/api/tools")
async def list_tools():
    """List all available tools with their descriptions"""
    if get_tool is None:
        raise HTTPException(status_code=503, detail="Tools not available")
    
    available_tools = []
    tool_names = ["web_search", "datetime", "calculator", "file_reader", "one_on_one_scheduler"]
    
    for tool_name in tool_names:
        tool = get_tool(tool_name)
        if tool:
            available_tools.append({
                "name": tool.name,
                "description": tool.description
            })
    
    return {
        "tools": available_tools,
        "count": len(available_tools)
    }

@app.post("/api/tools/{tool_name}", response_model=ToolResponse)
async def execute_tool(tool_name: str, request: ToolRequest):
    """Execute a specific tool with input data"""
    if get_tool is None:
        raise HTTPException(status_code=503, detail="Tools not available")
    
    start_time = time.time()
    
    try:
        # Get the tool instance
        tool = get_tool(tool_name)
        if not tool:
            return ToolResponse(
                tool_name=tool_name,
                result="",
                success=False,
                timestamp="2024-06-18T10:00:00Z",
                execution_time_ms=0,
                error=f"Tool '{tool_name}' not found"
            )
        
        # Special handling for web_search tool (needs LLM)
        if tool_name == "web_search" and web_search_tool:
            # Use the web_search_tool directly
            tool = web_search_tool
        
        # Execute the tool using LangChain invoke method
        if hasattr(tool, 'invoke'):
            # New LangChain tool format
            if tool_name == "web_search":
                result = tool.invoke({"query": request.input})
            elif tool_name == "one_on_one_scheduler":
                result = tool.invoke({"request": request.input})
            elif tool_name in ["datetime", "calculator", "file_reader"]:
                # These tools have different parameter names, check the tool's args_schema
                if hasattr(tool, 'args_schema') and tool.args_schema:
                    field_names = list(tool.args_schema.model_fields.keys())
                    if field_names:
                        param_name = field_names[0]  # Use first parameter
                        result = tool.invoke({param_name: request.input})
                    else:
                        result = tool.invoke({"input": request.input})
                else:
                    result = tool.invoke({"input": request.input})
            else:
                result = tool.invoke({"input": request.input})
        elif hasattr(tool, 'execute'):
            # Legacy tool format
            result = tool.execute(request.input)
        else:
            result = f"Tool {tool_name} does not have a supported execution method"
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return ToolResponse(
            tool_name=tool_name,
            result=result,
            success=True,
            timestamp="2024-06-18T10:00:00Z",
            execution_time_ms=execution_time_ms
        )
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        return ToolResponse(
            tool_name=tool_name,
            result="",
            success=False,
            timestamp="2024-06-18T10:00:00Z",
            execution_time_ms=execution_time_ms,
            error=str(e)
        )

@app.post("/api/tools/web_search", response_model=ToolResponse)
async def web_search(request: ToolRequest):
    """Web search with AI synthesis - convenient endpoint"""
    return await execute_tool("web_search", request)

@app.post("/api/tools/datetime", response_model=ToolResponse)
async def get_datetime(request: ToolRequest):
    """Get current date/time information - convenient endpoint"""
    return await execute_tool("datetime", request)

@app.post("/api/tools/calculator", response_model=ToolResponse)
async def calculate(request: ToolRequest):
    """Perform mathematical calculations - convenient endpoint"""
    return await execute_tool("calculator", request)

@app.post("/api/tools/file_reader", response_model=ToolResponse)
async def read_file(request: ToolRequest):
    """Read and analyze files - convenient endpoint"""
    return await execute_tool("file_reader", request)

@app.post("/api/tools/one_on_one_scheduler", response_model=ToolResponse)
async def schedule_meeting(request: ToolRequest):
    """Schedule 1:1 meetings - convenient endpoint"""
    return await execute_tool("one_on_one_scheduler", request)

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