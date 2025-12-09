"""
GitHub Helper Utilities
Handles fetching files and repositories from GitHub URLs.
"""

import re
import os
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import tempfile
import shutil
import subprocess
from github import Github, GithubException
import requests


class GitHubHelper:
    """Helper class for GitHub operations."""
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub helper.
        
        Args:
            github_token: GitHub personal access token (optional, for private repos)
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github = Github(self.github_token) if self.github_token else Github()
    
    @staticmethod
    def parse_github_url(url: str) -> Optional[Dict[str, str]]:
        """
        Parse a GitHub URL to extract components.
        
        Args:
            url: GitHub URL (repository, file, or directory)
            
        Returns:
            Dictionary with parsed components or None
            
        Examples:
            https://github.com/owner/repo
            https://github.com/owner/repo/blob/main/file.py
            https://github.com/owner/repo/tree/main/directory
        """
        patterns = [
            # File URL: https://github.com/owner/repo/blob/branch/path/to/file.py
            r'github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/(?P<ref>[^/]+)/(?P<path>.+)',
            # Directory URL: https://github.com/owner/repo/tree/branch/path/to/dir
            r'github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/tree/(?P<ref>[^/]+)/(?P<path>.+)',
            # Repository URL: https://github.com/owner/repo
            r'github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/?$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.groupdict()
        
        return None
    
    def fetch_file_content(self, url: str) -> Optional[Tuple[str, str]]:
        """
        Fetch content of a single file from GitHub.
        
        Args:
            url: GitHub file URL
            
        Returns:
            Tuple of (content, filename) or None
        """
        parsed = self.parse_github_url(url)
        if not parsed or 'path' not in parsed:
            return None
        
        try:
            repo = self.github.get_repo(f"{parsed['owner']}/{parsed['repo']}")
            ref = parsed.get('ref', repo.default_branch)
            file_content = repo.get_contents(parsed['path'], ref=ref)
            
            if isinstance(file_content, list):
                # It's a directory, not a file
                return None
            
            content = file_content.decoded_content.decode('utf-8')
            filename = Path(parsed['path']).name
            
            return content, filename
            
        except GithubException as e:
            print(f"GitHub API error: {e}")
            return None
        except Exception as e:
            print(f"Error fetching file: {e}")
            return None
    
    def fetch_raw_content(self, url: str) -> Optional[str]:
        """
        Fetch raw content using direct HTTP request (no auth required).
        
        Args:
            url: GitHub file URL
            
        Returns:
            File content as string or None
        """
        parsed = self.parse_github_url(url)
        if not parsed or 'path' not in parsed:
            return None
        
        # Convert to raw URL
        ref = parsed.get('ref', 'main')
        raw_url = f"https://raw.githubusercontent.com/{parsed['owner']}/{parsed['repo']}/{ref}/{parsed['path']}"
        
        try:
            response = requests.get(raw_url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching raw content: {e}")
            return None
    
    def clone_repository(self, url: str, target_dir: Optional[str] = None) -> Optional[str]:
        """
        Clone a GitHub repository to a local directory.
        
        Args:
            url: GitHub repository URL
            target_dir: Target directory (optional, creates temp dir if not provided)
            
        Returns:
            Path to cloned repository or None
        """
        parsed = self.parse_github_url(url)
        if not parsed:
            return None
        
        repo_url = f"https://github.com/{parsed['owner']}/{parsed['repo']}.git"
        
        if target_dir is None:
            target_dir = tempfile.mkdtemp(prefix=f"{parsed['repo']}_")
        
        try:
            # Use git clone
            cmd = ['git', 'clone', '--depth', '1']
            
            if 'ref' in parsed and parsed['ref']:
                cmd.extend(['--branch', parsed['ref']])
            
            if self.github_token:
                # Use token for authentication
                auth_url = repo_url.replace('https://', f'https://{self.github_token}@')
                cmd.extend([auth_url, target_dir])
            else:
                cmd.extend([repo_url, target_dir])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return target_dir
            
        except subprocess.CalledProcessError as e:
            print(f"Git clone error: {e.stderr}")
            if target_dir and os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            return None
        except Exception as e:
            print(f"Error cloning repository: {e}")
            return None
    
    def fetch_directory_files(self, url: str, pattern: str = "*.py") -> List[Dict[str, str]]:
        """
        Fetch all files from a GitHub directory.
        
        Args:
            url: GitHub directory URL
            pattern: File pattern to match
            
        Returns:
            List of dictionaries with file info
        """
        parsed = self.parse_github_url(url)
        if not parsed:
            return []
        
        try:
            repo = self.github.get_repo(f"{parsed['owner']}/{parsed['repo']}")
            ref = parsed.get('ref', repo.default_branch)
            path = parsed.get('path', '')
            
            contents = repo.get_contents(path, ref=ref)
            
            files = []
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path, ref=ref))
                else:
                    # Simple pattern matching
                    if pattern == "*.py" and file_content.name.endswith('.py'):
                        files.append({
                            'path': file_content.path,
                            'name': file_content.name,
                            'url': file_content.html_url,
                            'size': file_content.size
                        })
                    elif pattern in file_content.name:
                        files.append({
                            'path': file_content.path,
                            'name': file_content.name,
                            'url': file_content.html_url,
                            'size': file_content.size
                        })
            
            return files
            
        except GithubException as e:
            print(f"GitHub API error: {e}")
            return []
        except Exception as e:
            print(f"Error fetching directory: {e}")
            return []
    
    def get_repository_info(self, url: str) -> Optional[Dict]:
        """
        Get repository information.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Dictionary with repository info or None
        """
        parsed = self.parse_github_url(url)
        if not parsed:
            return None
        
        try:
            repo = self.github.get_repo(f"{parsed['owner']}/{parsed['repo']}")
            
            return {
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'language': repo.language,
                'default_branch': repo.default_branch,
                'url': repo.html_url,
                'size': repo.size,
                'topics': repo.get_topics()
            }
            
        except GithubException as e:
            print(f"GitHub API error: {e}")
            return None
        except Exception as e:
            print(f"Error getting repository info: {e}")
            return None


def is_github_url(input_str: str) -> bool:
    """
    Check if a string is a GitHub URL.
    
    Args:
        input_str: String to check
        
    Returns:
        True if it's a GitHub URL
    """
    return 'github.com' in input_str.lower()


def get_github_content(url_or_path: str, github_token: Optional[str] = None) -> Tuple[Optional[str], str]:
    """
    Get content from GitHub URL or local path.
    
    Args:
        url_or_path: GitHub URL or local file path
        github_token: GitHub token for authentication
        
    Returns:
        Tuple of (content, source_type) where source_type is 'github' or 'local'
    """
    if is_github_url(url_or_path):
        helper = GitHubHelper(github_token)
        result = helper.fetch_file_content(url_or_path)
        
        if result:
            content, _ = result
            return content, 'github'
        else:
            # Try raw content as fallback
            content = helper.fetch_raw_content(url_or_path)
            return content, 'github' if content else None
    else:
        # Local file
        try:
            with open(url_or_path, 'r', encoding='utf-8') as f:
                return f.read(), 'local'
        except Exception as e:
            print(f"Error reading local file: {e}")
            return None, None
