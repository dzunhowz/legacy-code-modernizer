# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### 1. Setup Environment

```bash
# Clone/navigate to project
cd legacy-code-modernizer

# Copy environment template
cp .env.example .env

# Edit with your AWS credentials
# Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
nano .env
```

### 2. Install Dependencies

```bash
# Install using UV
make install

# Or manually
uv sync
```

### 3. Quick Test

#### Test Code Scout (Fast Agent)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run Code Scout on itself
python -c "
from src.agents.code_scout import CodeScout
scout = CodeScout('.')
scout.scan_directory()
impact = scout.analyze_impact('CodeScout')
print(f'Found {impact[\"total_usages\"]} usages across {impact[\"file_count\"]} files')
"
```

#### Test Refactoring Crew (Slow Agent)

**Note: Requires AWS Bedrock access**

```bash
python examples/refactoring_crew_example.py
```

### 4. Run MCP Server

```bash
# Option 1: Docker
make docker-up

# Option 2: Direct
make run-server
```

## 📁 Project Structure

```
legacy-code-modernizer/
├── src/
│   ├── agents/
│   │   ├── code_scout.py          # Fast synchronous scanner
│   │   └── refactoring_crew.py    # Slow AI-powered refactoring
│   ├── mcp_server/
│   │   └── server.py              # MCP server
│   └── utils/
│       ├── config.py
│       └── logger.py
├── tests/                         # Test suite
├── examples/                      # Usage examples
├── aws/                          # AWS setup guides
├── Dockerfile                     # Container definition
├── docker-compose.yml            # Local development
├── Makefile                      # Common commands
└── README.md                     # Full documentation
```

## 🔧 Common Commands

```bash
# Install dependencies
make install

# Run tests
make test

# Run with coverage
make test-cov

# Format code
make format

# Lint code
make lint

# Build Docker image
make docker-build

# Deploy to AWS
make deploy

# View all commands
make help
```

## 🎯 Use Cases

### 1. Impact Analysis Before Refactoring

```python
from src.agents.code_scout import CodeScout

scout = CodeScout("/path/to/repo")
scout.scan_directory()

# Analyze what would break if you change this function
impact = scout.analyze_impact("legacy_function")
print(f"Affects {impact['file_count']} files")
print(f"Dependencies: {impact.get('dependencies', [])}")
```

### 2. AI-Powered Refactoring

```python
from src.agents.refactoring_crew import RefactoringCrew

crew = RefactoringCrew()
result = crew.full_refactoring_workflow(
    code=your_legacy_code,
    context="High-traffic API endpoint"
)

print("Plan:", result['refactoring_plan'])
print("Code:", result['refactored_code'])
```

### 3. MCP Server Integration

Expose both agents via MCP protocol:

```bash
# Start server
make run-server

# Use from any MCP client
# - scan_directory
# - analyze_impact
# - full_refactoring_workflow
# - generate_tests
# - etc.
```

## 🐳 Docker Usage

```bash
# Build and start
make docker-up

# View logs
make docker-logs

# Stop
make docker-down
```

## ☁️ AWS Deployment

### Prerequisites

1. AWS account with Bedrock access
2. AWS CLI configured
3. Enable Claude 3.5 Sonnet in Bedrock console

### Deploy

```bash
# One-command deployment
make deploy

# Manual steps available in aws/setup-guide.md
```

## 🧪 Testing

```bash
# Unit tests
make test

# With coverage
make test-cov

# Integration tests (requires AWS)
make test-integration
```

## 📊 Agent Comparison

| Feature | Code Scout | Refactoring Crew |
|---------|------------|------------------|
| **Speed** | < 1 second | 10-60 seconds |
| **Type** | Synchronous | Asynchronous |
| **AI** | No | Yes (Bedrock) |
| **Use Case** | Impact analysis | Code modernization |
| **MCP Wrapper** | `is_long_running=False` | `is_long_running=True` |

## 💰 Cost Estimate

**AWS Monthly Costs:**
- Fargate: $30-50 (1 vCPU, 2GB, always-on)
- Bedrock: $3-15 per 1M tokens
- ECR: ~$0.10/GB
- CloudWatch: ~$0.50/GB

**Total: ~$50-100/month** for moderate usage

## 🔐 Security

- Never commit `.env` file
- Use AWS Secrets Manager in production
- Enable VPC endpoints for Bedrock
- Rotate credentials regularly
- Use least-privilege IAM roles

## 🐛 Troubleshooting

### "Import errors in development"

```bash
source .venv/bin/activate
uv sync
```

### "Bedrock access denied"

```bash
# Check access
aws bedrock list-foundation-models --region us-east-1

# Request access in AWS Console → Bedrock → Model access
```

### "Docker build fails"

```bash
make clean
make docker-build
```

## 📚 Documentation

- **Full Guide**: README.md
- **AWS Setup**: aws/setup-guide.md
- **Examples**: examples/
- **API Docs**: Use `make help`

## 🛠️ Development

```bash
# Setup dev environment
make install-dev

# Run all checks
make check

# Format and lint
make format lint

# Type checking
make type-check
```

## 📝 Example Output

### Code Scout

```
Found 42 usages across 12 files
Dependencies: ['helper_function', 'util_module']
Dependents: ['main_service', 'api_handler']
```

### Refactoring Crew

```
Refactoring Plan:
- HIGH: Add type hints for all parameters
- HIGH: Implement proper error handling
- MEDIUM: Extract complex logic into separate functions
- LOW: Add comprehensive docstrings

Refactored Code:
[Clean, modern Python with type hints, error handling, and docs]
```

## 🎓 Learning Path

1. Start with Code Scout examples
2. Understand impact analysis
3. Try simple refactoring with CrewAI
4. Integrate with MCP server
5. Deploy to AWS Fargate

## 🤝 Support

- Issues: GitHub Issues
- Docs: Full README.md
- Examples: /examples directory

## ⚡ Next Steps

1. ✅ Setup environment variables
2. ✅ Run Code Scout locally
3. ✅ Test Refactoring Crew
4. ✅ Start MCP server
5. ✅ Deploy to AWS

**Ready to modernize your legacy code!** 🚀
