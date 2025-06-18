"""Simple agent implementation for Agent Factory."""

import os
import re
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from .config import AgentConfig
from .llm import BaseLLM, get_llm
from .tools import get_tool
from .memory_config import MemoryConfig, UserProfile, Goal


class MemoryManager:
    """Manages agent memory including user profiles, goals, and conversation history."""
    
    def __init__(self, config: MemoryConfig, llm: Optional[BaseLLM] = None):
        """Initialize memory manager with configuration.
        
        Args:
            config: Memory configuration settings
            llm: Optional LLM instance for intelligent extraction
        """
        self.config = config
        self.llm = llm
        self.user_profile = UserProfile()
        self.goals: List[Goal] = []
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Track confidence scores for extracted information
        self.profile_confidence = {
            "name": 0.0,
            "role": 0.0,
            "communication_style": 0.0
        }
    
    def _extract_user_info(self, user_message: str) -> dict:
        """Extract user information using LLM with confidence scoring.
        
        Args:
            user_message: User's message to analyze
            
        Returns:
            Dictionary with extracted information and confidence scores
        """
        if not self.llm:
            return {}
        
        try:
            # Create extraction prompt
            prompt = f"""Analyze this user message and extract personal information. Return ONLY valid JSON.

User message: "{user_message}"

Extract:
- name: user's name (string or null)
- role: job/profession (string or null) 
- communication_style: formal/casual/technical (string or null)
- goals: list of specific goals mentioned (array of strings)
- name_confidence: 0.0-1.0 confidence for name
- role_confidence: 0.0-1.0 confidence for role  
- style_confidence: 0.0-1.0 confidence for communication style
- goals_confidence: 0.0-1.0 confidence for each goal

Example response:
{{"name": "John", "role": "Software Engineer", "communication_style": null, "goals": ["become senior engineer"], "name_confidence": 0.9, "role_confidence": 0.8, "style_confidence": 0.0, "goals_confidence": [0.9]}}

JSON response:"""

            # Generate response with low temperature for consistency
            response = self.llm.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=200
            )
            
            # Clean response and parse JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Parse JSON
            extracted_info = json.loads(response)
            
            # Validate structure
            required_fields = ["name", "role", "communication_style", "goals", 
                             "name_confidence", "role_confidence", "style_confidence", "goals_confidence"]
            
            for field in required_fields:
                if field not in extracted_info:
                    extracted_info[field] = None if field != "goals" else []
                    if field.endswith("_confidence"):
                        extracted_info[field] = 0.0 if not field.startswith("goals") else []
            
            return extracted_info
            
        except (json.JSONDecodeError, Exception) as e:
            # Fall back to simple heuristics
            return self._fallback_extraction(user_message)
    
    def _fallback_extraction(self, user_message: str) -> dict:
        """Fallback extraction using simple heuristics.
        
        Args:
            user_message: User's message to analyze
            
        Returns:
            Dictionary with basic extracted information
        """
        content_lower = user_message.lower()
        result = {
            "name": None, "role": None, "communication_style": None, "goals": [],
            "name_confidence": 0.0, "role_confidence": 0.0, "style_confidence": 0.0, "goals_confidence": []
        }
        
        # Simple name extraction
        name_patterns = [r"my name is (\w+)", r"i'm (\w+)", r"i am (\w+)", r"call me (\w+)"]
        for pattern in name_patterns:
            match = re.search(pattern, content_lower)
            if match:
                potential_name = match.group(1).strip()
                if potential_name.isalpha() and len(potential_name) > 1:
                    result["name"] = potential_name.title()
                    result["name_confidence"] = 0.8
                    break
        
        # Simple role extraction
        role_keywords = ["engineer", "developer", "manager", "designer", "analyst", "teacher", "student"]
        for keyword in role_keywords:
            if keyword in content_lower:
                result["role"] = keyword.title()
                result["role_confidence"] = 0.6
                break
        
        # Simple goal detection
        goal_indicators = ["want to", "goal", "hoping to", "trying to", "plan to"]
        if any(indicator in content_lower for indicator in goal_indicators):
            result["goals"] = [user_message]
            result["goals_confidence"] = [0.7]
        
        return result
    
    def update_profile(self, user_message: str) -> None:
        """Extract and update user profile information from message using LLM.
        
        Args:
            user_message: User's message to analyze for profile info
        """
        if not self.config.user_profile_enabled:
            return
        
        # Extract user information using LLM
        extracted_info = self._extract_user_info(user_message)
        
        if not extracted_info:
            return
        
        # Update name if confidence is high enough and higher than existing
        if (extracted_info.get("name") and 
            extracted_info.get("name_confidence", 0) > 0.7 and
            extracted_info.get("name_confidence", 0) > self.profile_confidence.get("name", 0)):
            self.user_profile.name = extracted_info["name"]
            self.profile_confidence["name"] = extracted_info["name_confidence"]
        
        # Update role if confidence is high enough and higher than existing
        if (extracted_info.get("role") and 
            extracted_info.get("role_confidence", 0) > 0.7 and
            extracted_info.get("role_confidence", 0) > self.profile_confidence.get("role", 0)):
            self.user_profile.role = extracted_info["role"]
            self.profile_confidence["role"] = extracted_info["role_confidence"]
        
        # Update communication style if confidence is high enough and higher than existing
        if (extracted_info.get("communication_style") and 
            extracted_info.get("style_confidence", 0) > 0.7 and
            extracted_info.get("style_confidence", 0) > self.profile_confidence.get("communication_style", 0)):
            self.user_profile.communication_style = extracted_info["communication_style"]
            self.profile_confidence["communication_style"] = extracted_info["style_confidence"]
    
    def add_goal(self, user_message: str) -> None:
        """Detect and add goals from user message using LLM.
        
        Args:
            user_message: User's message to analyze for goals
        """
        if not self.config.goals_tracking_enabled:
            return
        
        # Extract user information using LLM
        extracted_info = self._extract_user_info(user_message)
        
        if not extracted_info or not extracted_info.get("goals"):
            return
        
        # Process each detected goal
        goals = extracted_info.get("goals", [])
        goals_confidence = extracted_info.get("goals_confidence", [])
        
        for i, goal_description in enumerate(goals):
            # Get confidence for this goal (default to 0.0 if not available)
            confidence = goals_confidence[i] if i < len(goals_confidence) else 0.0
            
            # Only add goals with high confidence
            if confidence > 0.7:
                # Check if this goal is already tracked (avoid duplicates)
                existing_goal_descriptions = [g.description.lower() for g in self.goals]
                if goal_description.lower() not in existing_goal_descriptions:
                    goal = Goal(
                        description=goal_description,
                        status="active",
                        notes=[f"Mentioned on {datetime.now().strftime('%Y-%m-%d')} (confidence: {confidence:.2f})"]
                    )
                    self.goals.append(goal)
        
        # Limit goals to max_goals
        if len(self.goals) > self.config.max_goals:
            # Keep most recent goals
            self.goals = self.goals[-self.config.max_goals:]
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        }
        
        self.conversation_history.append(message)
        
        # Process user messages for profile and goal updates
        if role == "user":
            self.update_profile(content)
            self.add_goal(content)
        
        # Handle conversation length limits
        if len(self.conversation_history) > self.config.conversation_max_messages:
            self._summarize_conversation()
    
    def get_memory_context(self) -> str:
        """Generate formatted memory context for LLM prompts.
        
        Returns:
            Formatted memory context string
        """
        if not self.config.enabled:
            return ""
        
        context_parts = []
        
        # User profile section
        if self.config.user_profile_enabled and (self.user_profile.name or self.user_profile.role):
            profile_info = []
            if self.user_profile.name:
                profile_info.append(f"Name: {self.user_profile.name}")
            if self.user_profile.role:
                profile_info.append(f"Role: {self.user_profile.role}")
            if self.user_profile.communication_style:
                profile_info.append(f"Communication Style: {self.user_profile.communication_style}")
            
            if profile_info:
                context_parts.append(f"User Profile: {', '.join(profile_info)}")
        
        # Active goals section
        if self.config.goals_tracking_enabled and self.goals:
            active_goals = [goal.description for goal in self.goals if goal.status == "active"]
            if active_goals:
                goals_text = "; ".join(active_goals[:3])  # Show top 3 goals
                context_parts.append(f"Active Goals: {goals_text}")
        
        # Recent conversation context
        if self.conversation_history:
            recent_messages = self.conversation_history[-4:]  # Last 4 messages
            conversation_summary = []
            for msg in recent_messages:
                role_prefix = "User" if msg["role"] == "user" else "Assistant"
                content_preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                conversation_summary.append(f"{role_prefix}: {content_preview}")
            
            if conversation_summary:
                context_parts.append(f"Recent Conversation: {' | '.join(conversation_summary)}")
        
        if context_parts:
            return "\n\nMemory Context:\n" + "\n".join(context_parts)
        
        return ""
    
    def _summarize_conversation(self) -> None:
        """Summarize old conversation when hitting message limits."""
        if len(self.conversation_history) <= self.config.summarize_after:
            return
        
        # Keep recent messages, summarize older ones
        recent_messages = self.conversation_history[-self.config.summarize_after:]
        old_messages = self.conversation_history[:-self.config.summarize_after]
        
        # Create summary (simplified approach)
        summary_content = f"[SUMMARY] Previous conversation covered {len(old_messages)} messages"
        
        # Extract key topics from old messages
        topics = set()
        for msg in old_messages:
            content_lower = msg["content"].lower()
            # Simple keyword extraction
            if "goal" in content_lower or "want" in content_lower:
                topics.add("goals")
            if "work" in content_lower or "job" in content_lower:
                topics.add("career")
            if "help" in content_lower or "support" in content_lower:
                topics.add("assistance")
        
        if topics:
            summary_content += f" about {', '.join(topics)}"
        
        summary_message = {
            "role": "system",
            "content": summary_content,
            "timestamp": datetime.now(),
            "metadata": {"type": "summary", "summarized_count": len(old_messages)}
        }
        
        # Replace old messages with summary + recent messages
        self.conversation_history = [summary_message] + recent_messages


class BaseAgent:
    """Base agent class that provides simple chat functionality."""
    
    def __init__(self, config: AgentConfig, llm: Optional[BaseLLM] = None, user_profile: Optional[Dict[str, Any]] = None):
        """Initialize the agent with configuration.
        
        Args:
            config: Validated agent configuration
            llm: Optional LLM instance, will create one if not provided
            user_profile: Optional pre-loaded user profile data
        """
        self.config = config
        self.llm = llm
        self.user_profile = user_profile
        
        # Initialize memory manager if memory is enabled
        self.memory_manager = None
        if hasattr(config, 'memory') and config.memory.enabled:
            self.memory_manager = MemoryManager(config.memory, self.llm)
            
            # Inject user profile data if available
            if user_profile:
                self._inject_profile_data(user_profile)
        
        # Load available tools
        self.available_tools = {}
        tool_names = getattr(config, 'tools', [])
        for tool_name in tool_names:
            tool = get_tool(tool_name)
            if tool:
                # If tool supports LLM injection and we have an LLM, pass it
                if hasattr(tool, '__init__') and 'llm' in tool.__init__.__code__.co_varnames:
                    # Create new instance with LLM if available
                    if self.llm:
                        tool_class = tool.__class__
                        tool = tool_class(llm=self.llm)
                
                self.available_tools[tool_name] = tool
            else:
                print(f"Warning: Tool '{tool_name}' not found")
        
        # Create LLM if not provided
        if self.llm is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.llm = get_llm(
                    provider=config.llm.provider,
                    api_key=api_key,
                    model_name=config.llm.model_name
                )
                
                # Update memory manager with LLM if it was created before LLM was available
                if self.memory_manager and not self.memory_manager.llm:
                    self.memory_manager.llm = self.llm
                
                # Re-initialize tools that support LLM injection
                for tool_name in list(self.available_tools.keys()):
                    tool = self.available_tools[tool_name]
                    if hasattr(tool, '__init__') and 'llm' in tool.__init__.__code__.co_varnames:
                        tool_class = tool.__class__
                        self.available_tools[tool_name] = tool_class(llm=self.llm)
    
    def _inject_profile_data(self, user_profile: Dict[str, Any]) -> None:
        """Inject user profile data into the memory manager.
        
        Args:
            user_profile: Formatted user profile data
        """
        if not self.memory_manager or not user_profile:
            return
        
        # Directly populate the user profile in memory manager
        if user_profile.get("name"):
            self.memory_manager.user_profile.name = user_profile["name"]
            self.memory_manager.profile_confidence["name"] = 1.0
        
        if user_profile.get("title"):
            role = user_profile["title"]
            if user_profile.get("level"):
                role = f"{user_profile['level']} {role}"
            self.memory_manager.user_profile.role = role
            self.memory_manager.profile_confidence["role"] = 1.0
        
        if user_profile.get("communication_style"):
            self.memory_manager.user_profile.communication_style = user_profile["communication_style"]
            self.memory_manager.profile_confidence["communication_style"] = 1.0
        
        # Add goals from career goals and learning goals
        goals_to_add = []
        if user_profile.get("career_goals"):
            goals_to_add.extend(user_profile["career_goals"].split(", "))
        if user_profile.get("learning_goals"):
            goals_to_add.extend(user_profile["learning_goals"].split(", "))
        
        for goal_text in goals_to_add:
            if goal_text.strip():
                goal = Goal(
                    description=goal_text.strip(),
                    created_at=datetime.now(),
                    confidence=1.0
                )
                self.memory_manager.goals.append(goal)
    
    def get_personalized_context(self) -> str:
        """Generate personalized context from user profile.
        
        Returns:
            Personalized context string for the agent
        """
        if not self.user_profile:
            return ""
        
        from .supabase_client import SupabaseProfileClient
        client = SupabaseProfileClient()
        return client.generate_personalized_context(self.user_profile)
    
    def chat(self, message: str) -> str:
        """Chat with the agent.
        
        Args:
            message: User message to respond to
            
        Returns:
            Agent response string
        """
        # Add user message to memory if memory is enabled
        if self.memory_manager:
            self.memory_manager.add_message("user", message)
        
        # Use LLM if available
        if self.llm:
            description = self.config.description or "a helpful assistant"
            
            # Build base prompt
            prompt = f"You are {self.config.name}. {description}"
            
            # Add personalized context from user profile
            personalized_context = self.get_personalized_context()
            if personalized_context:
                prompt += f"\n\nUser Context: {personalized_context}"
                print(f"DEBUG: Added personalized context: {personalized_context[:100]}...")
            else:
                print("DEBUG: No personalized context available")
            
            # Add memory context if available
            if self.memory_manager:
                memory_context = self.memory_manager.get_memory_context()
                if memory_context:
                    prompt += memory_context
                    print(f"DEBUG: Added memory context: {memory_context[:100]}...")
            
            prompt += "\n\n"
            
            # Add tools information if available
            if self.available_tools:
                tool_names = list(self.available_tools.keys())
                tool_descriptions = []
                for name, tool in self.available_tools.items():
                    tool_descriptions.append(f"{name}: {tool.description}")
                prompt += f"Available tools: {', '.join(tool_names)}\n"
                prompt += "Tool descriptions:\n" + "\n".join(tool_descriptions) + "\n\n"
                prompt += "If you need to use a tool, respond with TOOL: tool_name INPUT: input_data\n\n"
            
            prompt += f"User: {message}\nAgent:"
            
            print(f"DEBUG: Full prompt length: {len(prompt)} characters")
            
            response = self.llm.generate(
                prompt=prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # Check if response contains tool usage
            if "TOOL:" in response:
                lines = response.split('\n')
                for line in lines:
                    if line.strip().startswith("TOOL:"):
                        try:
                            # Extract tool name and input
                            tool_part = line.split("TOOL:")[1].strip()
                            if "INPUT:" in tool_part:
                                tool_name = tool_part.split("INPUT:")[0].strip()
                                tool_input = tool_part.split("INPUT:")[1].strip()
                            else:
                                tool_name = tool_part
                                tool_input = ""
                            
                            # Execute tool
                            tool_result = self.use_tool(tool_name, tool_input)
                            
                            # Append tool result to response
                            response += f"\n\nTool Result: {tool_result}"
                            
                        except Exception as e:
                            response += f"\n\nTool Error: {str(e)}"
            
            # Add assistant response to memory if memory is enabled
            if self.memory_manager:
                self.memory_manager.add_message("assistant", response)
            
            return response
        
        # Fallback to original behavior if no LLM
        fallback_response = f"Hello! I'm {self.config.name}. You said: {message}"
        
        # Add to memory even in fallback case
        if self.memory_manager:
            self.memory_manager.add_message("assistant", fallback_response)
        
        return fallback_response
    
    def chat_stream(self, message: str):
        """Chat with the agent using streaming responses.
        
        Args:
            message: User message to respond to
            
        Yields:
            Response chunks as they are generated
        """
        # Add user message to memory if memory is enabled
        if self.memory_manager:
            self.memory_manager.add_message("user", message)
        
        # Use LLM if available
        if self.llm:
            description = self.config.description or "a helpful assistant"
            
            # Build base prompt
            prompt = f"You are {self.config.name}. {description}"
            
            # Add personalized context from user profile
            personalized_context = self.get_personalized_context()
            if personalized_context:
                prompt += f"\n\nUser Context: {personalized_context}"
                print(f"DEBUG STREAM: Added personalized context: {personalized_context[:100]}...")
            else:
                print("DEBUG STREAM: No personalized context available")
            
            # Add memory context if available
            if self.memory_manager:
                memory_context = self.memory_manager.get_memory_context()
                if memory_context:
                    prompt += memory_context
                    print(f"DEBUG STREAM: Added memory context: {memory_context[:100]}...")
            
            prompt += "\n\n"
            
            # Add tools information if available
            if self.available_tools:
                tool_names = list(self.available_tools.keys())
                tool_descriptions = []
                for name, tool in self.available_tools.items():
                    tool_descriptions.append(f"{name}: {tool.description}")
                prompt += f"Available tools: {', '.join(tool_names)}\n"
                prompt += "Tool descriptions:\n" + "\n".join(tool_descriptions) + "\n\n"
                prompt += "If you need to use a tool, respond with TOOL: tool_name INPUT: input_data\n\n"
            
            prompt += f"User: {message}\nAgent:"
            
            print(f"DEBUG STREAM: Full prompt length: {len(prompt)} characters")
            
            # Collect full response for tool processing and memory
            full_response = ""
            
            # Stream the response
            for chunk in self.llm.generate_stream(
                prompt=prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            ):
                full_response += chunk
                yield chunk
            
            # Check if response contains tool usage
            if "TOOL:" in full_response:
                lines = full_response.split('\n')
                for line in lines:
                    if line.strip().startswith("TOOL:"):
                        try:
                            # Extract tool name and input
                            tool_part = line.split("TOOL:")[1].strip()
                            if "INPUT:" in tool_part:
                                tool_name = tool_part.split("INPUT:")[0].strip()
                                tool_input = tool_part.split("INPUT:")[1].strip()
                            else:
                                tool_name = tool_part
                                tool_input = ""
                            
                            # Execute tool
                            tool_result = self.use_tool(tool_name, tool_input)
                            
                            # Stream tool result
                            tool_output = f"\n\nTool Result: {tool_result}"
                            full_response += tool_output
                            yield tool_output
                            
                        except Exception as e:
                            error_output = f"\n\nTool Error: {str(e)}"
                            full_response += error_output
                            yield error_output
            
            # Add assistant response to memory if memory is enabled
            if self.memory_manager:
                self.memory_manager.add_message("assistant", full_response)
        
        else:
            # Fallback to original behavior if no LLM
            fallback_response = f"Hello! I'm {self.config.name}. You said: {message}"
            
            # Add to memory even in fallback case
            if self.memory_manager:
                self.memory_manager.add_message("assistant", fallback_response)
            
            yield fallback_response
    
    def use_tool(self, tool_name: str, input_data: str) -> str:
        """Use a tool with the given input data.
        
        Args:
            tool_name: Name of the tool to use
            input_data: Input data for the tool
            
        Returns:
            Tool execution result or error message
        """
        if tool_name not in self.available_tools:
            return f"Error: Tool '{tool_name}' is not available. Available tools: {list(self.available_tools.keys())}"
        
        tool = self.available_tools[tool_name]
        return tool.execute(input_data)
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"BaseAgent(name='{self.config.name}', id='{self.config.agent_id}')"


def create_agent(config: AgentConfig) -> BaseAgent:
    """Create an agent instance from configuration.
    
    Args:
        config: Validated agent configuration
        
    Returns:
        BaseAgent instance
    """
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Create LLM if API key is available
    llm = None
    if api_key:
        llm = get_llm(
            provider=config.llm.provider,
            api_key=api_key,
            model_name=config.llm.model_name
        )
    
    return BaseAgent(config, llm) 