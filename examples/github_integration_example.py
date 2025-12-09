# Example: Using Agents with GitHub URLs

from src.agents.code_scout import CodeScout
from src.agents.refactoring_crew import RefactoringCrew
import os

def example_code_scout_with_github():
    """Example: Analyze a GitHub repository with Code Scout."""
    
    print("="*70)
    print("CODE SCOUT WITH GITHUB REPOSITORY")
    print("="*70)
    
    # Example 1: Clone and analyze entire repository
    github_repo_url = "https://github.com/pallets/flask"
    
    print(f"\n1. Analyzing GitHub repository: {github_repo_url}")
    scout = CodeScout(github_repo_url)
    
    # Scan the repository
    print("   Scanning repository...")
    scout.scan_directory("*.py")
    
    # Analyze a specific symbol
    print("   Analyzing impact of 'Flask' class...")
    impact = scout.analyze_impact("Flask")
    print(f"   Found {impact['total_usages']} usages across {impact['file_count']} files")
    
    # Example 2: Analyze a single GitHub file
    print("\n2. Analyzing single GitHub file...")
    github_file_url = "https://github.com/pallets/flask/blob/main/src/flask/app.py"
    
    result = scout.analyze_github_file(github_file_url)
    print(f"   Found {len(result)} symbols in the file")
    print(f"   Symbols: {list(result.keys())[:5]}...")  # Show first 5
    
    print("\n✓ Code Scout GitHub analysis complete!")


def example_refactoring_crew_with_github():
    """Example: Refactor code from GitHub URL."""
    
    print("\n" + "="*70)
    print("REFACTORING CREW WITH GITHUB FILE")
    print("="*70)
    
    # Example GitHub file URL
    github_file_url = "https://github.com/pallets/flask/blob/main/src/flask/helpers.py"
    
    print(f"\n1. Fetching code from: {github_file_url}")
    
    # Initialize crew (requires AWS Bedrock access)
    crew = RefactoringCrew(
        bedrock_model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        aws_region="us-east-1",
        github_token=os.getenv("GITHUB_TOKEN")  # Optional for public repos
    )
    
    print("\n2. Analyzing and creating refactoring plan...")
    try:
        plan = crew.analyze_and_plan(
            code=github_file_url,
            context="Flask helper functions used throughout the framework"
        )
        
        print("\n--- REFACTORING PLAN ---")
        print(plan)
        
        print("\n✓ Analysis complete!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("   Note: This requires AWS Bedrock access")


def example_private_repo():
    """Example: Access private GitHub repository."""
    
    print("\n" + "="*70)
    print("PRIVATE GITHUB REPOSITORY ACCESS")
    print("="*70)
    
    # For private repos, you need a GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        print("\n⚠ No GITHUB_TOKEN found in environment")
        print("   Set GITHUB_TOKEN to access private repositories")
        print("   Example: export GITHUB_TOKEN=ghp_your_token_here")
        return
    
    # Your private repository URL
    private_repo_url = "https://github.com/your-org/your-private-repo"
    
    print(f"\nAnalyzing private repository: {private_repo_url}")
    
    try:
        scout = CodeScout(private_repo_url, github_token=github_token)
        scout.scan_directory("*.py")
        
        print(f"   ✓ Successfully scanned private repository")
        print(f"   Found {len(scout.symbol_usages)} symbols")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_mixed_usage():
    """Example: Mix of GitHub URLs and direct code."""
    
    print("\n" + "="*70)
    print("MIXED USAGE: GITHUB + DIRECT CODE")
    print("="*70)
    
    crew = RefactoringCrew()
    
    # Example 1: Direct code
    print("\n1. Analyzing direct code snippet...")
    direct_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total
"""
    
    plan1 = crew.analyze_and_plan(
        code=direct_code,
        context="E-commerce checkout function"
    )
    print("   ✓ Plan created for direct code")
    
    # Example 2: GitHub URL
    print("\n2. Analyzing code from GitHub...")
    github_url = "https://github.com/pallets/flask/blob/main/src/flask/cli.py"
    
    try:
        plan2 = crew.analyze_and_plan(
            code=github_url,
            context="Flask CLI module"
        )
        print("   ✓ Plan created for GitHub file")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_mcp_server_github_usage():
    """Example: MCP Server with GitHub URLs."""
    
    print("\n" + "="*70)
    print("MCP SERVER GITHUB USAGE")
    print("="*70)
    
    print("""
The MCP server now accepts GitHub URLs in all tools:

1. Fast Tools (Code Scout):
   - scan_directory: https://github.com/owner/repo
   - find_symbol: (after scanning a GitHub repo)
   - analyze_impact: (after scanning a GitHub repo)
   - grep_search: (on cloned GitHub repo)
   - git_blame: (on cloned GitHub repo)

2. Slow Tools (Refactoring Crew):
   - analyze_and_plan: GitHub file URL
   - refactor_code: GitHub file URL
   - full_refactoring_workflow: GitHub file URL
   - generate_tests: Works with GitHub URLs
   - architectural_review: Codebase description

Example MCP tool call:
{
  "name": "analyze_and_plan",
  "arguments": {
    "code": "https://github.com/pallets/flask/blob/main/src/flask/app.py",
    "context": "Main Flask application class",
    "github_token": "optional_token_for_private_repos"
  }
}

Example scan repository:
{
  "name": "scan_directory",
  "arguments": {
    "root_directory": "https://github.com/pallets/flask",
    "pattern": "*.py",
    "github_token": "optional_token_for_private_repos"
  }
}
""")


def main():
    """Run all examples."""
    
    print("\n" + "="*70)
    print("GITHUB INTEGRATION EXAMPLES")
    print("="*70)
    print("\nThese examples demonstrate how to use GitHub URLs with both agents.")
    print("Some examples require AWS Bedrock access.")
    print("\n")
    
    # Example 1: Code Scout with GitHub
    try:
        example_code_scout_with_github()
    except Exception as e:
        print(f"Code Scout example error: {e}")
    
    # Example 2: Refactoring Crew with GitHub (requires AWS)
    # Uncomment to run:
    # try:
    #     example_refactoring_crew_with_github()
    # except Exception as e:
    #     print(f"Refactoring Crew example error: {e}")
    
    # Example 3: Private repository access
    example_private_repo()
    
    # Example 4: Mixed usage
    # Uncomment to run:
    # try:
    #     example_mixed_usage()
    # except Exception as e:
    #     print(f"Mixed usage example error: {e}")
    
    # Example 5: MCP Server usage
    example_mcp_server_github_usage()
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70)


if __name__ == "__main__":
    main()
