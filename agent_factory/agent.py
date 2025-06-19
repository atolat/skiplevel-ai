"""Simplified LangGraph agent implementation for Agent Factory."""

import os
import uuid
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .config import AgentConfig
from .tools import AVAILABLE_TOOLS
from .conversation_manager import ConversationManager
from .traits import get_traits_registry


class SimpleLangGraphAgent:
    """Simplified LangGraph agent with proper tool binding."""
    
    def __init__(self, config: AgentConfig, user_profile: Optional[Dict[str, Any]] = None):
        """Initialize the agent.
        
        Args:
            config: Agent configuration
            user_profile: Optional user profile data
        """
        self.config = config
        self.user_profile = user_profile or {}
        self.last_tool_usage = []  # Track tool usage for UI indicators
        
        # Load environment variables
        load_dotenv()
        
        # Initialize LLM with tool binding
        self.llm = self._create_llm_with_tools()
        
        # Initialize conversation manager
        try:
            self.conversation_manager = ConversationManager()
        except Exception as e:
            print(f"⚠️ Failed to initialize conversation manager: {e}")
            self.conversation_manager = None
        
        # Setup LangGraph workflow
        self.graph = self._create_graph()
        self.current_session_id = None
        self.thread_id = str(uuid.uuid4())  # Generate unique thread ID for this agent instance
        
        print(f"✅ SimpleLangGraphAgent created: {config.name}")
        
        # Log memory and traits configuration
        if hasattr(config, 'memory') and config.memory:
            print(f"📝 Memory: max_messages={config.memory.conversation_max_messages}, profile_enabled={config.memory.user_profile_enabled}")
        
        if hasattr(config, 'traits') and config.traits:
            print(f"🎭 Traits: {', '.join(config.traits)}")
    
    def _create_llm_with_tools(self):
        """Create LLM with tools bound."""
        # Get tools for this agent
        tools = []
        for tool_name in self.config.tools:
            if tool_name in AVAILABLE_TOOLS:
                tools.append(AVAILABLE_TOOLS[tool_name])
            else:
                print(f"⚠️ Tool '{tool_name}' not found")
        
        # Create LLM
        llm = ChatOpenAI(
            model=self.config.llm.model_name,
            temperature=self.config.temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Bind tools to LLM
        if tools:
            llm = llm.bind_tools(tools)
            print(f"✅ Bound {len(tools)} tools to LLM")
        
        return llm
    
    def _create_graph(self):
        """Create the LangGraph workflow."""
        from langgraph.graph import MessagesState
        
        # Create tools node if we have tools
        tools = []
        for tool_name in self.config.tools:
            if tool_name in AVAILABLE_TOOLS:
                tools.append(AVAILABLE_TOOLS[tool_name])
        
        # Create workflow
        workflow = StateGraph(MessagesState)
        
        # Add agent node
        workflow.add_node("agent", self._agent_node)
        
        # Add tools node if we have tools
        if tools:
            tool_node = ToolNode(tools)
            workflow.add_node("tools", tool_node)
        
        # Set entry point
        workflow.add_edge(START, "agent")
        
        # Add conditional edges for tool calling
        if tools:
            workflow.add_conditional_edges(
                "agent",
                tools_condition,
                {
                    "tools": "tools",
                    "__end__": END,
                }
            )
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge("agent", END)
        
        # Compile with memory (using LangGraph's MemorySaver for checkpointing)
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    def _agent_node(self, state):
        """Agent node that processes messages."""
        # Build system message
        system_content = self._build_system_prompt()
        
        # Get messages and add system message if not present
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_content)] + messages
        
        # Call LLM
        response = self.llm.invoke(messages)
        
        return {"messages": [response]}
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for the agent."""
        prompt = f"You are {self.config.name}. {self.config.description}"
        
        # Add user context if available
        if self.user_profile:
            context = self._get_personalized_context()
            if context:
                prompt += f"\n\nUser Context: {context}"
        
        # Add system prompt from config
        if hasattr(self.config, 'system_prompt') and self.config.system_prompt:
            prompt += f"\n\n{self.config.system_prompt}"
        
        # Add traits-based behavioral instructions
        if hasattr(self.config, 'traits') and self.config.traits:
            traits_instructions = self._get_traits_instructions()
            if traits_instructions:
                prompt += f"\n\nBehavioral Guidelines:\n{traits_instructions}"
        
        return prompt
    
    def _get_personalized_context(self) -> str:
        """Generate personalized context from user profile."""
        if not self.user_profile:
            return ""
        
        context_parts = []
        
        if self.user_profile.get("name"):
            context_parts.append(f"User: {self.user_profile['name']}")
        
        if self.user_profile.get("title"):
            context_parts.append(f"Role: {self.user_profile['title']}")
        
        if self.user_profile.get("email"):
            context_parts.append(f"Email: {self.user_profile['email']}")
        
        if self.user_profile.get("current_projects"):
            projects = ", ".join(self.user_profile["current_projects"])
            context_parts.append(f"Current Projects: {projects}")
        
        if self.user_profile.get("career_goals"):
            goals = ", ".join(self.user_profile["career_goals"])
            context_parts.append(f"Career Goals: {goals}")
        
        if self.user_profile.get("biggest_challenges"):
            challenges = ", ".join(self.user_profile["biggest_challenges"])
            context_parts.append(f"Challenges: {challenges}")
        
        if self.user_profile.get("communication_style"):
            context_parts.append(f"Prefers {self.user_profile['communication_style']} communication")
        
        return ". ".join(context_parts)
    
    def _get_traits_instructions(self) -> str:
        """Generate behavioral instructions from configured traits."""
        if not hasattr(self.config, 'traits') or not self.config.traits:
            return ""
        
        try:
            traits_registry = get_traits_registry()
            instructions = traits_registry.resolve_traits(self.config.traits)
            
            if instructions:
                # Format as numbered behavioral guidelines
                formatted_instructions = []
                for i, instruction in enumerate(instructions, 1):
                    formatted_instructions.append(f"{i}. {instruction}")
                
                return "\n".join(formatted_instructions)
            
        except Exception as e:
            print(f"⚠️ Error loading traits instructions: {e}")
        
        return ""
    
    def _extract_tool_usage(self, result):
        """Extract tool usage information from the graph result."""
        if not result or "messages" not in result:
            return
        
        for message in result["messages"]:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_info = {
                        "name": tool_call.get("name", "unknown"),
                        "args": tool_call.get("args", {}),
                        "id": tool_call.get("id", "")
                    }
                    self.last_tool_usage.append(tool_info)
    
    def get_last_tool_usage(self) -> List[dict]:
        """Get the tools used in the last conversation turn."""
        usage = self.last_tool_usage.copy()
        # Clear the usage after returning it to prevent stale data
        self.last_tool_usage = []
        return usage
    
    def start_conversation(self, user_id: str, title: str = "New Conversation") -> bool:
        """Start a new conversation session."""
        if not self.conversation_manager:
            return True  # Continue without database persistence
        
        try:
            session = self.conversation_manager.start_new_session(user_id, title)
            if session:
                self.current_session_id = session.id
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to start conversation: {e}")
            return False
    
    def end_conversation(self, summary: Optional[str] = None) -> bool:
        """End the current conversation session."""
        if not self.conversation_manager or not self.current_session_id:
            return True
        
        try:
            # Generate summary if not provided
            if summary is None:
                summary = "Conversation completed successfully."
            
            success = self.conversation_manager.complete_session(summary)
            if success:
                self.current_session_id = None
            return success
        except Exception as e:
            print(f"❌ Failed to end conversation: {e}")
            return False
    
    def chat(self, message: str) -> str:
        """Chat with the agent."""
        try:
            # Reset tool usage tracking
            self.last_tool_usage = []
            
            # Create thread config for session persistence
            # Use unique thread ID to prevent cross-contamination between users
            thread_config = {"configurable": {"thread_id": self.current_session_id or self.thread_id}}
            
            # Invoke the graph
            result = self.graph.invoke(
                {"messages": [HumanMessage(content=message)]},
                config=thread_config
            )
            
            # Track tool usage from the conversation
            self._extract_tool_usage(result)
            
            # Extract response
            if result and "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    return last_message.content
            
            return "I apologize, but I couldn't generate a response."
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def chat_stream(self, message: str):
        """Stream chat response."""
        # For now, implement as a simple wrapper
        response = self.chat(message)
        
        # Simulate streaming
        chunk_size = 50
        for i in range(0, len(response), chunk_size):
            yield response[i:i+chunk_size]
    
    def __repr__(self) -> str:
        """String representation."""
        return f"SimpleLangGraphAgent(name='{self.config.name}', id='{self.config.agent_id}')"


def create_agent(config: AgentConfig, user_profile: Optional[Dict[str, Any]] = None) -> SimpleLangGraphAgent:
    """Create an agent instance from configuration.
    
    Args:
        config: Agent configuration
        user_profile: Optional user profile data
        
    Returns:
        SimpleLangGraphAgent instance
    """
    return SimpleLangGraphAgent(config, user_profile)


# Backward compatibility aliases
BaseAgent = SimpleLangGraphAgent
LangGraphAgent = SimpleLangGraphAgent 