"""
GitHub Repository Cache for Fargate Deployment

This module provides caching for GitHub repositories to avoid repeated clones
in containerized environments like AWS Fargate.
"""

import os
import hashlib
import subprocess
import threading
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta
import shutil


class GitHubRepositoryCache:
    """
    Cache GitHub repositories in container lifecycle.
    
    Benefits for Fargate:
    1. Reuses clones across multiple requests in same container
    2. Reduces cold start time after first request
    3. Thread-safe for concurrent requests
    4. Automatic cleanup of old repos
    5. Configurable cache location (EFS mount or ephemeral)
    """
    
    def __init__(
        self, 
        cache_dir: str = "/tmp/github_cache",
        max_age_hours: int = 24,
        max_cache_size_mb: int = 5000  # 5GB max
    ):
        """
        Initialize GitHub cache.
        
        Args:
            cache_dir: Directory to store cached repositories
            max_age_hours: Maximum age of cached repos before refresh
            max_cache_size_mb: Maximum total cache size in MB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)
        self.max_cache_size_mb = max_cache_size_mb
        self.lock = threading.Lock()
        self._cache_metadata: Dict[str, dict] = {}
    
    def _get_cache_key(self, repo_url: str, ref: Optional[str] = None) -> str:
        """Generate cache key from repository URL and ref."""
        key_string = f"{repo_url}:{ref or 'default'}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path for cached repository."""
        return self.cache_dir / cache_key
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cached repository is still valid."""
        if not cache_path.exists():
            return False
        
        # Check age
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        
        return age < self.max_age
    
    def _cleanup_old_caches(self):
        """Remove old or oversized caches."""
        if not self.cache_dir.exists():
            return
        
        # Get all cached repos sorted by modification time
        cached_repos = []
        for repo_dir in self.cache_dir.iterdir():
            if repo_dir.is_dir():
                stat = repo_dir.stat()
                cached_repos.append({
                    'path': repo_dir,
                    'mtime': stat.st_mtime,
                    'size_mb': sum(f.stat().st_size for f in repo_dir.rglob('*') if f.is_file()) / (1024 * 1024)
                })
        
        # Sort by modification time (oldest first)
        cached_repos.sort(key=lambda x: x['mtime'])
        
        # Calculate total size
        total_size_mb = sum(repo['size_mb'] for repo in cached_repos)
        
        # Remove old repos until under size limit
        while total_size_mb > self.max_cache_size_mb and cached_repos:
            oldest = cached_repos.pop(0)
            try:
                shutil.rmtree(oldest['path'])
                total_size_mb -= oldest['size_mb']
                print(f"Removed old cache: {oldest['path'].name} ({oldest['size_mb']:.1f}MB)")
            except Exception as e:
                print(f"Failed to remove cache {oldest['path']}: {e}")
    
    def get_or_clone(
        self, 
        repo_url: str, 
        ref: Optional[str] = None,
        github_token: Optional[str] = None,
        shallow: bool = True
    ) -> Optional[str]:
        """
        Get cached repository or clone if not cached.
        
        Args:
            repo_url: GitHub repository URL
            ref: Branch, tag, or commit ref
            github_token: GitHub token for private repos
            shallow: Use shallow clone (--depth 1)
            
        Returns:
            Path to cached repository or None on failure
        """
        cache_key = self._get_cache_key(repo_url, ref)
        cache_path = self._get_cache_path(cache_key)
        
        with self.lock:
            # Check if valid cache exists
            if self._is_cache_valid(cache_path):
                print(f"✓ Using cached repository: {cache_key}")
                return str(cache_path)
            
            # Clone repository
            print(f"⬇ Cloning repository to cache: {repo_url}")
            
            # Remove old cache if exists
            if cache_path.exists():
                shutil.rmtree(cache_path)
            
            # Prepare git clone command
            clone_url = repo_url
            if github_token and 'github.com' in repo_url:
                # Inject token into URL
                clone_url = repo_url.replace('https://', f'https://{github_token}@')
            
            cmd = ['git', 'clone']
            
            if shallow:
                cmd.extend(['--depth', '1'])
            
            if ref:
                cmd.extend(['--branch', ref, '--single-branch'])
            
            cmd.extend([clone_url, str(cache_path)])
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    print(f"✗ Clone failed: {result.stderr}")
                    return None
                
                print(f"✓ Repository cloned successfully")
                
                # Cleanup old caches if needed
                self._cleanup_old_caches()
                
                return str(cache_path)
                
            except subprocess.TimeoutExpired:
                print(f"✗ Clone timeout: Repository too large")
                return None
            except Exception as e:
                print(f"✗ Clone error: {e}")
                return None
    
    def clear_cache(self, cache_key: Optional[str] = None):
        """
        Clear cache.
        
        Args:
            cache_key: Specific cache to clear, or None to clear all
        """
        with self.lock:
            if cache_key:
                cache_path = self._get_cache_path(cache_key)
                if cache_path.exists():
                    shutil.rmtree(cache_path)
            else:
                # Clear all caches
                if self.cache_dir.exists():
                    shutil.rmtree(self.cache_dir)
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_info(self) -> dict:
        """Get information about current cache state."""
        if not self.cache_dir.exists():
            return {
                'total_repos': 0,
                'total_size_mb': 0,
                'repos': []
            }
        
        repos = []
        total_size = 0
        
        for repo_dir in self.cache_dir.iterdir():
            if repo_dir.is_dir():
                size = sum(f.stat().st_size for f in repo_dir.rglob('*') if f.is_file())
                size_mb = size / (1024 * 1024)
                total_size += size_mb
                
                repos.append({
                    'key': repo_dir.name,
                    'size_mb': round(size_mb, 2),
                    'mtime': datetime.fromtimestamp(repo_dir.stat().st_mtime).isoformat()
                })
        
        return {
            'total_repos': len(repos),
            'total_size_mb': round(total_size, 2),
            'max_size_mb': self.max_cache_size_mb,
            'repos': sorted(repos, key=lambda x: x['mtime'], reverse=True)
        }


# Global cache instance for Fargate deployment
_global_cache: Optional[GitHubRepositoryCache] = None


def get_github_cache(
    cache_dir: Optional[str] = None,
    use_efs: bool = False
) -> GitHubRepositoryCache:
    """
    Get or create global GitHub cache instance.
    
    Args:
        cache_dir: Custom cache directory (optional)
        use_efs: Use EFS mount point for persistent cache (Fargate with EFS)
        
    Returns:
        GitHubRepositoryCache instance
    """
    global _global_cache
    
    if _global_cache is None:
        # Determine cache directory
        if cache_dir:
            cache_location = cache_dir
        elif use_efs:
            # Use EFS mount point if available
            efs_mount = os.getenv('EFS_MOUNT_PATH', '/mnt/efs')
            cache_location = f"{efs_mount}/github_cache"
        else:
            # Use ephemeral storage
            cache_location = "/tmp/github_cache"
        
        # Adjust limits based on environment
        if use_efs:
            # EFS has much more space
            max_cache_size = 50000  # 50GB
            max_age_hours = 168  # 1 week
        else:
            # Ephemeral storage is limited
            max_cache_size = 5000  # 5GB
            max_age_hours = 24  # 1 day
        
        _global_cache = GitHubRepositoryCache(
            cache_dir=cache_location,
            max_age_hours=max_age_hours,
            max_cache_size_mb=max_cache_size
        )
    
    return _global_cache
