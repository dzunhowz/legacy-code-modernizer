# Server-Side Natural Language Formatting Setup

## Quick Start

The MCP server automatically formats all tool responses as natural language. **No configuration needed** - it works out of the box!

```bash
# Start the MCP server
python -m src.mcp_server.server

# Your MCP client will receive formatted responses automatically
```

## What You Get

Every tool response is now **human-readable**:

### Before (Raw JSON)

```json
{
  "symbol": "validate_input",
  "count": 12,
  "occurrences": [
    {"file": "src/validators.py", "line": 45},
    ...
  ]
}
```

### After (Natural Language via Server)

```
Found 12 usages of 'validate_input' across 3 file(s)

Key locations:
  • src/validators.py: line 45
  • src/api.py: line 123
  • src/handlers.py: line 67
  ... and 9 more

============================================================
Detailed Results:
============================================================
{...full JSON included...}
```

## Features

✅ **Automatic**: Server handles formatting, clients get text  
✅ **Smart**: Different formats for different tool types  
✅ **Complete**: Raw JSON included after summary  
✅ **Fast**: Direct formatting for small results  
✅ **Smart**: Uses Bedrock for complex analyses  
✅ **Works Everywhere**: Any MCP client benefits

## Configuration

### Enable/Disable Formatting

```bash
# Enable (default)
export ENABLE_NL_FORMAT=true

# Disable (get raw JSON only)
export ENABLE_NL_FORMAT=false
```

### Use Custom Bedrock Model

```bash
export BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
export AWS_REGION=us-east-1
```

## How It Works

```python
# In src/mcp_server/server.py:

@self.server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    # 1. Execute the tool
    result = await self._execute_tool(name, arguments)

    # 2. Format as natural language
    formatted = self.nl_formatter.format_response(name, result)

    # 3. Return to client
    return [TextContent(type="text", text=formatted)]
```

## All Supported Tools

### Code Scout (Fast Tools)

| Tool                     | Input       | Output Format                         |
| ------------------------ | ----------- | ------------------------------------- |
| `scan_directory`         | Path        | File count, lines, functions, classes |
| `find_symbol`            | Symbol name | Usages list with file/line            |
| `grep_search`            | Pattern     | Matches with context                  |
| `analyze_impact`         | Symbol      | Risk level, affected areas            |
| `build_dependency_graph` | Path        | Module count, coupling issues         |
| `git_blame`              | File, line  | Author, commit, date                  |

### Refactoring Crew (Slow Tools)

| Tool                        | Input       | Output Format                    |
| --------------------------- | ----------- | -------------------------------- |
| `analyze_and_plan`          | Code        | Plan steps, observations         |
| `refactor_code`             | Code, plan  | Improvements, refactored code    |
| `full_refactoring_workflow` | Code        | Full analysis + refactored code  |
| `generate_tests`            | Code        | Test cases, coverage             |
| `architectural_review`      | Description | Review findings, recommendations |

## Example Responses

### find_symbol

```
Found 8 usages of 'process_payment' across 4 file(s)

Key locations:
  • src/payment/processor.py: line 45
  • src/api/endpoints.py: lines 67, 89
  • src/services/billing.py: line 123
  • tests/test_payment.py: line 15

============================================================
Detailed Results:
============================================================
{...JSON...}
```

### scan_directory

```
Scanned 45 Python files totaling 3,250 lines. Found 127 functions
across 23 classes, indicating good structure. Main areas: agents
(15 files), utilities (8 files), tests (22 files). Consider
refactoring files exceeding 500 lines.

============================================================
Detailed Results:
============================================================
{...JSON...}
```

### grep_search

```
Found 6 match(es) for pattern 'TODO'

Matching lines:
  • src/main.py: TODO: refactor this function
  • src/utils.py: TODO: add error handling
  • src/api.py: TODO: implement caching

============================================================
Detailed Results:
============================================================
{...JSON...}
```

## Performance Impact

| Result Size        | Formatting Time | Total Response |
| ------------------ | --------------- | -------------- |
| Small (< 15 items) | ~50ms           | ~0.5s faster   |
| Medium (15-50)     | ~100ms          | ~2.5s          |
| Large (> 50)       | ~2-3s           | Uses Bedrock   |

**No significant performance impact for small results** - they're formatted directly without Bedrock.

## Integration with Different Clients

### With VS Code Extension

```typescript
// No changes needed - extension receives formatted text
const result = await client.callTool('find_symbol', args);
console.log(result); // Already formatted, ready to display
```

### With Interactive Client

```python
# No changes needed - formatted responses received
result = await client.call_tool("scan_directory", args)
# result already contains formatted natural language
```

### With Custom Client

```python
# Works with any MCP client library
result = await mcp_client.call_tool("analyze_impact", {
    "root_directory": "./src",
    "symbol_name": "validate"
})
# Returns formatted natural language string
```

## Customizing Response Format

### Create Custom Formatter

Edit `src/utils/natural_language_formatter.py`:

```python
def _format_my_tool(self, result: Dict) -> str:
    """Custom formatter for my_tool."""
    # Your custom formatting logic
    return formatted_string
```

The server will automatically use this formatter for `my_tool`.

### Modify Bedrock Prompt

In `_format_find_symbol()` or other methods:

```python
prompt = """Your custom prompt here.
Focus on:
- What matters most
- Specific format
- Tone/style
"""
```

## Troubleshooting

### I'm still getting JSON responses

**Cause**: `ENABLE_NL_FORMAT=false`

**Fix**:

```bash
export ENABLE_NL_FORMAT=true
python -m src.mcp_server.server
```

### Responses include too much detail

**Cause**: Detailed JSON included (intended behavior)

**Info**: The natural language summary is at the top, JSON is at the bottom

### "Error generating summary"

**Cause**: Bedrock not available or error

**Fix**:

1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify Bedrock access
3. Check region: `export AWS_REGION=ap-southeast-2`

### Very long responses for large codebases

**Cause**: Server includes both summary and complete JSON

**Info**: This is designed for transparency

**Optimization**: Consider limiting search scope or using filters

## Architecture

```
┌─────────────┐
│  MCP Client │
└──────┬──────┘
       │ Tool Call
       v
┌──────────────────┐
│  MCP Server      │
│                  │
│  [Tool Logic]    │
│        │         │
│        v         │
│  [Result JSON]   │
│        │         │
│        v         │
│  [Formatter]     │◄──────────┐
│  • Direct fmt    │           │
│  • Bedrock API   │           │
│        │         │           │
│        v         │ Optional  │
│  [NL String]     │ LangChain │
└──────┬───────────┘ + Bedrock │
       │ Natural Language       │
       v                        │
┌─────────────┐               │
│ MCP Client  │◄──────────────┘
│   Receives  │
│  Formatted  │
│    Text     │
└─────────────┘
```

## Next Steps

1. ✅ Start the server: `python -m src.mcp_server.server`
2. ✅ Use any MCP client (VS Code, interactive, custom)
3. ✅ Receive formatted responses automatically
4. ✅ (Optional) Configure Bedrock for complex results
5. ✅ (Optional) Customize formatters in `natural_language_formatter.py`

## Support

For detailed information, see:

- [MCP Server Natural Language Guide](MCP_SERVER_NATURAL_LANGUAGE.md)
- [LangChain Integration Guide](LANGCHAIN_BEDROCK_QUICKREF.md)
- Main [README.md](../../README.md)

---

**That's it!** Your MCP server now provides professional, human-readable responses to all clients. 🎉
