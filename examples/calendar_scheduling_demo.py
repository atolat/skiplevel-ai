#!/usr/bin/env python3
"""
Calendar Scheduling Demo

This example demonstrates the professional 1:1 scheduling capabilities
of Agent Factory's calendar tool with ICS integration.

Features demonstrated:
- Automatic ICS calendar file generation
- Professional email invites with attachments
- Natural language scheduling requests
- JSON-based scheduling configuration
- Agent integration for conversational scheduling

Setup Requirements:
1. Install dependencies: pip install icalendar
2. Set environment variables for email (optional):
   - SMTP_SERVER (default: smtp.gmail.com)
   - SMTP_PORT (default: 587)
   - SMTP_USERNAME (your email)
   - SMTP_PASSWORD (your app password)
   - SENDER_EMAIL (your email)
   - SENDER_NAME (your name)

Note: Without email configuration, the tool will generate ICS files
but won't send actual email invites.
"""

import json
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from agent_factory.config import load_config
from agent_factory.agent import create_agent
from agent_factory.calendar_tools import OneOnOneScheduler

console = Console()

def demo_ics_generation():
    """Demonstrate ICS calendar file generation."""
    console.print("\n📄 ICS Calendar File Generation", style="bold blue")
    console.print("=" * 50)
    
    scheduler = OneOnOneScheduler()
    
    # Create sample meeting details
    from datetime import datetime, timedelta
    
    meeting_details = {
        'title': 'Weekly Leadership 1:1',
        'start_time': datetime(2024, 6, 17, 14, 0),  # Monday 2:00 PM
        'end_time': datetime(2024, 6, 17, 15, 0),    # Monday 3:00 PM
        'description': 'Weekly one-on-one meeting to discuss goals, challenges, and development opportunities.',
        'location': 'Executive Conference Room / Zoom',
        'organizer_email': 'sarah.manager@company.com',
        'organizer_name': 'Sarah Johnson (Manager)',
        'attendee_email': 'alex.employee@company.com',
        'attendee_name': 'Alex Smith (Direct Report)',
        'recurring': True,
        'recurrence_rule': 'FREQ=WEEKLY;BYDAY=MO'
    }
    
    try:
        ics_content = scheduler.create_ics_file(meeting_details)
        
        console.print("✅ ICS file generated successfully!", style="green")
        
        # Display meeting details in a nice table
        table = Table(title="Meeting Details")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Title", meeting_details['title'])
        table.add_row("Date & Time", meeting_details['start_time'].strftime('%A, %B %d, %Y at %I:%M %p'))
        table.add_row("Duration", "60 minutes")
        table.add_row("Location", meeting_details['location'])
        table.add_row("Organizer", meeting_details['organizer_name'])
        table.add_row("Attendee", meeting_details['attendee_name'])
        table.add_row("Recurring", "Weekly (Mondays)")
        
        console.print(table)
        
        # Show ICS content preview
        console.print("\n📋 ICS File Preview:", style="bold")
        ics_preview = ics_content[:400] + "..." if len(ics_content) > 400 else ics_content
        console.print(Panel(ics_preview, title="RFC-Compliant ICS Content"))
        
    except Exception as e:
        console.print(f"❌ Error generating ICS: {e}", style="red")

def demo_json_scheduling():
    """Demonstrate JSON-based scheduling."""
    console.print("\n🔧 JSON-Based Scheduling", style="bold blue")
    console.print("=" * 50)
    
    scheduler = OneOnOneScheduler()
    
    # Example JSON configuration
    scheduling_config = {
        "manager_email": "sarah.manager@company.com",
        "manager_name": "Sarah Johnson",
        "report_email": "alex.employee@company.com", 
        "report_name": "Alex Smith",
        "day": "Tuesday",
        "time": "10:00 AM",
        "duration": 45,
        "title": "Engineering 1:1 - Growth & Development",
        "location": "Building A, Room 204",
        "description": "Weekly 1:1 focused on career development, project updates, and team collaboration."
    }
    
    console.print("📝 Scheduling Configuration:", style="bold")
    console.print(Panel(json.dumps(scheduling_config, indent=2), title="JSON Input"))
    
    # Execute scheduling
    result = scheduler.execute(json.dumps(scheduling_config))
    
    console.print("\n📤 Scheduling Result:", style="bold")
    if result.startswith('✅'):
        console.print(result, style="green")
    else:
        console.print(result, style="yellow")

def demo_natural_language_scheduling():
    """Demonstrate natural language scheduling."""
    console.print("\n🗣️ Natural Language Scheduling", style="bold blue")
    console.print("=" * 50)
    
    scheduler = OneOnOneScheduler()
    
    # Example natural language requests
    requests = [
        "Schedule a weekly 1:1 between manager@company.com and employee@company.com every Wednesday at 3:30 PM for 30 minutes",
        "Set up a recurring meeting with boss@startup.com and dev@startup.com on Fridays at 11 AM for 45 minutes",
        "Create a weekly check-in between sarah.lead@tech.com and john.junior@tech.com every Thursday at 2 PM"
    ]
    
    for i, request in enumerate(requests, 1):
        console.print(f"\n📝 Request {i}:", style="bold")
        console.print(Panel(request, title="Natural Language Input"))
        
        result = scheduler.execute(request)
        
        console.print("📤 Result:", style="bold")
        if result.startswith('✅'):
            console.print(result, style="green")
        else:
            console.print(result, style="yellow")

def demo_agent_integration():
    """Demonstrate agent integration with conversational scheduling."""
    console.print("\n🤖 Agent Integration Demo", style="bold blue")
    console.print("=" * 50)
    
    try:
        # Load scheduling assistant
        config = load_config("configs/scheduling_assistant.yaml")
        if not config:
            console.print("❌ Failed to load scheduling assistant config", style="red")
            return
        
        console.print(f"✅ Loaded agent: {config.name}", style="green")
        
        # Create agent
        agent = create_agent(config)
        
        # Verify tool availability
        if "one_on_one_scheduler" not in agent.available_tools:
            console.print("❌ Calendar tool not available to agent", style="red")
            return
        
        console.print("✅ Calendar tool is available to the agent", style="green")
        
        # Simulate conversation
        conversations = [
            "Hi! I need help scheduling a weekly 1:1 meeting.",
            "I want to set up a meeting between sarah@company.com and alex@company.com every Monday at 2 PM for 30 minutes.",
            "Can you also schedule a different meeting between manager@startup.com and developer@startup.com on Fridays at 4 PM?"
        ]
        
        console.print("\n💬 Conversational Scheduling:", style="bold")
        
        for i, message in enumerate(conversations, 1):
            console.print(f"\n👤 User Message {i}:", style="bold cyan")
            console.print(Panel(message, title="User Input"))
            
            response = agent.chat(message)
            
            console.print("🤖 Agent Response:", style="bold green")
            console.print(Panel(response, title="Agent Output"))
            
    except Exception as e:
        console.print(f"❌ Error in agent demo: {e}", style="red")

def show_setup_instructions():
    """Show setup instructions for email functionality."""
    console.print("\n⚙️ Email Setup Instructions", style="bold blue")
    console.print("=" * 50)
    
    setup_text = """
To enable email functionality, set these environment variables:

Required:
• SMTP_USERNAME - Your email address
• SMTP_PASSWORD - Your email app password

Optional (with defaults):
• SMTP_SERVER - SMTP server (default: smtp.gmail.com)
• SMTP_PORT - SMTP port (default: 587)
• SENDER_EMAIL - Sender email (default: SMTP_USERNAME)
• SENDER_NAME - Sender name (default: "Meeting Scheduler")

Example for Gmail:
export SMTP_USERNAME="your.email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SENDER_NAME="Your Name"

Note: Use app passwords, not regular passwords for Gmail.
Without email setup, ICS files are generated but not sent.
    """
    
    console.print(Panel(setup_text.strip(), title="Email Configuration"))

def main():
    """Run the complete calendar scheduling demo."""
    console.print("📅 Agent Factory Calendar Scheduling Demo", style="bold magenta")
    console.print("=" * 60)
    
    # Check email configuration
    email_configured = bool(os.getenv("SMTP_USERNAME") and os.getenv("SMTP_PASSWORD"))
    
    if email_configured:
        console.print("✅ Email configuration detected", style="green")
    else:
        console.print("⚠️ Email not configured - ICS generation only", style="yellow")
    
    # Run demos
    demo_ics_generation()
    demo_json_scheduling()
    demo_natural_language_scheduling()
    demo_agent_integration()
    
    if not email_configured:
        show_setup_instructions()
    
    console.print("\n🎉 Demo completed!", style="bold green")
    console.print("The calendar tool is ready for production use with proper email configuration.", style="italic")

if __name__ == "__main__":
    main() 