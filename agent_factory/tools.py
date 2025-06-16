"""Simple tool system for Agent Factory."""

import ast
import operator
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional


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


# Tool registry
_TOOLS: Dict[str, BaseTool] = {
    "calculator": CalculatorTool(),
    "file_reader": FileReaderTool(),
}


def get_tool(tool_name: str) -> Optional[BaseTool]:
    """Get a tool instance by name.
    
    Args:
        tool_name: Name of the tool to retrieve
        
    Returns:
        Tool instance or None if not found
    """
    return _TOOLS.get(tool_name.lower()) 