# MCP Client Testing Guide

This guide shows how to test the Legacy Code Modernizer MCP server using the provided client tools.

## Prerequisites

- Dependencies installed: `uv sync`
- For Refactoring Crew tools: AWS credentials configured for Bedrock access

## Available Client Tools

### 1. Automated Test Suite (`mcp_client_test.py`)

Runs automated tests against all fast (Code ./start-mcp-client.shScout) tools.

```bash
uv run python examples/mcp_client_test.py
```

**What it tests:**

- ✅ Connection to MCP server
- ✅ List all available tools
- ✅ Scan directory for symbols
- ✅ Find symbol usages
- ✅ Grep search
- ✅ Build dependency graph

### 2. Interactive Client (`mcp_client_interactive.py`)

Provides an interactive shell for manual testing.

```bash
uv run python examples/mcp_client_interactive.py
```

**Available commands:**

- `list` - Show all available tools
- `scan` - Scan a directory for Python files
- `find` - Find usages of a specific symbol
- `grep` - Search for text patterns
- `graph` - Build dependency graph
- `quit` - Exit

**Example session:**

```
mcp> list
[Shows all 11 tools]

mcp> scan
Directory path (default: .): ./src
File pattern (default: *.py): *.py
[Scans and shows results]

mcp> find
Directory path (default: .): ./src
Symbol name: CodeScout
[Shows all usages of CodeScout]

mcp> quit
```

## Exposed MCP Tools

### Fast Tools (Code Scout) - No AWS Required

1. **scan_directory** - Scan directory or GitHub repo for symbols
2. **find_symbol** - Find all usages of a specific symbol
3. **analyze_impact** - Analyze impact of changing a symbol
4. **grep_search** - Fast text search
5. **git_blame** - Get git blame for a line
6. **build_dependency_graph** - Build dependency graph

### Slow Tools (Refactoring Crew) - Requires AWS Bedrock

7. **analyze_and_plan** - AI-powered refactoring plan
8. **refactor_code** - AI-powered code refactoring
9. **full_refactoring_workflow** - Complete analyze + refactor
10. **generate_tests** - Generate unit tests
11. **architectural_review** - Architectural review

## Testing with GitHub URLs

Both agents support GitHub URLs:

```python
# Code Scout
await session.call_tool("scan_directory", {
    "root_directory": "https://github.com/owner/repo",
    "github_token": "ghp_your_token"  # Optional for public repos
})

# Refactoring Crew
await session.call_tool("analyze_and_plan", {
    "code": "https://github.com/owner/repo/blob/main/file.py",
    "github_token": "ghp_your_token"  # Optional
})
```

## Manual Server Start

To start the MCP server manually:

```bash
uv run python -m src.mcp_server.server
```

The server runs as a stdio-based MCP server and communicates via stdin/stdout.

## Architecture

```
┌─────────────────────────┐
│   MCP Client (Test)     │
│  - mcp_client_test.py   │
│  - mcp_client_interactive│
└───────────┬─────────────┘
            │ MCP Protocol (stdio)
            │
┌───────────▼─────────────┐
│   MCP Server            │
│  src/mcp_server/server.py│
└───────────┬─────────────┘
            │
      ┌─────┴─────┐
      │           │
┌─────▼────┐ ┌───▼─────────┐
│Code Scout│ │Refactoring  │
│ (Fast)   │ │Crew (Slow)  │
└──────────┘ └─────────────┘
```

## Troubleshooting

### CrewAI Stream Warnings

Ignore these warnings - they're harmless cleanup messages:

```
Exception ignored on flushing sys.stdout:
ValueError: I/O operation on closed file.
```

### AWS Credentials

For Refactoring Crew tools, ensure AWS credentials are configured:

```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=ap-southeast-2
```

### No Symbols Found

If scanning returns few symbols, try:

- Scanning a directory with more Python files
- Using a different pattern (e.g., `**/*.py` for recursive)
- Checking file permissions

## Next Steps

1. ✅ Run the test suite to verify installation
2. ✅ Try the interactive client
3. Set up AWS credentials for AI features
4. Test with your own codebase
5. Integrate with Claude Desktop or other MCP clients
