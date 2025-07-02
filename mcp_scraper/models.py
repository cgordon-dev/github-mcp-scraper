"""Data models for MCP server metadata."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, HttpUrl, Field


class ServerType(str, Enum):
    """Type of MCP server."""
    REFERENCE = "reference"
    THIRD_PARTY = "third_party"


class ToolParameter(BaseModel):
    """Parameter definition for an MCP tool."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None


class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str
    description: Optional[str] = None
    parameters: List[ToolParameter] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)


class MCPPrompt(BaseModel):
    """MCP prompt definition."""
    name: str
    description: Optional[str] = None
    arguments: List[ToolParameter] = Field(default_factory=list)


class MCPResource(BaseModel):
    """MCP resource definition."""
    name: str
    description: Optional[str] = None
    uri: Optional[str] = None
    mime_type: Optional[str] = None


class RepositoryStats(BaseModel):
    """GitHub repository statistics."""
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    size_kb: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    pushed_at: Optional[datetime] = None
    language: Optional[str] = None
    topics: List[str] = Field(default_factory=list)


class PackageInfo(BaseModel):
    """Package information from package.json or pyproject.toml."""
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    dev_dependencies: Dict[str, str] = Field(default_factory=dict)
    scripts: Dict[str, str] = Field(default_factory=dict)


class MCPServer(BaseModel):
    """Complete MCP server metadata."""
    # Basic registry information
    name: str
    github_url: HttpUrl
    description: Optional[str] = None
    favicon_url: Optional[HttpUrl] = None
    server_type: ServerType
    
    # Enhanced metadata
    readme_content: Optional[str] = None
    installation_instructions: Optional[str] = None
    usage_examples: Optional[str] = None
    
    # Repository information
    repository_stats: Optional[RepositoryStats] = None
    package_info: Optional[PackageInfo] = None
    
    # MCP capabilities
    tools: List[MCPTool] = Field(default_factory=list)
    prompts: List[MCPPrompt] = Field(default_factory=list)
    resources: List[MCPResource] = Field(default_factory=list)
    
    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    is_accessible: bool = True
    is_archived: bool = False
    error_message: Optional[str] = None\n    extraction_log: Optional[List[str]] = None
    
    # Categories and tags
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class ScrapingResults(BaseModel):
    """Results from scraping the MCP registry."""
    total_servers: int
    successful_scrapes: int
    failed_scrapes: int
    reference_servers: int
    third_party_servers: int
    servers: List[MCPServer]
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    errors: List[str] = Field(default_factory=list)