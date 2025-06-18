"""Memory System V1 Demo - Showcasing intelligent conversation memory."""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich import box

# Import Agent Factory components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from agent_factory.config import load_config
from agent_factory.memory_config import MemoryConfig, UserProfile, Goal


class MemoryDemo:
    """Demonstrates the V1 memory system with a growth coach agent."""
    
    def __init__(self):
        self.console = Console()
        self.agent_config = None
        self.user_profile = UserProfile()
        self.goals: List[Goal] = []
        self.conversation_history: List[Dict[str, Any]] = []
        self.memory_config = MemoryConfig()
        
    def load_agent(self) -> bool:
        """Load the growth coach agent configuration."""
        config_path = Path(__file__).parent.parent / "configs" / "growth_coach.yaml"
        
        if not config_path.exists():
            self.console.print(f"[red]Error: Agent config not found at {config_path}[/red]")
            return False
            
        self.agent_config = load_config(str(config_path))
        if not self.agent_config:
            self.console.print("[red]Error: Failed to load agent configuration[/red]")
            return False
            
        # Enable memory for this demo
        self.agent_config.memory.enabled = True
        self.agent_config.memory.conversation_max_messages = 8  # Lower for demo
        self.agent_config.memory.summarize_after = 6
        
        return True
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to conversation history with memory processing."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        
        self.conversation_history.append(message)
        
        # Process memory updates based on message content
        if role == "user":
            self._process_user_message(content)
        elif role == "assistant":
            self._process_assistant_message(content)
        
        # Handle conversation length limits
        if len(self.conversation_history) > self.memory_config.conversation_max_messages:
            self._summarize_old_messages()
    
    def _process_user_message(self, content: str):
        """Extract user profile information and goals from user messages."""
        content_lower = content.lower()
        
        # Extract name
        if "my name is" in content_lower or "i'm" in content_lower or "i am" in content_lower:
            # Simple name extraction (in real implementation, use NLP)
            words = content.split()
            for i, word in enumerate(words):
                if word.lower() in ["name", "i'm", "i", "am"] and i + 1 < len(words):
                    potential_name = words[i + 1].strip(".,!?")
                    if potential_name.isalpha():
                        self.user_profile.name = potential_name
                        break
        
        # Extract role/job
        if any(phrase in content_lower for phrase in ["work as", "job is", "i'm a", "i am a", "my role"]):
            # Simple role extraction
            role_keywords = ["developer", "engineer", "manager", "designer", "analyst", "consultant", "teacher", "student"]
            for keyword in role_keywords:
                if keyword in content_lower:
                    self.user_profile.role = keyword.title()
                    break
        
        # Extract goals
        if any(phrase in content_lower for phrase in ["goal", "want to", "hoping to", "trying to", "objective"]):
            # Create a new goal
            goal = Goal(
                description=content,
                status="active",
                notes=[f"Mentioned on {datetime.now().strftime('%Y-%m-%d')}"]
            )
            self.goals.append(goal)
            
            # Limit goals
            if len(self.goals) > self.memory_config.max_goals:
                self.goals = self.goals[-self.memory_config.max_goals:]
    
    def _process_assistant_message(self, content: str):
        """Process assistant messages for memory updates."""
        # In a real implementation, this would analyze assistant responses
        # for user preference extraction, goal updates, etc.
        pass
    
    def _summarize_old_messages(self):
        """Summarize old messages when hitting conversation limits."""
        if len(self.conversation_history) <= self.memory_config.summarize_after:
            return
        
        # Keep recent messages, summarize older ones
        recent_messages = self.conversation_history[-self.memory_config.summarize_after:]
        old_messages = self.conversation_history[:-self.memory_config.summarize_after]
        
        # Create summary (simplified for demo)
        summary = {
            "role": "system",
            "content": f"[SUMMARY] Previous conversation covered {len(old_messages)} messages about user goals and preferences.",
            "timestamp": datetime.now(),
            "metadata": {"type": "summary", "summarized_count": len(old_messages)}
        }
        
        self.conversation_history = [summary] + recent_messages
    
    def get_memory_state(self) -> Dict[str, Any]:
        """Get current memory state for display."""
        return {
            "user_profile": self.user_profile.model_dump(),
            "goals": [goal.model_dump() for goal in self.goals],
            "conversation_length": len(self.conversation_history),
            "memory_config": self.memory_config.model_dump()
        }
    
    def display_memory_state(self):
        """Display current memory state with rich formatting."""
        memory_state = self.get_memory_state()
        
        # Create user profile table
        profile_table = Table(title="👤 User Profile", box=box.ROUNDED)
        profile_table.add_column("Field", style="cyan")
        profile_table.add_column("Value", style="green")
        
        profile = memory_state["user_profile"]
        profile_table.add_row("Name", profile.get("name") or "Not set")
        profile_table.add_row("Role", profile.get("role") or "Not set")
        profile_table.add_row("Communication Style", profile.get("communication_style") or "Not set")
        profile_table.add_row("Preferences", str(len(profile.get("preferences", {}))) + " items")
        
        # Create goals table
        goals_table = Table(title="🎯 Active Goals", box=box.ROUNDED)
        goals_table.add_column("Goal", style="yellow")
        goals_table.add_column("Status", style="green")
        goals_table.add_column("Created", style="blue")
        
        for goal in memory_state["goals"]:
            created_date = goal["created_date"]
            if isinstance(created_date, str):
                created_date = created_date.split("T")[0]  # Just date part
            else:
                created_date = created_date.strftime("%Y-%m-%d")
            
            goals_table.add_row(
                goal["description"][:50] + "..." if len(goal["description"]) > 50 else goal["description"],
                goal["status"],
                created_date
            )
        
        if not memory_state["goals"]:
            goals_table.add_row("No goals tracked yet", "-", "-")
        
        # Create conversation stats table
        conv_table = Table(title="💬 Conversation Memory", box=box.ROUNDED)
        conv_table.add_column("Metric", style="cyan")
        conv_table.add_column("Value", style="green")
        
        conv_table.add_row("Messages in Memory", str(memory_state["conversation_length"]))
        conv_table.add_row("Max Messages", str(memory_state["memory_config"]["conversation_max_messages"]))
        conv_table.add_row("Summarize After", str(memory_state["memory_config"]["summarize_after"]))
        conv_table.add_row("Memory Enabled", "✅" if memory_state["memory_config"]["enabled"] else "❌")
        
        # Display all tables
        self.console.print(profile_table)
        self.console.print()
        self.console.print(goals_table)
        self.console.print()
        self.console.print(conv_table)


def demo_conversation(demo: MemoryDemo):
    """Run a multi-turn conversation demo showing memory in action."""
    console = demo.console
    
    # Conversation turns
    conversation_turns = [
        {
            "user": "Hi there! My name is Sarah and I work as a software engineer at a tech startup.",
            "assistant": "Hello Sarah! It's great to meet you. As a software engineer at a tech startup, you must be working on some exciting projects. I'm here to help you with your professional growth and development. What brings you here today?",
            "memory_update": "👤 Learned: Name=Sarah, Role=Software Engineer"
        },
        {
            "user": "I'm hoping to transition into a senior engineering role within the next year. I want to improve my leadership skills.",
            "assistant": "That's a fantastic goal, Sarah! Transitioning to a senior role is an exciting step. Leadership skills are crucial for senior engineers. I'll help you track this goal and we can work on developing those leadership capabilities. What specific leadership areas would you like to focus on?",
            "memory_update": "🎯 New Goal: Transition to senior engineering role + improve leadership"
        },
        {
            "user": "I'd like to get better at mentoring junior developers and leading technical discussions in meetings.",
            "assistant": "Excellent focus areas, Sarah! Mentoring and leading technical discussions are key senior engineer responsibilities. Since you mentioned wanting to improve leadership skills for your senior role transition, these align perfectly with your goal. Have you had any mentoring experience so far?",
            "memory_update": "📝 Updated preferences: Focus on mentoring & technical leadership"
        },
        {
            "user": "Not much formal mentoring, but I've helped a few interns. I sometimes struggle with explaining complex concepts simply.",
            "assistant": "That's actually great experience to build on, Sarah! Helping interns shows you have the right instincts. The challenge of explaining complex concepts simply is common - it's a skill that improves with practice. This directly supports your goal of becoming a senior engineer with strong leadership skills.",
            "memory_update": "💡 Noted: Has intern mentoring experience, needs help with simplifying explanations"
        },
        {
            "user": "Thanks! Can you remind me what we discussed about my goals?",
            "assistant": "Of course, Sarah! We've been discussing your goal to transition into a senior engineering role within the next year, with a focus on improving leadership skills. Specifically, you want to get better at mentoring junior developers and leading technical discussions. You mentioned having some experience with interns but wanting to improve at explaining complex concepts simply.",
            "memory_update": "🧠 Memory recall: Referenced previous goals and context"
        }
    ]
    
    console.print(Panel.fit(
        "[bold blue]🤖 Multi-Turn Conversation Demo[/bold blue]\n"
        "Watch how the agent builds context and remembers information across turns",
        border_style="blue"
    ))
    console.print()
    
    for i, turn in enumerate(conversation_turns, 1):
        # Display turn header
        console.print(f"[bold cyan]--- Turn {i} ---[/bold cyan]")
        
        # User message
        console.print(Panel(
            turn["user"],
            title="👤 Sarah (User)",
            border_style="green"
        ))
        
        # Add to memory
        demo.add_message("user", turn["user"])
        
        # Show memory update
        if turn["memory_update"]:
            console.print(f"[dim yellow]{turn['memory_update']}[/dim yellow]")
        
        # Simulate thinking time
        time.sleep(1)
        
        # Assistant response
        console.print(Panel(
            turn["assistant"],
            title="🤖 Growth Coach (Assistant)",
            border_style="blue"
        ))
        
        # Add assistant response to memory
        demo.add_message("assistant", turn["assistant"])
        
        console.print()
        time.sleep(1.5)
    
    return len(conversation_turns)


def demonstrate_summarization(demo: MemoryDemo):
    """Demonstrate conversation summarization when hitting limits."""
    console = demo.console
    
    console.print(Panel.fit(
        "[bold yellow]📝 Conversation Summarization Demo[/bold yellow]\n"
        "Adding more messages to trigger automatic summarization",
        border_style="yellow"
    ))
    console.print()
    
    # Add more messages to trigger summarization
    additional_messages = [
        ("user", "I also want to learn more about system design for my senior role."),
        ("assistant", "System design is crucial for senior engineers, Sarah! This aligns perfectly with your career goal."),
        ("user", "What resources do you recommend for learning system design?"),
        ("assistant", "I recommend starting with 'Designing Data-Intensive Applications' and practicing with system design interviews."),
    ]
    
    console.print(f"[cyan]Current conversation length: {len(demo.conversation_history)} messages[/cyan]")
    console.print(f"[cyan]Will summarize after: {demo.memory_config.summarize_after} messages[/cyan]")
    console.print()
    
    for role, content in additional_messages:
        demo.add_message(role, content)
        console.print(f"[dim]Added {role} message... (total: {len(demo.conversation_history)})[/dim]")
        
        # Check if summarization happened
        if any(msg.get("metadata", {}).get("type") == "summary" for msg in demo.conversation_history):
            console.print("[bold yellow]🔄 Automatic summarization triggered![/bold yellow]")
            break
    
    console.print()
    console.print(f"[green]Final conversation length: {len(demo.conversation_history)} messages[/green]")


def main():
    """Run the complete memory system demo."""
    console = Console()
    
    # Title
    console.print(Panel.fit(
        "[bold magenta]🧠 Agent Factory V1 Memory System Demo[/bold magenta]\n"
        "Showcasing intelligent conversation memory with user profiles, goals, and context",
        border_style="magenta"
    ))
    console.print()
    
    # Initialize demo
    demo = MemoryDemo()
    
    # Section 1: Setup
    console.print(Panel.fit(
        "[bold blue]🔧 Setting Up Memory System[/bold blue]",
        border_style="blue"
    ))
    
    if not demo.load_agent():
        console.print("[red]Failed to load agent. Exiting demo.[/red]")
        return
    
    console.print("[green]✅ Growth Coach agent loaded successfully[/green]")
    console.print(f"[green]✅ Memory system enabled with {demo.memory_config.conversation_max_messages} message limit[/green]")
    console.print()
    
    # Section 2: Conversation Demo
    turn_count = demo_conversation(demo)
    
    # Section 3: Memory State Inspection
    console.print(Panel.fit(
        "[bold green]🔍 Memory State Inspection[/bold green]\n"
        f"After {turn_count} conversation turns",
        border_style="green"
    ))
    console.print()
    
    demo.display_memory_state()
    console.print()
    
    # Section 4: Summarization Demo
    demonstrate_summarization(demo)
    
    # Section 5: Final Memory State
    console.print(Panel.fit(
        "[bold purple]📊 Final Memory State[/bold purple]",
        border_style="purple"
    ))
    console.print()
    
    demo.display_memory_state()
    
    # Conclusion
    console.print()
    console.print(Panel.fit(
        "[bold green]🎉 Demo Complete![/bold green]\n\n"
        "The V1 Memory System demonstrated:\n"
        "• User profile tracking (name, role, preferences)\n"
        "• Goal creation and tracking\n"
        "• Context-aware responses\n"
        "• Automatic conversation summarization\n"
        "• Intelligent memory management\n\n"
        "This makes conversations more personal and intelligent!",
        border_style="green"
    ))


if __name__ == "__main__":
    main() 