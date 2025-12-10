# GitHub URL Support Guide

This guide explains how to work with GitHub repositories in the Legacy Code Modernizer MCP server.

## Overview

The MCP server supports three ways to work with GitHub repositories:

1. **Direct GitHub URL** - Server clones automatically
2. **Local Clone** - Clone first, then scan (recommended)
3. **Single File Analysis** - For individual files only

---

## Method 1: Direct GitHub URL

### How It Works

Pass a GitHub repository URL directly to the `scan_directory` tool. The server will:

- Automatically clone the repository to a temporary directory
- Scan the files
- Clean up the temporary directory after completion

### Pros & Cons

✅ **Pros:**

- Simple - just paste the URL
- No local setup required
- Works for public and private repos (with token)

❌ **Cons:**

- Slower (clones every time)
- Network dependent
- May timeout on large repositories
- Potential cleanup issues on errors

### Usage Example

#### In Interactive Client:

```bash
$ uv run python examples/mcp_client_interactive.py

mcp> scan
Directory path (default: .): https://github.com/owner/repo
⚠️  GitHub URL detected!
This will clone the entire repository (can be slow).

Recommendation: Clone locally first:
  git clone https://github.com/owner/repo /tmp/repo
  Then scan: /tmp/repo

Continue anyway? (y/n): y
GitHub token (press Enter if public repo): [your-token-here]
File pattern (default: *.py): *.py
```

#### Programmatically:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async with stdio_client(server_params) as (stdio, write):
    async with ClientSession(stdio, write) as session:
        await session.initialize()

        result = await session.call_tool(
            "scan_directory",
            arguments={
                "root_directory": "https://github.com/owner/repo",
                "pattern": "*.py",
                "github_token": "ghp_xxxxx"  # Optional for private repos
            }
        )
```

### Best For

- Small repositories (<100 files)
- Quick one-time scans
- Testing/demos

---

## Method 2: Local Clone (Recommended)

### How It Works

Clone the repository to your local machine first, then scan the local directory.

### Pros & Cons

✅ **Pros:**

- **Much faster** (~10x faster than direct URL)
- More reliable (no network issues during scan)
- Can reuse the clone for multiple operations
- Better error handling
- Can inspect/modify code locally

❌ **Cons:**

- Requires extra step
- Uses local disk space
- Manual cleanup needed

### Usage Example

#### Step 1: Clone Repository

```bash
# Clone to temporary location
git clone https://github.com/owner/repo /tmp/repo

# Or clone with specific branch
git clone --branch main https://github.com/owner/repo /tmp/repo

# For shallow clone (faster)
git clone --depth 1 https://github.com/owner/repo /tmp/repo
```

#### Step 2: Scan Local Directory

```bash
$ uv run python examples/mcp_client_interactive.py

mcp> scan
Directory path (default: .): /tmp/repo
File pattern (default: *.py): *.py

# Fast scan of local files!
```

#### Step 3: Cleanup (Optional)

```bash
rm -rf /tmp/repo
```

#### Automated Script:

See `examples/github_scan_example.py` for a complete automated example:

```python
import subprocess
import tempfile
import shutil
from pathlib import Path

# Clone
temp_dir = tempfile.mkdtemp()
local_path = Path(temp_dir) / "repo"
subprocess.run([
    'git', 'clone', '--depth', '1',
    'https://github.com/owner/repo',
    str(local_path)
], check=True)

# Scan using MCP
result = await session.call_tool(
    "scan_directory",
    arguments={"root_directory": str(local_path), "pattern": "*.py"}
)

# Cleanup
shutil.rmtree(temp_dir)
```

### Best For

- Large repositories
- Multiple operations on same repo
- Production workflows
- Repeated scans during development

---

## Method 3: Single File Analysis

### How It Works

Use the `analyze_and_plan` tool to analyze a single file from GitHub without cloning the entire repository.

### Pros & Cons

✅ **Pros:**

- Very fast (no full clone)
- Perfect for single file analysis
- Works with GitHub file URLs directly

❌ **Cons:**

- Only works for single files
- Requires AI tools (needs AWS Bedrock)
- Can't do cross-file analysis

### Usage Example

```python
result = await session.call_tool(
    "analyze_and_plan",
    arguments={
        "code": "https://github.com/owner/repo/blob/main/src/file.py",
        "context": "Analyze this legacy code",
        "github_token": "ghp_xxxxx"  # Optional for private repos
    }
)
```

### Best For

- Single file refactoring
- Quick code reviews
- Focused analysis without full repository context

---

## Private Repositories

All three methods support private repositories using GitHub personal access tokens.

### Creating a Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` - Full control of private repositories
4. Copy the token (starts with `ghp_`)

### Using the Token

#### Method 1: Environment Variable

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
uv run python examples/mcp_client_interactive.py
```

#### Method 2: Pass as Parameter

```python
arguments={
    "root_directory": "https://github.com/owner/private-repo",
    "github_token": "ghp_xxxxxxxxxxxxx"
}
```

#### Method 3: Git Credential Helper

```bash
# Configure git to use the token
git config --global credential.helper store
echo "https://YOUR_TOKEN@github.com" > ~/.git-credentials

# Now git clone will use the token automatically
git clone https://github.com/owner/private-repo /tmp/repo
```

---

## Troubleshooting

### Issue: "Operation timed out after 5 minutes"

**Cause:** Repository is too large or network is slow.

**Solution:**

1. Use Method 2 (local clone) instead
2. Clone with `--depth 1` for shallow clone
3. Clone only specific branch: `--branch main --single-branch`

### Issue: "Failed to clone GitHub repository"

**Causes:**

- Invalid URL
- Network issues
- Private repo without token
- Rate limiting

**Solutions:**

```bash
# Test clone manually first
git clone https://github.com/owner/repo /tmp/test-clone

# For private repos, ensure token works
git clone https://YOUR_TOKEN@github.com/owner/repo /tmp/test-clone

# Check GitHub token permissions
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### Issue: Async cleanup errors

**Cause:** Server encountered error during GitHub operation.

**Solution:**

- Use Method 2 (local clone) for better reliability
- The interactive client now has timeout handling
- Temporary directories are cleaned up automatically

### Issue: "Rate limit exceeded"

**Cause:** Too many GitHub API calls without authentication.

**Solutions:**

1. Provide a GitHub token (increases rate limit from 60 to 5000 req/hour)
2. Use Method 2 (local clone) which doesn't use API
3. Wait for rate limit to reset (check headers: `X-RateLimit-Reset`)

---

## Performance Comparison

| Method      | Speed       | Reliability | Best Use Case            |
| ----------- | ----------- | ----------- | ------------------------ |
| Direct URL  | ⚡ Slow     | ⚠️ Medium   | Small repos, quick tests |
| Local Clone | ⚡⚡⚡ Fast | ✅ High     | Large repos, production  |
| Single File | ⚡⚡ Medium | ✅ High     | Individual file analysis |

### Benchmark Example

Repository: 50 Python files, ~10,000 LOC

- **Method 1 (Direct URL):** ~30-45 seconds
- **Method 2 (Local Clone):** ~3-5 seconds (after clone)
- **Method 3 (Single File):** ~2-3 seconds per file

---

## Complete Examples

### Example 1: Scan Public Repository

```bash
# Direct URL (simple but slow)
mcp> scan
Directory path: https://github.com/psf/requests
File pattern: *.py

# OR Local Clone (faster)
$ git clone --depth 1 https://github.com/psf/requests /tmp/requests
mcp> scan
Directory path: /tmp/requests
File pattern: *.py
```

### Example 2: Scan Private Repository

```bash
# Set token first
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# Then scan
mcp> scan
Directory path: https://github.com/myorg/private-repo
GitHub token: ghp_xxxxxxxxxxxxx
File pattern: *.py
```

### Example 3: Automated Workflow

```python
# See examples/github_scan_example.py
async def scan_and_analyze(repo_url: str):
    # Clone locally
    local_path = clone_repository(repo_url)

    # Scan
    scan_results = await mcp_scan(local_path)

    # Find specific symbols
    symbols = await mcp_find_symbol(local_path, "MyClass")

    # Build dependency graph
    graph = await mcp_build_graph(local_path)

    # Cleanup
    cleanup(local_path)

    return scan_results, symbols, graph
```

---

## Tips & Best Practices

1. **Start Local:** Always prefer Method 2 (local clone) for reliability
2. **Shallow Clones:** Use `git clone --depth 1` to speed up cloning
3. **Token Security:** Never commit tokens to code, use environment variables
4. **Cleanup:** Always cleanup temporary directories after use
5. **Network:** Direct URLs work best on fast, stable networks
6. **Testing:** Test with small repos first before scanning large codebases
7. **Timeouts:** The interactive client has 5-minute timeout for operations
8. **Error Handling:** Wrap calls in try/except for production use

---

## See Also

- `examples/mcp_client_interactive.py` - Interactive client with GitHub support
- `examples/github_scan_example.py` - Complete examples of all three methods
- `src/agents/code_scout.py` - Implementation of GitHub URL handling
- `src/utils/github_helper.py` - GitHub API utilities

---

## Quick Reference

```bash
# Interactive client with help
$ uv run python examples/mcp_client_interactive.py
mcp> help

# Run example scripts
$ python examples/github_scan_example.py

# Manual workflow (recommended)
$ git clone https://github.com/owner/repo /tmp/repo
$ uv run python examples/mcp_client_interactive.py
mcp> scan
Directory path: /tmp/repo
```
