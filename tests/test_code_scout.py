"""
Test suite for Code Scout agent.
"""

import pytest
from pathlib import Path
from src.agents.code_scout import CodeScout, SymbolUsage


@pytest.fixture
def sample_code_dir(tmp_path):
    """Create a temporary directory with sample Python files."""
    # Create sample Python file
    sample_file = tmp_path / "sample.py"
    sample_file.write_text("""
def legacy_function(x):
    return x * 2

class LegacyClass:
    def method(self):
        return legacy_function(10)

def another_function():
    result = legacy_function(5)
    return result
""")
    
    return tmp_path


def test_code_scout_initialization(sample_code_dir):
    """Test Code Scout initialization."""
    scout = CodeScout(str(sample_code_dir))
    assert scout.root_directory == sample_code_dir


def test_scan_directory(sample_code_dir):
    """Test directory scanning."""
    scout = CodeScout(str(sample_code_dir))
    result = scout.scan_directory("*.py")
    
    assert len(result) > 0
    assert "legacy_function" in result
    assert "LegacyClass" in result


def test_find_symbol(sample_code_dir):
    """Test finding specific symbol."""
    scout = CodeScout(str(sample_code_dir))
    scout.scan_directory("*.py")
    
    usages = scout.find_symbol("legacy_function")
    assert len(usages) >= 1
    assert all(isinstance(u, SymbolUsage) for u in usages)


def test_analyze_impact(sample_code_dir):
    """Test impact analysis."""
    scout = CodeScout(str(sample_code_dir))
    scout.scan_directory("*.py")
    
    impact = scout.analyze_impact("legacy_function")
    assert "symbol" in impact
    assert impact["symbol"] == "legacy_function"
    assert "total_usages" in impact
    assert impact["total_usages"] > 0


def test_grep_search(sample_code_dir):
    """Test grep search functionality."""
    scout = CodeScout(str(sample_code_dir))
    results = scout.grep_search("legacy_function", "*.py")
    
    assert len(results) > 0
    assert all("file" in r for r in results)


def test_build_dependency_graph(sample_code_dir):
    """Test dependency graph building."""
    scout = CodeScout(str(sample_code_dir))
    scout.scan_directory("*.py")
    
    graph = scout.build_dependency_graph()
    assert isinstance(graph, dict)
