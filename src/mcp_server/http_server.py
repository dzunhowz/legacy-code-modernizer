"""
HTTP wrapper for MCP Server to run in ECS/Fargate.
Exposes REST API endpoints for Code Scout and Refactoring Crew operations.
"""

import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.code_scout import CodeScout
from agents.refactoring_crew import RefactoringCrew

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Legacy Code Modernizer API",
    description="REST API for code analysis and refactoring using AI agents",
    version="0.1.0"
)

# Initialize agents (lazy loading)
code_scout: Optional[CodeScout] = None
refactoring_crew: Optional[RefactoringCrew] = None


def get_code_scout() -> CodeScout:
    """Get or initialize CodeScout agent."""
    global code_scout
    if code_scout is None:
        logger.info("Initializing CodeScout agent...")
        code_scout = CodeScout()
    return code_scout


def get_refactoring_crew() -> RefactoringCrew:
    """Get or initialize RefactoringCrew agent."""
    global refactoring_crew
    if refactoring_crew is None:
        logger.info("Initializing RefactoringCrew agent...")
        refactoring_crew = RefactoringCrew()
    return refactoring_crew


# Request models
class ScanDirectoryRequest(BaseModel):
    root_directory: str
    pattern: str = "*.py"
    github_token: Optional[str] = None


class FindUsagesRequest(BaseModel):
    root_directory: str
    symbol_name: str
    symbol_type: str = "function"
    github_token: Optional[str] = None


class AnalyzeRefactoringRequest(BaseModel):
    code: str
    focus_area: Optional[str] = None


class GenerateRefactoringRequest(BaseModel):
    code: str
    analysis: str


class GenerateTestsRequest(BaseModel):
    code: str
    refactored_code: str


class ArchitecturalReviewRequest(BaseModel):
    codebase_description: str


# Health check endpoint
@app.get("/")
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "legacy-code-modernizer",
        "version": "0.1.0"
    }


# Code Scout endpoints (fast operations)
@app.post("/api/scan-directory")
async def scan_directory(request: ScanDirectoryRequest):
    """Scan a directory or GitHub repository for Python files."""
    try:
        logger.info(f"Scanning directory: {request.root_directory}")
        scout = get_code_scout()
        
        result = scout.scan_directory(
            root_directory=request.root_directory,
            pattern=request.pattern,
            github_token=request.github_token
        )
        
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error scanning directory: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/find-usages")
async def find_usages(request: FindUsagesRequest):
    """Find usages of a symbol across the codebase."""
    try:
        logger.info(f"Finding usages of {request.symbol_name}")
        scout = get_code_scout()
        
        result = scout.find_usages(
            root_directory=request.root_directory,
            symbol_name=request.symbol_name,
            symbol_type=request.symbol_type,
            github_token=request.github_token
        )
        
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error finding usages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Refactoring Crew endpoints (long-running operations)
@app.post("/api/analyze-refactoring")
async def analyze_refactoring(request: AnalyzeRefactoringRequest):
    """Analyze code and suggest refactoring opportunities."""
    try:
        logger.info("Analyzing code for refactoring...")
        crew = get_refactoring_crew()
        
        result = crew.analyze_refactoring(
            code=request.code,
            focus_area=request.focus_area
        )
        
        return {"success": True, "data": {"analysis": result}}
    except Exception as e:
        logger.error(f"Error analyzing refactoring: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-refactoring")
async def generate_refactoring(request: GenerateRefactoringRequest):
    """Generate refactored code based on analysis."""
    try:
        logger.info("Generating refactored code...")
        crew = get_refactoring_crew()
        
        result = crew.generate_refactoring(
            code=request.code,
            analysis=request.analysis
        )
        
        return {"success": True, "data": {"refactored_code": result}}
    except Exception as e:
        logger.error(f"Error generating refactoring: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-tests")
async def generate_tests(request: GenerateTestsRequest):
    """Generate tests for refactored code."""
    try:
        logger.info("Generating tests...")
        crew = get_refactoring_crew()
        
        result = crew.generate_tests(
            code=request.code,
            refactored_code=request.refactored_code
        )
        
        return {"success": True, "data": {"test_code": result}}
    except Exception as e:
        logger.error(f"Error generating tests: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/architectural-review")
async def architectural_review(request: ArchitecturalReviewRequest):
    """Perform architectural review of codebase."""
    try:
        logger.info("Performing architectural review...")
        crew = get_refactoring_crew()
        
        result = crew.architectural_review(
            codebase_description=request.codebase_description
        )
        
        return {"success": True, "data": {"review": result}}
    except Exception as e:
        logger.error(f"Error in architectural review: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# API documentation
@app.get("/api/tools")
async def list_tools():
    """List all available tools and their descriptions."""
    return {
        "tools": [
            {
                "name": "scan_directory",
                "category": "code-scout",
                "description": "Scan directory or GitHub repo for Python files",
                "endpoint": "/api/scan-directory"
            },
            {
                "name": "find_usages",
                "category": "code-scout",
                "description": "Find usages of a symbol across codebase",
                "endpoint": "/api/find-usages"
            },
            {
                "name": "analyze_refactoring",
                "category": "refactoring-crew",
                "description": "Analyze code and suggest refactoring",
                "endpoint": "/api/analyze-refactoring"
            },
            {
                "name": "generate_refactoring",
                "category": "refactoring-crew",
                "description": "Generate refactored code",
                "endpoint": "/api/generate-refactoring"
            },
            {
                "name": "generate_tests",
                "category": "refactoring-crew",
                "description": "Generate tests for refactored code",
                "endpoint": "/api/generate-tests"
            },
            {
                "name": "architectural_review",
                "category": "refactoring-crew",
                "description": "Perform architectural review",
                "endpoint": "/api/architectural-review"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
