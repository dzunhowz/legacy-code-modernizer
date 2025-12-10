"""
Test GitHub URL Support with MCP Client

This script demonstrates testing GitHub URLs locally with the MCP server.
Run this to verify that GitHub URL caching works correctly.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack


async def test_github_url(repo_url: str, github_token: str = None):
    """
    Test scanning a GitHub repository URL.
    
    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)
        github_token: GitHub token for private repos (optional)
    """
    print("\n" + "="*70)
    print("Testing GitHub URL Support")
    print("="*70)
    print(f"\nRepository: {repo_url}")
    print(f"Token: {'Provided' if github_token else 'None (public repo)'}")
    
    async with AsyncExitStack() as stack:
        # Connect to MCP server
        print("\n1. Connecting to MCP server...")
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
        print("   ✓ Connected!")
        
        # Test 1: First scan (will clone and cache)
        print("\n2. First scan (will clone repository)...")
        args = {
            "root_directory": repo_url,
            "pattern": "*.py"
        }
        if github_token:
            args["github_token"] = github_token
        
        try:
            import time
            start = time.time()
            
            result = await asyncio.wait_for(
                session.call_tool("scan_directory", arguments=args),
                timeout=60.0
            )
            
            elapsed = time.time() - start
            
            response_text = result.content[0].text
            response_data = json.loads(response_text)
            
            if "error" in response_data:
                print(f"   ✗ Error: {response_data['error']}")
                return
            
            symbol_count = len(response_data)
            print(f"   ✓ Scan complete!")
            print(f"   - Time: {elapsed:.2f}s")
            print(f"   - Symbols found: {symbol_count}")
            print(f"   - Sample symbols: {list(response_data.keys())[:5]}")
            
        except asyncio.TimeoutError:
            print("   ✗ Timeout: Repository too large or network slow")
            return
        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 2: Second scan (should use cache)
        print("\n3. Second scan (from cache)...")
        try:
            start = time.time()
            
            result = await asyncio.wait_for(
                session.call_tool("scan_directory", arguments=args),
                timeout=60.0
            )
            
            elapsed = time.time() - start
            
            response_text = result.content[0].text
            response_data = json.loads(response_text)
            
            symbol_count = len(response_data)
            print(f"   ✓ Scan complete!")
            print(f"   - Time: {elapsed:.2f}s")
            print(f"   - Symbols found: {symbol_count}")
            
            if elapsed < 1.0:
                print(f"   🚀 Cache working! Much faster than first scan")
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 3: Find symbol
        if symbol_count > 0:
            print("\n4. Testing find_symbol...")
            sample_symbol = list(response_data.keys())[0]
            
            try:
                result = await session.call_tool(
                    "find_symbol",
                    arguments={
                        "root_directory": repo_url,
                        "symbol_name": sample_symbol
                    }
                )
                
                response_text = result.content[0].text
                usages = json.loads(response_text)
                
                print(f"   ✓ Found symbol '{sample_symbol}'")
                print(f"   - Usages: {len(usages)}")
                if usages:
                    print(f"   - First usage: {usages[0]['file_path']}:{usages[0]['line_number']}")
                
            except Exception as e:
                print(f"   ✗ Error: {e}")
        
        print("\n" + "="*70)
        print("✅ Test completed successfully!")
        print("="*70)


async def main():
    """Main entry point."""
    import sys
    import os
    
    print("\n" + "="*70)
    print("GitHub URL Testing Script")
    print("="*70)
    
    # Get repository URL
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
    else:
        print("\nUsage: python test_github_url.py <repo_url> [github_token]")
        print("\nExamples:")
        print("  # Public repo")
        print("  python examples/test_github_url.py https://github.com/owner/repo")
        print("\n  # Private repo with token")
        print("  python examples/test_github_url.py https://github.com/owner/repo ghp_xxx")
        print("\n  # Using environment variable")
        print("  export GITHUB_TOKEN=ghp_xxx")
        print("  python examples/test_github_url.py https://github.com/owner/repo")
        
        # Default test repo
        repo_url = input("\nEnter GitHub URL (or press Enter for test repo): ").strip()
        if not repo_url:
            repo_url = "https://github.com/duongle-wizeline/wizelit"
            print(f"Using test repo: {repo_url}")
    
    # Get GitHub token
    github_token = None
    if len(sys.argv) > 2:
        github_token = sys.argv[2]
    else:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            token_input = input("\nGitHub token (optional, press Enter to skip): ").strip()
            if token_input:
                github_token = token_input
    
    # Run test
    await test_github_url(repo_url, github_token)


if __name__ == "__main__":
    asyncio.run(main())
