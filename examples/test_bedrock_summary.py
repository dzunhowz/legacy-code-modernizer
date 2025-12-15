"""
Test script for Bedrock natural language summarization.
Run this to verify LangChain + AWS Bedrock integration works.
"""

import os
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage


def test_bedrock_connection():
    """Test basic Bedrock connection and natural language conversion."""
    
    print("Testing AWS Bedrock with LangChain...")
    print("=" * 60)
    
    try:
        # Initialize Bedrock LLM
        llm = ChatBedrock(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            region_name=os.getenv("AWS_REGION", "ap-southeast-2"),
            model_kwargs={
                "max_tokens": 500,
                "temperature": 0.3,
            }
        )
        
        print("✓ Bedrock client initialized\n")
        
        # Test with sample JSON result
        sample_result = {
            "tool": "scan_directory",
            "files_scanned": 45,
            "total_lines": 3250,
            "functions_found": 127,
            "classes_found": 23,
            "files": [
                {"path": "src/agents/code_scout.py", "lines": 245},
                {"path": "src/agents/refactoring_crew.py", "lines": 423},
                {"path": "src/utils/github_helper.py", "lines": 156}
            ]
        }
        
        # Create prompt for natural language conversion
        prompt = f"""Convert this JSON analysis result into a clear, concise natural language summary.

JSON Result:
{sample_result}

Provide a 2-3 sentence summary highlighting:
- Key statistics (files, lines, functions)
- Notable findings
- Any patterns or insights

Keep it conversational and easy to understand."""
        
        print("Sending request to Bedrock...\n")
        
        # Invoke Bedrock
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        
        print("=" * 60)
        print("Natural Language Summary:")
        print("=" * 60)
        print(response.content)
        print("=" * 60)
        
        print("\n✓ Test successful!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure:")
        print("1. AWS credentials are configured")
        print("2. You have Bedrock access")
        print("3. Region is set correctly")


if __name__ == "__main__":
    test_bedrock_connection()
