"""
Interactive MCP Client
Provides an interactive shell to test MCP server tools.
"""

import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage


class BedrockSummarizer:
    """Summarizes MCP tool results using AWS Bedrock via LangChain."""
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region: str = "ap-southeast-2"
    ):
        self.model_id = model_id
        self.region = region
        self.llm = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize LangChain Bedrock client lazily."""
        if not self._initialized:
            try:
                self.llm = ChatBedrock(
                    model_id=self.model_id,
                    region_name=self.region,
                    model_kwargs={
                        "max_tokens": 500,
                        "temperature": 0.3,  # Lower temperature for more focused summaries
                    }
                )
                self._initialized = True
                print("✓ AWS Bedrock summarization enabled\n")
            except Exception as e:
                print(f"⚠️  Failed to initialize Bedrock: {e}")
                print("   Continuing without summarization...\n")
    
    def summarize(self, tool_name: str, result_data: dict) -> str:
        """Convert JSON result to natural language using LangChain + Bedrock.
        
        Args:
            tool_name: Name of the tool that was executed
            result_data: The JSON result from the tool
            
        Returns:
            Human-readable natural language summary
        """
        if not self._initialized:
            self._initialize()
        
        if not self._initialized:
            return "Summary unavailable (Bedrock not initialized)"
        
        try:
            # Create a prompt for natural language conversion
            prompt = self._create_summary_prompt(tool_name, result_data)
            
            # Use LangChain to invoke Bedrock
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])
            
            # Extract the natural language summary
            summary = response.content.strip()
            
            return summary
            
        except Exception as e:
            return f"Error generating summary: {e}"
    
    def _create_summary_prompt(self, tool_name: str, result_data: dict) -> str:
        """Create a prompt for summarizing tool results."""
        result_json = json.dumps(result_data, indent=2)
        
        # Truncate if too long
        if len(result_json) > 8000:
            result_json = result_json[:8000] + "\n... (truncated)"
        
        prompt = f"""You are analyzing the results of a code analysis tool.

Tool: {tool_name}
Result:
{result_json}

Provide a concise, human-readable summary that highlights:
1. Key statistics (e.g., "Found X usages", "Analyzed Y files")
2. Important findings or patterns
3. Any notable insights or recommendations

Keep the summary under 5 sentences. Focus on actionable information."""
        
        return prompt


class InteractiveMCPClient:
    """Interactive client for testing MCP server."""
    
    def __init__(self):
        self.session = None
        self.tools = []
        self.summarizer = BedrockSummarizer()
        self.enable_summary = os.getenv("ENABLE_SUMMARY", "true").lower() == "true"
    
    async def connect(self):
        """Connect to the MCP server."""
        print("Connecting to MCP server...")
        
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "src.mcp_server.server"],
            env=None
        )
        
        self.stack = AsyncExitStack()
        stdio_transport = await self.stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        self.session = await self.stack.enter_async_context(ClientSession(stdio, write))
        
        await self.session.initialize()
        
        # Get available tools
        tools_response = await self.session.list_tools()
        self.tools = tools_response.tools
        
        print(f"✓ Connected! Found {len(self.tools)} tools\n")
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.stack:
            await self.stack.aclose()
    
    def show_tools(self):
        """Display available tools."""
        print("\n" + "="*60)
        print("Available Tools:")
        print("="*60)
        
        # Group by category
        fast_tools = []
        slow_tools = []
        
        for i, tool in enumerate(self.tools, 1):
            if any(keyword in tool.description.lower() for keyword in ['fast', 'synchronous']):
                fast_tools.append((i, tool))
            else:
                slow_tools.append((i, tool))
        
        if fast_tools:
            print("\n📊 Fast Tools (Code Scout):")
            for i, tool in fast_tools:
                print(f"  {i}. {tool.name}")
                print(f"     {tool.description}")
        
        if slow_tools:
            print("\n🤖 Slow Tools (Refactoring Crew - requires AWS):")
            for i, tool in slow_tools:
                print(f"  {i}. {tool.name}")
                print(f"     {tool.description}")
        
        print("\n" + "="*60 + "\n")
    
    async def call_tool(self, tool_name, arguments):
        """Call a specific tool."""
        try:
            print(f"\nCalling tool: {tool_name}")
            print(f"Arguments: {json.dumps(arguments, indent=2)}")
            print("\nExecuting...")
            
            # Add timeout for long-running operations
            result = await asyncio.wait_for(
                self.session.call_tool(tool_name, arguments=arguments),
                timeout=300.0  # 5 minute timeout
            )
            
            # Parse and display result
            response_text = result.content[0].text
            parsed_json = None
            response_data = None
            try:
                parsed_json = json.loads(response_text)
            except json.JSONDecodeError:
                parsed_json = None
            
            # If server returns natural language (non-JSON), just print it
            if parsed_json is None:
                print("\n" + "="*60)
                print("Result (natural language from server):")
                print("="*60)
                print(response_text)
                print("="*60 + "\n")
                response_data = response_text
                # Skip client-side summarization because server already formatted it
            else:
                print("\n" + "="*60)
                print("Result:")
                print("="*60)
                print(json.dumps(parsed_json, indent=2))
                print("="*60 + "\n")
                
                # Generate AI summary if enabled and we have raw JSON
                if self.enable_summary:
                    print("\n" + "="*60)
                    print("🤖 AI Summary (AWS Bedrock):")
                    print("="*60)
                    summary = self.summarizer.summarize(tool_name, parsed_json)
                    print(summary)
                    print("="*60 + "\n")
                response_data = parsed_json
            
            return response_data
            
        except asyncio.TimeoutError:
            print(f"\n✗ Error: Operation timed out after 5 minutes\n")
            print("Tip: For GitHub URLs, try cloning locally first.\n")
            return None
        except KeyboardInterrupt:
            print(f"\n✗ Operation cancelled by user\n")
            raise  # Re-raise to handle in main loop
        except Exception as e:
            print(f"\n✗ Error: {e}\n")
            return None
    
    async def run_interactive(self):
        """Run interactive shell."""
        await self.connect()
        
        print("\n" + "="*60)
        print("Interactive MCP Client")
        print("Legacy Code Modernizer Server")
        print("="*60)
        print("\nCommands:")
        print("  list    - Show available tools")
        print("  scan    - Scan directory (local paths recommended)")
        print("  find    - Find symbol usages")
        print("  grep    - Grep search")
        print("  graph   - Build dependency graph")
        print("  summary - Toggle AI summary (currently: " + ("ON" if self.enable_summary else "OFF") + ")")
        print("  help    - Show GitHub URL usage tips")
        print("  quit    - Exit")
        print("="*60 + "\n")
        
        while True:
            try:
                command = input("mcp> ").strip().lower()
                
                if not command:
                    continue
                
                if command == "quit" or command == "exit":
                    print("Goodbye!")
                    break
                
                elif command == "list":
                    self.show_tools()
                
                elif command == "scan":
                    path = input("Directory path (default: .): ").strip() or "."
                    
                    # Warn if GitHub URL
                    if path.startswith("http") and "github.com" in path:
                        print("\n⚠️  GitHub URL detected!")
                        print("This will clone the entire repository (can be slow).")
                        print("\nRecommendation: Clone locally first:")
                        print(f"  git clone {path} /tmp/repo")
                        print("  Then scan: /tmp/repo\n")
                        
                        choice = input("Continue anyway? (y/n): ").strip().lower()
                        if choice != 'y':
                            print("Cancelled.")
                            continue
                        
                        # Ask for GitHub token if private repo
                        token = input("GitHub token (press Enter if public repo): ").strip()
                    
                    pattern = input("File pattern (default: *.py): ").strip() or "*.py"
                    
                    args = {"root_directory": path, "pattern": pattern}
                    if path.startswith("http") and token:
                        args["github_token"] = token
                    
                    await self.call_tool("scan_directory", args)
                
                elif command == "find":
                    path = input("Directory path (default: .): ").strip() or "."
                    symbol = input("Symbol name: ").strip()
                    
                    if symbol:
                        await self.call_tool("find_symbol", {
                            "root_directory": path,
                            "symbol_name": symbol
                        })
                    else:
                        print("Symbol name is required")
                
                elif command == "grep":
                    path = input("Directory path (default: .): ").strip() or "."
                    pattern = input("Search pattern: ").strip()
                    file_pattern = input("File pattern (default: *.py): ").strip() or "*.py"
                    
                    if pattern:
                        await self.call_tool("grep_search", {
                            "root_directory": path,
                            "pattern": pattern,
                            "file_pattern": file_pattern
                        })
                    else:
                        print("Search pattern is required")
                
                elif command == "graph":
                    path = input("Directory path (default: .): ").strip() or "."
                    
                    await self.call_tool("build_dependency_graph", {
                        "root_directory": path
                    })
                
                elif command == "summary":
                    self.enable_summary = not self.enable_summary
                    status = "enabled" if self.enable_summary else "disabled"
                    print(f"\n🤖 AI summary {status}\n")
                
                elif command == "help":
                    print("\n" + "="*60)
                    print("GitHub URL Support")
                    print("="*60)
                    print("\n🔧 How to use GitHub repositories:\n")
                    print("Option 1: Clone Locally First (Recommended)")
                    print("  $ git clone https://github.com/owner/repo /tmp/repo")
                    print("  $ # Then in MCP client:")
                    print("  mcp> scan")
                    print("  Directory path: /tmp/repo\n")
                    print("Option 2: Direct GitHub URL (Slower)")
                    print("  mcp> scan")
                    print("  Directory path: https://github.com/owner/repo")
                    print("  # Server clones repo to temp dir automatically\n")
                    print("Option 3: Single File Analysis")
                    print("  # Use analyze_and_plan tool for single files")
                    print("  # URL: https://github.com/owner/repo/blob/main/file.py\n")
                    print("⚡ Performance Tips:")
                    print("  - Local paths are ~10x faster")
                    print("  - scan, find, grep work on cloned repos")
                    print("  - Use GitHub token for private repos\n")
                    print("="*60 + "\n")
                
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'list' for commands or 'help' for GitHub tips")
            
            except KeyboardInterrupt:
                print("\n\nUse 'quit' to exit")
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        await self.disconnect()


async def main():
    """Main entry point."""
    client = InteractiveMCPClient()
    await client.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
