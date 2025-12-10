"""Configuration management for Legacy Code Modernizer."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration."""
    
    # AWS Configuration
    aws_region: str = os.getenv("AWS_REGION", "ap-southeast-2")
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_session_token: Optional[str] = os.getenv("AWS_SESSION_TOKEN")
    
    # Bedrock Configuration
    bedrock_model_id: str = os.getenv(
        "BEDROCK_MODEL_ID",
        "anthropic.claude-3-5-sonnet-20241022-v2:0"
    )
    
    # Application Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # MCP Server Configuration
    mcp_server_name: str = "legacy-code-modernizer"
    mcp_server_version: str = "1.0.0"
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.aws_region:
            raise ValueError("AWS_REGION is required")
        
        return True


# Global config instance
config = Config()
