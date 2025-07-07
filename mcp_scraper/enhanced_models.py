"""Enhanced data models for the comprehensive MCP knowledge graph."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, HttpUrl, Field


class ServerType(str, Enum):
    """Type of MCP server."""
    REFERENCE = "reference"
    THIRD_PARTY = "third_party"


class DependencyType(str, Enum):
    """Type of package dependency."""
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    PEER = "peer"
    OPTIONAL = "optional"


class LicenseType(str, Enum):
    """License category."""
    PERMISSIVE = "permissive"
    COPYLEFT = "copyleft"
    PROPRIETARY = "proprietary"
    PUBLIC_DOMAIN = "public_domain"


class OrganizationType(str, Enum):
    """Type of organization."""
    COMPANY = "company"
    INDIVIDUAL = "individual"
    COMMUNITY = "community"
    ACADEMIC = "academic"
    GOVERNMENT = "government"


class MetricType(str, Enum):
    """Quality metric types."""
    CODE_QUALITY = "code_quality"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"


class TechnicalDebtType(str, Enum):
    """Technical debt categories."""
    CODE_SMELLS = "code_smells"
    SECURITY_HOTSPOTS = "security_hotspots"
    BUGS = "bugs"
    VULNERABILITIES = "vulnerabilities"
    DUPLICATION = "duplication"
    COMPLEXITY = "complexity"


# ============================================================================
# Core Entity Models
# ============================================================================

class ToolParameter(BaseModel):
    """Enhanced parameter definition for an MCP tool."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None
    schema: Optional[Dict[str, Any]] = None
    examples: List[str] = Field(default_factory=list)


class MCPTool(BaseModel):
    """Enhanced MCP tool definition."""
    name: str
    description: Optional[str] = None
    server_name: str
    parameters: List[ToolParameter] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    complexity_score: Optional[float] = None
    usage_frequency: Optional[int] = None
    category_tags: List[str] = Field(default_factory=list)
    return_schema: Optional[Dict[str, Any]] = None


class MCPPrompt(BaseModel):
    """Enhanced MCP prompt definition."""
    name: str
    description: Optional[str] = None
    server_name: str
    arguments: List[ToolParameter] = Field(default_factory=list)
    template_type: Optional[str] = None
    examples: List[str] = Field(default_factory=list)
    use_cases: List[str] = Field(default_factory=list)


class MCPResource(BaseModel):
    """Enhanced MCP resource definition."""
    name: str
    description: Optional[str] = None
    server_name: str
    uri_pattern: Optional[str] = None
    mime_type: Optional[str] = None
    access_level: Optional[str] = None
    supported_operations: List[str] = Field(default_factory=list)
    schema: Optional[Dict[str, Any]] = None


class Repository(BaseModel):
    """Enhanced GitHub repository information."""
    url: HttpUrl
    owner: str
    name: str
    primary_language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    size_kb: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    pushed_at: Optional[datetime] = None
    default_branch: str = "main"
    topics: List[str] = Field(default_factory=list)
    is_fork: bool = False
    is_archived: bool = False
    license_name: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[HttpUrl] = None


class Package(BaseModel):
    """Enhanced package manager information."""
    name: str
    ecosystem: str  # npm, pypi, cargo, etc.
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    homepage: Optional[HttpUrl] = None
    repository_url: Optional[HttpUrl] = None
    download_stats: Optional[Dict[str, int]] = None
    dependencies: Dict[str, str] = Field(default_factory=dict)
    dev_dependencies: Dict[str, str] = Field(default_factory=dict)
    scripts: Dict[str, str] = Field(default_factory=dict)


# ============================================================================
# Classification Models
# ============================================================================

class Category(BaseModel):
    """Functional categorization."""
    name: str
    description: Optional[str] = None
    parent_category: Optional[str] = None
    server_count: int = 0
    subcategories: List[str] = Field(default_factory=list)


class Domain(BaseModel):
    """Business domain classification."""
    name: str
    description: Optional[str] = None
    industry_sector: Optional[str] = None
    use_cases: List[str] = Field(default_factory=list)


class Language(BaseModel):
    """Programming language information."""
    name: str
    paradigm: Optional[str] = None
    ecosystem: Optional[str] = None
    popularity_rank: Optional[int] = None
    first_appeared: Optional[int] = None
    file_extensions: List[str] = Field(default_factory=list)


class Framework(BaseModel):
    """MCP framework/SDK information."""
    name: str
    version: Optional[str] = None
    language: str
    features: List[str] = Field(default_factory=list)
    adoption_level: Optional[str] = None
    documentation_url: Optional[HttpUrl] = None


class License(BaseModel):
    """Software license information."""
    name: str
    type: LicenseType
    osi_approved: bool = False
    commercial_use: bool = True
    modification_allowed: bool = True
    distribution_allowed: bool = True
    patent_grant: bool = False
    spdx_id: Optional[str] = None


# ============================================================================
# Ecosystem Models
# ============================================================================

class Organization(BaseModel):
    """Maintainer organization."""
    name: str
    type: OrganizationType
    github_url: Optional[HttpUrl] = None
    website: Optional[HttpUrl] = None
    location: Optional[str] = None
    employee_count: Optional[int] = None
    founded_year: Optional[int] = None
    description: Optional[str] = None


class Developer(BaseModel):
    """Individual contributor."""
    identifier: str  # username
    name: Optional[str] = None
    email: Optional[str] = None
    github_url: Optional[HttpUrl] = None
    contributions_count: int = 0
    primary_language: Optional[str] = None
    join_date: Optional[datetime] = None
    location: Optional[str] = None
    bio: Optional[str] = None


class Version(BaseModel):
    """Package version information."""
    number: str
    package_name: str
    release_date: Optional[datetime] = None
    is_prerelease: bool = False
    is_latest: bool = False
    changelog: Optional[str] = None
    downloads: int = 0
    vulnerabilities_count: int = 0
    size_bytes: Optional[int] = None


class Dependency(BaseModel):
    """Package dependency."""
    name: str
    version_constraint: str
    dependency_type: DependencyType = DependencyType.PRODUCTION
    is_optional: bool = False
    ecosystem: str
    resolved_version: Optional[str] = None


# ============================================================================
# Quality & Metrics Models
# ============================================================================

class QualityMetric(BaseModel):
    """Repository quality indicators."""
    metric_name: str
    metric_type: MetricType
    value: Union[float, int, str]
    measurement_date: datetime = Field(default_factory=datetime.utcnow)
    calculation_method: Optional[str] = None
    target_value: Optional[Union[float, int]] = None
    threshold_met: Optional[bool] = None


class UsagePattern(BaseModel):
    """Installation and usage patterns."""
    pattern_type: str  # docker, npm, pip, etc.
    frequency: int = 0
    instructions: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list)
    success_rate: Optional[float] = None
    estimated_setup_time: Optional[int] = None  # minutes


class TechnicalDebt(BaseModel):
    """Code quality indicators."""
    debt_type: TechnicalDebtType
    severity: str  # critical, major, minor, info
    estimated_effort: Optional[str] = None  # time to fix
    detection_date: datetime = Field(default_factory=datetime.utcnow)
    status: str = "open"  # open, in_progress, resolved
    description: Optional[str] = None
    file_path: Optional[str] = None


# ============================================================================
# Relationship Models
# ============================================================================

class SimilarityRelationship(BaseModel):
    """Represents similarity between entities."""
    source_id: str
    target_id: str
    similarity_score: float
    algorithm: str
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    features_compared: List[str] = Field(default_factory=list)


class MaintenanceRelationship(BaseModel):
    """Organization maintains server relationship."""
    organization_name: str
    server_name: str
    role: str = "maintainer"
    since: Optional[datetime] = None
    is_primary: bool = True
    contact_info: Optional[str] = None


class ContributionRelationship(BaseModel):
    """Developer contributes to repository relationship."""
    developer_identifier: str
    repository_url: str
    commits: int = 0
    last_contribution: Optional[datetime] = None
    contribution_types: List[str] = Field(default_factory=list)  # code, docs, issues, etc.
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None


class CompatibilityRelationship(BaseModel):
    """Tool compatibility relationship."""
    tool1_name: str
    tool2_name: str
    compatibility_score: float
    compatibility_type: str  # functional, data, workflow
    tested: bool = False
    notes: Optional[str] = None


# ============================================================================
# Enhanced Core Server Model
# ============================================================================

class EnhancedMCPServer(BaseModel):
    """Enhanced MCP server with full ecosystem context."""
    # Basic information
    name: str
    github_url: HttpUrl
    description: Optional[str] = None
    favicon_url: Optional[HttpUrl] = None
    server_type: ServerType
    
    # Content
    readme_content: Optional[str] = None
    installation_instructions: Optional[str] = None
    usage_examples: Optional[str] = None
    
    # Enhanced capabilities
    tools: List[MCPTool] = Field(default_factory=list)
    prompts: List[MCPPrompt] = Field(default_factory=list)
    resources: List[MCPResource] = Field(default_factory=list)
    
    # Repository and package info
    repository: Optional[Repository] = None
    packages: List[Package] = Field(default_factory=list)
    
    # Classifications
    categories: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    # Quality metrics
    quality_metrics: List[QualityMetric] = Field(default_factory=list)
    usage_patterns: List[UsagePattern] = Field(default_factory=list)
    technical_debt: List[TechnicalDebt] = Field(default_factory=list)
    
    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    is_accessible: bool = True
    is_archived: bool = False
    error_message: Optional[str] = None
    extraction_log: Optional[List[str]] = None
    
    # Computed fields
    complexity_score: Optional[float] = None
    maturity_score: Optional[float] = None
    popularity_score: Optional[float] = None


class EnhancedScrapingResults(BaseModel):
    """Enhanced results from scraping the MCP registry."""
    total_servers: int
    successful_scrapes: int
    failed_scrapes: int
    reference_servers: int
    third_party_servers: int
    servers: List[EnhancedMCPServer]
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    errors: List[str] = Field(default_factory=list)
    
    # Enhanced statistics
    total_tools: int = 0
    total_prompts: int = 0
    total_resources: int = 0
    unique_categories: List[str] = Field(default_factory=list)
    unique_languages: List[str] = Field(default_factory=list)
    unique_frameworks: List[str] = Field(default_factory=list)
    processing_time_seconds: Optional[float] = None