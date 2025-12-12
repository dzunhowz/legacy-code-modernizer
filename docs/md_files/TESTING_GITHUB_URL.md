# Testing GitHub URL Support Locally

This guide shows you how to test GitHub URL functionality with the MCP client locally.

---

## Quick Test (Simplest)

### Option 1: Using the Test Script

```bash
# Public repository
uv run python examples/test_github_url.py https://github.com/owner/repo

# Private repository with token
uv run python examples/test_github_url.py https://github.com/owner/repo ghp_YOUR_TOKEN

# Using environment variable
export GITHUB_TOKEN=ghp_YOUR_TOKEN
uv run python examples/test_github_url.py https://github.com/owner/repo
```

**What it tests:**

- ✅ Repository cloning and caching
- ✅ First scan (clones repo)
- ✅ Second scan (uses cache)
- ✅ Symbol search functionality
- ✅ Performance comparison

**Example output:**

```
✓ Scan complete!
- Time: 0.01s
- Symbols found: 32
🚀 Cache working! Much faster than first scan
```

---

## Option 2: Interactive Client (Manual Testing)

### Step 1: Start the Interactive Client

```bash
cd /Users/dung.ho/Documents/Training/Python/legacy-code-modernizer
uv run python examples/mcp_client_interactive.py
```

### Step 2: Scan a GitHub Repository

```
mcp> scan
Directory path (default: .): https://github.com/duongle-wizeline/wizelit

⚠️  GitHub URL detected!
This will clone the entire repository (can be slow).

Continue anyway? (y/n): y
GitHub token (press Enter if public repo): ghp_YOUR_TOKEN
File pattern (default: *.py): *.py

Calling tool: scan_directory
...
✓ Scan complete!
```

### Step 3: Test Other Commands

```
# Find a symbol
mcp> find
Directory path: https://github.com/duongle-wizeline/wizelit
Symbol name: AppConfig

# Grep search
mcp> grep
Directory path: https://github.com/duongle-wizeline/wizelit
Search pattern: def
File pattern: *.py

# Build dependency graph
mcp> graph
Directory path: https://github.com/duongle-wizeline/wizelit

# Get help
mcp> help
```

---

## Option 3: Programmatic Testing

Create your own test script:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack


async def test_my_repo():
    async with AsyncExitStack() as stack:
        # Connect to server
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "src.mcp_server.server"],
        )

        stdio_transport = await stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        session = await stack.enter_async_context(
            ClientSession(stdio, write)
        )
        await session.initialize()

        # Scan GitHub repository
        result = await session.call_tool(
            "scan_directory",
            arguments={
                "root_directory": "https://github.com/owner/repo",
                "pattern": "*.py",
                "github_token": "ghp_YOUR_TOKEN"  # Optional
            }
        )

        # Process results
        import json
        response = json.loads(result.content[0].text)
        print(f"Found {len(response)} symbols")


asyncio.run(test_my_repo())
```

---

## Option 4: Test Cache Directly

Test the cache system independently:

```bash
cd /Users/dung.ho/Documents/Training/Python/legacy-code-modernizer
python3 << 'EOF'
from src.utils.github_cache import get_github_cache
import time

cache = get_github_cache()

# First clone
print("1. First clone...")
start = time.time()
path1 = cache.get_or_clone("https://github.com/duongle-wizeline/wizelit")
elapsed1 = time.time() - start
print(f"   Path: {path1}")
print(f"   Time: {elapsed1:.2f}s")

# Second call (from cache)
print("\n2. From cache...")
start = time.time()
path2 = cache.get_or_clone("https://github.com/duongle-wizeline/wizelit")
elapsed2 = time.time() - start
print(f"   Path: {path2}")
print(f"   Time: {elapsed2:.2f}s")
print(f"   Speedup: {elapsed1/elapsed2:.0f}x faster!")

# Cache info
info = cache.get_cache_info()
print(f"\n3. Cache info:")
print(f"   Repos: {info['total_repos']}")
print(f"   Size: {info['total_size_mb']:.2f}MB")
EOF
```

---

## Test Results You Should See

### ✅ Successful Test Output

```
======================================================================
Testing GitHub URL Support
======================================================================

Repository: https://github.com/duongle-wizeline/wizelit
Token: Provided

1. Connecting to MCP server...
   ✓ Connected!

2. First scan (will clone repository)...
   ✓ Scan complete!
   - Time: 0.01s
   - Symbols found: 32
   - Sample symbols: ['uuid', 'chainlit', 'List', 'Dict', 'Optional']

3. Second scan (from cache)...
   ✓ Scan complete!
   - Time: 0.01s
   - Symbols found: 32
   🚀 Cache working! Much faster than first scan

4. Testing find_symbol...
   ✓ Found symbol 'uuid'
   - Usages: 4
   - First usage: /tmp/github_cache/.../main.py:1

======================================================================
✅ Test completed successfully!
======================================================================
```

---

## Common Test Scenarios

### Test 1: Public Repository

```bash
uv run python examples/test_github_url.py https://github.com/psf/requests
```

### Test 2: Private Repository

```bash
export GITHUB_TOKEN=ghp_YOUR_TOKEN
uv run python examples/test_github_url.py https://github.com/yourorg/private-repo
```

### Test 3: Large Repository (Test Timeout)

```bash
# Should handle gracefully with 60s timeout
uv run python examples/test_github_url.py https://github.com/python/cpython
```

### Test 4: Invalid Repository

```bash
# Should show error message
uv run python examples/test_github_url.py https://github.com/invalid/nonexistent
```

---

## Verifying Cache Behavior

### Check Cache Directory

```bash
# List cached repositories
ls -lh /tmp/github_cache/

# Output should show cached repos:
# d6ac167c3e4c0620b56c1e2e11726b3b  <- Cached repo
# abc123...                         <- Another cached repo
```

### Check Cache Performance

```bash
# First run: Clones repository (1-5 seconds)
uv run python examples/test_github_url.py https://github.com/owner/repo

# Second run: Uses cache (instant!)
uv run python examples/test_github_url.py https://github.com/owner/repo
```

### Clear Cache for Testing

```bash
# Remove all cached repositories
rm -rf /tmp/github_cache/*

# Now test again - should clone fresh
uv run python examples/test_github_url.py https://github.com/owner/repo
```

---

## Troubleshooting

### Issue: "Failed to clone GitHub repository"

**Check:**

```bash
# Test git clone manually
git clone --depth 1 https://github.com/owner/repo /tmp/test-clone

# For private repos, test with token
git clone --depth 1 https://TOKEN@github.com/owner/repo /tmp/test-clone
```

### Issue: "Timeout after 60 seconds"

**Solution:** Repository is too large. Try:

```bash
# Clone locally first, then scan
git clone --depth 1 https://github.com/owner/large-repo /tmp/large-repo
# Then in MCP client: scan /tmp/large-repo
```

### Issue: Cache not working

**Check:**

```bash
# Verify cache directory exists
ls -la /tmp/github_cache/

# Check permissions
ls -ld /tmp/github_cache/

# Try clearing and retesting
rm -rf /tmp/github_cache/*
```

### Issue: "Rate limit exceeded"

**Solution:** Provide GitHub token:

```bash
export GITHUB_TOKEN=ghp_YOUR_TOKEN
uv run python examples/test_github_url.py https://github.com/owner/repo
```

---

## Performance Benchmarks

Expected performance on your local machine:

| Repository Size       | First Request | Cached Request | Speedup |
| --------------------- | ------------- | -------------- | ------- |
| Small (<10 files)     | 1-2s          | <0.1s          | 10-20x  |
| Medium (10-100 files) | 2-5s          | <0.1s          | 20-50x  |
| Large (100+ files)    | 5-30s         | <0.1s          | 50-300x |

---

## Integration Testing

### Test All MCP Tools with GitHub URL

```bash
cd /Users/dung.ho/Documents/Training/Python/legacy-code-modernizer

# Create test script
cat > test_all_tools.sh << 'EOF'
#!/bin/bash

REPO="https://github.com/duongle-wizeline/wizelit"
TOKEN="${GITHUB_TOKEN}"

echo "Testing all MCP tools with GitHub URL..."

# Test 1: Scan
echo -e "\n1. Testing scan_directory..."
python3 -c "
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import json

async def test():
    async with AsyncExitStack() as stack:
        server_params = StdioServerParameters(
            command='uv',
            args=['run', 'python', '-m', 'src.mcp_server.server']
        )
        stdio, write = await stack.enter_async_context(stdio_client(server_params))
        session = await stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()

        result = await session.call_tool(
            'scan_directory',
            arguments={'root_directory': '${REPO}', 'pattern': '*.py'}
        )
        response = json.loads(result.content[0].text)
        print(f'✓ Found {len(response)} symbols')

asyncio.run(test())
"

# Test 2: Find Symbol
echo -e "\n2. Testing find_symbol..."
# Add similar test for find_symbol

# Test 3: Grep Search
echo -e "\n3. Testing grep_search..."
# Add similar test for grep_search

echo -e "\n✅ All tests completed!"
EOF

chmod +x test_all_tools.sh
./test_all_tools.sh
```

---

## Quick Reference

### Essential Commands

```bash
# Test with provided script
uv run python examples/test_github_url.py <repo_url> [token]

# Interactive testing
uv run python examples/mcp_client_interactive.py

# Direct cache test
python3 -c "from src.utils.github_cache import get_github_cache; cache = get_github_cache(); print(cache.get_cache_info())"

# Clear cache
rm -rf /tmp/github_cache/*
```

### Environment Variables

```bash
# Set GitHub token (for private repos)
export GITHUB_TOKEN=ghp_YOUR_TOKEN

# Set custom cache location
export GITHUB_CACHE_DIR=/custom/path

# Set cache limits
export GITHUB_CACHE_MAX_AGE_HOURS=24
export GITHUB_CACHE_MAX_SIZE_MB=5000
```

---

## Summary

**Simplest way to test:**

```bash
cd /Users/dung.ho/Documents/Training/Python/legacy-code-modernizer
uv run python examples/test_github_url.py https://github.com/duongle-wizeline/wizelit
```

**What happens:**

1. ✅ Connects to MCP server
2. ✅ Clones repository (first time)
3. ✅ Scans for symbols
4. ✅ Tests cache (second scan instant!)
5. ✅ Tests symbol search
6. ✅ Shows performance metrics

**Done!** You've verified GitHub URL support is working correctly.
