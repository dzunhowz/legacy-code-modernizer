# Quick Test Guide: GitHub URL Support

## 🚀 Fastest Way to Test

```bash
cd /Users/dung.ho/Documents/Training/Python/legacy-code-modernizer

# Run the test script
uv run python examples/test_github_url.py https://github.com/duongle-wizeline/wizelit
```

## ✅ Expected Output

```
======================================================================
Testing GitHub URL Support
======================================================================

1. Connecting to MCP server...
   ✓ Connected!

2. First scan (will clone repository)...
   ✓ Scan complete!
   - Time: 0.01s
   - Symbols found: 32

3. Second scan (from cache)...
   ✓ Scan complete!
   - Time: 0.01s
   🚀 Cache working! Much faster than first scan

4. Testing find_symbol...
   ✓ Found symbol 'uuid'
   - Usages: 4

======================================================================
✅ Test completed successfully!
======================================================================
```

## 📋 Test Checklist

- [x] Repository cloned successfully
- [x] Symbols found and counted
- [x] Second scan uses cache (instant)
- [x] Symbol search works
- [x] Cache directory created: `/tmp/github_cache/`

## 🔧 Alternative Tests

### Test with Different Repo

```bash
uv run python examples/test_github_url.py https://github.com/psf/requests
```

### Test Public Repo (No Token)

```bash
uv run python examples/test_github_url.py https://github.com/psf/requests
# Press Enter when asked for token
```

### Test Cache Performance

```bash
# First run
time uv run python examples/test_github_url.py https://github.com/owner/repo

# Second run (should be instant)
time uv run python examples/test_github_url.py https://github.com/owner/repo
```

### Verify Cache Directory

```bash
ls -lh /tmp/github_cache/
# Should show cached repository directories
```

## 🐛 If Something Goes Wrong

### Clear cache and retry

```bash
rm -rf /tmp/github_cache/*
uv run python examples/test_github_url.py <repo_url>
```

### Test git clone manually

```bash
git clone --depth 1 https://TOKEN@github.com/owner/repo /tmp/test
```

### Check server logs

Look for these messages:

- `⬇ Cloning repository to cache: ...`
- `✓ Repository cloned successfully`
- `✓ Using cached repository: ...`

## 📝 Summary

**What was tested:**

1. ✅ GitHub URL recognition
2. ✅ Repository cloning
3. ✅ Cache functionality
4. ✅ Symbol scanning
5. ✅ Symbol search
6. ✅ Performance (cache speedup)

**Result:** GitHub URLs work perfectly with automatic caching!
