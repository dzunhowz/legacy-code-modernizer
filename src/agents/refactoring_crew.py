"""
Refactoring Crew Agent - Slow Asynchronous Refactoring
Uses CrewAI with AWS Bedrock for complex refactoring tasks.
Supports both local files and GitHub URLs.
"""

import os
import sys
from typing import Optional, Dict, Any, Union
import json
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import boto3

# Import GitHub helper
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.github_helper import GitHubHelper, is_github_url, get_github_content


class BedrockLLM:
    """
    Custom LLM wrapper for AWS Bedrock.
    Integrates with CrewAI agents.
    """
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region: str = "us-east-1"
    ):
        self.model_id = model_id
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=region
        )
    
    def __call__(self, prompt: str) -> str:
        """Call the Bedrock API."""
        return self.invoke(prompt)
    
    def invoke(self, prompt: str, max_tokens: int = 4096) -> str:
        """
        Invoke the Bedrock model.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens in response
            
        Returns:
            Model response text
        """
        try:
            # Prepare request for Claude on Bedrock
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            print(f"Bedrock invocation error: {e}")
            return f"Error: {str(e)}"


class CodeAnalysisTool(BaseTool):
    """Tool for analyzing code structure."""
    
    name: str = "code_analyzer"
    description: str = "Analyzes code structure, complexity, and identifies improvement opportunities"
    
    def _run(self, code: str) -> str:
        """Analyze the provided code."""
        # Basic analysis
        lines = code.split('\n')
        functions = [l for l in lines if 'def ' in l]
        classes = [l for l in lines if 'class ' in l]
        
        analysis = {
            "total_lines": len(lines),
            "functions_count": len(functions),
            "classes_count": len(classes),
            "functions": [f.strip() for f in functions],
            "classes": [c.strip() for c in classes]
        }
        
        return json.dumps(analysis, indent=2)


class RefactoringCrew:
    """
    Slow agent for complex refactoring tasks.
    Uses CrewAI with an Architect and Coder agent.
    Supports both local code and GitHub URLs.
    """
    
    def __init__(
        self,
        bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        aws_region: str = "us-east-1",
        github_token: Optional[str] = None
    ):
        self.bedrock_llm = BedrockLLM(
            model_id=bedrock_model_id,
            region=aws_region
        )
        self.code_analysis_tool = CodeAnalysisTool()
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_helper = GitHubHelper(self.github_token)
        
        # Initialize agents
        self.architect_agent = self._create_architect()
        self.coder_agent = self._create_coder()
    
    def _create_architect(self) -> Agent:
        """Create the Architect agent."""
        return Agent(
            role='Software Architect',
            goal='Analyze legacy code and create comprehensive refactoring plans',
            backstory="""You are a senior software architect with 15+ years of experience 
            modernizing legacy systems. You excel at identifying code smells, architectural 
            issues, and creating detailed improvement plans. You understand SOLID principles, 
            design patterns, and modern Python best practices.""",
            verbose=True,
            allow_delegation=False,
            tools=[self.code_analysis_tool],
            llm=self.bedrock_llm
        )
    
    def _create_coder(self) -> Agent:
        """Create the Coder agent."""
        return Agent(
            role='Senior Python Developer',
            goal='Implement refactoring plans with clean, tested, and well-documented code',
            backstory="""You are an expert Python developer specializing in code refactoring 
            and modernization. You write clean, maintainable code following PEP 8 standards. 
            You're skilled at implementing design patterns, writing comprehensive tests, and 
            adding clear documentation. You always consider backwards compatibility and 
            migration paths.""",
            verbose=True,
            allow_delegation=False,
            llm=self.bedrock_llm
        )
    
    def _get_code_content(self, code_or_url: str) -> tuple[str, str]:
        """
        Get code content from string or GitHub URL.
        
        Args:
            code_or_url: Code string or GitHub URL
            
        Returns:
            Tuple of (code_content, source_info)
        """
        if is_github_url(code_or_url):
            content, source_type = get_github_content(code_or_url, self.github_token)
            if content:
                return content, f"GitHub: {code_or_url}"
            else:
                raise ValueError(f"Failed to fetch content from GitHub URL: {code_or_url}")
        else:
            return code_or_url, "Direct input"
    
    def analyze_and_plan(self, code: str, context: Optional[str] = None) -> str:
        """
        Analyze code and create a refactoring plan.
        
        Args:
            code: The legacy code to analyze OR a GitHub URL to a Python file
            context: Additional context about the code
            
        Returns:
            Bullet-point refactoring plan
        """
        # Handle GitHub URL or direct code
        code_content, source_info = self._get_code_content(code)
        
        context_info = f"\n\nAdditional Context:\n{context}" if context else ""
        context_info += f"\n\nSource: {source_info}"
        
        task = Task(
            description=f"""Analyze the following legacy code and create a detailed 
            refactoring plan. Identify:
            
            1. Code smells and anti-patterns
            2. Performance bottlenecks
            3. Security vulnerabilities
            4. Missing error handling
            5. Lack of type hints or documentation
            6. Opportunities for design pattern application
            7. Testing gaps
            
            Code to analyze:
            ```python
            {code_content}
            ```
            {context_info}
            
            Provide a bullet-point action plan with priorities (High/Medium/Low).
            """,
            agent=self.architect_agent,
            expected_output="A detailed bullet-point refactoring plan with priorities"
        )
        
        crew = Crew(
            agents=[self.architect_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)
    
    def refactor_code(self, code: str, plan: str) -> str:
        """
        Refactor code based on a plan.
        
        Args:
            code: The original code to refactor OR a GitHub URL
            plan: The refactoring plan from the architect
            
        Returns:
            Refactored code
        """
        # Handle GitHub URL or direct code
        code_content, source_info = self._get_code_content(code)
        
        task = Task(
            description=f"""Implement the following refactoring plan for the given code.
            
            Original Code (Source: {source_info}):
            ```python
            {code_content}
            ```
            
            Refactoring Plan:
            {plan}
            
            Requirements:
            1. Implement all high-priority items from the plan
            2. Add comprehensive type hints
            3. Add docstrings for all functions and classes
            4. Include error handling where appropriate
            5. Make the code more testable
            6. Preserve functionality while improving structure
            7. Add comments explaining complex logic
            
            Return ONLY the refactored Python code, properly formatted.
            """,
            agent=self.coder_agent,
            expected_output="Clean, refactored Python code with improvements implemented"
        )
        
        crew = Crew(
            agents=[self.coder_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)
    
    def full_refactoring_workflow(
        self,
        code: str,
        context: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Execute complete refactoring workflow: analyze, plan, and refactor.
        
        Args:
            code: The legacy code to refactor OR a GitHub URL
            context: Additional context about the code
            
        Returns:
            Dictionary with plan and refactored code
        """
        # Get actual code content if GitHub URL
        code_content, source_info = self._get_code_content(code)
        print("Phase 1: Analyzing and creating refactoring plan...")
        plan = self.analyze_and_plan(code, context)
        
        print("\nPhase 2: Implementing refactoring...")
        refactored_code = self.refactor_code(code, plan)
        
        return {
            "original_code": code_content,
            "source": source_info,
            "refactoring_plan": plan,
            "refactored_code": refactored_code
        }
    
    def generate_tests(self, code: str, refactored_code: str) -> str:
        """
        Generate unit tests for refactored code.
        
        Args:
            code: Original code
            refactored_code: Refactored version
            
        Returns:
            Test code using pytest
        """
        task = Task(
            description=f"""Generate comprehensive unit tests for the refactored code.
            
            Original Code:
            ```python
            {code}
            ```
            
            Refactored Code:
            ```python
            {refactored_code}
            ```
            
            Create pytest-based tests that:
            1. Test all public functions/methods
            2. Include edge cases and error conditions
            3. Use fixtures where appropriate
            4. Mock external dependencies
            5. Aim for >80% code coverage
            6. Include docstrings explaining what each test does
            
            Return ONLY the test code.
            """,
            agent=self.coder_agent,
            expected_output="Complete pytest test suite for the refactored code"
        )
        
        crew = Crew(
            agents=[self.coder_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)
    
    def architectural_review(self, codebase_description: str) -> str:
        """
        Perform architectural review of a codebase.
        
        Args:
            codebase_description: Description of the codebase structure
            
        Returns:
            Architectural review and recommendations
        """
        task = Task(
            description=f"""Perform an architectural review of the following codebase:
            
            {codebase_description}
            
            Provide:
            1. Overall architecture assessment
            2. Identified architectural issues
            3. Recommendations for improvement
            4. Suggested migration strategy
            5. Risk assessment
            6. Estimated complexity (Low/Medium/High)
            
            Focus on scalability, maintainability, and testability.
            """,
            agent=self.architect_agent,
            expected_output="Comprehensive architectural review with actionable recommendations"
        )
        
        crew = Crew(
            agents=[self.architect_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)


if __name__ == "__main__":
    # Example usage
    crew = RefactoringCrew()
    
    legacy_code = """
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
"""
    
    output = crew.full_refactoring_workflow(
        code=legacy_code,
        context="This function is used in a high-traffic API endpoint"
    )
    
    print("\\n" + "="*50)
    print("REFACTORING PLAN:")
    print("="*50)
    print(output['refactoring_plan'])
    
    print("\\n" + "="*50)
    print("REFACTORED CODE:")
    print("="*50)
    print(output['refactored_code'])
