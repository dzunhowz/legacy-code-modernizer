"""
Example: Using LangChain + AWS Bedrock for Natural Language Summaries

This example demonstrates how to use the BedrockSummarizer class
to convert JSON analysis results into natural language summaries.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage
import json


def example_1_basic_summary():
    """Example 1: Basic JSON to natural language conversion."""
    
    print("\n" + "="*60)
    print("Example 1: Basic Summary")
    print("="*60 + "\n")
    
    # Initialize LangChain Bedrock client
    llm = ChatBedrock(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="ap-southeast-2",
        model_kwargs={
            "max_tokens": 500,
            "temperature": 0.3,
        }
    )
    
    # Sample analysis result
    result = {
        "tool": "scan_directory",
        "files_scanned": 23,
        "total_lines": 1850,
        "functions_found": 67,
        "classes_found": 15,
        "issues_found": 3
    }
    
    # Create prompt
    prompt = f"""Convert this code analysis result to natural language:

{json.dumps(result, indent=2)}

Provide a 2-3 sentence summary in plain English."""
    
    # Get natural language summary
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])
    
    print("JSON Result:")
    print(json.dumps(result, indent=2))
    print("\nNatural Language Summary:")
    print(response.content)
    print()


def example_2_find_symbol_summary():
    """Example 2: Summarize symbol usage findings."""
    
    print("\n" + "="*60)
    print("Example 2: Symbol Usage Summary")
    print("="*60 + "\n")
    
    llm = ChatBedrock(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="ap-southeast-2",
        model_kwargs={"max_tokens": 500, "temperature": 0.3}
    )
    
    # Symbol search result
    result = {
        "symbol": "process_payment",
        "occurrences": 18,
        "files": [
            {"path": "src/payment/processor.py", "count": 8},
            {"path": "src/api/payment_endpoint.py", "count": 5},
            {"path": "src/services/billing.py", "count": 3},
            {"path": "tests/test_payment.py", "count": 2}
        ],
        "complexity": "medium",
        "has_tests": True
    }
    
    prompt = f"""Analyze this function usage data and provide insights:

{json.dumps(result, indent=2)}

Focus on:
1. How widely the function is used
2. Where it's primarily used
3. Any recommendations"""
    
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])
    
    print("JSON Result:")
    print(json.dumps(result, indent=2))
    print("\nNatural Language Analysis:")
    print(response.content)
    print()


def example_3_dependency_graph_summary():
    """Example 3: Summarize dependency graph analysis."""
    
    print("\n" + "="*60)
    print("Example 3: Dependency Graph Summary")
    print("="*60 + "\n")
    
    llm = ChatBedrock(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="ap-southeast-2",
        model_kwargs={"max_tokens": 500, "temperature": 0.3}
    )
    
    # Dependency graph result
    result = {
        "total_modules": 45,
        "total_dependencies": 123,
        "circular_dependencies": 2,
        "highly_coupled_modules": [
            {"module": "src/utils/helpers.py", "dependencies": 15},
            {"module": "src/core/engine.py", "dependencies": 12}
        ],
        "isolated_modules": 3,
        "max_depth": 5,
        "recommendations": [
            "Break circular dependency between auth.py and session.py",
            "Reduce coupling in helpers.py"
        ]
    }
    
    prompt = f"""Summarize this dependency analysis in plain English:

{json.dumps(result, indent=2)}

Highlight:
1. Overall architecture health
2. Key issues
3. Priority actions"""
    
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])
    
    print("JSON Result:")
    print(json.dumps(result, indent=2))
    print("\nNatural Language Summary:")
    print(response.content)
    print()


def example_4_custom_temperature():
    """Example 4: Different temperature settings for various summary styles."""
    
    print("\n" + "="*60)
    print("Example 4: Temperature Control")
    print("="*60 + "\n")
    
    result = {
        "code_quality": "good",
        "maintainability_score": 7.5,
        "test_coverage": 68,
        "documentation_coverage": 45
    }
    
    temperatures = [
        (0.1, "Very focused and factual"),
        (0.5, "Balanced"),
        (0.9, "Creative and varied")
    ]
    
    for temp, description in temperatures:
        print(f"\nTemperature: {temp} ({description})")
        print("-" * 40)
        
        llm = ChatBedrock(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            region_name="ap-southeast-2",
            model_kwargs={"max_tokens": 300, "temperature": temp}
        )
        
        prompt = f"""Summarize this code quality report in 2 sentences:

{json.dumps(result, indent=2)}"""
        
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        print(response.content)
    
    print()


def example_5_streaming_response():
    """Example 5: Streaming responses for real-time output."""
    
    print("\n" + "="*60)
    print("Example 5: Streaming Response")
    print("="*60 + "\n")
    
    llm = ChatBedrock(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="ap-southeast-2",
        model_kwargs={"max_tokens": 500, "temperature": 0.3}
    )
    
    result = {
        "refactoring_opportunities": 12,
        "duplicate_code_blocks": 5,
        "long_functions": 8,
        "suggested_improvements": [
            "Extract common validation logic",
            "Split large functions",
            "Add type hints"
        ]
    }
    
    prompt = f"""Analyze and provide recommendations:

{json.dumps(result, indent=2)}"""
    
    print("Streaming summary:\n")
    
    message = HumanMessage(content=prompt)
    
    # Stream the response
    for chunk in llm.stream([message]):
        print(chunk.content, end="", flush=True)
    
    print("\n")


def main():
    """Run all examples."""
    
    print("\n" + "="*60)
    print("LangChain + AWS Bedrock Examples")
    print("Natural Language Summaries for Code Analysis")
    print("="*60)
    
    try:
        # Run examples
        example_1_basic_summary()
        example_2_find_symbol_summary()
        example_3_dependency_graph_summary()
        example_4_custom_temperature()
        example_5_streaming_response()
        
        print("\n" + "="*60)
        print("✓ All examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("1. AWS credentials are configured")
        print("2. You have Bedrock access")
        print("3. langchain-aws is installed: uv pip install langchain-aws")


if __name__ == "__main__":
    main()
