# Example: Using Code Scout for Impact Analysis

from src.agents.code_scout import CodeScout
import json

def main():
    """Example usage of Code Scout agent."""
    
    # Initialize Code Scout with your repository path
    print("Initializing Code Scout...")
    scout = CodeScout("/path/to/your/repository")
    
    # 1. Scan the directory for Python files
    print("\n1. Scanning directory...")
    symbol_usages = scout.scan_directory("*.py")
    print(f"Found {len(symbol_usages)} unique symbols")
    
    # 2. Find all usages of a specific function
    print("\n2. Finding symbol usages...")
    function_name = "legacy_function"
    usages = scout.find_symbol(function_name)
    print(f"Found {len(usages)} usages of '{function_name}':")
    for usage in usages[:5]:  # Show first 5
        print(f"  - {usage.file_path}:{usage.line_number} ({usage.usage_type})")
    
    # 3. Analyze impact of changing a symbol
    print(f"\n3. Analyzing impact of '{function_name}'...")
    impact = scout.analyze_impact(function_name)
    print(json.dumps(impact, indent=2))
    
    # 4. Build dependency graph
    print("\n4. Building dependency graph...")
    graph = scout.build_dependency_graph()
    print(f"Built graph with {len(graph)} nodes")
    
    # Show dependencies for a symbol
    if function_name in graph:
        node = graph[function_name]
        print(f"\n'{function_name}' dependencies:")
        print(f"  Depends on: {node.dependencies}")
        print(f"  Depended by: {node.dependents}")
    
    # 5. Search for patterns using grep
    print("\n5. Searching for patterns...")
    results = scout.grep_search("TODO|FIXME|HACK", "*.py")
    print(f"Found {len(results)} code comments requiring attention:")
    for result in results[:5]:  # Show first 5
        print(f"  - {result['file']}:{result['line_number']}")
    
    # 6. Get git blame information
    print("\n6. Getting git blame information...")
    if usages:
        usage = usages[0]
        blame = scout.git_blame(usage.file_path, usage.line_number)
        if blame:
            print(f"Last modified by: {blame.get('author', 'Unknown')}")
            print(f"Commit: {blame.get('commit_message', 'N/A')}")


if __name__ == "__main__":
    main()
