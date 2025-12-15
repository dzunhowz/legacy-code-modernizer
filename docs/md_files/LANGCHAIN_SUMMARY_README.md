# Natural Language Summaries with LangChain + AWS Bedrock

## What's New

Your MCP interactive client now **converts JSON responses to natural language** using LangChain and AWS Bedrock! 🎉

## Quick Start

```bash
# 1. Install dependencies
uv pip install langchain langchain-aws

# 2. Configure AWS
export AWS_REGION=ap-southeast-2
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# 3. Test connection
python examples/test_bedrock_summary.py

# 4. Run interactive client (summaries enabled by default)
python examples/mcp_client_interactive.py
```

## How It Works

```
┌─────────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────┐
│   User      │────>│   MCP    │────>│  JSON    │────>│  LangChain   │
│   Command   │     │   Tool   │     │  Result  │     │  + Bedrock   │
└─────────────┘     └──────────┘     └──────────┘     └──────────────┘
                                                              │
                                                              v
                                                      ┌──────────────┐
                                                      │   Natural    │
                                                      │   Language   │
                                                      └──────────────┘
```

## Example

### Before (Raw JSON)

```json
{
  "symbol": "validate_input",
  "occurrences": 12,
  "files": ["validators.py", "api.py", "handlers.py"]
}
```

### After (Natural Language via LangChain + Bedrock)

```
Found 12 instances of 'validate_input' across 3 modules. Most frequent
use in validators.py. This function is called before all API endpoints,
suggesting it's a critical validation utility. Consider adding
comprehensive unit tests.
```

## Features

- ✅ **Automatic conversion**: JSON → Plain English
- ✅ **LangChain powered**: Clean, maintainable code
- ✅ **Toggle on/off**: Type `summary` in the client
- ✅ **Cost efficient**: ~$0.01 per summary
- ✅ **Works with all tools**: scan, find, grep, graph

## Commands

```
mcp> summary          # Toggle summaries on/off
mcp> scan            # Scan directory (with summary)
mcp> find            # Find symbol usages (with summary)
mcp> grep            # Search code (with summary)
mcp> graph           # Build dependency graph (with summary)
mcp> help            # Show help
mcp> quit            # Exit
```

## Files Changed

1. **pyproject.toml** - Added `langchain` and `langchain-aws` dependencies
2. **examples/mcp_client_interactive.py** - Added `BedrockSummarizer` class
3. **examples/test_bedrock_summary.py** - New test script
4. **docs/md_files/** - Documentation files

## Configuration

### Enable/Disable Summaries

```bash
# Enable (default)
export ENABLE_SUMMARY=true

# Disable
export ENABLE_SUMMARY=false
```

### Change Model

```bash
# Use Claude 3.5 Sonnet (default, most capable)
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Use Claude 3 Haiku (faster, cheaper)
export BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

## Testing

```bash
# Test Bedrock connection
python examples/test_bedrock_summary.py

# Test with interactive client
python examples/mcp_client_interactive.py
# Then type: scan
# Enter path: ./src
```

## Troubleshooting

| Issue                       | Solution                                             |
| --------------------------- | ---------------------------------------------------- |
| "No module named langchain" | `uv pip install langchain langchain-aws`             |
| "Bedrock not initialized"   | Check AWS credentials: `aws sts get-caller-identity` |
| "Access denied"             | Request Bedrock access in AWS Console                |
| Summaries disabled          | Type `summary` in the client to enable               |

## Cost Estimate

- **Per summary**: ~$0.01-0.02 USD
- **Per session** (10 commands): ~$0.10-0.20 USD
- **Monthly** (100 commands): ~$1-2 USD

💡 **Tip**: Disable summaries for batch operations to save costs.

## Documentation

- 📘 [Complete Guide](docs/md_files/BEDROCK_SUMMARY_GUIDE.md)
- 📗 [Quick Reference](docs/md_files/LANGCHAIN_BEDROCK_QUICKREF.md)

## Why LangChain?

| Feature            | boto3 (before) | LangChain (now) |
| ------------------ | -------------- | --------------- |
| Code lines         | ~30            | ~15             |
| Message formatting | Manual         | Automatic       |
| Error handling     | Custom         | Built-in        |
| Model switching    | Hard           | Easy            |
| Streaming          | Complex        | Simple          |
| Future features    | Limited        | Unlimited       |

## Next Steps

1. ✅ Test the connection: `python examples/test_bedrock_summary.py`
2. ✅ Run interactive client: `python examples/mcp_client_interactive.py`
3. ✅ Try different commands with summaries
4. ✅ Toggle summary on/off with the `summary` command
5. 🔜 Customize prompts in `BedrockSummarizer._create_summary_prompt()`

## Support

If you encounter issues:

1. Check AWS credentials
2. Verify Bedrock access
3. Review [Troubleshooting Guide](docs/md_files/BEDROCK_SUMMARY_GUIDE.md#troubleshooting)
4. Run test script: `python examples/test_bedrock_summary.py`

---

**Enjoy natural language insights from your code analysis!** 🚀
