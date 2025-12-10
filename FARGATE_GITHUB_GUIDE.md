# GitHub URL Support in AWS Fargate

This guide explains the best approaches for handling GitHub URLs when deploying the MCP server to AWS Fargate.

## The Challenge

When using GitHub URLs in Fargate, you face several issues:

1. **Ephemeral Storage** - Container filesystem is temporary
2. **Cold Starts** - Cloning adds latency to first requests
3. **Concurrent Requests** - Multiple clones can conflict
4. **Storage Limits** - Fargate has 20GB ephemeral storage max
5. **Network Costs** - Repeated clones waste bandwidth

## Solutions

### ✅ Solution 1: GitHub Repository Cache (Recommended)

Uses an in-memory/disk cache to reuse cloned repositories within container lifecycle.

**How it works:**

```python
from utils.github_cache import get_github_cache

# First request: Clones repository
cache = get_github_cache()
path = cache.get_or_clone("https://github.com/owner/repo")

# Subsequent requests in same container: Uses cached clone
path = cache.get_or_clone("https://github.com/owner/repo")  # Instant!
```

**Benefits:**

- ✅ First request clones, subsequent requests instant
- ✅ Thread-safe for concurrent requests
- ✅ Automatic cleanup of old repos
- ✅ Configurable cache size limits
- ✅ Works with ephemeral or EFS storage

**Configuration:**

```python
# Ephemeral storage (default)
cache = get_github_cache()  # 5GB cache, 24h retention

# With EFS mount (persistent across containers)
cache = get_github_cache(use_efs=True)  # 50GB cache, 7 day retention
```

**Fargate Task Definition:**

```json
{
  "ephemeralStorage": {
    "sizeInGiB": 20
  }
}
```

---

### ✅ Solution 2: EFS Persistent Cache

Mount Amazon EFS to Fargate tasks for persistent repository cache across all containers.

**Benefits:**

- ✅ Cache survives container restarts
- ✅ Shared across all Fargate tasks
- ✅ Reduces cold start time dramatically
- ✅ No repeated clones

**Setup:**

1. **Create EFS filesystem:**

```bash
aws efs create-file-system \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --tags Key=Name,Value=github-cache
```

2. **Update Fargate task definition:**

```json
{
  "containerDefinitions": [
    {
      "name": "mcp-server",
      "mountPoints": [
        {
          "sourceVolume": "efs-github-cache",
          "containerPath": "/mnt/efs",
          "readOnly": false
        }
      ],
      "environment": [
        {
          "name": "EFS_MOUNT_PATH",
          "value": "/mnt/efs"
        }
      ]
    }
  ],
  "volumes": [
    {
      "name": "efs-github-cache",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxx",
        "transitEncryption": "ENABLED"
      }
    }
  ]
}
```

3. **Use EFS cache in code:**

```python
# Automatically uses EFS if mounted
cache = get_github_cache(use_efs=True)
```

**Cost:** ~$0.30/GB-month + data transfer

---

### ✅ Solution 3: GitHub API + In-Memory Processing

For small repositories, fetch files directly via GitHub API without cloning.

**Benefits:**

- ✅ No cloning needed
- ✅ Very fast for small repos
- ✅ No storage used
- ✅ Works with rate limits

**Limitations:**

- ❌ Limited to repos with <100 files
- ❌ Rate limits (60 req/hour without token, 5000 with token)
- ❌ Can't use git operations

**Implementation:**

```python
from utils.github_helper import GitHubHelper

helper = GitHubHelper(token)
# Fetch single file
content, filename = helper.fetch_file_content(
    "https://github.com/owner/repo/blob/main/file.py"
)

# For full repo analysis, still need clone
```

---

### ✅ Solution 4: Pre-build Common Repos into Container Image

For frequently analyzed repos, include them in the Docker image.

**Benefits:**

- ✅ Zero clone time
- ✅ No network dependency
- ✅ Instant cold start

**Limitations:**

- ❌ Repos become stale
- ❌ Larger image size
- ❌ Only works for public repos

**Dockerfile:**

```dockerfile
FROM python:3.13

# Pre-clone common repositories
RUN git clone --depth 1 https://github.com/popular/repo1 /opt/repos/repo1
RUN git clone --depth 1 https://github.com/popular/repo2 /opt/repos/repo2

COPY . /app
WORKDIR /app

CMD ["python", "-m", "src.mcp_server.http_server"]
```

---

## Performance Comparison

| Approach          | First Request | Subsequent | Storage    | Cost   | Best For     |
| ----------------- | ------------- | ---------- | ---------- | ------ | ------------ |
| Direct Clone      | 10-30s        | 10-30s     | Ephemeral  | Low    | Dev/Testing  |
| Cache (Ephemeral) | 10-30s        | <1s        | Ephemeral  | Low    | Production   |
| Cache (EFS)       | <1s\*         | <1s        | Persistent | Medium | High traffic |
| GitHub API        | 2-5s          | 2-5s       | None       | Low    | Small repos  |
| Pre-built         | <1s           | <1s        | Image      | Medium | Known repos  |

\*After first container clones it

---

## Recommended Architecture for Fargate

### Option A: Cache with Ephemeral Storage (Simple)

Best for: Low to medium traffic, cost-sensitive

```
┌─────────────────────────────────────┐
│         Fargate Task                │
│  ┌──────────────────────────────┐  │
│  │  MCP Server Container        │  │
│  │  - GitHub Cache (/tmp)       │  │
│  │  - 20GB ephemeral storage    │  │
│  │  - Auto cleanup after 24h    │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Configuration:**

```python
# In server initialization
cache = get_github_cache()  # Uses ephemeral storage by default
```

**Pros:**

- Simple setup
- No additional AWS services
- Low cost

**Cons:**

- Cache lost when container stops
- Each new container clones repos again

---

### Option B: Shared EFS Cache (Recommended for Production)

Best for: Production, high traffic, multiple tasks

```
┌─────────────────────────────────────┐
│         Fargate Task 1              │
│  ┌──────────────────────────────┐  │
│  │  MCP Server Container        │  │
│  │  - Mounts EFS                │  │
│  └──────────────────────────────┘  │
└─────────────┬───────────────────────┘
              │
              ├──> EFS: /mnt/efs/github_cache
              │     (Persistent, shared)
              │
┌─────────────┴───────────────────────┐
│         Fargate Task 2              │
│  ┌──────────────────────────────┐  │
│  │  MCP Server Container        │  │
│  │  - Mounts EFS                │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Configuration:**

```python
# Enable EFS cache
cache = get_github_cache(use_efs=True)
```

**Pros:**

- Cache persists across containers
- Shared by all tasks
- Near-instant for popular repos
- Minimal cold start impact

**Cons:**

- Additional EFS cost
- Requires VPC configuration

---

## Implementation in Server

The server already supports caching! Here's how it works:

```python
# src/mcp_server/server.py

async def _execute_code_scout_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
    root_dir = arguments.get("root_directory")
    github_token = arguments.get("github_token")

    if is_github_url(root_dir):
        # Async clone in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        self.code_scout = await loop.run_in_executor(
            None,
            lambda: CodeScout(root_dir, github_token=github_token, use_cache=True)
        )
    else:
        # Local directory
        self.code_scout = CodeScout(root_dir)
```

The `use_cache=True` parameter enables automatic caching!

---

## Environment Variables

Configure cache behavior via environment variables:

```bash
# EFS mount path (if using EFS)
EFS_MOUNT_PATH=/mnt/efs

# GitHub token for private repos
GITHUB_TOKEN=ghp_xxxxx

# Cache configuration
GITHUB_CACHE_DIR=/tmp/github_cache  # Override cache location
GITHUB_CACHE_MAX_AGE_HOURS=24       # Max cache age
GITHUB_CACHE_MAX_SIZE_MB=5000       # Max cache size
```

---

## Deployment Checklist

### For Ephemeral Storage:

- [ ] Set ephemeralStorage to 20GB in task definition
- [ ] Ensure cache is enabled (`use_cache=True`)
- [ ] Monitor storage usage via CloudWatch
- [ ] Set appropriate cache size limits

### For EFS Storage:

- [ ] Create EFS filesystem in same VPC
- [ ] Configure mount targets in all subnets
- [ ] Update task definition with EFS volume
- [ ] Set `EFS_MOUNT_PATH` environment variable
- [ ] Enable EFS encryption in transit
- [ ] Monitor EFS metrics and costs

---

## Monitoring

### CloudWatch Metrics to Track:

```python
# Add custom metrics in code
import boto3
cloudwatch = boto3.client('cloudwatch')

# Track cache hits
cloudwatch.put_metric_data(
    Namespace='MCPServer',
    MetricData=[{
        'MetricName': 'GitHubCacheHit',
        'Value': 1,
        'Unit': 'Count'
    }]
)

# Track cache size
cache_info = cache.get_cache_info()
cloudwatch.put_metric_data(
    Namespace='MCPServer',
    MetricData=[{
        'MetricName': 'GitHubCacheSize',
        'Value': cache_info['total_size_mb'],
        'Unit': 'Megabytes'
    }]
)
```

### Useful Queries:

```python
# Get cache statistics
from utils.github_cache import get_github_cache

cache = get_github_cache()
info = cache.get_cache_info()
print(f"Cached repos: {info['total_repos']}")
print(f"Total size: {info['total_size_mb']}MB")
```

---

## Cost Optimization

### Tips:

1. **Use shallow clones** - `--depth 1` (default in cache)
2. **Set appropriate cache size** - Don't cache more than needed
3. **Use EFS Infrequent Access** - For repos accessed <1/day
4. **Monitor cache hit rate** - If low, consider pre-building
5. **Clean old caches** - Automatic in cache implementation

### Example Costs (us-east-1):

**Ephemeral Storage:**

- 20GB: $0.00 (included in Fargate)

**EFS:**

- 10GB cache: ~$3/month (standard)
- 10GB cache: ~$1.60/month (IA, after 30 days)

**Network:**

- GitHub clone: ~$0.09/GB (out to internet)
- Typical repo: 50MB = $0.0045

**Total for 1000 requests/day:**

- Ephemeral cache: ~$1-2/month
- EFS cache: ~$5-10/month (but much faster!)

---

## Testing

Test GitHub URL handling:

```python
# Test cache functionality
from utils.github_cache import get_github_cache

cache = get_github_cache()

# First call: Clones
path1 = cache.get_or_clone("https://github.com/owner/repo")

# Second call: Instant (from cache)
path2 = cache.get_or_clone("https://github.com/owner/repo")

assert path1 == path2  # Same cached path

# Check cache info
info = cache.get_cache_info()
print(info)
```

---

## Summary

**For Development:**

- Use direct cloning or ephemeral cache
- Simple, no extra setup

**For Production (Low Traffic):**

- Use ephemeral cache with 20GB storage
- Enable `use_cache=True` in CodeScout

**For Production (High Traffic):**

- Use EFS-backed cache
- Configure EFS mount in Fargate
- Set `use_efs=True` in cache

**Best Practice:**

```python
# Automatic: Uses EFS if mounted, ephemeral otherwise
cache = get_github_cache(
    use_efs=bool(os.getenv('EFS_MOUNT_PATH'))
)
```

The cache system handles everything automatically - just enable it and deploy!
