"""
MCP Server Wrapper
Exposes both Code Scout (fast) and Refactoring Crew (slow) agents via MCP protocol.
"""

import asyncio
import json
from typing import Any, Dict, Optional
from functools import wraps
from dataclasses import dataclass, asdict
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.code_scout import CodeScout
from agents.refactoring_crew import RefactoringCrew


@dataclass
class MCPWrapperConfig:
    """Configuration for MCP wrapper decorators."""
    is_long_running: bool
    timeout: Optional[int] = None  # Timeout in seconds
    cache_results: bool = False


def mcp_wrapper(config: MCPWrapperConfig):
    """
    Decorator to wrap agent methods for MCP exposure.
    
    Args:
        config: MCPWrapperConfig with is_long_running flag and other options
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if config.is_long_running:
                # Run in background for long-running tasks
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, func, *args, **kwargs)
            else:
                # Run synchronously for fast tasks
                return func(*args, **kwargs)
        
        # Attach metadata
        async_wrapper._mcp_config = config
        async_wrapper._original_func = func
        
        return async_wrapper
    return decorator


class LegacyCodeModernizerServer:
    """
    MCP Server exposing Code Scout and Refactoring Crew agents.
    """
    
    def __init__(self):
        self.server = Server("legacy-code-modernizer")
        self.code_scout: Optional[CodeScout] = None
        self.refactoring_crew: Optional[RefactoringCrew] = None
        
        # Register tools
        self._register_tools()
        self._register_handlers()
    
    def _register_tools(self):
        """Register all available tools."""
        
        # Fast tools (Code Scout)
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="scan_directory",
                    description="Scan a directory for Python files and analyze symbol usages. Fast synchronous operation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "root_directory": {
                                "type": "string",
                                "description": "Path to the root directory to scan"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "File pattern to match (default: *.py)",
                                "default": "*.py"
                            }
                        },
                        "required": ["root_directory"]
                    }
                ),
                Tool(
                    name="find_symbol",
                    description="Find all usages of a specific symbol in the codebase. Fast synchronous operation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "root_directory": {
                                "type": "string",
                                "description": "Path to the root directory"
                            },
                            "symbol_name": {
                                "type": "string",
                                "description": "Name of the symbol to find"
                            }
                        },
                        "required": ["root_directory", "symbol_name"]
                    }
                ),
                Tool(
                    name="analyze_impact",
                    description="Analyze the impact of changing a symbol. Fast synchronous operation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "root_directory": {
                                "type": "string",
                                "description": "Path to the root directory"
                            },
                            "symbol_name": {
                                "type": "string",
                                "description": "Name of the symbol to analyze"
                            }
                        },
                        "required": ["root_directory", "symbol_name"]
                    }
                ),
                Tool(
                    name="grep_search",
                    description="Perform a grep search for a pattern. Fast synchronous operation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "root_directory": {
                                "type": "string",
                                "description": "Path to the root directory"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "Pattern to search for"
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "File pattern to search in (default: *.py)",
                                "default": "*.py"
                            }
                        },
                        "required": ["root_directory", "pattern"]
                    }
                ),
                Tool(
                    name="git_blame",
                    description="Get git blame information for a specific line. Fast synchronous operation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "root_directory": {
                                "type": "string",
                                "description": "Path to the root directory"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file"
                            },
                            "line_number": {
                                "type": "integer",
                                "description": "Line number to blame"
                            }
                        },
                        "required": ["root_directory", "file_path", "line_number"]
                    }
                ),
                Tool(
                    name="build_dependency_graph",
                    description="Build a dependency graph from symbol usages. Fast synchronous operation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "root_directory": {
                                "type": "string",
                                "description": "Path to the root directory"
                            }
                        },
                        "required": ["root_directory"]
                    }
                ),
                # Slow tools (Refactoring Crew)
                Tool(
                    name="analyze_and_plan",
                    description="Analyze code and create a refactoring plan using AI. Slow asynchronous operation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The legacy code to analyze"
                            },
                            "context": {
                                "type": "string",
                                "description": "Additional context about the code (optional)"
                            },
                            "aws_region": {
                                "type": "string",
                                "description": "AWS region for Bedrock (default: us-east-1)",
                                "default": "us-east-1"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="refactor_code",
                    description="Refactor code based on a plan using AI. Slow asynchronous operation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The original code to refactor"
                            },
                            "plan": {
                                "type": "string",
                                "description": "The refactoring plan"
                            },
                            "aws_region": {
                                "type": "string",
                                "description": "AWS region for Bedrock (default: us-east-1)",
                                "default": "us-east-1"
                            }
                        },
                        "required": ["code", "plan"]
                    }
                ),
                Tool(
                    name="full_refactoring_workflow",
                    description="Execute complete refactoring: analyze, plan, and refactor. Slow asynchronous operation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The legacy code to refactor"
                            },
                            "context": {
                                "type": "string",
                                "description": "Additional context about the code (optional)"
                            },
                            "aws_region": {
                                "type": "string",
                                "description": "AWS region for Bedrock (default: us-east-1)",
                                "default": "us-east-1"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="generate_tests",
                    description="Generate unit tests for refactored code using AI. Slow asynchronous operation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Original code"
                            },
                            "refactored_code": {
                                "type": "string",
                                "description": "Refactored version"
                            },
                            "aws_region": {
                                "type": "string",
                                "description": "AWS region for Bedrock (default: us-east-1)",
                                "default": "us-east-1"
                            }
                        },
                        "required": ["code", "refactored_code"]
                    }
                ),
                Tool(
                    name="architectural_review",
                    description="Perform architectural review of a codebase using AI. Slow asynchronous operation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "codebase_description": {
                                "type": "string",
                                "description": "Description of the codebase structure"
                            },
                            "aws_region": {
                                "type": "string",
                                "description": "AWS region for Bedrock (default: us-east-1)",
                                "default": "us-east-1"
                            }
                        },
                        "required": ["codebase_description"]
                    }
                )
            ]
    
    def _register_handlers(self):
        """Register tool call handlers."""
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls."""
            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]
    
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool based on its name."""
        
        # Code Scout tools (Fast - Synchronous)
        if name in ["scan_directory", "find_symbol", "analyze_impact", "grep_search", 
                    "git_blame", "build_dependency_graph"]:
            return await self._execute_code_scout_tool(name, arguments)
        
        # Refactoring Crew tools (Slow - Asynchronous)
        elif name in ["analyze_and_plan", "refactor_code", "full_refactoring_workflow",
                      "generate_tests", "architectural_review"]:
            return await self._execute_refactoring_crew_tool(name, arguments)
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    @mcp_wrapper(MCPWrapperConfig(is_long_running=False))
    async def _execute_code_scout_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute Code Scout tools (fast, synchronous)."""
        root_dir = arguments.get("root_directory")
        
        if not root_dir:
            raise ValueError("root_directory is required")
        
        # Initialize scout if needed
        if not self.code_scout or self.code_scout.root_directory != root_dir:
            self.code_scout = CodeScout(root_dir)
        
        if name == "scan_directory":
            pattern = arguments.get("pattern", "*.py")
            result = self.code_scout.scan_directory(pattern)
            # Convert to serializable format
            return {
                symbol: [asdict(usage) for usage in usages]
                for symbol, usages in result.items()
            }
        
        elif name == "find_symbol":
            symbol_name = arguments.get("symbol_name")
            if not symbol_name:
                raise ValueError("symbol_name is required")
            
            # Ensure we have scanned first
            if not self.code_scout.symbol_usages:
                self.code_scout.scan_directory()
            
            result = self.code_scout.find_symbol(symbol_name)
            return [asdict(usage) for usage in result]
        
        elif name == "analyze_impact":
            symbol_name = arguments.get("symbol_name")
            if not symbol_name:
                raise ValueError("symbol_name is required")
            
            # Ensure we have scanned first
            if not self.code_scout.symbol_usages:
                self.code_scout.scan_directory()
            
            return self.code_scout.analyze_impact(symbol_name)
        
        elif name == "grep_search":
            pattern = arguments.get("pattern")
            file_pattern = arguments.get("file_pattern", "*.py")
            if not pattern:
                raise ValueError("pattern is required")
            
            return self.code_scout.grep_search(pattern, file_pattern)
        
        elif name == "git_blame":
            file_path = arguments.get("file_path")
            line_number = arguments.get("line_number")
            if not file_path or line_number is None:
                raise ValueError("file_path and line_number are required")
            
            return self.code_scout.git_blame(file_path, line_number)
        
        elif name == "build_dependency_graph":
            # Ensure we have scanned first
            if not self.code_scout.symbol_usages:
                self.code_scout.scan_directory()
            
            graph = self.code_scout.build_dependency_graph()
            return {
                symbol: asdict(node)
                for symbol, node in graph.items()
            }
    
    @mcp_wrapper(MCPWrapperConfig(is_long_running=True))
    async def _execute_refactoring_crew_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute Refactoring Crew tools (slow, asynchronous)."""
        aws_region = arguments.get("aws_region", "us-east-1")
        
        # Initialize crew if needed
        if not self.refactoring_crew:
            self.refactoring_crew = RefactoringCrew(aws_region=aws_region)
        
        loop = asyncio.get_event_loop()
        
        if name == "analyze_and_plan":
            code = arguments.get("code")
            context = arguments.get("context")
            if not code:
                raise ValueError("code is required")
            
            result = await loop.run_in_executor(
                None,
                self.refactoring_crew.analyze_and_plan,
                code,
                context
            )
            return {"plan": result}
        
        elif name == "refactor_code":
            code = arguments.get("code")
            plan = arguments.get("plan")
            if not code or not plan:
                raise ValueError("code and plan are required")
            
            result = await loop.run_in_executor(
                None,
                self.refactoring_crew.refactor_code,
                code,
                plan
            )
            return {"refactored_code": result}
        
        elif name == "full_refactoring_workflow":
            code = arguments.get("code")
            context = arguments.get("context")
            if not code:
                raise ValueError("code is required")
            
            result = await loop.run_in_executor(
                None,
                self.refactoring_crew.full_refactoring_workflow,
                code,
                context
            )
            return result
        
        elif name == "generate_tests":
            code = arguments.get("code")
            refactored_code = arguments.get("refactored_code")
            if not code or not refactored_code:
                raise ValueError("code and refactored_code are required")
            
            result = await loop.run_in_executor(
                None,
                self.refactoring_crew.generate_tests,
                code,
                refactored_code
            )
            return {"test_code": result}
        
        elif name == "architectural_review":
            codebase_description = arguments.get("codebase_description")
            if not codebase_description:
                raise ValueError("codebase_description is required")
            
            result = await loop.run_in_executor(
                None,
                self.refactoring_crew.architectural_review,
                codebase_description
            )
            return {"review": result}
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    server = LegacyCodeModernizerServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
