# Legacy Code Modernizer

A powerful system for modernizing risky legacy functions using AI agents exposed via Model Context Protocol (MCP). The system features two specialized agents with **GitHub integration** for direct repository and file analysis.

1. **Code Scout (Fast Agent)** - Synchronous symbol scanner for impact analysis
2. **Refactoring Crew (Slow Agent)** - Asynchronous AI-powered refactoring using CrewAI and AWS Bedrock

**🆕 GitHub Integration**: Both agents now support GitHub URLs! Analyze repositories or files directly without cloning manually.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Server                           │
│                 (Fargate Container)                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐      ┌──────────────────────┐   │
│  │   Code Scout     │      │  Refactoring Crew    │   │
│  │  (Fast/Sync)     │      │   (Slow/Async)       │   │
│  ├──────────────────┤      ├──────────────────────┤   │
│  │ • AST parsing    │      │ • Architect Agent    │   │
│  │ • Grep search    │      │ • Coder Agent        │   │
│  │ • Git blame      │      │ • AWS Bedrock        │   │
│  │ • Impact analysis│      │ • CrewAI             │   │
│  │ • Dependency     │      │ • Test generation    │   │
│  │   graphing       │      │ • Architecture review│   │
│  │ • GitHub URLs    │      │ • GitHub URLs        │   │
│  └──────────────────┘      └──────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Features

### Code Scout (Fast Agent)

- **Symbol Scanning**: AST-based Python code analysis
- **Impact Analysis**: Understand the blast radius of changes
- **Dependency Graphing**: Build and visualize dependencies
- **Grep Search**: Fast text-based searches across codebases
- **Git Blame**: Track code ownership and history
- **GitHub Support**: Analyze repositories directly via URL
- **MCP Wrapper**: `@wrapper.ingest(is_long_running=False)`

### Refactoring Crew (Slow Agent)

- **Architect Agent**: Analyzes code and creates refactoring plans
- **Coder Agent**: Implements refactoring plans with clean code
- **AI-Powered**: Uses AWS Bedrock (Claude 3.5 Sonnet)
- **Test Generation**: Automatic pytest test suite creation
- **Architectural Review**: High-level codebase assessment
- **GitHub Support**: Refactor files directly from GitHub URLs
- **MCP Wrapper**: `@wrapper.ingest(is_long_running=True)`

## Prerequisites

- Python 3.13+
- UV (Python package manager)
- Docker & Docker Compose
- AWS Account with Bedrock access
- AWS CLI configured

## Quick Start

### 1. Clone and Setup

```bash
cd legacy-code-modernizer

# Copy environment template
cp .env.example .env

# Edit .env with your AWS credentials
nano .env
```

### 2. Install Dependencies

```bash
# UV will create a virtual environment and install dependencies
uv sync
```

### 3. Local Development

#### Run with Docker Compose

```bash
docker-compose up --build
```

#### Run Directly

```bash
# Activate virtual environment
source .venv/bin/activate

# Run Code Scout
python -m src.agents.code_scout

# Run Refactoring Crew
python -m src.agents.refactoring_crew

# Run MCP Server
python -m src.mcp_server.server
```

## Usage Examples

### 🆕 GitHub Integration Examples

Both agents now support GitHub URLs directly!

```python
from src.agents.code_scout import CodeScout
from src.agents.refactoring_crew import RefactoringCrew

# Analyze a GitHub repository
scout = CodeScout("https://github.com/pallets/flask")
scout.scan_directory("*.py")
impact = scout.analyze_impact("Flask")

# Analyze a single GitHub file
scout.analyze_github_file("https://github.com/owner/repo/blob/main/file.py")

# Refactor code from GitHub
crew = RefactoringCrew()
result = crew.full_refactoring_workflow(
    code="https://github.com/owner/repo/blob/main/legacy.py",
    context="Legacy authentication module"
)

# Private repositories (requires token)
scout = CodeScout(
    "https://github.com/your-org/private-repo",
    github_token="ghp_your_token"
)
```

### Code Scout Examples

```python
from src.agents.code_scout import CodeScout

# Local directory
scout = CodeScout("/path/to/your/repo")

# Scan directory
scout.scan_directory("*.py")

# Find all usages of a function
usages = scout.find_symbol("legacy_function")

# Analyze impact
impact = scout.analyze_impact("legacy_function")
print(f"Found {impact['total_usages']} usages across {impact['file_count']} files")

# Build dependency graph
graph = scout.build_dependency_graph()

# Git blame
blame = scout.git_blame("src/main.py", 42)
print(f"Last modified by: {blame['author']}")
```

### Refactoring Crew Examples

```python
from src.agents.refactoring_crew import RefactoringCrew

# Initialize crew with Bedrock
crew = RefactoringCrew(
    bedrock_model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    aws_region="us-east-1"
)

legacy_code = """
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
"""

# Full refactoring workflow
output = crew.full_refactoring_workflow(
    code=legacy_code,
    context="High-traffic API endpoint processing user data"
)

print("Refactoring Plan:")
print(output['refactoring_plan'])

print("\nRefactored Code:")
print(output['refactored_code'])

# Generate tests
tests = crew.generate_tests(
    code=legacy_code,
    refactored_code=output['refactored_code']
)
```

### MCP Server Usage

The MCP server exposes both agents via standardized tools:

**Fast Tools (Code Scout)**:

- `scan_directory` - Scan and analyze Python files
- `find_symbol` - Find symbol usages
- `analyze_impact` - Impact analysis
- `grep_search` - Text search
- `git_blame` - Git history
- `build_dependency_graph` - Dependency analysis

**Slow Tools (Refactoring Crew)**:

- `analyze_and_plan` - Create refactoring plan
- `refactor_code` - Implement refactoring
- `full_refactoring_workflow` - Complete workflow
- `generate_tests` - Generate test suite
- `architectural_review` - Architecture assessment

## Deployment to AWS Fargate

### Prerequisites

1. AWS account with appropriate permissions
2. AWS CLI configured
3. Docker installed
4. ECR repository access

### Deploy

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The deployment script will:

1. Create ECR repository
2. Build and push Docker image
3. Register ECS task definition
4. Update/create ECS service

### Manual Deployment Steps

```bash
# Build image
docker build -t legacy-code-modernizer .

# Tag for ECR
docker tag legacy-code-modernizer:latest \
  ${ECR_URI}/legacy-code-modernizer:latest

# Push to ECR
docker push ${ECR_URI}/legacy-code-modernizer:latest

# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://fargate-task-definition.json

# Update service
aws ecs update-service \
  --cluster legacy-code-modernizer-cluster \
  --service legacy-code-modernizer-service \
  --force-new-deployment
```

## Configuration

### Environment Variables

| Variable                | Description            | Default                                     |
| ----------------------- | ---------------------- | ------------------------------------------- |
| `AWS_REGION`            | AWS region for Bedrock | `us-east-1`                                 |
| `AWS_ACCESS_KEY_ID`     | AWS access key         | -                                           |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key         | -                                           |
| `BEDROCK_MODEL_ID`      | Bedrock model ID       | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `LOG_LEVEL`             | Logging level          | `INFO`                                      |

### AWS Permissions Required

The ECS task role needs:

- `bedrock:InvokeModel` - For AI agent calls
- CloudWatch Logs permissions for logging
- Secrets Manager access (if using)

### Bedrock Model Access

Ensure your AWS account has access to Claude 3.5 Sonnet in Bedrock:

```bash
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `claude-3-5-sonnet`)]'
```

## Project Structure

```
legacy-code-modernizer/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── code_scout.py          # Fast synchronous agent
│   │   └── refactoring_crew.py    # Slow asynchronous agent
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   └── server.py              # MCP server implementation
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   └── logger.py              # Logging setup
│   └── __init__.py
├── tests/                         # Test files (to be added)
├── Dockerfile                     # Container definition
├── docker-compose.yml             # Local development
├── fargate-task-definition.json   # ECS task definition
├── deploy.sh                      # Deployment script
├── pyproject.toml                 # UV project configuration
├── uv.lock                        # Dependency lock file
├── .env.example                   # Environment template
└── README.md                      # This file
```

## Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test
uv run pytest tests/test_code_scout.py
```

## Development

### Adding New Tools to MCP Server

1. Add method to agent class
2. Register tool in `_register_tools()` method
3. Add handler in `_execute_tool()` method
4. Decorate with `@mcp_wrapper()` if needed

### Code Style

This project follows:

- PEP 8 style guide
- Type hints for all functions
- Comprehensive docstrings
- Black for formatting
- isort for import sorting

```bash
# Format code
uv run black src/

# Sort imports
uv run isort src/

# Type checking
uv run mypy src/
```

## Troubleshooting

### Common Issues

**1. Bedrock Access Denied**

```bash
# Check Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

**2. Docker Build Issues**

```bash
# Clean build
docker system prune -a
docker-compose build --no-cache
```

**3. MCP Server Connection Issues**

```bash
# Check server logs
docker-compose logs -f legacy-code-modernizer
```

**4. Import Errors in Development**

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
uv sync
```

## Performance Considerations

### Code Scout (Fast Agent)

- **Typical Response**: < 1 second for single file analysis
- **Large Repositories**: 5-30 seconds for full scan
- **Optimization**: Results are cached per directory

### Refactoring Crew (Slow Agent)

- **Typical Response**: 10-60 seconds per operation
- **Full Workflow**: 2-5 minutes (analysis + refactoring)
- **Factors**: Code complexity, Bedrock API latency

## Security Best Practices

1. **Never commit** `.env` file with real credentials
2. Use AWS Secrets Manager for production credentials
3. Enable VPC endpoints for Bedrock to avoid internet egress
4. Use least-privilege IAM roles
5. Enable CloudTrail for audit logging
6. Regularly rotate AWS credentials

## Cost Estimation

### AWS Services

- **Fargate**: ~$30-50/month (1 vCPU, 2GB RAM, always on)
- **Bedrock**: ~$3-15/1M tokens (Claude 3.5 Sonnet)
- **ECR**: ~$0.10/GB/month
- **CloudWatch**: ~$0.50/GB ingested

**Typical monthly cost**: $50-100 for moderate usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:

- GitHub Issues: [Create an issue](https://github.com/yourusername/legacy-code-modernizer/issues)
- Documentation: [Wiki](https://github.com/yourusername/legacy-code-modernizer/wiki)

## Roadmap

- [ ] Add support for more languages (JavaScript, TypeScript, Java)
- [ ] Web UI for visualizing dependency graphs
- [ ] Integration with GitHub Actions
- [ ] Support for more AI models (GPT-4, Gemini)
- [ ] Batch processing capabilities
- [ ] Interactive refactoring mode
- [ ] Code quality metrics dashboard

## Acknowledgments

- Built with [CrewAI](https://github.com/joaomdmoura/crewAI)
- Uses [AWS Bedrock](https://aws.amazon.com/bedrock/)
- MCP Protocol by [Anthropic](https://www.anthropic.com/)
- Package management by [UV](https://github.com/astral-sh/uv)
