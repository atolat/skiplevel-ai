"""Simple tool system for Agent Factory."""

import ast
import operator
import os
import re
import json
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import pytz


class BaseTool(ABC):
    """Abstract base class for tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @abstractmethod
    def execute(self, input_data: str) -> str:
        """Execute the tool with input data.
        
        Args:
            input_data: Input string for the tool
            
        Returns:
            Tool execution result as string
        """
        pass


class DateTimeTool(BaseTool):
    """Tool for getting current date, time, and timezone information."""
    
    name = "datetime"
    description = "Get current date, time, timezone, and day of week information"
    
    def __init__(self, user_timezone: str = None):
        """Initialize with optional user timezone.
        
        Args:
            user_timezone: User's timezone (e.g., 'America/New_York', 'Europe/London')
        """
        self.user_timezone = user_timezone or os.getenv("USER_TIMEZONE", "America/New_York")
    
    def execute(self, input_data: str = "") -> str:
        """Get current date and time information.
        
        Args:
            input_data: Optional timezone override
            
        Returns:
            Formatted date/time information
        """
        try:
            # Use provided timezone or default
            timezone_name = input_data.strip() if input_data.strip() else self.user_timezone
            
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


class CalculatorTool(BaseTool):
    """Simple calculator tool for mathematical operations."""
    
    name = "calculator"
    description = "Perform mathematical calculations and operations"
    
    def execute(self, input_data: str) -> str:
        """Execute mathematical calculation.
        
        Args:
            input_data: Mathematical expression to evaluate
            
        Returns:
            Calculation result or error message
        """
        if not input_data.strip():
            return "Error: Please provide a mathematical expression to calculate"
        
        try:
            # Parse the expression safely
            result = self._safe_eval(input_data.strip())
            return f"Result: {input_data} = {result}"
        except Exception as e:
            return f"Error: Invalid mathematical expression - {str(e)}"
    
    def _safe_eval(self, expression: str) -> float:
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


class FileReaderTool(BaseTool):
    """Tool for reading and analyzing text files."""
    
    name = "file_reader"
    description = "Read and analyze the contents of text files"
    
    def execute(self, input_data: str) -> str:
        """Read file contents.
        
        Args:
            input_data: File path to read
            
        Returns:
            File contents or error message
        """
        if not input_data.strip():
            return "Error: Please provide a file path to read"
        
        file_path = input_data.strip()
        
        # Security check - only allow reading from certain directories
        if not self._validate_file_path(file_path):
            return "Error: Access denied - file path not allowed for security reasons"
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                return f"Error: File not found - {file_path}"
            
            if not path.is_file():
                return f"Error: Path is not a file - {file_path}"
            
            # Check file size (limit to 1MB)
            if path.stat().st_size > 1024 * 1024:
                return "Error: File too large (max 1MB allowed)"
            
            # Read file contents
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Provide file analysis
            lines = content.split('\n')
            word_count = len(content.split())
            char_count = len(content)
            
            result = f"""File: {file_path}
Size: {char_count} characters, {word_count} words, {len(lines)} lines

Content:
{content}"""
            
            return result
            
        except UnicodeDecodeError:
            return f"Error: Cannot read file - appears to be binary or non-UTF-8 encoded"
        except PermissionError:
            return f"Error: Permission denied reading file - {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def _validate_file_path(self, file_path: str) -> bool:
        """Validate that file path is safe to read.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if path is safe to read
        """
        # Convert to Path object for easier manipulation
        try:
            path = Path(file_path).resolve()
        except Exception:
            return False
        
        # Get current working directory
        cwd = Path.cwd().resolve()
        
        # Only allow reading files within the current working directory
        try:
            path.relative_to(cwd)
            return True
        except ValueError:
            return False


class WebSearchTool(BaseTool):
    """Web search tool with AI-powered result synthesis."""
    
    name = "web_search"
    description = "Search the web and synthesize results using AI"
    
    def __init__(self, llm=None):
        """Initialize with optional LLM for result synthesis.
        
        Args:
            llm: Language model instance for synthesizing results
        """
        self.llm = llm
    
    def execute(self, input_data: str) -> str:
        """Execute web search and synthesize results.
        
        Args:
            input_data: Search query
            
        Returns:
            Search results or synthesized summary
        """
        if not input_data.strip():
            return "Error: Please provide a search query"
        
        query = input_data.strip()
        
        try:
            # Perform web search
            search_results = self._search_web(query)
            
            if not search_results:
                return f"No search results found for: {query}"
            
            # If LLM is available, synthesize results
            if self.llm:
                return self._synthesize_results(query, search_results)
            else:
                # Return raw results if no LLM available
                return self._format_raw_results(query, search_results)
                
        except Exception as e:
            return f"Error performing web search: {str(e)}"
    
    def _search_web(self, query: str) -> list:
        """Perform web search using a search API.
        
        Args:
            query: Search query string
            
        Returns:
            List of search result dictionaries
        """
        # This is a placeholder implementation
        # In a real implementation, you would integrate with:
        # - Google Custom Search API
        # - Bing Search API
        # - DuckDuckGo API
        # - SerpAPI
        
        # For now, return mock results
        return [
            {
                "title": f"Search result for: {query}",
                "url": "https://example.com",
                "snippet": f"This is a mock search result for the query '{query}'. In a real implementation, this would contain actual web search results."
            }
        ]
    
    def _synthesize_results(self, query: str, results: list) -> str:
        """Use LLM to synthesize search results into a coherent summary.
        
        Args:
            query: Original search query
            results: List of search result dictionaries
            
        Returns:
            Synthesized summary of results
        """
        if not self.llm:
            return self._format_raw_results(query, results)
        
        # Prepare results for LLM
        results_text = ""
        for i, result in enumerate(results[:5], 1):  # Limit to top 5 results
            results_text += f"{i}. {result['title']}\n   {result['snippet']}\n   Source: {result['url']}\n\n"
        
        # Create synthesis prompt
        prompt = f"""Based on the following web search results for the query "{query}", provide a comprehensive and accurate summary of the key information found. Focus on the most relevant and reliable information.

Search Results:
{results_text}

Please provide:
1. A clear summary of the main findings
2. Key insights or important details
3. Any relevant recommendations or next steps
4. Source citations where appropriate

Summary:"""
        
        try:
            # Generate synthesis using LLM
            synthesis = self.llm.generate(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=500
            )
            
            return f"🔍 **Web Search Results for: {query}**\n\n{synthesis}\n\n📚 **Sources:** {len(results)} results found"
            
        except Exception as e:
            # Fall back to raw results if LLM fails
            return f"Search completed but synthesis failed: {str(e)}\n\n" + self._format_raw_results(query, results)
    
    def _format_raw_results(self, query: str, results: list) -> str:
        """Format raw search results without LLM synthesis.
        
        Args:
            query: Original search query
            results: List of search result dictionaries
            
        Returns:
            Formatted search results
        """
        formatted = f"🔍 **Search Results for: {query}**\n\n"
        
        for i, result in enumerate(results[:5], 1):
            formatted += f"**{i}. {result['title']}**\n"
            formatted += f"   {result['snippet']}\n"
            formatted += f"   🔗 {result['url']}\n\n"
        
        formatted += f"📊 Found {len(results)} total results"
        
        return formatted


# Tool registry
_TOOLS: Dict[str, BaseTool] = {
    "datetime": DateTimeTool(),
    "calculator": CalculatorTool(),
    "file_reader": FileReaderTool(),
    "web_search": WebSearchTool(),  # Will be re-initialized with LLM by agent
}

# Import and register calendar tool if available
try:
    from .calendar_tools import OneOnOneScheduler
    _TOOLS["one_on_one_scheduler"] = OneOnOneScheduler()
except ImportError:
    # Calendar tool dependencies not available
    pass


def get_tool(tool_name: str) -> Optional[BaseTool]:
    """Get a tool instance by name.
    
    Args:
        tool_name: Name of the tool to retrieve
        
    Returns:
        Tool instance or None if not found
    """
    return _TOOLS.get(tool_name.lower()) 