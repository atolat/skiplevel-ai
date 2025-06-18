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


class CalculatorTool(BaseTool):
    """Tool for performing basic math calculations."""
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Performs basic math calculations"
    
    def execute(self, input_data: str) -> str:
        """Safely evaluate a math expression.
        
        Args:
            input_data: Math expression to evaluate
            
        Returns:
            Calculation result or error message
        """
        try:
            # Clean the input
            expression = input_data.strip()
            
            # Validate input contains only allowed characters
            if not re.match(r'^[0-9+\-*/().\s]+$', expression):
                return "Error: Invalid characters in expression. Only numbers and +, -, *, /, (, ) are allowed."
            
            # Parse and evaluate safely
            parsed = ast.parse(expression, mode='eval')
            result = self._safe_eval(parsed.body)
            
            return str(result)
            
        except ZeroDivisionError:
            return "Error: Division by zero"
        except (ValueError, SyntaxError, TypeError):
            return "Error: Invalid mathematical expression"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _safe_eval(self, node):
        """Safely evaluate an AST node with only basic math operations."""
        if isinstance(node, ast.Constant):  # Numbers
            return node.value
        elif isinstance(node, ast.BinOp):  # Binary operations
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                return left / right
            else:
                raise ValueError("Unsupported operation")
        elif isinstance(node, ast.UnaryOp):  # Unary operations (like -5)
            operand = self._safe_eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
            else:
                raise ValueError("Unsupported unary operation")
        else:
            raise ValueError("Unsupported expression")


class FileReaderTool(BaseTool):
    """Tool for reading text file contents."""
    
    @property
    def name(self) -> str:
        return "file_reader"
    
    @property
    def description(self) -> str:
        return "Reads the contents of a text file"
    
    def execute(self, input_data: str) -> str:
        """Read file contents.
        
        Args:
            input_data: File path to read
            
        Returns:
            File contents or error message
        """
        try:
            file_path = Path(input_data.strip())
            
            # Basic security check - don't allow going up directories
            if '..' in str(file_path):
                return "Error: Path traversal not allowed"
            
            # Check if file exists
            if not file_path.exists():
                return f"Error: File not found: {input_data}"
            
            # Check if it's a file (not directory)
            if not file_path.is_file():
                return f"Error: Path is not a file: {input_data}"
            
            # Read file contents
            with open(file_path, 'r', encoding='utf-8') as f:
                contents = f.read()
            
            return contents
            
        except PermissionError:
            return f"Error: Permission denied reading file: {input_data}"
        except UnicodeDecodeError:
            return f"Error: File is not a text file or has unsupported encoding: {input_data}"
        except Exception as e:
            return f"Error: Failed to read file: {str(e)}"


class WebSearchTool(BaseTool):
    """Intelligent web search tool for engineering management research."""
    
    def __init__(self, llm=None):
        """Initialize with optional LLM for intelligent query generation and synthesis.
        
        Args:
            llm: LLM instance for intelligent search and synthesis
        """
        self.llm = llm
        
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return """Intelligent web search for engineering management research and best practices.
        
        Automatically researches current industry practices, methodologies, and expert insights.
        Focuses on authoritative sources like engineering management blogs, company handbooks, 
        and industry research. Returns synthesized insights rather than raw search results.
        
        Use for: performance review frameworks, team scaling, compensation benchmarking, 
        1:1 best practices, management methodologies, industry trends."""
    
    def execute(self, input_data: str) -> str:
        """Execute intelligent web search with LLM-powered query generation and synthesis.
        
        Args:
            input_data: Search topic or question
            
        Returns:
            Synthesized research insights and recommendations
        """
        try:
            # Parse input - could be JSON or natural language
            search_topic = input_data.strip()
            if search_topic.startswith('{'):
                try:
                    data = json.loads(search_topic)
                    search_topic = data.get('topic', data.get('query', search_topic))
                except json.JSONDecodeError:
                    pass
            
            if not search_topic:
                return "❌ Please provide a search topic or question."
            
            # Generate intelligent search queries using LLM
            search_queries = self._generate_search_queries(search_topic)
            
            # Perform searches and collect results
            all_results = []
            for query in search_queries:
                results = self._perform_search(query)
                all_results.extend(results)
            
            # Filter and rank results for quality and relevance
            filtered_results = self._filter_results(all_results, search_topic)
            
            # Synthesize findings using LLM
            synthesis = self._synthesize_results(search_topic, filtered_results)
            
            return synthesis
            
        except Exception as e:
            return f"❌ Error during web search: {str(e)}"
    
    def _generate_search_queries(self, topic: str) -> list:
        """Generate targeted search queries using LLM intelligence."""
        if not self.llm:
            # Fallback to basic query generation
            return [
                f"{topic} engineering management best practices",
                f"{topic} engineering manager guide 2024",
                f"{topic} engineering leadership framework"
            ]
        
        try:
            prompt = f"""
Generate 3 targeted web search queries to research current best practices for this engineering management topic:

Topic: {topic}

Focus on finding:
- Recent articles (2022-2024) from respected engineering leaders
- Company engineering handbooks and documented practices
- Industry research and surveys
- Proven frameworks and methodologies

Generate queries that will find authoritative sources like:
- Engineering management blogs (Will Larson, Charity Majors, Camille Fournier)
- Company engineering handbooks (GitLab, Stripe, Shopify, etc.)
- Industry surveys (Stack Overflow, GitHub, etc.)
- Academic or industry research

Return ONLY a JSON array of 3 search query strings, no other text:
["query1", "query2", "query3"]
"""
            
            response = self.llm.generate(prompt, temperature=0.3, max_tokens=200)
            
            # Try to parse JSON response
            try:
                queries = json.loads(response.strip())
                if isinstance(queries, list) and len(queries) > 0:
                    return queries[:3]  # Limit to 3 queries
            except json.JSONDecodeError:
                pass
            
            # Fallback if JSON parsing fails
            return [
                f"{topic} engineering management best practices 2024",
                f"{topic} engineering manager framework guide",
                f"{topic} engineering leadership methodology"
            ]
            
        except Exception:
            # Fallback to basic queries
            return [
                f"{topic} engineering management",
                f"{topic} engineering manager guide",
                f"{topic} engineering leadership"
            ]
    
    def _perform_search(self, query: str) -> list:
        """Perform real web search using SerpAPI."""
        serpapi_key = os.getenv("SERPAPI_KEY")
        
        if not serpapi_key:
            return [{"error": "SerpAPI not configured. Set SERPAPI_KEY environment variable."}]
        
        try:
            import requests
            url = "https://serpapi.com/search.json"
            params = {
                "engine": "google",
                "q": query,
                "api_key": serpapi_key,
                "num": 5,
                "safe": "active"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("organic_results", []):
                results.append({
                    "title": item.get("title", "Unknown"),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "No description"),
                    "source": item.get("displayed_link", "Unknown")
                })
            
            return results[:5]  # Top 5 results
            
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]
    
    def _filter_results(self, results: list, topic: str) -> list:
        """Filter and rank results for quality and relevance."""
        # Prioritize authoritative sources
        authority_domains = [
            'lethain.com', 'charity.wtf', 'about.gitlab.com', 'stripe.com',
            'shopify.engineering', 'engineering.atspotify.com', 'github.blog',
            'stackoverflow.blog', 'increment.com', 'firstround.com'
        ]
        
        # Simple filtering - in real implementation, use LLM for intelligent filtering
        filtered = []
        for result in results:
            url = result.get('url', '')
            # Prioritize known authority domains
            if any(domain in url for domain in authority_domains):
                result['authority_score'] = 10
            else:
                result['authority_score'] = 5
            
            # Basic relevance check
            title_snippet = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            if any(word in title_snippet for word in topic.lower().split()):
                result['relevance_score'] = 8
            else:
                result['relevance_score'] = 3
            
            filtered.append(result)
        
        # Sort by combined score and return top results
        filtered.sort(key=lambda x: x.get('authority_score', 0) + x.get('relevance_score', 0), reverse=True)
        return filtered[:5]  # Return top 5 results
    
    def _synthesize_results(self, topic: str, results: list) -> str:
        """Synthesize search results into actionable insights using LLM."""
        if not results:
            return f"❌ No relevant results found for: {topic}"
        
        if not self.llm:
            # Fallback synthesis without LLM
            synthesis = f"## Research Findings: {topic}\n\n"
            for i, result in enumerate(results[:3], 1):
                synthesis += f"**{i}. {result.get('title', 'Unknown')}**\n"
                synthesis += f"Source: {result.get('source', 'Unknown')}\n"
                synthesis += f"{result.get('snippet', 'No description available')}\n\n"
            return synthesis
        
        try:
            # Prepare results for LLM synthesis
            results_text = ""
            for i, result in enumerate(results[:3], 1):
                results_text += f"Source {i}: {result.get('title', 'Unknown')}\n"
                results_text += f"From: {result.get('source', 'Unknown')}\n"
                results_text += f"Summary: {result.get('snippet', 'No description')}\n"
                results_text += f"URL: {result.get('url', 'No URL')}\n\n"
            
            prompt = f"""
As a Senior Engineering Manager with 8+ years of experience, synthesize these research findings into actionable insights and recommendations.

Research Topic: {topic}

Research Sources:
{results_text}

Provide a comprehensive response that:
1. Synthesizes the key insights from these authoritative sources
2. Combines research findings with practical management experience
3. Offers specific, actionable recommendations
4. References the sources appropriately
5. Maintains a professional, experienced tone

Format as a clear, well-structured response that an engineering manager can immediately apply.
Focus on practical implementation rather than theory.
"""
            
            synthesis = self.llm.generate(prompt, temperature=0.4, max_tokens=800)
            
            # Add source references at the end
            synthesis += "\n\n**Sources:**\n"
            for i, result in enumerate(results[:3], 1):
                synthesis += f"{i}. {result.get('source', 'Unknown')} - {result.get('url', 'No URL')}\n"
            
            return synthesis
            
        except Exception as e:
            # Fallback if LLM synthesis fails
            return f"❌ Error synthesizing results: {str(e)}\n\nRaw results available but synthesis failed."


# Tool registry
_TOOLS: Dict[str, BaseTool] = {
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