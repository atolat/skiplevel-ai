"""LangChain-compatible tools for Agent Factory."""

import ast
import operator
import os
import re
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import pytz

from langchain_core.tools import tool


@tool("datetime")
def datetime_tool(timezone: str = "") -> str:
    """Get current date, time, timezone, and day of week information.
    
    Args:
        timezone: Optional timezone (e.g., 'America/New_York', 'Europe/London')
        
    Returns:
        Formatted date/time information
    """
    try:
        # Use provided timezone or default
        user_timezone = os.getenv("USER_TIMEZONE", "America/New_York")
        timezone_name = timezone.strip() if timezone.strip() else user_timezone
        
        # Get timezone object
        try:
            tz = pytz.timezone(timezone_name)
        except pytz.exceptions.UnknownTimeZoneError:
            tz = pytz.timezone("America/New_York")  # fallback
            timezone_name = "America/New_York"
        
        # Get current time in the specified timezone
        now = datetime.now(tz)
        
        # Format the response
        response = f"""📅 **Current Date & Time Information**

🕐 **Current Time:** {now.strftime('%I:%M %p')}
📆 **Today's Date:** {now.strftime('%A, %B %d, %Y')}
🌍 **Timezone:** {timezone_name}
📅 **Day of Week:** {now.strftime('%A')}
📊 **Week of Year:** Week {now.isocalendar()[1]}
🗓️ **ISO Date:** {now.strftime('%Y-%m-%d')}

**Useful for scheduling:**
- Today is {now.strftime('%A')}
- Current time is {now.strftime('%I:%M %p')} {timezone_name.split('/')[-1]} time
- For meetings, consider times after {(now + timedelta(hours=1)).strftime('%I:%M %p')}"""

        return response
        
    except Exception as e:
        return f"❌ Error getting date/time: {str(e)}"


@tool("calculator")
def calculator_tool(expression: str) -> str:
    """Perform mathematical calculations and operations.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Calculation result or error message
    """
    if not expression.strip():
        return "Error: Please provide a mathematical expression to calculate"
    
    try:
        # Parse the expression safely
        result = _safe_eval(expression.strip())
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error: Invalid mathematical expression - {str(e)}"


def _safe_eval(expression: str) -> float:
    """Safely evaluate mathematical expressions.
    
    Args:
        expression: Mathematical expression string
        
    Returns:
        Numerical result
        
    Raises:
        ValueError: If expression contains unsafe operations
    """
    # Define allowed operations
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    allowed_functions = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
    }
    
    # Parse the expression
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError:
        raise ValueError("Invalid syntax in mathematical expression")
    
    def _eval_node(node):
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            op = allowed_operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = _eval_node(node.operand)
            op = allowed_operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operation: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name not in allowed_functions:
                raise ValueError(f"Unsupported function: {func_name}")
            args = [_eval_node(arg) for arg in node.args]
            return allowed_functions[func_name](*args)
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")
    
    return _eval_node(tree.body)


@tool("file_reader")
def file_reader_tool(file_path: str) -> str:
    """Read and analyze the contents of text files.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File contents with analysis or error message
    """
    if not file_path.strip():
        return "Error: Please provide a file path to read"
    
    try:
        # Validate and clean the file path
        clean_path = file_path.strip().strip('"').strip("'")
        
        # Security check - prevent directory traversal
        if not _validate_file_path(clean_path):
            return "Error: Invalid file path or access denied for security reasons"
        
        # Convert to Path object
        path = Path(clean_path)
        
        # Check if file exists
        if not path.exists():
            return f"Error: File '{clean_path}' does not exist"
        
        # Check if it's a file (not a directory)
        if not path.is_file():
            return f"Error: '{clean_path}' is not a file"
        
        # Check file size (limit to 1MB for safety)
        if path.stat().st_size > 1024 * 1024:
            return f"Error: File '{clean_path}' is too large (>1MB)"
        
        # Read the file
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Analyze the content
        lines = content.split('\n')
        word_count = len(content.split())
        char_count = len(content)
        
        # Create response with analysis
        response = f"""📄 **File Analysis: {path.name}**

📊 **Statistics:**
- Lines: {len(lines)}
- Words: {word_count}
- Characters: {char_count}
- Size: {path.stat().st_size} bytes

📝 **Content Preview:**
```
{content[:500]}{'...' if len(content) > 500 else ''}
```

✅ File read successfully"""

        return response
        
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"


def _validate_file_path(file_path: str) -> bool:
    """Validate file path for security.
    
    Args:
        file_path: File path to validate
        
    Returns:
        True if path is safe to access
    """
    try:
        # Convert to absolute path
        abs_path = Path(file_path).resolve()
        
        # Get current working directory
        cwd = Path.cwd().resolve()
        
        # Check if the file is within the current working directory or its subdirectories
        try:
            abs_path.relative_to(cwd)
            return True
        except ValueError:
            # File is outside the working directory
            return False
            
    except Exception:
        return False


@tool("web_search")
def web_search_tool(query: str) -> str:
    """Search the web and synthesize results using AI.
    
    Args:
        query: Search query to look up
        
    Returns:
        AI-synthesized search results or error message
    """
    if not query.strip():
        return "Error: Please provide a search query"
    
    try:
        # Initialize with environment variables
        llm = None  # Will be injected by agent if available
        
        # Perform web search
        results = _search_web(query.strip())
        
        if not results:
            return f"❌ No search results found for: {query}"
        
        # Try to synthesize results with AI if LLM is available
        if llm:
            try:
                return _synthesize_results(query, results, llm)
            except Exception as e:
                print(f"⚠️ AI synthesis failed: {e}")
                # Fall back to formatted raw results
                return _format_raw_results(query, results)
        else:
            # Return formatted raw results
            return _format_raw_results(query, results)
            
    except Exception as e:
        return f"❌ Error performing web search: {str(e)}"


def _search_web(query: str) -> List[Dict[str, Any]]:
    """Perform web search using multiple search engines.
    
    Args:
        query: Search query
        
    Returns:
        List of search results
    """
    results = []
    
    # Try DuckDuckGo first (no API key required)
    try:
        results.extend(_search_duckduckgo(query))
    except Exception as e:
        print(f"⚠️ DuckDuckGo search failed: {e}")
    
    # Try SerpAPI if available
    serpapi_key = os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI_API_KEY")
    if serpapi_key and len(results) < 5:
        try:
            results.extend(_search_serpapi(query, serpapi_key))
        except Exception as e:
            print(f"⚠️ SerpAPI search failed: {e}")
    
    return results[:10]  # Limit to top 10 results


def _search_duckduckgo(query: str) -> List[Dict[str, Any]]:
    """Search using DuckDuckGo Instant Answer API.
    
    Args:
        query: Search query
        
    Returns:
        List of search results
    """
    try:
        # Use DuckDuckGo's instant answer API
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        # Extract abstract if available
        if data.get('Abstract'):
            results.append({
                'title': data.get('Heading', query),
                'snippet': data.get('Abstract'),
                'url': data.get('AbstractURL', ''),
                'source': 'DuckDuckGo'
            })
        
        # Extract related topics
        for topic in data.get('RelatedTopics', [])[:3]:
            if isinstance(topic, dict) and 'Text' in topic:
                results.append({
                    'title': topic.get('Text', '')[:100],
                    'snippet': topic.get('Text', ''),
                    'url': topic.get('FirstURL', ''),
                    'source': 'DuckDuckGo'
                })
        
        return results
        
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
        return []


def _search_serpapi(query: str, api_key: str) -> List[Dict[str, Any]]:
    """Search using SerpAPI (Google Search).
    
    Args:
        query: Search query
        api_key: SerpAPI key
        
    Returns:
        List of search results
    """
    try:
        url = "https://serpapi.com/search"
        params = {
            'q': query,
            'api_key': api_key,
            'engine': 'google',
            'num': 5
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get('organic_results', []):
            results.append({
                'title': item.get('title', ''),
                'snippet': item.get('snippet', ''),
                'url': item.get('link', ''),
                'source': 'Google'
            })
        
        return results
        
    except Exception as e:
        print(f"SerpAPI search error: {e}")
        return []


def _synthesize_results(query: str, results: List[Dict[str, Any]], llm) -> str:
    """Synthesize search results using AI.
    
    Args:
        query: Original search query
        results: List of search results
        llm: Language model for synthesis
        
    Returns:
        AI-synthesized summary
    """
    # Prepare context for AI synthesis
    context = f"Search Query: {query}\n\nSearch Results:\n"
    for i, result in enumerate(results[:5], 1):
        context += f"{i}. {result['title']}\n"
        context += f"   {result['snippet']}\n"
        if result['url']:
            context += f"   Source: {result['url']}\n"
        context += "\n"
    
    # Create synthesis prompt
    prompt = f"""Based on the following search results, provide a comprehensive and accurate summary that answers the query: "{query}"

{context}

Please synthesize the information into a clear, well-structured response that:
1. Directly addresses the search query
2. Combines relevant information from multiple sources
3. Highlights key points and insights
4. Maintains factual accuracy
5. Cites sources when appropriate

Response:"""

    try:
        # Generate synthesis using the LLM
        synthesis = llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=800
        )
        
        return f"🔍 **Web Search Results for: \"{query}\"**\n\n{synthesis}"
        
    except Exception as e:
        raise Exception(f"AI synthesis failed: {str(e)}")


def _format_raw_results(query: str, results: List[Dict[str, Any]]) -> str:
    """Format raw search results when AI synthesis is not available.
    
    Args:
        query: Search query
        results: List of search results
        
    Returns:
        Formatted search results
    """
    response = f"🔍 **Web Search Results for: \"{query}\"**\n\n"
    
    for i, result in enumerate(results[:5], 1):
        response += f"**{i}. {result['title']}**\n"
        response += f"{result['snippet']}\n"
        if result['url']:
            response += f"🔗 Source: {result['url']}\n"
        response += "\n"
    
    response += f"Found {len(results)} results total."
    return response


@tool("one_on_one_scheduler")
def one_on_one_scheduler_tool(request: str) -> str:
    """Schedule 1:1 meetings with simple calendar information.
    
    Args:
        request: Meeting request in JSON format or natural language
        
    Examples:
        - '{"employee_email": "john@company.com", "date": "2025-06-20", "time": "2:00 PM"}'
        - "Schedule a 1:1 with sarah@company.com next Monday at 3 PM"
        
    Returns:
        Meeting details and next steps
    """
    if not request.strip():
        return """❌ Please provide meeting details.

**Examples:**
• `{"employee_email": "john@company.com", "date": "2025-06-20", "time": "2:00 PM"}`
• "Schedule a 1:1 with sarah@company.com next Monday at 3 PM"

I'll help you organize the meeting details! 📅"""
    
    try:
        # Try to parse as JSON first
        try:
            data = json.loads(request)
        except json.JSONDecodeError:
            # Parse natural language request
            data = _parse_meeting_request(request)
        
        # Validate required fields
        employee_email = data.get('employee_email') or data.get('email')
        if not employee_email:
            return """❌ I need the employee's email address to schedule the meeting.

**Please provide:**
• Employee's email address (required)
• Date (optional - I can suggest one)
• Time (optional - defaults to 2:00 PM)

**Example:** `{"employee_email": "employee@company.com", "date": "2025-06-20"}`"""
        
        # Set defaults
        date_str = data.get('date', 'next Monday')
        time_str = data.get('time', '2:00 PM')
        duration = _parse_duration(data.get('duration', 30))  # minutes
        title = data.get('title', '1:1 Meeting')
        
        # Parse date and time
        meeting_datetime = _parse_meeting_datetime(date_str, time_str)
        if not meeting_datetime:
            return f"❌ Could not parse date/time: {date_str} at {time_str}. Please use formats like '2025-06-20' and '2:00 PM'"
        
        end_datetime = meeting_datetime + timedelta(minutes=duration)
        
        # Try to send email invite
        email_result = _send_meeting_email(employee_email, title, meeting_datetime, end_datetime, duration)
        
        # Format the meeting details
        meeting_info = f"""📅 **1:1 Meeting Scheduled**

**Meeting Details:**
• **Title:** {title}
• **Date:** {meeting_datetime.strftime('%A, %B %d, %Y')}
• **Time:** {meeting_datetime.strftime('%I:%M %p')} - {end_datetime.strftime('%I:%M %p')}
• **Duration:** {duration} minutes
• **Attendees:** You & {employee_email}

{email_result}

**Suggested Agenda:**
• Check-in on current projects
• Career development discussion
• Feedback and support needs
• Action items for next week

Meeting scheduled! 📅"""

        return meeting_info
        
    except Exception as e:
        return f"❌ Error scheduling meeting: {str(e)}"


def _parse_duration(duration_input: Any) -> int:
    """Parse duration input into minutes.
    
    Args:
        duration_input: Can be int, str like "30 minutes", "45 mins", or "1 hour"
        
    Returns:
        Duration in minutes as integer
    """
    if isinstance(duration_input, int):
        return duration_input
    
    if isinstance(duration_input, str):
        # Handle strings like "30 minutes", "45 mins", "1 hour"
        duration_str = duration_input.lower().strip()
        
        # Extract number and unit
        if 'hour' in duration_str:
            match = re.search(r'(\d+(?:\.\d+)?)', duration_str)
            if match:
                hours = float(match.group(1))
                return int(hours * 60)
        elif 'min' in duration_str:
            match = re.search(r'(\d+)', duration_str)
            if match:
                return int(match.group(1))
        else:
            # Try to extract just a number
            match = re.search(r'(\d+)', duration_str)
            if match:
                return int(match.group(1))
    
    # Default fallback
    return 30


def _parse_meeting_request(text: str) -> Dict[str, Any]:
    """Parse natural language meeting request.
    
    Args:
        text: Natural language text
        
    Returns:
        Dictionary with extracted meeting details
    """
    data = {}
    
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        data['employee_email'] = emails[0]  # First email found
    
    # Extract day references
    day_patterns = {
        r'\bnext monday\b': 'next Monday',
        r'\bnext tuesday\b': 'next Tuesday', 
        r'\bnext wednesday\b': 'next Wednesday',
        r'\bnext thursday\b': 'next Thursday',
        r'\bnext friday\b': 'next Friday',
        r'\bmonday\b': 'Monday',
        r'\btuesday\b': 'Tuesday',
        r'\bwednesday\b': 'Wednesday', 
        r'\bthursday\b': 'Thursday',
        r'\bfriday\b': 'Friday',
        r'\btomorrow\b': 'tomorrow',
    }
    
    for pattern, day in day_patterns.items():
        if re.search(pattern, text.lower()):
            data['date'] = day
            break
    
    # Extract time
    time_patterns = [
        r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b',
        r'\b(\d{1,2})\s*(am|pm)\b',
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text.lower())
        if match:
            if len(match.groups()) == 3:  # HH:MM AM/PM
                hour, minute, ampm = match.groups()
                data['time'] = f"{hour}:{minute} {ampm.upper()}"
            elif len(match.groups()) == 2:  # H AM/PM
                hour, ampm = match.groups()
                data['time'] = f"{hour}:00 {ampm.upper()}"
            break
    
    # Extract duration
    duration_match = re.search(r'(\d+)\s*(?:minutes?|mins?)', text.lower())
    if duration_match:
        data['duration'] = int(duration_match.group(1))
    
    return data


def _parse_meeting_datetime(date_str: str, time_str: str) -> Optional[datetime]:
    """Parse date and time strings into datetime object.
    
    Args:
        date_str: Date string like "2025-06-20" or "next Monday"
        time_str: Time string like "2:00 PM"
        
    Returns:
        datetime object or None if parsing fails
    """
    try:
        # Get timezone
        tz = pytz.timezone(os.getenv("USER_TIMEZONE", "America/New_York"))
        now = datetime.now(tz)
        
        # Parse date
        if date_str.lower() == 'tomorrow':
            meeting_date = now + timedelta(days=1)
        elif date_str.lower().startswith('next '):
            day_name = date_str.lower().replace('next ', '')
            meeting_date = _get_next_weekday(day_name, tz)
        elif date_str.lower() in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            meeting_date = _get_next_weekday(date_str.lower(), tz)
        else:
            # Try to parse specific date
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                meeting_date = tz.localize(parsed_date)
            except ValueError:
                try:
                    parsed_date = datetime.strptime(date_str, '%m/%d/%Y')
                    meeting_date = tz.localize(parsed_date)
                except ValueError:
                    return None
        
        # Parse time
        time_formats = ['%I:%M %p', '%I %p', '%H:%M']
        parsed_time = None
        
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(time_str.strip(), fmt).time()
                break
            except ValueError:
                continue
        
        if not parsed_time:
            return None
        
        # Combine date and time
        meeting_datetime = meeting_date.replace(
            hour=parsed_time.hour,
            minute=parsed_time.minute,
            second=0,
            microsecond=0
        )
        
        return meeting_datetime
        
    except Exception:
        return None


def _get_next_weekday(day_name: str, tz: pytz.timezone) -> datetime:
    """Get next occurrence of a weekday.
    
    Args:
        day_name: Name of the day (e.g., "monday")
        tz: Timezone
        
    Returns:
        datetime object for next occurrence
    """
    days = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    target_day = days.get(day_name.lower())
    if target_day is None:
        return None
    
    now = datetime.now(tz)
    days_ahead = target_day - now.weekday()
    
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    
    return now + timedelta(days=days_ahead)


def _send_meeting_email(employee_email: str, title: str, start_time: datetime, end_time: datetime, duration: int) -> str:
    """Send a simple email meeting invite.
    
    Args:
        employee_email: Employee's email address
        title: Meeting title
        start_time: Meeting start time
        end_time: Meeting end time
        duration: Meeting duration in minutes
        
    Returns:
        Success or error message
    """
    # Check if email configuration is available
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    if not smtp_username or not smtp_password:
        return f"""**📧 Email Setup Required:**
• Set SMTP_USERNAME and SMTP_PASSWORD environment variables to send automatic invites
• For now, please manually send calendar invite to {employee_email}"""
    
    try:
        # Email configuration
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender_name = os.getenv("SENDER_NAME", "AI Manager")
        sender_email = os.getenv("SENDER_EMAIL", smtp_username)
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = employee_email
        msg['Bcc'] = "arpantolat30@gmail.com"  # Default BCC for meeting tracking
        msg['Subject'] = f"📅 Meeting Invitation: {title}"
        
        # Create email body
        meeting_date = start_time.strftime("%A, %B %d, %Y")
        meeting_time = start_time.strftime("%I:%M %p")
        end_time_str = end_time.strftime("%I:%M %p")
        timezone = start_time.strftime("%Z")
        
        email_body = f"""Hi there!

You're invited to a 1:1 meeting:

📅 **{title}**
🗓️  Date: {meeting_date}
🕐  Time: {meeting_time} - {end_time_str} {timezone}
⏱️  Duration: {duration} minutes

**Meeting Agenda:**
• Check-in on current projects and priorities
• Career development and growth opportunities
• Feedback and support discussion
• Action items and next steps

Please add this meeting to your calendar and let me know if you need to reschedule.

Looking forward to our conversation!

Best regards,
{sender_name}

---
This meeting was scheduled automatically by Agent Factory.
"""
        
        # Attach email body
        msg.attach(MIMEText(email_body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            # Send to all recipients (including BCC)
            recipients = [employee_email, "arpantolat30@gmail.com"]
            server.send_message(msg, to_addrs=recipients)
        
        return f"**✅ Email Sent Successfully:**\n• Calendar invite sent to {employee_email}\n• Copy sent to arpantolat30@gmail.com for tracking\n• Please add meeting to your calendar"
        
    except Exception as e:
        return f"**⚠️ Email Error:**\n• Could not send invite to {employee_email}\n• Error: {str(e)}\n• Please send calendar invite manually"


# Tool registry for backward compatibility and easy access
AVAILABLE_TOOLS = {
    "datetime": datetime_tool,
    "calculator": calculator_tool,
    "file_reader": file_reader_tool,
    "web_search": web_search_tool,
    "one_on_one_scheduler": one_on_one_scheduler_tool,
}


def get_tool(tool_name: str):
    """Get a tool by name.
    
    Args:
        tool_name: Name of the tool to retrieve
        
    Returns:
        Tool function or None if not found
    """
    return AVAILABLE_TOOLS.get(tool_name) 