# Example: Using the MCP Server

This example shows how to interact with the MCP server that exposes both agents.

## Starting the Server

```bash
# Option 1: Using Docker Compose
docker-compose up

# Option 2: Direct execution
uv run python -m src.mcp_server.server
```

## MCP Client Integration

The MCP server exposes tools that can be called by any MCP-compatible client.

### Available Tools

#### Fast Tools (Code Scout)

1. **scan_directory**
```json
{
  "name": "scan_directory",
  "arguments": {
    "root_directory": "/path/to/repo",
    "pattern": "*.py"
  }
}
```

2. **find_symbol**
```json
{
  "name": "find_symbol",
  "arguments": {
    "root_directory": "/path/to/repo",
    "symbol_name": "legacy_function"
  }
}
```

3. **analyze_impact**
```json
{
  "name": "analyze_impact",
  "arguments": {
    "root_directory": "/path/to/repo",
    "symbol_name": "legacy_function"
  }
}
```

4. **grep_search**
```json
{
  "name": "grep_search",
  "arguments": {
    "root_directory": "/path/to/repo",
    "pattern": "TODO|FIXME",
    "file_pattern": "*.py"
  }
}
```

5. **git_blame**
```json
{
  "name": "git_blame",
  "arguments": {
    "root_directory": "/path/to/repo",
    "file_path": "src/main.py",
    "line_number": 42
  }
}
```

6. **build_dependency_graph**
```json
{
  "name": "build_dependency_graph",
  "arguments": {
    "root_directory": "/path/to/repo"
  }
}
```

#### Slow Tools (Refactoring Crew)

1. **analyze_and_plan**
```json
{
  "name": "analyze_and_plan",
  "arguments": {
    "code": "def old_function(): ...",
    "context": "Used in high-traffic API",
    "aws_region": "us-east-1"
  }
}
```

2. **refactor_code**
```json
{
  "name": "refactor_code",
  "arguments": {
    "code": "def old_function(): ...",
    "plan": "1. Add type hints\n2. Improve error handling...",
    "aws_region": "us-east-1"
  }
}
```

3. **full_refactoring_workflow**
```json
{
  "name": "full_refactoring_workflow",
  "arguments": {
    "code": "def old_function(): ...",
    "context": "Legacy payment processing",
    "aws_region": "us-east-1"
  }
}
```

4. **generate_tests**
```json
{
  "name": "generate_tests",
  "arguments": {
    "code": "def old_function(): ...",
    "refactored_code": "def new_function(): ...",
    "aws_region": "us-east-1"
  }
}
```

5. **architectural_review**
```json
{
  "name": "architectural_review",
  "arguments": {
    "codebase_description": "Monolithic Django app with 50k LOC...",
    "aws_region": "us-east-1"
  }
}
```

## Python Client Example

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "src.mcp_server.server"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])
            
            # Call fast tool (Code Scout)
            result = await session.call_tool(
                "find_symbol",
                arguments={
                    "root_directory": "/path/to/repo",
                    "symbol_name": "legacy_function"
                }
            )
            print("Symbol usages:", result)
            
            # Call slow tool (Refactoring Crew)
            result = await session.call_tool(
                "analyze_and_plan",
                arguments={
                    "code": "def process(x): return x * 2",
                    "context": "Used in data pipeline"
                }
            )
            print("Refactoring plan:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing the Server

```bash
# Run server health check
curl http://localhost:8080/health

# Check server logs
docker-compose logs -f legacy-code-modernizer
```

## Integration with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "legacy-code-modernizer": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "src.mcp_server.server"
      ],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "your-key",
        "AWS_SECRET_ACCESS_KEY": "your-secret"
      }
    }
  }
}
```

## Expected Response Times

- **Fast Tools**: < 1 second for most operations
- **Slow Tools**: 10-60 seconds depending on complexity
- **Full Workflow**: 2-5 minutes for complete refactoring

## Error Handling

All tools return JSON responses with error information:

```json
{
  "error": "Error message here",
  "details": "Additional context"
}
```
