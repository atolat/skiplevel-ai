"""Professional 1:1 scheduling tool with ICS calendar integration."""

import os
import smtplib
import uuid
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional
import json
import re
import pytz

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not available, skip loading
    pass

try:
    from icalendar import Calendar, Event, vRecur
    ICALENDAR_AVAILABLE = True
except ImportError:
    ICALENDAR_AVAILABLE = False

from .tools import BaseTool

# Try to import LLM for intelligent parsing
try:
    from .llm import get_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class OneOnOneScheduler(BaseTool):
    """Professional 1:1 meeting scheduler with automatic calendar invites."""
    
    name = "one_on_one_scheduler"
    description = """Schedule 1:1 meetings with automatic calendar invites. 

REQUIRED FORMAT: Use JSON with 'employee_email' field.

Examples:
- {"employee_email": "employee@company.com", "date": "2025-06-20", "time": "2:00 PM"}
- {"employee_email": "user@company.com", "title": "Weekly 1:1"}

Or natural language: "Schedule a 1:1 with employee@company.com on June 20, 2025"

The AI agent automatically acts as the manager - only employee email is needed."""
    
    def __init__(self, user_timezone: str = None):
        """Initialize the scheduler with SMTP configuration and user timezone.
        
        Args:
            user_timezone: User's timezone (e.g., 'America/Los_Angeles', 'Europe/London')
        """
        super().__init__()
        
        # SMTP Configuration from environment variables
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_username)
        self.sender_name = os.getenv("SENDER_NAME", "Meeting Scheduler")
        
        # Default timezone - use user's timezone if provided, otherwise fall back to environment or NY
        self.default_timezone = user_timezone or os.getenv("DEFAULT_TIMEZONE", "America/New_York")
    
    def create_ics_file(self, meeting_details: Dict[str, Any]) -> str:
        """Generate RFC-compliant ICS file content.
        
        Args:
            meeting_details: Dictionary containing meeting information
                - title: Meeting title
                - start_time: Start datetime
                - end_time: End datetime
                - description: Meeting description
                - location: Meeting location (optional)
                - organizer_email: Organizer email
                - organizer_name: Organizer name
                - attendee_email: Attendee email
                - attendee_name: Attendee name
                - recurring: Whether meeting is recurring (optional)
                - recurrence_rule: RRULE string for recurring meetings (optional)
        
        Returns:
            ICS file content as string
            
        Example:
            >>> scheduler = OneOnOneScheduler()
            >>> details = {
            ...     "title": "Weekly 1:1 Meeting",
            ...     "start_time": datetime(2024, 1, 15, 14, 0),
            ...     "end_time": datetime(2024, 1, 15, 15, 0),
            ...     "description": "Weekly check-in meeting",
            ...     "organizer_email": "manager@company.com",
            ...     "organizer_name": "Manager Name",
            ...     "attendee_email": "employee@company.com",
            ...     "attendee_name": "Employee Name"
            ... }
            >>> ics_content = scheduler.create_ics_file(details)
        """
        if not ICALENDAR_AVAILABLE:
            raise ImportError("icalendar library is required. Install with: pip install icalendar")
        
        # Create calendar
        cal = Calendar()
        cal.add('prodid', '-//Agent Factory//1:1 Scheduler//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'REQUEST')
        
        # Create event
        event = Event()
        event.add('uid', str(uuid.uuid4()))
        event.add('dtstamp', datetime.now())
        event.add('dtstart', meeting_details['start_time'])
        event.add('dtend', meeting_details['end_time'])
        event.add('summary', meeting_details['title'])
        event.add('description', meeting_details.get('description', ''))
        
        # Add location if provided
        if meeting_details.get('location'):
            event.add('location', meeting_details['location'])
        
        # Add organizer
        organizer_email = meeting_details['organizer_email']
        organizer_name = meeting_details.get('organizer_name', organizer_email)
        event.add('organizer', f'MAILTO:{organizer_email}')
        event['organizer'].params['cn'] = organizer_name
        
        # Add attendee
        attendee_email = meeting_details['attendee_email']
        attendee_name = meeting_details.get('attendee_name', attendee_email)
        event.add('attendee', f'MAILTO:{attendee_email}')
        event['attendee'].params['cn'] = attendee_name
        event['attendee'].params['role'] = 'REQ-PARTICIPANT'
        event['attendee'].params['partstat'] = 'NEEDS-ACTION'
        event['attendee'].params['rsvp'] = 'TRUE'
        
        # Add recurrence rule if specified
        if meeting_details.get('recurring') and meeting_details.get('recurrence_rule'):
            event.add('rrule', vRecur.from_ical(meeting_details['recurrence_rule']))
        
        # Add event to calendar
        cal.add_component(event)
        
        return cal.to_ical().decode('utf-8')
    
    def send_calendar_invite(self, manager_email: str, report_email: str, meeting_details: Dict[str, Any]) -> str:
        """Send professional email with ICS attachment.
        
        Args:
            manager_email: Manager's email address
            report_email: Direct report's email address
            meeting_details: Meeting details dictionary
            
        Returns:
            Success or error message
            
        Example:
            >>> scheduler = OneOnOneScheduler()
            >>> result = scheduler.send_calendar_invite(
            ...     "manager@company.com",
            ...     "employee@company.com",
            ...     meeting_details
            ... )
        """
        if not all([self.smtp_username, self.smtp_password]):
            return "❌ Email configuration missing. Please set SMTP_USERNAME and SMTP_PASSWORD environment variables."
        
        try:
            # Create ICS file content
            ics_content = self.create_ics_file(meeting_details)
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = f"{report_email}, {manager_email}"
            
            # Add SMTP username as BCC for monitoring/validation
            if self.smtp_username and self.smtp_username not in [report_email, manager_email]:
                msg['Bcc'] = self.smtp_username
            
            msg['Subject'] = f"📅 Calendar Invite: {meeting_details['title']}"
            
            # Create email body
            meeting_time = meeting_details['start_time'].strftime("%A, %B %d, %Y at %I:%M %p")
            duration = int((meeting_details['end_time'] - meeting_details['start_time']).total_seconds() / 60)
            
            email_body = f"""
Hello,

You're invited to a 1:1 meeting:

📅 **{meeting_details['title']}**
🕐 **When:** {meeting_time}
⏱️ **Duration:** {duration} minutes
📍 **Location:** {meeting_details.get('location', 'To be determined')}

**Meeting Details:**
{meeting_details.get('description', 'Regular 1:1 check-in meeting')}

**Attendees:**
• {meeting_details.get('organizer_name', manager_email)} (Organizer)
• {meeting_details.get('attendee_name', report_email)}

Please accept this calendar invitation to confirm your attendance.

Best regards,
{self.sender_name}

---
This meeting was scheduled automatically by Agent Factory.
"""
            
            # Attach email body
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Create ICS attachment
            ics_attachment = MIMEBase('text', 'calendar')
            ics_attachment.set_payload(ics_content.encode('utf-8'))
            encoders.encode_base64(ics_attachment)
            ics_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="meeting_invite.ics"'
            )
            ics_attachment.add_header('Content-Type', 'text/calendar; method=REQUEST')
            msg.attach(ics_attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                # Prepare recipient list including BCC
                recipients = [report_email, manager_email]
                if self.smtp_username and self.smtp_username not in recipients:
                    recipients.append(self.smtp_username)
                
                # Send to all recipients (including BCC)
                server.send_message(msg, to_addrs=recipients)
            
            # Create success message
            success_msg = f"✅ Calendar invite sent successfully to {report_email} and {manager_email}"
            if self.smtp_username and self.smtp_username not in [report_email, manager_email]:
                success_msg += f" (BCC: {self.smtp_username})"
            
            return success_msg
            
        except Exception as e:
            return f"❌ Failed to send calendar invite: {str(e)}"
    
    def schedule_weekly_one_on_one(self, input_data: str) -> str:
        """Parse scheduling request and create recurring 1:1.
        
        Args:
            input_data: JSON string or natural language scheduling request
            
        Returns:
            Success or error message with meeting details
            
        Example:
            >>> scheduler = OneOnOneScheduler()
            >>> result = scheduler.schedule_weekly_one_on_one(
            ...     '{"employee_email": "employee@company.com", '
            ...     '"date": "2025-06-20", "time": "2:00 PM", "duration": 30}'
            ... )
        """
        try:
            # Try to parse as JSON first
            try:
                data = json.loads(input_data)
            except json.JSONDecodeError:
                # Use LLM-based extraction for natural language requests
                llm_data = self._extract_employee_info_with_llm(input_data)
                # Fall back to regex-based parsing if LLM fails
                regex_data = self._parse_natural_language_request(input_data)
                # Merge the results, preferring LLM data
                data = {**regex_data, **llm_data}
            
            # Get default manager info (since the agent is the manager)
            manager_info = self._get_default_manager_info()
            
            # Handle legacy format or cases where only attendees are provided
            if 'attendees' in data and not data.get('employee_email'):
                # This is likely a case where the user provided names instead of emails
                attendees = data['attendees']
                if isinstance(attendees, list) and len(attendees) > 0:
                    # Ask for the employee's email address
                    return f"""❌ I need the employee's email address to send the calendar invite.

I see you want to schedule a meeting with: {', '.join(attendees)}

Since I'm an AI manager, I only need the **employee's email address** to send the calendar invite.

**Please provide the employee's email address:**

**Option 1 - JSON format:**
```json
{{
    "employee_email": "employee@company.com",
    "date": "{data.get('date', '2025-06-20')}",
    "time": "2:00 PM",
    "duration": 30,
    "title": "1:1 Meeting"
}}
```

**Option 2 - Tell me directly:**
"Schedule a 1:1 with employee@company.com on {data.get('date', 'June 20, 2025')}"

I'll handle the rest automatically as your AI manager! 🤖"""
            
            # Check if we have employee email (the only required field now)
            if not data.get('employee_email') and not data.get('report_email') and not data.get('email'):
                return f"""❌ I need the employee's email address to send the calendar invite.

As your AI manager, I only need the **employee's email address** to schedule our 1:1 meeting.

**Please provide:**
• **Employee's email address** (the person you want to meet with)
• **Date** (optional, I can pick a good time)
• **Time** (optional, defaults to 2:00 PM)

**Example:**
```json
{{
    "employee_email": "john.employee@company.com",
    "date": "2025-06-20",
    "time": "2:00 PM",
    "duration": 30,
    "title": "1:1 Check-in"
}}
```

**Or simply tell me:** "Schedule a 1:1 with john.employee@company.com on June 20, 2025"

I'll take care of the rest as your AI manager! 🤖"""
            
            # Use employee_email or fall back to report_email/email for backward compatibility
            employee_email = data.get('employee_email') or data.get('report_email') or data.get('email')
            employee_name = data.get('employee_name') or data.get('report_name') or employee_email
            
            # Set defaults
            day = data.get('day', 'Monday')
            time_str = data.get('time', '2:00 PM')
            duration = int(data.get('duration', 30))  # minutes
            title = data.get('title', '1:1 Meeting')
            location = data.get('location', 'Conference Room / Video Call')
            description = data.get('description', 'One-on-one check-in meeting')
            
            # Get user timezone preference (default to Eastern Time)
            user_timezone = data.get('timezone', self.default_timezone)
            tz = pytz.timezone(user_timezone)
            
            # Handle specific date if provided
            if data.get('date'):
                try:
                    # Try to parse the date
                    date_str = data['date']
                    if isinstance(date_str, str):
                        # Handle various date formats
                        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%B %d, %Y']
                        meeting_date = None
                        for fmt in date_formats:
                            try:
                                meeting_date = datetime.strptime(date_str, fmt)
                                # Make it timezone-aware
                                meeting_date = tz.localize(meeting_date.replace(hour=0, minute=0, second=0, microsecond=0))
                                break
                            except ValueError:
                                continue
                        
                        if not meeting_date:
                            return f"❌ Invalid date format: {date_str}. Please use format like '2025-06-20', '06/20/2025', or 'June 20, 2025'"
                    else:
                        meeting_date = date_str
                except Exception as e:
                    return f"❌ Error parsing date: {str(e)}"
            else:
                # Calculate next occurrence of the specified day
                meeting_date = self._get_next_weekday(day, user_timezone)
                if not meeting_date:
                    return f"❌ Invalid day: {day}. Use day names like 'Monday', 'Tuesday', etc."
            
            # Parse time
            start_time = self._parse_time_string(time_str)
            if not start_time:
                return f"❌ Invalid time format: {time_str}. Use format like '2:00 PM' or '14:00'"
            
            # Combine date and time with timezone awareness
            if hasattr(meeting_date, 'tzinfo') and meeting_date.tzinfo:
                # meeting_date is already timezone-aware
                meeting_start = meeting_date.replace(
                    hour=start_time.hour,
                    minute=start_time.minute,
                    second=0,
                    microsecond=0
                )
            else:
                # meeting_date is naive, make it timezone-aware
                meeting_start = tz.localize(datetime.combine(
                    meeting_date.date(),
                    start_time.time()
                ))
            
            meeting_end = meeting_start + timedelta(minutes=duration)
            
            # Create meeting details
            meeting_details = {
                'title': title,
                'start_time': meeting_start,
                'end_time': meeting_end,
                'description': description,
                'location': location,
                'organizer_email': manager_info['manager_email'],
                'organizer_name': manager_info['manager_name'],
                'attendee_email': employee_email,
                'attendee_name': employee_name,
                'recurring': data.get('recurring', False),
                'recurrence_rule': 'FREQ=WEEKLY;BYDAY=' + day[:2].upper() if data.get('recurring', False) else None
            }
            
            # Send calendar invite
            result = self.send_calendar_invite(
                manager_info['manager_email'],
                employee_email,
                meeting_details
            )
            
            if result.startswith('✅'):
                meeting_type = "Weekly Recurring" if data.get('recurring', False) else "One-time"
                meeting_summary = f"""
📅 **{meeting_type} 1:1 Meeting Scheduled Successfully!**

**Meeting Details:**
• **Title:** {title}
• **When:** {meeting_start.strftime('%A, %B %d, %Y at %I:%M %p')}
• **Duration:** {duration} minutes
• **Location:** {location}
• **Attendees:** {meeting_details['organizer_name']} & {meeting_details['attendee_name']}
{f"• **Recurring:** Every {day}" if data.get('recurring', False) else ""}

{result}
"""
                return meeting_summary
            else:
                return result
                
        except Exception as e:
            return f"❌ Error scheduling meeting: {str(e)}"
    
    def _parse_natural_language_request(self, text: str) -> Dict[str, Any]:
        """Parse natural language scheduling request.
        
        Args:
            text: Natural language text describing the meeting request
            
        Returns:
            Dictionary with parsed meeting details
        """
        data = {}
        
        # Check if this looks like a JSON-like structure with attendees
        if 'attendees' in text.lower() and '[' in text and ']' in text:
            # Try to extract attendees list
            attendees_match = re.search(r'"attendees":\s*\[(.*?)\]', text)
            if attendees_match:
                attendees_str = attendees_match.group(1)
                # Extract names from the list
                names = re.findall(r'"([^"]+)"', attendees_str)
                if names:
                    data['attendees'] = names
        
        # Extract date if present
        date_match = re.search(r'"date":\s*"([^"]+)"', text)
        if date_match:
            data['date'] = date_match.group(1)
        
        # Extract agenda if present
        agenda_match = re.search(r'"agenda":\s*"([^"]+)"', text)
        if agenda_match:
            data['description'] = agenda_match.group(1)
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        if len(emails) >= 2:
            # If multiple emails, assume first is manager, second is employee
            data['manager_email'] = emails[0]
            data['employee_email'] = emails[1]
        elif len(emails) == 1:
            # If only one email, assume it's the employee (since AI is the manager)
            data['employee_email'] = emails[0]
        
        # Extract day of week
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            if day in text.lower():
                data['day'] = day.title()
                break
        
        # Extract time
        time_patterns = [
            r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b',
            r'\b(\d{1,2})\s*(am|pm)\b',
            r'\b(\d{1,2}):(\d{2})\b'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                if len(match.groups()) == 3:  # HH:MM AM/PM
                    hour, minute, ampm = match.groups()
                    data['time'] = f"{hour}:{minute} {ampm.upper()}"
                elif len(match.groups()) == 2 and match.groups()[1] in ['am', 'pm']:  # H AM/PM
                    hour, ampm = match.groups()
                    data['time'] = f"{hour}:00 {ampm.upper()}"
                else:  # HH:MM (24-hour)
                    hour, minute = match.groups()
                    data['time'] = f"{hour}:{minute}"
                break
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*(?:minutes?|mins?)', text.lower())
        if duration_match:
            data['duration'] = int(duration_match.group(1))
        
        return data
    
    def _parse_time_string(self, time_str: str) -> Optional[datetime]:
        """Parse time string into datetime object.
        
        Args:
            time_str: Time string like "2:00 PM" or "14:00"
            
        Returns:
            datetime object or None if parsing fails
        """
        time_formats = [
            '%I:%M %p',  # 2:00 PM
            '%I %p',     # 2 PM
            '%H:%M',     # 14:00
            '%H'         # 14
        ]
        
        for fmt in time_formats:
            try:
                return datetime.strptime(time_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def _get_next_weekday(self, day_name: str, timezone_name: str = None) -> Optional[datetime]:
        """Get the next occurrence of a specific weekday in the specified timezone.
        
        Args:
            day_name: Name of the day (e.g., "Monday")
            timezone_name: Timezone name (e.g., "America/New_York")
            
        Returns:
            datetime object for the next occurrence of that day
        """
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_day = days.get(day_name.lower())
        if target_day is None:
            return None
        
        # Use timezone-aware datetime
        tz = pytz.timezone(timezone_name or self.default_timezone)
        today = datetime.now(tz)
        days_ahead = target_day - today.weekday()
        
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        return today + timedelta(days=days_ahead)
    
    def execute(self, input_data: str) -> str:
        """Main tool interface for agent integration.
        
        Args:
            input_data: JSON string or natural language scheduling request
            
        Returns:
            Success or error message
            
        Example usage:
            Schedule a 1:1 meeting (AI agent as manager):
            {
                "employee_email": "employee@company.com",
                "date": "2025-06-20",
                "time": "2:00 PM",
                "duration": 30,
                "title": "1:1 Check-in",
                "location": "Conference Room A"
            }
            
            Or use natural language:
            "Schedule a 1:1 with employee@company.com on June 20, 2025 at 2:00 PM"
            
            The AI agent automatically acts as the manager, so only employee email is needed.
        """
        if not input_data or not input_data.strip():
            return """❌ Please provide meeting details. 

**Example JSON format:**
```json
{
    "employee_email": "employee@company.com",
    "date": "2025-06-20",
    "time": "2:00 PM",
    "duration": 30,
    "title": "1:1 Check-in"
}
```

**Or use natural language:**
"Schedule a 1:1 with employee@company.com on June 20, 2025 at 2:00 PM"

As an AI manager, I only need the employee's email address! 🤖
"""
        
        return self.schedule_weekly_one_on_one(input_data)
    
    def _extract_employee_info_with_llm(self, text: str) -> Dict[str, Any]:
        """Use LLM to intelligently extract employee information from scheduling request.
        
        Args:
            text: The scheduling request text
            
        Returns:
            Dictionary with extracted employee information
        """
        if not LLM_AVAILABLE:
            return {}
        
        try:
            # Get OpenAI API key from environment
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {}
            
            llm = get_llm("openai", api_key=api_key, model_name="gpt-3.5-turbo")
            if not llm:
                return {}
            
            prompt = f"""
You are helping to extract employee information from a meeting scheduling request. The context is that an AI agent (manager) is scheduling a 1:1 meeting with a human employee.

Extract the following information from this scheduling request:
"{text}"

Please respond with ONLY a JSON object containing:
- "employee_email": the employee's email address (if mentioned)
- "employee_name": the employee's name (if mentioned) 
- "date": the meeting date (if mentioned, in YYYY-MM-DD format)
- "time": the meeting time (if mentioned, in HH:MM AM/PM format)
- "duration": meeting duration in minutes (if mentioned)
- "title": meeting title/subject (if mentioned)
- "description": meeting description/agenda (if mentioned)

If any information is not found, omit that field from the JSON.

Examples:
- "Schedule a 1:1 with john@company.com on June 20, 2025" → {{"employee_email": "john@company.com", "date": "2025-06-20"}}
- "Meeting with Sarah tomorrow at 2 PM" → {{"employee_name": "Sarah", "time": "2:00 PM"}}
- "1:1 with alex.smith@tech.com next Monday" → {{"employee_email": "alex.smith@tech.com"}}

JSON:
"""
            
            response_text = llm.generate(prompt, temperature=0.1, max_tokens=200)
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Try to parse the entire response as JSON
                return json.loads(response_text)
                
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            return {}
    
    def _get_default_manager_info(self) -> Dict[str, str]:
        """Get default manager information for the AI agent.
        
        Returns:
            Dictionary with manager email and name
        """
        # Use environment variable if set, otherwise use a placeholder
        manager_email = os.getenv("AGENT_EMAIL", "ai.manager@company.local")
        manager_name = os.getenv("AGENT_NAME", "AI Manager")
        
        return {
            "manager_email": manager_email,
            "manager_name": manager_name
        }


# Register the tool
def get_one_on_one_scheduler():
    """Get an instance of the OneOnOneScheduler tool."""
    return OneOnOneScheduler() 