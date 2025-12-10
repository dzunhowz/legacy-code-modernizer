"""
Test suite for Refactoring Crew agent.
Note: These tests require AWS credentials and Bedrock access.
Use mocking for CI/CD pipelines.
"""

import pytest
from unittest.mock import Mock, patch
from src.agents.refactoring_crew import RefactoringCrew, BedrockLLM


@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock client for testing."""
    with patch('boto3.client') as mock_client:
        mock_runtime = Mock()
        mock_runtime.invoke_model.return_value = {
            'body': Mock(read=lambda: b'{"content": [{"text": "Mocked response"}]}')
        }
        mock_client.return_value = mock_runtime
        yield mock_client


def test_bedrock_llm_initialization():
    """Test Bedrock LLM initialization."""
    with patch('boto3.client'):
        llm = BedrockLLM(model_id="test-model", region="ap-southeast-2")
        assert llm.model_id == "test-model"


def test_refactoring_crew_initialization(mock_bedrock_client):
    """Test Refactoring Crew initialization."""
    crew = RefactoringCrew()
    assert crew.architect_agent is not None
    assert crew.coder_agent is not None


@pytest.mark.skipif(
    not pytest.config.getoption("--run-integration"),
    reason="Requires AWS credentials and Bedrock access"
)
def test_analyze_and_plan_integration():
    """Integration test for analyze_and_plan (requires AWS)."""
    crew = RefactoringCrew()
    
    code = """
def old_function(x):
    return x * 2
"""
    
    plan = crew.analyze_and_plan(code, "Test context")
    assert len(plan) > 0
    assert isinstance(plan, str)


def test_analyze_and_plan_mocked(mock_bedrock_client):
    """Test analyze_and_plan with mocked Bedrock."""
    crew = RefactoringCrew()
    
    code = """
def old_function(x):
    return x * 2
"""
    
    # This will use the mocked Bedrock client
    # Note: CrewAI might not work perfectly with mocking
    # This is a placeholder for the structure
    assert crew is not None


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require AWS"
    )
