# MCP Server Natural Language Integration

## Overview

The MCP server now **automatically formats all tool responses as natural language** using LangChain + AWS Bedrock. When any MCP client calls a tool, the response is automatically converted from JSON to human-readable natural language with formatting.

## Architecture

```
┌─────────────────────────────────────────────┐
│         MCP Client (Any Client)             │
│    (interactive, IDE extension, etc)        │
└──────────────────┬──────────────────────────┘
                   │ Tool Call
                   v
┌─────────────────────────────────────────────┐
│        MCP Server                           │
│  ┌─────────────────────────────────────┐   │
│  │ Execute Tool (Code Scout, Crew)     │   │
│  │ Returns: JSON Result Dict           │   │
│  └──────────────────┬──────────────────┘   │
│                     │                       │
│  ┌──────────────────v──────────────────┐   │
│  │ NaturalLanguageFormatter            │   │
│  │ (NEW!)                              │   │
│  │ - Format results                    │   │
│  │ - Use LangChain + Bedrock if        │   │
│  │   result large or complex           │   │
│  │ - Returns: Natural Language String  │   │
│  └──────────────────┬──────────────────┘   │
└──────────────────┬──────────────────────────┘
                   │ Natural Language Response
                   v
┌─────────────────────────────────────────────┐
│         MCP Client                          │
│      Receives formatted response:           │
│  "Found 15 usages across 3 files..."       │
│  • file1.py: line 45                       │
│  • file2.py: lines 67, 89                  │
│  ...                                        │
└─────────────────────────────────────────────┘
```

## How It Works

### 1. Tool Execution

```python
result = await self._execute_tool(name, arguments)
# Returns: {"symbol": "process_data", "occurrences": [...], ...}
```

### 2. Natural Language Formatting

```python
formatted_response = self.nl_formatter.format_response(name, result)
# Returns: "Found 15 usages of 'process_data' across 3 files..."
```

### 3. Response to Client

```python
return [TextContent(type="text", text=formatted_response)]
```

## Features

✅ **Automatic Conversion**: All tool responses are converted to natural language  
✅ **Smart Formatting**: Different formats for different tool types  
✅ **Detailed + Raw**: Shows both summary and detailed JSON  
✅ **Bedrock Integration**: Uses Claude for complex result analysis  
✅ **Fallback**: Uses simple formatting for small results  
✅ **Toggle-able**: Can be disabled via environment variable

## Response Examples

### Before (Raw JSON)

```json
{
  "symbol": "validate_input",
  "occurrences": [
    { "file": "src/validators.py", "line": 45 },
    { "file": "src/api.py", "line": 123 },
    { "file": "src/handlers.py", "line": 67 }
  ],
  "files": ["src/validators.py", "src/api.py", "src/handlers.py"],
  "count": 3
}
```

### After (Natural Language)

```
Found 3 usages of 'validate_input' across 3 file(s)

Key locations:
  • src/validators.py: line 45
  • src/api.py: line 123
  • src/handlers.py: line 67

============================================================
Detailed Results:
============================================================
{
  "symbol": "validate_input",
  ...
}
```

## Supported Tools

### Code Scout Tools (Fast)

1. **scan_directory** → Analysis of file structure
2. **find_symbol** → Symbol usage locations (bullet points)
3. **grep_search** → Search results (formatted)
4. **analyze_impact** → Impact assessment (summary)
5. **build_dependency_graph** → Dependency analysis
6. **git_blame** → Git history (formatted)

### Refactoring Crew Tools (Slow)

1. **analyze_and_plan** → Refactoring plan with steps
2. **refactor_code** → Code changes with improvements
3. **full_refactoring_workflow** → Complete analysis + code
4. **generate_tests** → Test suite with coverage
5. **architectural_review** → Architecture recommendations

## Configuration

### Enable/Disable Natural Language Formatting

```bash
# Enable (default)
export ENABLE_NL_FORMAT=true

# Disable (get raw JSON)
export ENABLE_NL_FORMAT=false
```

### Custom Bedrock Model

```bash
export BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
export AWS_REGION=us-east-1
```

## Implementation Details

### NaturalLanguageFormatter Class

Location: `src/utils/natural_language_formatter.py`

```python
class NaturalLanguageFormatter:
    def format_response(self, tool_name: str, result: Any) -> str:
        """Convert JSON result to natural language."""
        # 1. Determine formatter method
        # 2. Call tool-specific formatter
        # 3. Format with summary + detailed results
        # 4. Return formatted string
```

### Tool-Specific Formatters

Each tool has its own formatter method:

```python
def _format_find_symbol(self, result: Dict) -> str:
    """Format find_symbol results with:
    - Total occurrences count
    - List of files with line numbers
    - Optional Bedrock summary for large results
    """

def _format_scan_directory(self, result: Dict) -> str:
    """Format scan results with:
    - Total files analyzed
    - Total lines of code
    - Functions and classes count
    - Code structure insights
    """
```

### Smart Fallback

- **Small results** (≤ 15 items): Direct formatting without Bedrock
- **Large results** (> 15 items): Uses Bedrock for intelligent summary
- **Errors**: Returns raw JSON with error message

## Usage Examples

### Example 1: Find Symbol (via any MCP client)

**Request:**

```json
{
  "name": "find_symbol",
  "arguments": {
    "root_directory": "./src",
    "symbol_name": "process_data"
  }
}
```

**Response:**

```
Found 12 usages of 'process_data' across 3 file(s)

Key locations:
  • src/main.py: line 45
  • src/utils.py: line 123
  • src/handlers.py: line 67
  • ... and 9 more

============================================================
Detailed Results:
============================================================
{
  "symbol": "process_data",
  "occurrences": [
    {"file": "src/main.py", "line": 45},
    ...
  ],
  "count": 12
}
```

### Example 2: Scan Directory

**Response:**

```
Scanned 45 Python files containing 3,250 lines of code. Found 127
functions across 23 classes, indicating a well-structured codebase.
Key areas include agent implementations (15 files) and utilities
(8 files). Consider refactoring larger functions exceeding 100 lines.

============================================================
Detailed Results:
============================================================
{
  "files_scanned": 45,
  "total_lines": 3250,
  ...
}
```

### Example 3: Grep Search

**Response:**

```
Found 8 match(es) for pattern 'TODO'

Matching lines:
  • src/main.py: Line 45: TODO: refactor this function
  • src/utils.py: Line 123: TODO: add error handling
  ...

============================================================
Detailed Results:
============================================================
{
  "pattern": "TODO",
  "matches": [...],
  "count": 8
}
```

## Performance

| Aspect         | Time   | Notes             |
| -------------- | ------ | ----------------- |
| Initialization | ~100ms | One-time, lazy    |
| Small results  | ~50ms  | Direct formatting |
| Large results  | ~2-3s  | Bedrock call      |
| JSON parsing   | <10ms  | Built-in          |

## Cost Estimate

- **Small results** (no Bedrock): ~$0 (formatting only)
- **Large results** (~2000 input tokens): ~$0.01-0.02
- **Per session** (10 commands): ~$0.02-0.10
- **Monthly** (100 commands): ~$0.20-1.00

## Integration with MCP Clients

The formatter is **transparent** to MCP clients:

### For VS Code Extension

```javascript
// Client receives formatted text automatically
const response = await client.callTool('find_symbol', {
  root_directory: './src',
  symbol_name: 'validate',
});
console.log(response); // Natural language, ready to display
```

### For Interactive Client

```python
# Already formatted when received
response = await session.call_tool("scan_directory", {...})
# response.content[0].text = formatted natural language
```

### For Custom Clients

```python
# Works with any MCP client
response = await call_mcp_tool("find_symbol", args)
# response = human-readable natural language
```

## Customization

### Add Custom Formatter for New Tool

```python
def _format_my_tool(self, result: Dict) -> str:
    """Custom formatter for my_tool."""
    count = result.get("count", 0)
    items = result.get("items", [])

    summary = f"Found {count} items\n"
    summary += "\n".join([f"  • {item}" for item in items[:5]])

    if len(items) > 5:
        summary += f"\n  ... and {len(items) - 5} more"

    return summary
```

The formatter will automatically call `_format_my_tool()` when tool name is `my_tool`.

### Modify Bedrock Temperature

```python
# In natural_language_formatter.py __init__:
model_kwargs={
    "max_tokens": 1000,
    "temperature": 0.7,  # Higher = more creative
}
```

## Troubleshooting

### Issue: Responses still show JSON

**Cause**: `ENABLE_NL_FORMAT=false` or Bedrock not initialized

**Solution**:

```bash
export ENABLE_NL_FORMAT=true
# Check AWS credentials
aws sts get-caller-identity
```

### Issue: Very long responses

**Cause**: Large result with detailed JSON

**Intended behavior**: Shows natural language summary + full JSON details

**Solution**: Check the natural language portion (first part)

### Issue: "Error generating summary"

**Cause**: Bedrock API error

**Solution**:

1. Check AWS credentials
2. Verify Bedrock access
3. Check region: `export AWS_REGION=ap-southeast-2`

## Files Changed

| File                                      | Changes                                    |
| ----------------------------------------- | ------------------------------------------ |
| `src/mcp_server/server.py`                | Added NaturalLanguageFormatter integration |
| `src/utils/natural_language_formatter.py` | New file with formatter implementation     |
| `pyproject.toml`                          | Already has langchain dependencies         |

## Benefits

### For Users

- ✅ Easier to read results
- ✅ Bullet points and formatting
- ✅ Key info highlighted
- ✅ Recommendations included

### For Developers

- ✅ No client code changes needed
- ✅ Works with all MCP clients
- ✅ Transparent integration
- ✅ Easy to customize

### For Organizations

- ✅ Better user experience
- ✅ Reduced support burden
- ✅ Professional output
- ✅ Cost-effective (optional Bedrock)

## Future Enhancements

1. **Streaming Responses**: Real-time output for long operations
2. **HTML Output**: Format responses as styled HTML
3. **Markdown Export**: Save results as markdown files
4. **Custom Templates**: User-defined response templates
5. **Multi-language**: Responses in different languages
6. **Caching**: Cache summaries for identical results

## Summary

The MCP server now provides **professional, human-readable responses** automatically. Any MCP client (VS Code extension, interactive client, custom tools) receives formatted natural language results instead of raw JSON, making code analysis insights more accessible and actionable.

**Key Achievement**: Zero client changes needed - the server handles everything! 🎉
