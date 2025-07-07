// Enhanced Neo4j Knowledge Graph Schema for MCP Server Ecosystem
// This schema provides comprehensive modeling of the Model Context Protocol ecosystem

// ============================================================================
// NODE CONSTRAINTS AND INDEXES
// ============================================================================

// Core Entity Constraints
CREATE CONSTRAINT mcp_server_name_unique IF NOT EXISTS 
FOR (s:MCPServer) REQUIRE s.name IS UNIQUE;

CREATE CONSTRAINT tool_composite_unique IF NOT EXISTS 
FOR (t:Tool) REQUIRE (t.name, t.server_name) IS UNIQUE;

CREATE CONSTRAINT prompt_composite_unique IF NOT EXISTS 
FOR (p:Prompt) REQUIRE (p.name, p.server_name) IS UNIQUE;

CREATE CONSTRAINT resource_composite_unique IF NOT EXISTS 
FOR (r:Resource) REQUIRE (r.name, r.server_name) IS UNIQUE;

CREATE CONSTRAINT repository_url_unique IF NOT EXISTS 
FOR (repo:Repository) REQUIRE repo.url IS UNIQUE;

CREATE CONSTRAINT package_composite_unique IF NOT EXISTS 
FOR (pkg:Package) REQUIRE (pkg.name, pkg.ecosystem) IS UNIQUE;

// Classification Constraints
CREATE CONSTRAINT category_name_unique IF NOT EXISTS 
FOR (c:Category) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT domain_name_unique IF NOT EXISTS 
FOR (d:Domain) REQUIRE d.name IS UNIQUE;

CREATE CONSTRAINT language_name_unique IF NOT EXISTS 
FOR (l:Language) REQUIRE l.name IS UNIQUE;

CREATE CONSTRAINT framework_name_unique IF NOT EXISTS 
FOR (f:Framework) REQUIRE f.name IS UNIQUE;

CREATE CONSTRAINT license_name_unique IF NOT EXISTS 
FOR (lic:License) REQUIRE lic.name IS UNIQUE;

// Ecosystem Constraints
CREATE CONSTRAINT organization_name_unique IF NOT EXISTS 
FOR (o:Organization) REQUIRE o.name IS UNIQUE;

CREATE CONSTRAINT developer_identifier_unique IF NOT EXISTS 
FOR (dev:Developer) REQUIRE dev.identifier IS UNIQUE;

CREATE CONSTRAINT version_composite_unique IF NOT EXISTS 
FOR (v:Version) REQUIRE (v.number, v.package_name) IS UNIQUE;

CREATE CONSTRAINT dependency_composite_unique IF NOT EXISTS 
FOR (dep:Dependency) REQUIRE (dep.name, dep.version_constraint) IS UNIQUE;

// Performance Indexes
CREATE INDEX mcp_server_type_idx IF NOT EXISTS FOR (s:MCPServer) ON (s.server_type);
CREATE INDEX mcp_server_stars_idx IF NOT EXISTS FOR (s:MCPServer) ON (s.stars);
CREATE INDEX mcp_server_updated_idx IF NOT EXISTS FOR (s:MCPServer) ON (s.updated_at);
CREATE INDEX mcp_server_accessible_idx IF NOT EXISTS FOR (s:MCPServer) ON (s.is_accessible);

CREATE INDEX tool_name_idx IF NOT EXISTS FOR (t:Tool) ON (t.name);
CREATE INDEX repository_language_idx IF NOT EXISTS FOR (repo:Repository) ON (repo.primary_language);
CREATE INDEX package_ecosystem_idx IF NOT EXISTS FOR (pkg:Package) ON (pkg.ecosystem);

// Text search indexes
CREATE INDEX mcp_server_description_text IF NOT EXISTS FOR (s:MCPServer) ON (s.description);
CREATE INDEX tool_description_text IF NOT EXISTS FOR (t:Tool) ON (t.description);

// ============================================================================
// NODE LABELS AND PROPERTIES SCHEMA
// ============================================================================

// Core Entities
// MCPServer: Central entity representing an MCP server
// Properties: name, github_url, description, server_type, is_accessible, 
//            is_archived, scraped_at, tools_count, prompts_count, resources_count,
//            readme_content, installation_instructions, usage_examples

// Tool: MCP tools provided by servers
// Properties: name, description, server_name, parameters_count, complexity_score,
//            usage_frequency, category_tags

// Prompt: MCP prompts provided by servers
// Properties: name, description, server_name, arguments_count, template_type

// Resource: MCP resources provided by servers  
// Properties: name, description, server_name, uri_pattern, mime_type, access_level

// Repository: GitHub repository information
// Properties: url, owner, name, primary_language, stars, forks, watchers,
//            open_issues, size_kb, created_at, updated_at, pushed_at, 
//            default_branch, topics, is_fork, is_archived

// Package: Package manager information
// Properties: name, ecosystem (npm/pypi/etc), version, description, author,
//            keywords, homepage, repository_url, download_stats

// Classification Nodes
// Category: Functional categorization
// Properties: name, description, parent_category, server_count

// Domain: Business domain classification
// Properties: name, description, industry_sector, use_cases

// Language: Programming language
// Properties: name, paradigm, ecosystem, popularity_rank, first_appeared

// Framework: MCP framework/SDK used
// Properties: name, version, language, features, adoption_level

// License: Software license
// Properties: name, type (permissive/copyleft/proprietary), osi_approved, 
//            commercial_use, modification_allowed

// Ecosystem Nodes
// Organization: Maintainer organization
// Properties: name, type (company/individual/community), github_url, 
//            website, location, employee_count, founded_year

// Developer: Individual contributor
// Properties: identifier (username), name, email, github_url, contributions_count,
//            primary_language, join_date, location

// Version: Package version information
// Properties: number, package_name, release_date, is_prerelease, is_latest,
//            changelog, downloads, vulnerabilities_count

// Dependency: Package dependency
// Properties: name, version_constraint, dependency_type (dev/prod/peer),
//            is_optional, ecosystem

// Quality & Metrics Nodes
// QualityMetric: Repository quality indicators
// Properties: metric_name, value, measurement_date, calculation_method

// UsagePattern: Installation and usage patterns
// Properties: pattern_type, frequency, instructions, prerequisites

// TechnicalDebt: Code quality indicators
// Properties: debt_type, severity, estimated_effort, detection_date, status

// ============================================================================
// RELATIONSHIPS SCHEMA
// ============================================================================

// Core Relationships
// (MCPServer)-[:PROVIDES_TOOL]->(Tool)
// (MCPServer)-[:PROVIDES_PROMPT]->(Prompt)  
// (MCPServer)-[:PROVIDES_RESOURCE]->(Resource)
// (MCPServer)-[:HOSTED_IN]->(Repository)
// (MCPServer)-[:PACKAGED_AS]->(Package)

// Classification Relationships
// (MCPServer)-[:BELONGS_TO_CATEGORY {confidence: float, assigned_at: datetime}]->(Category)
// (MCPServer)-[:OPERATES_IN_DOMAIN {relevance_score: float}]->(Domain)
// (MCPServer)-[:IMPLEMENTED_IN {lines_of_code: int, percentage: float}]->(Language)
// (MCPServer)-[:USES_FRAMEWORK {version: string, adoption_level: string}]->(Framework)
// (Repository)-[:LICENSED_UNDER]->(License)

// Ecosystem Relationships
// (Organization)-[:MAINTAINS {role: string, since: datetime}]->(MCPServer)
// (Developer)-[:CONTRIBUTES_TO {commits: int, last_contribution: datetime}]->(Repository)
// (Package)-[:HAS_VERSION {is_current: boolean}]->(Version)
// (Package)-[:DEPENDS_ON {constraint: string, type: string}]->(Dependency)

// Similarity & Recommendation Relationships
// (MCPServer)-[:SIMILAR_TO {similarity_score: float, algorithm: string}]->(MCPServer)
// (Tool)-[:SIMILAR_FUNCTIONALITY {similarity_score: float}]->(Tool)
// (MCPServer)-[:RECOMMENDED_WITH {confidence: float, reason: string}]->(MCPServer)

// Quality Relationships  
// (Repository)-[:HAS_QUALITY_METRIC {measured_at: datetime}]->(QualityMetric)
// (MCPServer)-[:HAS_USAGE_PATTERN]->(UsagePattern)
// (Repository)-[:HAS_TECHNICAL_DEBT {priority: string}]->(TechnicalDebt)

// Hierarchical Relationships
// (Category)-[:SUBCATEGORY_OF]->(Category)
// (Organization)-[:MEMBER_OF]->(Organization)
// (Version)-[:SUCCEEDS {release_gap_days: int}]->(Version)

// Network Relationships
// (Tool)-[:COMPATIBLE_WITH {compatibility_score: float}]->(Tool)
// (MCPServer)-[:INTEGRATES_WITH {integration_type: string}]->(MCPServer)
// (Framework)-[:EXTENDS]->(Framework)

// ============================================================================
// SAMPLE CYPHER QUERIES FOR VALIDATION
// ============================================================================

// Find most popular servers by category
// MATCH (s:MCPServer)-[:BELONGS_TO_CATEGORY]->(c:Category)
// WHERE s.stars > 100
// RETURN c.name, count(s) as server_count, avg(s.stars) as avg_stars
// ORDER BY server_count DESC;

// Discover tool similarity networks  
// MATCH (t1:Tool)-[:SIMILAR_FUNCTIONALITY {similarity_score: score}]->(t2:Tool)
// WHERE score > 0.7
// RETURN t1.name, t2.name, score
// ORDER BY score DESC;

// Analyze framework adoption
// MATCH (s:MCPServer)-[u:USES_FRAMEWORK]->(f:Framework)
// RETURN f.name, count(s) as adoption_count, 
//        collect(DISTINCT u.version) as versions_used
// ORDER BY adoption_count DESC;

// Find servers with similar tech stacks
// MATCH (s1:MCPServer)-[:IMPLEMENTED_IN]->(l:Language)<-[:IMPLEMENTED_IN]-(s2:MCPServer)
// WHERE s1 <> s2
// WITH s1, s2, count(l) as shared_languages
// MATCH (s1)-[:USES_FRAMEWORK]->(f:Framework)<-[:USES_FRAMEWORK]-(s2)
// WITH s1, s2, shared_languages, count(f) as shared_frameworks  
// WHERE shared_languages > 0 OR shared_frameworks > 0
// RETURN s1.name, s2.name, shared_languages, shared_frameworks
// ORDER BY shared_languages + shared_frameworks DESC;