# GitHub Integration Update

## 🎉 New Feature: GitHub URL Support

Both Code Scout and Refactoring Crew agents now support **GitHub URLs** as input parameters! You can analyze repositories and files directly without manual cloning.

## What's New

### Code Scout (Fast Agent)

- ✅ Accepts GitHub repository URLs
- ✅ Accepts GitHub file URLs
- ✅ Automatic repository cloning
- ✅ Support for private repositories (with token)
- ✅ All existing features work with GitHub URLs

### Refactoring Crew (Slow Agent)

- ✅ Accepts GitHub file URLs for refactoring
- ✅ Automatic file fetching
- ✅ Support for private repositories (with token)
- ✅ All AI-powered features work with GitHub URLs

### MCP Server

- ✅ All 11 tools now support GitHub URLs
- ✅ GitHub token parameter for private repos
- ✅ Seamless integration with existing workflow

## Usage Examples

### 1. Analyze GitHub Repository

```python
from src.agents.code_scout import CodeScout

# Public repository
scout = CodeScout("https://github.com/pallets/flask")
scout.scan_directory("*.py")

# Analyze impact
impact = scout.analyze_impact("Flask")
print(f"Total usages: {impact['total_usages']}")
print(f"Affected files: {impact['file_count']}")
```

### 2. Analyze Single GitHub File

```python
# Analyze specific file
scout.analyze_github_file(
    "https://github.com/pallets/flask/blob/main/src/flask/app.py"
)
```

### 3. Refactor Code from GitHub

```python
from src.agents.refactoring_crew import RefactoringCrew

crew = RefactoringCrew()

# Refactor file from GitHub
result = crew.full_refactoring_workflow(
    code="https://github.com/owner/repo/blob/main/legacy.py",
    context="Legacy payment processing module"
)

print("Plan:", result['refactoring_plan'])
print("Source:", result['source'])
print("Refactored:", result['refactored_code'])
```

### 4. Private Repository Access

```python
import os

# With GitHub token
scout = CodeScout(
    "https://github.com/your-org/private-repo",
    github_token=os.getenv("GITHUB_TOKEN")
)

crew = RefactoringCrew(
    github_token=os.getenv("GITHUB_TOKEN")
)
```

### 5. MCP Server with GitHub URLs

```json
{
  "name": "scan_directory",
  "arguments": {
    "root_directory": "https://github.com/pallets/flask",
    "pattern": "*.py",
    "github_token": "optional_for_private_repos"
  }
}
```

```json
{
  "name": "analyze_and_plan",
  "arguments": {
    "code": "https://github.com/owner/repo/blob/main/file.py",
    "context": "Legacy function",
    "github_token": "optional_for_private_repos"
  }
}
```

## Supported URL Formats

### Repository URLs

```
https://github.com/owner/repo
https://github.com/owner/repo/tree/branch/path
```

### File URLs

```
https://github.com/owner/repo/blob/main/file.py
https://github.com/owner/repo/blob/branch/path/to/file.py
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# GitHub Configuration (optional)
GITHUB_TOKEN=ghp_your_personal_access_token_here
```

### Getting a GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories)
4. Copy token and add to `.env`

## MCP Tools Updated

All tools now support GitHub URLs:

### Fast Tools (Code Scout)

1. `scan_directory` - Scan GitHub repositories
2. `find_symbol` - After scanning GitHub repo
3. `analyze_impact` - After scanning GitHub repo
4. `grep_search` - On cloned GitHub repo
5. `git_blame` - On cloned GitHub repo
6. `build_dependency_graph` - After scanning GitHub repo

### Slow Tools (Refactoring Crew)

1. `analyze_and_plan` - GitHub file URLs
2. `refactor_code` - GitHub file URLs
3. `full_refactoring_workflow` - GitHub file URLs
4. `generate_tests` - Works with GitHub URLs
5. `architectural_review` - Accepts codebase descriptions

## Implementation Details

### New Components

1. **GitHub Helper Module** (`src/utils/github_helper.py`)

   - URL parsing
   - File fetching
   - Repository cloning
   - Authentication handling

2. **Updated Agents**

   - Code Scout: Auto-clones repos, supports GitHub files
   - Refactoring Crew: Fetches files on-demand

3. **MCP Server**
   - All tools accept `github_token` parameter
   - Seamless URL handling

### How It Works

#### Code Scout

1. Detects GitHub URL in input
2. Clones repository to temporary directory
3. Performs all analysis on cloned repo
4. Cleans up temp directory when done

#### Refactoring Crew

1. Detects GitHub URL in input
2. Fetches file content via GitHub API or raw URL
3. Performs refactoring on fetched content
4. Returns results with source information

## Examples

See `examples/github_integration_example.py` for comprehensive examples:

```bash
# Run GitHub integration examples
python examples/github_integration_example.py
```

## Benefits

1. **No Manual Cloning**: Direct analysis of GitHub repos
2. **Quick Prototyping**: Test on public repos instantly
3. **CI/CD Integration**: Analyze PRs and commits directly
4. **Remote Analysis**: No need for local copies
5. **Private Repos**: Secure access with tokens

## Use Cases

### 1. Code Review Automation

```python
# Analyze PR file before merge
scout.analyze_github_file(pr_file_url)
impact = scout.analyze_impact(changed_function)
```

### 2. Open Source Exploration

```python
# Analyze popular projects
scout = CodeScout("https://github.com/django/django")
scout.scan_directory("*.py")
```

### 3. Legacy Code Assessment

```python
# Refactor legacy files
crew.full_refactoring_workflow(
    code="https://github.com/company/app/blob/main/legacy.py",
    context="Critical payment module"
)
```

### 4. Dependency Analysis

```python
# Understand dependencies in OSS
scout = CodeScout("https://github.com/requests/requests")
graph = scout.build_dependency_graph()
```

## Testing

```bash
# Test GitHub integration
uv run pytest tests/test_github_integration.py

# Manual test
python -c "
from src.agents.code_scout import CodeScout
scout = CodeScout('https://github.com/pallets/flask')
print('Success!')
"
```

## Limitations

1. **Public Repos**: Work without token
2. **Private Repos**: Require GitHub token
3. **Rate Limits**: GitHub API has rate limits (60/hour without auth, 5000/hour with auth)
4. **Large Repos**: May take time to clone
5. **Network**: Requires internet connection

## Performance

- **File Fetch**: < 1 second (via raw API)
- **Repo Clone**: 5-30 seconds (depends on size)
- **Analysis**: Same as local files

## Security

- Tokens stored in environment variables
- Never logged or exposed
- Temp directories auto-cleaned
- HTTPS for all connections

## Migration Guide

### Before (Local Only)

```python
scout = CodeScout("/local/path/to/repo")
```

### After (Supports Both)

```python
# Local path still works
scout = CodeScout("/local/path/to/repo")

# GitHub URL now works too!
scout = CodeScout("https://github.com/owner/repo")
```

No code changes needed! Existing code continues to work.

## Troubleshooting

### Error: Failed to clone repository

- Check GitHub URL is correct
- For private repos, ensure GITHUB_TOKEN is set
- Verify git is installed

### Error: API rate limit exceeded

- Use GitHub token for higher limits
- Wait for rate limit reset
- Use raw URL as fallback

### Error: File not found

- Verify file URL is correct
- Check branch name
- Ensure you have access permissions

## Next Steps

1. Try the examples: `python examples/github_integration_example.py`
2. Update your `.env` with GITHUB_TOKEN
3. Test with your repositories
4. Integrate into CI/CD pipeline

## Questions?

See examples and documentation:

- `examples/github_integration_example.py`
- `README.md` - Updated with GitHub examples
- `examples/mcp_server_usage.md` - MCP integration

Enjoy analyzing GitHub repositories! 🚀
