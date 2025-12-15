# LangChain AWS Bedrock Integration - Quick Reference

## What Changed

The MCP interactive client now uses **LangChain** instead of direct boto3 calls for AWS Bedrock integration.

## Architecture

```
User Command → MCP Tool → JSON Result → LangChain → AWS Bedrock → Natural Language
```

### Before (boto3)

```python
bedrock_runtime = boto3.client('bedrock-runtime')
response = bedrock_runtime.invoke_model(
    modelId=model_id,
    body=json.dumps(request_body)
)
```

### After (LangChain)

```python
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage

llm = ChatBedrock(model_id=model_id, region_name=region)
message = HumanMessage(content=prompt)
response = llm.invoke([message])
```

## Benefits of LangChain

1. **Cleaner Code**: Less boilerplate, more readable
2. **Better Abstractions**: Standard message format across LLMs
3. **Future-Ready**: Easy to add streaming, chaining, agents
4. **Error Handling**: Built-in retry logic and error management
5. **Model Flexibility**: Switch between Bedrock, OpenAI, etc. easily

## Key Components

### ChatBedrock

```python
from langchain_aws import ChatBedrock

llm = ChatBedrock(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    region_name="ap-southeast-2",
    model_kwargs={
        "max_tokens": 500,
        "temperature": 0.3,
    }
)
```

### HumanMessage

```python
from langchain_core.messages import HumanMessage

message = HumanMessage(content="Summarize this data...")
response = llm.invoke([message])
print(response.content)  # Natural language output
```

## Usage Examples

### Example 1: Scan Directory

**Command:**

```
mcp> scan
Directory path: ./src
```

**JSON Response:**

```json
{
  "files_scanned": 45,
  "total_lines": 3250,
  "functions_found": 127,
  "classes_found": 23
}
```

**Natural Language (via LangChain + Bedrock):**

```
Scanned 45 Python files containing 3,250 lines of code. Found 127
functions across 23 classes, indicating a well-structured codebase
with good object-oriented design. Average of 72 lines per file suggests
manageable module sizes.
```

### Example 2: Find Symbol

**Command:**

```
mcp> find
Symbol name: process_data
```

**JSON Response:**

```json
{
  "symbol": "process_data",
  "occurrences": 15,
  "files": ["main.py", "utils.py", "handlers.py"]
}
```

**Natural Language:**

```
The function 'process_data' is used 15 times across 3 different modules
(main.py, utils.py, and handlers.py), indicating it's a core utility
function. Consider adding comprehensive unit tests given its widespread use.
```

## Code Organization

### BedrockSummarizer Class

```python
class BedrockSummarizer:
    """Converts JSON to natural language using LangChain + AWS Bedrock."""

    def __init__(self, model_id, region):
        self.llm = ChatBedrock(...)  # LangChain client

    def summarize(self, tool_name, result_data) -> str:
        """Main entry point for summarization."""
        prompt = self._create_summary_prompt(tool_name, result_data)
        message = HumanMessage(content=prompt)
        response = self.llm.invoke([message])
        return response.content

    def _create_summary_prompt(self, tool_name, result_data) -> str:
        """Creates prompt for natural language conversion."""
        # Converts JSON to text prompt
        ...
```

## Configuration

### Environment Variables

```bash
# AWS credentials
export AWS_REGION=ap-southeast-2
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Feature toggle
export ENABLE_SUMMARY=true

# Optional: Custom model
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### In-Code Configuration

```python
# Initialize with custom settings
summarizer = BedrockSummarizer(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",  # Faster, cheaper
    region="us-east-1"
)
```

## Testing

### Unit Test

```python
def test_summarizer():
    summarizer = BedrockSummarizer()
    result = {"files": 10, "lines": 500}
    summary = summarizer.summarize("scan", result)
    assert len(summary) > 0
    assert "10" in summary or "ten" in summary
```

### Integration Test

```bash
python examples/test_bedrock_summary.py
```

Expected output:

```
Testing AWS Bedrock with LangChain...
============================================================
✓ Bedrock client initialized

Sending request to Bedrock...

============================================================
Natural Language Summary:
============================================================
The scan analyzed 45 Python files totaling 3,250 lines of code...
============================================================

✓ Test successful!
```

## Troubleshooting

### Issue: "No module named 'langchain_aws'"

**Solution:**

```bash
uv pip install langchain-aws
```

### Issue: "ChatBedrock requires boto3"

**Solution:**

```bash
uv pip install boto3>=1.28.0
```

### Issue: Summarization returns "Bedrock not initialized"

**Causes:**

1. AWS credentials not set
2. No Bedrock access in account
3. Wrong region

**Debug:**

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region ap-southeast-2

# Test connection
python examples/test_bedrock_summary.py
```

## Performance

### Latency

- LangChain overhead: ~50ms
- Bedrock API call: ~2-3 seconds
- Total: ~2-3 seconds per summary

### Cost

- Input tokens: ~2,000 per summary
- Output tokens: ~500 per summary
- Cost per summary: ~$0.01-0.02 USD

## Future Enhancements

### 1. Streaming Responses

```python
for chunk in llm.stream([message]):
    print(chunk.content, end="", flush=True)
```

### 2. Caching

```python
from langchain.cache import InMemoryCache
llm.cache = InMemoryCache()
```

### 3. Chain Multiple Summaries

```python
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=prompt_template)
```

### 4. Different Summary Styles

```python
# Technical summary
prompt = "Provide technical details..."

# Executive summary
prompt = "Provide high-level overview..."

# Action items
prompt = "List recommended actions..."
```

## Resources

- [LangChain Documentation](https://python.langchain.com/)
- [LangChain AWS Integration](https://python.langchain.com/docs/integrations/platforms/aws)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude Model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids-arns.html)

## Summary

The LangChain integration provides:

- ✓ Cleaner, more maintainable code
- ✓ Natural language conversion of JSON results
- ✓ Easy model switching
- ✓ Future extensibility (streaming, chains, agents)
- ✓ Better developer experience
