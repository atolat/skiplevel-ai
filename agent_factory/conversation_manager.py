"""Simple conversation session management for Agent Factory."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .supabase_client import SupabaseProfileClient


@dataclass
class ConversationSession:
    """Represents a conversation session."""
    id: str
    user_id: str
    title: str
    summary: Optional[str] = None
    status: str = "active"
    message_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ConversationManager:
    """Manages conversation sessions with database persistence."""
    
    def __init__(self):
        """Initialize conversation manager."""
        self.supabase_client = SupabaseProfileClient()
        self.client = self.supabase_client.client
        self.current_session: Optional[ConversationSession] = None
    
    def start_new_session(self, user_id: str, initial_title: str = "New Conversation") -> ConversationSession:
        """Start a new conversation session.
        
        Args:
            user_id: User's UUID
            initial_title: Initial title for the conversation
            
        Returns:
            ConversationSession object
        """
        session_id = str(uuid.uuid4())
        
        # Create session in database
        session_data = {
            "id": session_id,
            "user_id": user_id,
            "title": initial_title,
            "status": "active",
            "message_count": 0
        }
        
        try:
            response = self.client.table("conversation_sessions").insert(session_data).execute()
            
            if response.data:
                session_record = response.data[0]
                self.current_session = ConversationSession(
                    id=session_record["id"],
                    user_id=session_record["user_id"],
                    title=session_record["title"],
                    status=session_record["status"],
                    message_count=session_record["message_count"],
                    created_at=datetime.fromisoformat(session_record["created_at"].replace('Z', '+00:00'))
                )
                
                print(f"✅ Started new conversation session: {session_id}")
                return self.current_session
            else:
                raise Exception("Failed to create session in database")
                
        except Exception as e:
            print(f"❌ Error creating conversation session: {e}")
            # Create a local session as fallback
            self.current_session = ConversationSession(
                id=session_id,
                user_id=user_id,
                title=initial_title,
                created_at=datetime.now()
            )
            return self.current_session
    
    def increment_message_count(self) -> None:
        """Increment the message count for the current session."""
        if not self.current_session:
            return
        
        self.current_session.message_count += 1
        
        # Update in database
        try:
            self.client.table("conversation_sessions").update({
                "message_count": self.current_session.message_count,
                "updated_at": datetime.now().isoformat()
            }).eq("id", self.current_session.id).execute()
        except Exception as e:
            print(f"⚠️ Failed to update message count: {e}")
    
    def complete_session(self, final_summary: Optional[str] = None) -> bool:
        """Complete the current conversation session.
        
        Args:
            final_summary: Optional summary of the conversation
            
        Returns:
            True if successful, False otherwise
        """
        if not self.current_session:
            print("No active session to complete.")
            return False
        
        update_data = {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        if final_summary:
            update_data["summary"] = final_summary
        
        try:
            response = self.client.table("conversation_sessions").update(update_data).eq("id", self.current_session.id).execute()
            
            if response.data:
                print(f"✅ Completed conversation session: {self.current_session.id}")
                self.current_session = None
                return True
            else:
                print(f"❌ Failed to complete session in database")
                return False
                
        except Exception as e:
            print(f"❌ Error completing conversation session: {e}")
            return False
    
    def get_recent_sessions(self, user_id: str, limit: int = 5) -> List[ConversationSession]:
        """Get recent conversation sessions for a user.
        
        Args:
            user_id: User's UUID
            limit: Maximum number of sessions to return
            
        Returns:
            List of ConversationSession objects
        """
        try:
            response = self.client.table("conversation_sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            
            sessions = []
            if response.data:
                for record in response.data:
                    sessions.append(ConversationSession(
                        id=record["id"],
                        user_id=record["user_id"],
                        title=record["title"],
                        summary=record.get("summary"),
                        status=record["status"],
                        message_count=record["message_count"],
                        created_at=datetime.fromisoformat(record["created_at"].replace('Z', '+00:00')) if record.get("created_at") else None,
                        updated_at=datetime.fromisoformat(record["updated_at"].replace('Z', '+00:00')) if record.get("updated_at") else None,
                        completed_at=datetime.fromisoformat(record["completed_at"].replace('Z', '+00:00')) if record.get("completed_at") else None
                    ))
            
            return sessions
            
        except Exception as e:
            print(f"❌ Error fetching recent sessions: {e}")
            return []
    
    def update_session_title(self, new_title: str) -> bool:
        """Update the title of the current session.
        
        Args:
            new_title: New title for the session
            
        Returns:
            True if successful, False otherwise
        """
        if not self.current_session:
            return False
        
        try:
            response = self.client.table("conversation_sessions").update({
                "title": new_title,
                "updated_at": datetime.now().isoformat()
            }).eq("id", self.current_session.id).execute()
            
            if response.data:
                self.current_session.title = new_title
                print(f"✅ Updated session title to: {new_title}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error updating session title: {e}")
            return False
    
    def generate_markdown_summary(self, conversation_content: str, user_profile: Optional[Dict[str, Any]] = None, agent_name: str = "Emreq") -> str:
        """Generate a markdown-formatted conversation summary.
        
        Args:
            conversation_content: The conversation content to summarize
            user_profile: Optional user profile information
            agent_name: Name of the AI agent
            
        Returns:
            Markdown-formatted summary string
        """
        if not self.current_session:
            return ""
        
        # Get session info
        session_date = self.current_session.created_at.strftime("%B %d, %Y") if self.current_session.created_at else "Unknown Date"
        session_time = self.current_session.created_at.strftime("%I:%M %p") if self.current_session.created_at else "Unknown Time"
        duration_minutes = self._calculate_session_duration()
        
        # User information
        user_name = user_profile.get("name", "Engineer") if user_profile else "Engineer"
        user_title = user_profile.get("title", "Software Engineer") if user_profile else "Software Engineer"
        user_email = user_profile.get("email", "") if user_profile else ""
        
        # Build markdown summary
        markdown_summary = f"""# 📋 Conversation Summary

## 📅 Session Information
- **Date:** {session_date}
- **Time:** {session_time}
- **Duration:** ~{duration_minutes} minutes
- **Messages:** {self.current_session.message_count} exchanges
- **Status:** {self.current_session.status.title()}

## 👥 Participants
- **Manager:** {agent_name} (AI Engineering Manager)
- **Engineer:** {user_name} ({user_title})
{f"- **Email:** {user_email}" if user_email else ""}

## 🎯 Key Discussion Points

### Main Topics Covered:
{self._extract_key_topics(conversation_content)}

### Decisions Made:
{self._extract_decisions(conversation_content)}

### Action Items:
{self._extract_action_items(conversation_content)}

## 📊 Session Metrics
- **Engagement Level:** {self._assess_engagement_level()}
- **Topics Covered:** {self._count_topics_covered(conversation_content)}
- **Tools Used:** {self._identify_tools_used(conversation_content)}

## 🔄 Next Steps
{self._generate_next_steps(conversation_content)}

---
*📝 Summary generated by {agent_name} AI Manager*  
*🕐 Generated at: {datetime.now().strftime("%Y-%m-%d %I:%M %p")}*"""

        return markdown_summary
    
    def _calculate_session_duration(self) -> int:
        """Calculate approximate session duration in minutes."""
        if not self.current_session or not self.current_session.created_at:
            return 0
        
        # Handle timezone-aware/naive datetime comparison
        now = datetime.now()
        created_at = self.current_session.created_at
        
        # If created_at is timezone-aware, make now timezone-aware too
        if created_at.tzinfo is not None and created_at.utcoffset() is not None:
            import pytz
            now = now.replace(tzinfo=pytz.UTC)
        
        duration = now - created_at
        return max(1, int(duration.total_seconds() / 60))
    
    def _extract_key_topics(self, content: str) -> str:
        """Extract key topics from conversation content."""
        # Simple keyword-based topic extraction
        topics = []
        
        # Common engineering topics
        topic_keywords = {
            "Career Development": ["career", "growth", "promotion", "advancement", "goals"],
            "Technical Skills": ["skills", "technology", "programming", "coding", "technical"],
            "Project Management": ["project", "deadline", "planning", "milestone", "delivery"],
            "Team Collaboration": ["team", "collaboration", "communication", "meeting", "standup"],
            "Performance": ["performance", "review", "feedback", "improvement", "metrics"],
            "Leadership": ["leadership", "mentor", "guide", "lead", "responsibility"],
            "Work-Life Balance": ["balance", "stress", "workload", "time", "schedule"],
            "Learning": ["learning", "training", "course", "skill", "development"]
        }
        
        content_lower = content.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.append(topic)
        
        if not topics:
            topics = ["General Discussion"]
        
        return "\n".join([f"- {topic}" for topic in topics[:5]])  # Top 5 topics
    
    def _extract_decisions(self, content: str) -> str:
        """Extract decisions from conversation content."""
        # Look for decision indicators
        decision_phrases = [
            "we decided", "agreed to", "will do", "plan to", "decided to",
            "going to", "next step", "action plan", "resolution"
        ]
        
        decisions = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(phrase in line_lower for phrase in decision_phrases):
                # Clean up the line and add as decision
                clean_line = line.strip()
                if len(clean_line) > 20 and len(clean_line) < 200:  # Reasonable length
                    decisions.append(clean_line)
        
        if not decisions:
            return "- No specific decisions documented in this session"
        
        return "\n".join([f"- {decision}" for decision in decisions[:3]])  # Top 3 decisions
    
    def _extract_action_items(self, content: str) -> str:
        """Extract action items from conversation content."""
        # Look for action indicators
        action_phrases = [
            "action:", "todo:", "task:", "will", "need to", "should",
            "follow up", "next week", "by", "deadline", "complete"
        ]
        
        actions = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(phrase in line_lower for phrase in action_phrases):
                clean_line = line.strip()
                if len(clean_line) > 15 and len(clean_line) < 150:
                    actions.append(clean_line)
        
        if not actions:
            return "- No specific action items identified"
        
        return "\n".join([f"- {action}" for action in actions[:4]])  # Top 4 actions
    
    def _assess_engagement_level(self) -> str:
        """Assess engagement level based on message count and session duration."""
        if not self.current_session:
            return "Unknown"
        
        messages_per_minute = self.current_session.message_count / max(1, self._calculate_session_duration())
        
        if messages_per_minute > 2:
            return "High 🔥"
        elif messages_per_minute > 1:
            return "Medium 📈"
        else:
            return "Low 📊"
    
    def _count_topics_covered(self, content: str) -> str:
        """Count approximate number of topics covered."""
        # Simple heuristic: count topic transitions
        topic_transitions = content.count('?') + content.count('!') + content.count('.')
        topic_count = max(1, topic_transitions // 10)  # Rough estimate
        
        return f"{topic_count} topics"
    
    def _identify_tools_used(self, content: str) -> str:
        """Identify tools used during the conversation."""
        tools_used = []
        
        tool_indicators = {
            "Web Search": ["search", "research", "found", "according to"],
            "Calculator": ["calculate", "math", "result", "equals"],
            "DateTime": ["time", "date", "schedule", "calendar"],
            "Scheduler": ["meeting", "1:1", "appointment", "schedule"]
        }
        
        content_lower = content.lower()
        for tool, keywords in tool_indicators.items():
            if any(keyword in content_lower for keyword in keywords):
                tools_used.append(tool)
        
        if not tools_used:
            return "None identified"
        
        return ", ".join(tools_used)
    
    def _generate_next_steps(self, content: str) -> str:
        """Generate suggested next steps based on conversation."""
        # Simple next steps based on content analysis
        next_steps = []
        
        content_lower = content.lower()
        
        if "goal" in content_lower or "career" in content_lower:
            next_steps.append("Schedule follow-up career development discussion")
        
        if "project" in content_lower or "work" in content_lower:
            next_steps.append("Review project progress in next 1:1")
        
        if "team" in content_lower or "collaboration" in content_lower:
            next_steps.append("Discuss team dynamics and collaboration")
        
        if "skill" in content_lower or "learning" in content_lower:
            next_steps.append("Identify learning opportunities and resources")
        
        if not next_steps:
            next_steps = ["Schedule regular follow-up session"]
        
        return "\n".join([f"- {step}" for step in next_steps[:3]]) 