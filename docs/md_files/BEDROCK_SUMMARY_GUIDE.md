# AWS Bedrock Natural Language Summary Integration

## Overview

The interactive MCP client now uses **LangChain with AWS Bedrock** to automatically convert JSON command results into natural language summaries. This makes it easier to understand what the analysis found without parsing raw JSON output.

### Technology Stack

- **LangChain**: Framework for LLM applications
- **AWS Bedrock**: Managed AI service with Claude models
- **Claude 3.5 Sonnet**: Advanced language model for analysis

## Features

- **Automatic Summarization**: Results from scan, find, grep, and graph commands are automatically summarized
- **Key Statistics**: Get quick insights like "Found 15 usages across 8 files"
- **Actionable Insights**: Bedrock identifies patterns and provides recommendations
- **Toggle On/Off**: Enable or disable summarization anytime

## Setup

### Install Dependencies

```bash
# Install LangChain and AWS Bedrock integration
uv pip install langchain langchain-aws

# Or with pip
pip install langchain langchain-aws
```

### Prerequisites

1. AWS credentials configured
2. Access to AWS Bedrock with Claude models
3. Required environment variables:

````bash
export AWS_REGION=ap-southeast-2
export AWS_ACCESS_KEY_ID=your_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_key

# Optional: Disable summary by default
export ENABLE_SUMMARY=false
```Test Bedrock Connection

```bash
# Test LangChain + Bedrock integration
python examples/test_bedrock_summary.py
````

###

### AWS Bedrock Access

Ensure you have requested access to Claude models in AWS Bedrock:

- Go to AWS Console → Bedrock → Model Access
- Request access to: `anthropic.claude-3-5-sonnet-20241022-v2:0`

## Usage

### Running with Summarization

```bash
# Summary enabled by default
python examples/mcp_client_interactive.py

# Or explicitly enable
ENABLE_SUMMARY=true python examples/mcp_client_interactive.py
```

### Example Session

```
mcp> scan
Directory path (default: .): ./src
File pattern (default: *.py): *.py

[Scanning...]

==============================================================
Result:
==============================================================
{
  "files_scanned": 45,
  "total_lines": 3250,
  "functions_found": 127,
  ...
}
==============================================================

==============================================================
🤖 AI Summary (AWS Bedrock):
==============================================================
Analyzed 45 Python files totaling 3,250 lines of code. Found 127
functions across 23 classes. The codebase shows moderate complexity
with an average of 25 lines per function. Key areas include agent
implementations (15 files) and utilities (8 files). Consider
refactoring larger functions exceeding 100 lines.
==============================================================
```

### Toggle Summarization

```
mcp> summary
🤖 AI summary disabled

mcp> summary
🤖 AI summary enabled
```

## Commands That Support Summarization

All analysis commands automatically get summarized when enabled:

- `scan` - Directory scanning results
- `find` - Symbol usage findings
- `grep` - Search results
- `graph` - Dependency graph analysis

## Configuration

### Environment Variables

| Variable           | Default                                     | Description                     |
| ------------------ | ------------------------------------------- | ------------------------------- |
| `ENABLE_SUMMARY`   | `true`                                      | Enable/disable AI summarization |
| `AWS_REGION`       | `ap-southeast-2`                            | AWS region for Bedrock          |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Claude model to use             |

### Cost Considerations

Each summary generates ~500 tokens. Approximate costs:

- Input: ~2,000 tokens per summary (result data)
- Output: ~500 tokens per summary
- Total per command: ~$0.01-0.02 USD

**Tip**: Disable summary for large batch operations to save costs.

## Benefits

### Before (Raw JSON)

```json
{
  "symbol": "process_data",
  "occurrences": [
    {"file": "src/main.py", "line": 45},
    {"file": "src/utils.py", "line": 123},
    ...
  ]
}
```

### After (AI Summary)

```
Found 8 usages of 'process_data' across 3 files. Primary usage
is in src/main.py (4 calls) and src/utils.py (2 calls). The
function appears to be a core data processing utility. Consider
adding type hints for better IDE support.
```

## Troubleshooting

### "Failed to initialize Bedrock"

**Cause**: AWS credentials not configured or no Bedrock access

**Solution**:

1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify Bedrock access in AWS Console
3. Ensure correct region is set

### "Summary unavailable"

**Cause**: Bedrock initialization failed

**Solution**:

- Client continues working without summaries
- Fix AWS credentials and restart client

### Summary seems inaccurate

**Cause**: Result data too large and was truncated
Using LangChain Features

The implementation uses LangChain's `ChatBedrock` class, which provides:

- Automatic message formatting
- Streaming support (future enhancement)
- Easy model switching
- Built-in error handling

### Custom Summary Prompts

To customize summary style, modify `BedrockSummarizer._create_summary_prompt()`:

```python
def _create_summary_prompt(self, tool_name: str, result_data: dict) -> str:
    # Customize prompt here
    prompt = f"""Analyze {tool_name} results and provide:
    1. Executive summary (2 sentences)
    2. Key metrics
    3. Top 3 recommendations

    Results: {json.dumps(result_data)}
    """
    return prompt
```

### Temperature Control

Adjust response creativity in the initializer:

```python
self.llm = ChatBedrock(
    model_id=self.model_id,
    region_name=self.region,
    model_kwargs={
        "max_tokens": 500,
        "temperature": 0.7,  # Higher = more creative
    }
)Analyze {tool_name} results and provide:
    1. Executive summary (2 sentences)
    2. Key metrics
    3. Top 3 recommendations

    Results: {json.dumps(result_data)}
    """
    return prompt
```

### Different Models

Use a different Claude model:

```bash
export BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
python examples/mcp_client_interactive.py
```

## Performance

- Summary generation: ~2-3 seconds per command
- Network latency: Depends on AWS region
- No impact on tool execution time

## Examples

### Finding Function Usages

```
mcp> find
Directory path: ./src
Symbol name: validate_input

🤖 Summary: Located 12 instances of 'validate_input' across
5 modules. Most frequent use in validators.py (7 calls).
Function is called before all API endpoints. All usages pass
string arguments. Consider adding input validation schema.
```

### Scanning Large Directories

```
mcp> scan
Directory path: ./src
File pattern: *.py

🤖 Summary: Scanned 156 Python files (12,450 lines).
Identified 340 functions and 67 classes. Largest files are
in agents/ directory (avg 150 lines). Code complexity is
moderate. 23% of functions lack docstrings.
```

## Disabling Summarization

Three ways to disable:

1. **Environment variable**: `export ENABLE_SUMMARY=false`
2. **Interactive command**: `mcp> summary`
3. **Code modification**: Set `enable_summary = False` in constructor

## Best Practices

1. **Enable for exploration**: When learning a new codebase
2. **Disable for automation**: When running batch scripts
3. **Cost awareness**: Monitor AWS bills if running frequently
4. **Review raw data**: Always available above the summary
5. **Verify insights**: AI summaries are helpful but not perfect

## Integration with Other Tools

The summary feature works seamlessly with:

- GitHub URL scanning
- Local directory analysis
- Symbol search and grep
- Dependency graph building

All existing functionality remains unchanged; summarization is purely additive.
