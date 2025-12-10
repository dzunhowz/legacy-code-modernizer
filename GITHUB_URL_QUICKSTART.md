# Quick Answer: Using GitHub URLs with MCP Server

## Three Ways to Handle GitHub Repositories

### 1. Direct GitHub URL (Simple but Slower)

Your MCP server **already supports** GitHub URLs out of the box:

```bash
mcp> scan
Directory path: https://github.com/duongle-wizeline/wizelit
```

**What happens:** Server clones repo → scans files → returns results → cleans up

**Issue you hit:** The clone/cleanup process can fail with async errors on large repos or interruptions.

---

### 2. Clone Locally First (✅ Recommended)

```bash
# Step 1: Clone locally
$ git clone https://github.com/duongle-wizeline/wizelit /tmp/wizelit

# Step 2: Scan local directory
mcp> scan
Directory path: /tmp/wizelit
```

**Benefits:**

- 10x faster
- More reliable
- Better error handling
- Can reuse for multiple operations

---

### 3. Single File Analysis

```python
# For analyzing individual files only
await session.call_tool(
    "analyze_and_plan",
    arguments={
        "code": "https://github.com/owner/repo/blob/main/file.py",
        "github_token": "ghp_xxxxx"  # if private
    }
)
```

---

## Your Error Explained

The error you encountered:

```
RuntimeError: Attempted to exit cancel scope in a different task
asyncio.exceptions.CancelledError
```

**Root cause:** When passing a GitHub URL, the server:

1. Starts cloning the repository
2. The operation is slow/large
3. Something interrupted it (timeout, Ctrl+C, error)
4. The async cleanup failed due to task cancellation

**Solution:** Use Method 2 (clone locally first)

---

## Quick Fix for Your Case

```bash
# 1. Clone the repo
git clone --depth 1 https://github.com/duongle-wizeline/wizelit /tmp/wizelit

# 2. Run MCP client
uv run python examples/mcp_client_interactive.py

# 3. Scan local directory
mcp> scan
Directory path: /tmp/wizelit
File pattern: *.py

# 4. Done! Much faster and more reliable
```

---

## Updated Interactive Client

Your `examples/mcp_client_interactive.py` now has:

✅ **GitHub URL warning** - Prompts user before cloning  
✅ **Timeout handling** - 5-minute timeout for operations  
✅ **Better error messages** - Shows helpful tips  
✅ **Help command** - `mcp> help` shows GitHub usage

Try it:

```bash
$ uv run python examples/mcp_client_interactive.py
mcp> help
```

---

## Complete Examples

See these new files:

- **`GITHUB_URL_GUIDE.md`** - Comprehensive guide with all methods
- **`examples/github_scan_example.py`** - Working code examples

---

## For Private Repos

Add your GitHub token:

```bash
# Option 1: Environment variable
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# Option 2: Pass to tool
mcp> scan
GitHub token: ghp_xxxxxxxxxxxxx
```

Get token: https://github.com/settings/tokens (need `repo` scope)

---

## Summary

**Your original question:** _"How can we use GitHub URLs with MCP server?"_

**Answer:**

1. **It already works** - just pass the URL to `scan_directory`
2. **But it's slow/unreliable** - Better to clone locally first
3. **Your error was** - async cleanup failure during interrupted clone
4. **Best practice** - Clone → Scan local → Much faster

**Use this workflow:**

```bash
git clone <github-url> /tmp/repo && \
uv run python examples/mcp_client_interactive.py
# Then scan /tmp/repo
```
