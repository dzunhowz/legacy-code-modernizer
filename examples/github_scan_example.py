"""
Example: Scanning GitHub Repositories with MCP Server

This script demonstrates different approaches to scanning GitHub repositories:
1. Direct GitHub URL (server clones automatically)
2. Pre-cloned local directory (recommended)
3. Single file analysis
"""

import asyncio
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack


async def scan_github_url_direct(repo_url: str, github_token: str = None):
    """
    Method 1: Pass GitHub URL directly to MCP server.
    Server clones the repository automatically.
    
    Pros: Simple, no local setup needed
    Cons: Slower, clones on every scan, temp cleanup issues
    """
    print(f"\n{'='*60}")
    print("Method 1: Direct GitHub URL")
    print(f"{'='*60}\n")
    
    async with AsyncExitStack() as stack:
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "src.mcp_server.server"],
            env=None
        )
        
        stdio_transport = await stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        session = await stack.enter_async_context(
            ClientSession(stdio, write)
        )
        
        await session.initialize()
        
        # Call scan_directory with GitHub URL
        args = {
            "root_directory": repo_url,
            "pattern": "*.py"
        }
        if github_token:
            args["github_token"] = github_token
        
        print(f"Scanning: {repo_url}")
        print("This may take a while (cloning repository)...\n")
        
        try:
            result = await asyncio.wait_for(
                session.call_tool("scan_directory", arguments=args),
                timeout=300.0
            )
            
            response_text = result.content[0].text
            response_data = json.loads(response_text)
            
            print(f"✓ Scan complete!")
            print(f"Found {len(response_data)} symbols\n")
            return response_data
            
        except asyncio.TimeoutError:
            print("✗ Timeout: Repository too large or network slow")
            return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None


async def scan_github_url_local(repo_url: str, temp_dir: str = None):
    """
    Method 2: Clone repository locally first, then scan.
    
    Pros: Faster, more reliable, can reuse clone, easier debugging
    Cons: Requires extra step, uses local disk space
    """
    print(f"\n{'='*60}")
    print("Method 2: Clone Locally First (Recommended)")
    print(f"{'='*60}\n")
    
    # Clone repository
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="mcp_scan_")
    
    repo_name = repo_url.rstrip('/').split('/')[-1]
    local_path = Path(temp_dir) / repo_name
    
    print(f"Step 1: Cloning repository to {local_path}")
    try:
        subprocess.run(
            ['git', 'clone', '--depth', '1', repo_url, str(local_path)],
            check=True,
            capture_output=True
        )
        print("✓ Clone complete\n")
    except subprocess.CalledProcessError as e:
        print(f"✗ Clone failed: {e}")
        return None
    
    # Now scan the local directory
    print("Step 2: Scanning local directory")
    
    async with AsyncExitStack() as stack:
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "src.mcp_server.server"],
            env=None
        )
        
        stdio_transport = await stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        session = await stack.enter_async_context(
            ClientSession(stdio, write)
        )
        
        await session.initialize()
        
        try:
            result = await session.call_tool(
                "scan_directory",
                arguments={
                    "root_directory": str(local_path),
                    "pattern": "*.py"
                }
            )
            
            response_text = result.content[0].text
            response_data = json.loads(response_text)
            
            print(f"✓ Scan complete!")
            print(f"Found {len(response_data)} symbols\n")
            
            # Cleanup
            print(f"Cleaning up: {temp_dir}")
            shutil.rmtree(temp_dir)
            
            return response_data
            
        except Exception as e:
            print(f"✗ Error: {e}")
            shutil.rmtree(temp_dir)
            return None


async def analyze_github_file(file_url: str, github_token: str = None):
    """
    Method 3: Analyze a single file from GitHub.
    Use the analyze_and_plan tool which supports GitHub file URLs.
    
    Pros: Very fast for single files, no full clone needed
    Cons: Only works for single files, requires AI (slower tools)
    """
    print(f"\n{'='*60}")
    print("Method 3: Single File Analysis")
    print(f"{'='*60}\n")
    
    async with AsyncExitStack() as stack:
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "src.mcp_server.server"],
            env=None
        )
        
        stdio_transport = await stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        session = await stack.enter_async_context(
            ClientSession(stdio, write)
        )
        
        await session.initialize()
        
        args = {
            "code": file_url,
            "context": "Analyze this file from GitHub"
        }
        if github_token:
            args["github_token"] = github_token
        
        print(f"Analyzing: {file_url}\n")
        
        try:
            result = await asyncio.wait_for(
                session.call_tool("analyze_and_plan", arguments=args),
                timeout=180.0
            )
            
            response_text = result.content[0].text
            response_data = json.loads(response_text)
            
            print("✓ Analysis complete\n")
            print(json.dumps(response_data, indent=2))
            
            return response_data
            
        except asyncio.TimeoutError:
            print("✗ Timeout: AI analysis took too long")
            return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None


async def main():
    """Demonstrate all three methods."""
    print("\n" + "="*60)
    print("GitHub Repository Scanning Examples")
    print("="*60)
    
    # Example repository (small public repo)
    repo_url = "https://github.com/python/cpython"
    file_url = "https://github.com/python/cpython/blob/main/Lib/ast.py"
    
    print("\n⚠️  Note: These examples use the CPython repo.")
    print("For testing, use a smaller repository!\n")
    
    # Uncomment the method you want to test:
    
    # Method 1: Direct GitHub URL (slower)
    # await scan_github_url_direct(repo_url)
    
    # Method 2: Clone locally first (recommended)
    await scan_github_url_local(repo_url)
    
    # Method 3: Single file (requires AWS for AI)
    # await analyze_github_file(file_url)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Best Practices for GitHub URLs:")
    print("="*60)
    print("""
    1. FOR SMALL REPOS (<100 files):
       Use Method 1 (direct URL) - simple and works
    
    2. FOR LARGE REPOS or REPEATED SCANS:
       Use Method 2 (clone locally) - faster and more reliable
    
    3. FOR SINGLE FILE ANALYSIS:
       Use Method 3 (analyze_and_plan) - no full clone needed
    
    4. PRIVATE REPOS:
       Always provide github_token parameter
       Get token from: https://github.com/settings/tokens
    """)
    print("="*60 + "\n")
    
    # Run example
    asyncio.run(main())
