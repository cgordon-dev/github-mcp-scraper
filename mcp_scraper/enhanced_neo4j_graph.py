"""Enhanced Neo4j knowledge graph integration for comprehensive MCP server ecosystem."""

import os
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from neo4j import GraphDatabase, Driver
from .enhanced_models import (
    EnhancedMCPServer, EnhancedScrapingResults, MCPTool, MCPPrompt, MCPResource,
    Repository, Package, Category, Domain, Language, Framework, License,
    Organization, Developer, Version, Dependency, QualityMetric, UsagePattern,
    TechnicalDebt, SimilarityRelationship, MaintenanceRelationship,
    ContributionRelationship, CompatibilityRelationship
)


class EnhancedMCPKnowledgeGraph:
    """Enhanced Neo4j knowledge graph for comprehensive MCP server ecosystem analysis."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 username: str = "neo4j", 
                 password: str = "password"):
        """Initialize Neo4j connection."""
        self.driver: Driver = GraphDatabase.driver(uri, auth=(username, password))
        self._setup_schema()
    
    def close(self):
        """Close the driver connection."""
        if self.driver:
            self.driver.close()
    
    def _setup_schema(self):
        """Setup constraints, indexes, and schema from schema file."""
        schema_file = os.path.join(os.path.dirname(__file__), "..", "neo4j_schema.cypher")
        
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                schema_content = f.read()
            
            # Split and execute each constraint/index command
            commands = [cmd.strip() for cmd in schema_content.split(';') if cmd.strip() and not cmd.strip().startswith('//')]
            
            with self.driver.session() as session:
                for command in commands:
                    if command and ('CREATE CONSTRAINT' in command or 'CREATE INDEX' in command):
                        try:
                            session.run(command)
                        except Exception as e:
                            print(f"Note: Schema command may already exist: {str(e)[:100]}")
    
    def clear_graph(self):
        """Clear all data from the graph (use with caution!)."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("🗑️  Graph cleared")
    
    def store_enhanced_results(self, results: EnhancedScrapingResults) -> Dict[str, int]:
        """Store complete enhanced scraping results in Neo4j."""
        stats = {
            "servers_created": 0,
            "tools_created": 0,
            "prompts_created": 0,
            "resources_created": 0,
            "repositories_created": 0,
            "packages_created": 0,
            "categories_created": 0,
            "domains_created": 0,
            "languages_created": 0,
            "frameworks_created": 0,
            "licenses_created": 0,
            "organizations_created": 0,
            "developers_created": 0,
            "versions_created": 0,
            "dependencies_created": 0,
            "quality_metrics_created": 0,
            "usage_patterns_created": 0,
            "technical_debt_created": 0,
            "relationships_created": 0
        }
        
        with self.driver.session() as session:
            # Store scraping metadata
            self._store_scraping_metadata(session, results)
            
            # Process each server
            for server in results.servers:
                server_stats = self._store_enhanced_server(session, server)
                for key, value in server_stats.items():
                    stats[key] += value
        
        return stats
    
    def _store_scraping_metadata(self, session, results: EnhancedScrapingResults):
        """Store enhanced scraping run metadata."""
        query = """
        MERGE (run:ScrapingRun {
            scraped_at: $scraped_at,
            total_servers: $total_servers,
            successful_scrapes: $successful_scrapes,
            failed_scrapes: $failed_scrapes,
            reference_servers: $reference_servers,
            third_party_servers: $third_party_servers,
            total_tools: $total_tools,
            total_prompts: $total_prompts,
            total_resources: $total_resources,
            processing_time_seconds: $processing_time_seconds
        })
        RETURN run
        """
        
        session.run(query, {
            "scraped_at": results.scraped_at.isoformat(),
            "total_servers": results.total_servers,
            "successful_scrapes": results.successful_scrapes,
            "failed_scrapes": results.failed_scrapes,
            "reference_servers": results.reference_servers,
            "third_party_servers": results.third_party_servers,
            "total_tools": results.total_tools,
            "total_prompts": results.total_prompts,
            "total_resources": results.total_resources,
            "processing_time_seconds": results.processing_time_seconds
        })
    
    def _store_enhanced_server(self, session, server: EnhancedMCPServer) -> Dict[str, int]:
        """Store an enhanced MCP server and all its relationships."""
        stats = {key: 0 for key in [
            "servers_created", "tools_created", "prompts_created", "resources_created",
            "repositories_created", "packages_created", "categories_created", 
            "domains_created", "languages_created", "frameworks_created",
            "licenses_created", "organizations_created", "developers_created",
            "versions_created", "dependencies_created", "quality_metrics_created",
            "usage_patterns_created", "technical_debt_created", "relationships_created"
        ]}
        
        # Create server node
        server_stats = self._create_server_node(session, server)
        stats["servers_created"] += server_stats
        
        # Store tools, prompts, resources
        for tool in server.tools:
            stats["tools_created"] += self._store_tool(session, tool)
        
        for prompt in server.prompts:
            stats["prompts_created"] += self._store_prompt(session, prompt)
        
        for resource in server.resources:
            stats["resources_created"] += self._store_resource(session, resource)
        
        # Store repository information
        if server.repository:
            repo_stats = self._store_repository(session, server.repository, server.name)
            stats["repositories_created"] += repo_stats["repositories_created"]
            stats["relationships_created"] += repo_stats["relationships_created"]
        
        # Store package information
        for package in server.packages:
            pkg_stats = self._store_package(session, package, server.name)
            stats["packages_created"] += pkg_stats["packages_created"]
            stats["relationships_created"] += pkg_stats["relationships_created"]
        
        # Store classifications
        for category in server.categories:
            cat_stats = self._store_category_relationship(session, server.name, category)
            stats["categories_created"] += cat_stats["categories_created"]
            stats["relationships_created"] += cat_stats["relationships_created"]
        
        for domain in server.domains:
            domain_stats = self._store_domain_relationship(session, server.name, domain)
            stats["domains_created"] += domain_stats["domains_created"]
            stats["relationships_created"] += domain_stats["relationships_created"]
        
        for language in server.languages:
            lang_stats = self._store_language_relationship(session, server.name, language)
            stats["languages_created"] += lang_stats["languages_created"]
            stats["relationships_created"] += lang_stats["relationships_created"]
        
        for framework in server.frameworks:
            fw_stats = self._store_framework_relationship(session, server.name, framework)
            stats["frameworks_created"] += fw_stats["frameworks_created"]
            stats["relationships_created"] += fw_stats["relationships_created"]
        
        # Store quality metrics
        for metric in server.quality_metrics:
            stats["quality_metrics_created"] += self._store_quality_metric(session, metric, server.name)
        
        # Store usage patterns
        for pattern in server.usage_patterns:
            stats["usage_patterns_created"] += self._store_usage_pattern(session, pattern, server.name)
        
        # Store technical debt
        for debt in server.technical_debt:
            stats["technical_debt_created"] += self._store_technical_debt(session, debt, server.name)
        
        return stats
    
    def _create_server_node(self, session, server: EnhancedMCPServer) -> int:
        """Create the main server node with enhanced properties."""
        query = """
        MERGE (s:MCPServer {name: $name})
        SET s.github_url = $github_url,
            s.description = $description,
            s.server_type = $server_type,
            s.is_accessible = $is_accessible,
            s.is_archived = $is_archived,
            s.scraped_at = $scraped_at,
            s.favicon_url = $favicon_url,
            s.error_message = $error_message,
            s.tools_count = $tools_count,
            s.prompts_count = $prompts_count,
            s.resources_count = $resources_count,
            s.complexity_score = $complexity_score,
            s.maturity_score = $maturity_score,
            s.popularity_score = $popularity_score,
            s.readme_content = $readme_content,
            s.installation_instructions = $installation_instructions,
            s.usage_examples = $usage_examples
        RETURN s
        """
        
        props = {
            "name": server.name,
            "github_url": str(server.github_url),
            "description": server.description,
            "server_type": server.server_type.value,
            "is_accessible": server.is_accessible,
            "is_archived": server.is_archived,
            "scraped_at": server.scraped_at.isoformat(),
            "favicon_url": str(server.favicon_url) if server.favicon_url else None,
            "error_message": server.error_message,
            "tools_count": len(server.tools),
            "prompts_count": len(server.prompts),
            "resources_count": len(server.resources),
            "complexity_score": server.complexity_score,
            "maturity_score": server.maturity_score,
            "popularity_score": server.popularity_score,
            "readme_content": server.readme_content,
            "installation_instructions": server.installation_instructions,
            "usage_examples": server.usage_examples
        }
        
        result = session.run(query, props)
        return 1 if result.consume().counters.nodes_created > 0 else 0
    
    def _store_tool(self, session, tool: MCPTool) -> int:
        """Store an enhanced tool."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (t:Tool {name: $tool_name, server_name: $server_name})
        SET t.description = $description,
            t.parameters_count = $parameters_count,
            t.complexity_score = $complexity_score,
            t.usage_frequency = $usage_frequency,
            t.category_tags = $category_tags
        MERGE (s)-[:PROVIDES_TOOL]->(t)
        RETURN t
        """
        
        result = session.run(query, {
            "server_name": tool.server_name,
            "tool_name": tool.name,
            "description": tool.description,
            "parameters_count": len(tool.parameters),
            "complexity_score": tool.complexity_score,
            "usage_frequency": tool.usage_frequency,
            "category_tags": tool.category_tags
        })
        
        return 1 if result.consume().counters.nodes_created > 0 else 0
    
    def _store_prompt(self, session, prompt: MCPPrompt) -> int:
        """Store an enhanced prompt."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (p:Prompt {name: $prompt_name, server_name: $server_name})
        SET p.description = $description,
            p.arguments_count = $arguments_count,
            p.template_type = $template_type
        MERGE (s)-[:PROVIDES_PROMPT]->(p)
        RETURN p
        """
        
        result = session.run(query, {
            "server_name": prompt.server_name,
            "prompt_name": prompt.name,
            "description": prompt.description,
            "arguments_count": len(prompt.arguments),
            "template_type": prompt.template_type
        })
        
        return 1 if result.consume().counters.nodes_created > 0 else 0
    
    def _store_resource(self, session, resource: MCPResource) -> int:
        """Store an enhanced resource."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (r:Resource {name: $resource_name, server_name: $server_name})
        SET r.description = $description,
            r.uri_pattern = $uri_pattern,
            r.mime_type = $mime_type,
            r.access_level = $access_level,
            r.supported_operations = $supported_operations
        MERGE (s)-[:PROVIDES_RESOURCE]->(r)
        RETURN r
        """
        
        result = session.run(query, {
            "server_name": resource.server_name,
            "resource_name": resource.name,
            "description": resource.description,
            "uri_pattern": resource.uri_pattern,
            "mime_type": resource.mime_type,
            "access_level": resource.access_level,
            "supported_operations": resource.supported_operations
        })
        
        return 1 if result.consume().counters.nodes_created > 0 else 0
    
    def _store_repository(self, session, repo: Repository, server_name: str) -> Dict[str, int]:
        """Store repository information and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (repo:Repository {url: $url})
        SET repo.owner = $owner,
            repo.name = $name,
            repo.primary_language = $primary_language,
            repo.stars = $stars,
            repo.forks = $forks,
            repo.watchers = $watchers,
            repo.open_issues = $open_issues,
            repo.size_kb = $size_kb,
            repo.created_at = $created_at,
            repo.updated_at = $updated_at,
            repo.pushed_at = $pushed_at,
            repo.default_branch = $default_branch,
            repo.topics = $topics,
            repo.is_fork = $is_fork,
            repo.is_archived = $is_archived,
            repo.license_name = $license_name,
            repo.description = $description,
            repo.homepage = $homepage
        MERGE (s)-[:HOSTED_IN]->(repo)
        RETURN repo
        """
        
        props = {
            "server_name": server_name,
            "url": str(repo.url),
            "owner": repo.owner,
            "name": repo.name,
            "primary_language": repo.primary_language,
            "stars": repo.stars,
            "forks": repo.forks,
            "watchers": repo.watchers,
            "open_issues": repo.open_issues,
            "size_kb": repo.size_kb,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
            "default_branch": repo.default_branch,
            "topics": repo.topics,
            "is_fork": repo.is_fork,
            "is_archived": repo.is_archived,
            "license_name": repo.license_name,
            "description": repo.description,
            "homepage": str(repo.homepage) if repo.homepage else None
        }
        
        result = session.run(query, props)
        counters = result.consume().counters
        return {
            "repositories_created": counters.nodes_created,
            "relationships_created": counters.relationships_created
        }
    
    def _store_package(self, session, package: Package, server_name: str) -> Dict[str, int]:
        """Store package information and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (pkg:Package {name: $name, ecosystem: $ecosystem})
        SET pkg.version = $version,
            pkg.description = $description,
            pkg.author = $author,
            pkg.keywords = $keywords,
            pkg.homepage = $homepage,
            pkg.repository_url = $repository_url
        MERGE (s)-[:PACKAGED_AS]->(pkg)
        RETURN pkg
        """
        
        props = {
            "server_name": server_name,
            "name": package.name,
            "ecosystem": package.ecosystem,
            "version": package.version,
            "description": package.description,
            "author": package.author,
            "keywords": package.keywords,
            "homepage": str(package.homepage) if package.homepage else None,
            "repository_url": str(package.repository_url) if package.repository_url else None
        }
        
        result = session.run(query, props)
        counters = result.consume().counters
        return {
            "packages_created": counters.nodes_created,
            "relationships_created": counters.relationships_created
        }
    
    def _store_category_relationship(self, session, server_name: str, category: str) -> Dict[str, int]:
        """Store category and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (c:Category {name: $category})
        MERGE (s)-[:BELONGS_TO_CATEGORY {
            confidence: 1.0,
            assigned_at: datetime()
        }]->(c)
        RETURN c
        """
        
        result = session.run(query, {"server_name": server_name, "category": category})
        counters = result.consume().counters
        return {
            "categories_created": counters.nodes_created,
            "relationships_created": counters.relationships_created
        }
    
    def _store_domain_relationship(self, session, server_name: str, domain: str) -> Dict[str, int]:
        """Store domain and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (d:Domain {name: $domain})
        MERGE (s)-[:OPERATES_IN_DOMAIN {
            relevance_score: 1.0
        }]->(d)
        RETURN d
        """
        
        result = session.run(query, {"server_name": server_name, "domain": domain})
        counters = result.consume().counters
        return {
            "domains_created": counters.nodes_created,
            "relationships_created": counters.relationships_created
        }
    
    def _store_language_relationship(self, session, server_name: str, language: str) -> Dict[str, int]:
        """Store language and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (l:Language {name: $language})
        MERGE (s)-[:IMPLEMENTED_IN {
            percentage: 100.0
        }]->(l)
        RETURN l
        """
        
        result = session.run(query, {"server_name": server_name, "language": language})
        counters = result.consume().counters
        return {
            "languages_created": counters.nodes_created,
            "relationships_created": counters.relationships_created
        }
    
    def _store_framework_relationship(self, session, server_name: str, framework: str) -> Dict[str, int]:
        """Store framework and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (f:Framework {name: $framework})
        MERGE (s)-[:USES_FRAMEWORK {
            adoption_level: "full"
        }]->(f)
        RETURN f
        """
        
        result = session.run(query, {"server_name": server_name, "framework": framework})
        counters = result.consume().counters
        return {
            "frameworks_created": counters.nodes_created,
            "relationships_created": counters.relationships_created
        }
    
    def _store_quality_metric(self, session, metric: QualityMetric, server_name: str) -> int:
        """Store quality metric and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (qm:QualityMetric {
            metric_name: $metric_name,
            server_name: $server_name
        })
        SET qm.metric_type = $metric_type,
            qm.value = $value,
            qm.measurement_date = $measurement_date,
            qm.calculation_method = $calculation_method,
            qm.target_value = $target_value,
            qm.threshold_met = $threshold_met
        MERGE (s)-[:HAS_QUALITY_METRIC {
            measured_at: $measurement_date
        }]->(qm)
        RETURN qm
        """
        
        result = session.run(query, {
            "server_name": server_name,
            "metric_name": metric.metric_name,
            "metric_type": metric.metric_type.value,
            "value": metric.value,
            "measurement_date": metric.measurement_date.isoformat(),
            "calculation_method": metric.calculation_method,
            "target_value": metric.target_value,
            "threshold_met": metric.threshold_met
        })
        
        return 1 if result.consume().counters.nodes_created > 0 else 0
    
    def _store_usage_pattern(self, session, pattern: UsagePattern, server_name: str) -> int:
        """Store usage pattern and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (up:UsagePattern {
            pattern_type: $pattern_type,
            server_name: $server_name
        })
        SET up.frequency = $frequency,
            up.instructions = $instructions,
            up.prerequisites = $prerequisites,
            up.success_rate = $success_rate,
            up.estimated_setup_time = $estimated_setup_time
        MERGE (s)-[:HAS_USAGE_PATTERN]->(up)
        RETURN up
        """
        
        result = session.run(query, {
            "server_name": server_name,
            "pattern_type": pattern.pattern_type,
            "frequency": pattern.frequency,
            "instructions": pattern.instructions,
            "prerequisites": pattern.prerequisites,
            "success_rate": pattern.success_rate,
            "estimated_setup_time": pattern.estimated_setup_time
        })
        
        return 1 if result.consume().counters.nodes_created > 0 else 0
    
    def _store_technical_debt(self, session, debt: TechnicalDebt, server_name: str) -> int:
        """Store technical debt and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (td:TechnicalDebt {
            debt_type: $debt_type,
            server_name: $server_name,
            file_path: $file_path
        })
        SET td.severity = $severity,
            td.estimated_effort = $estimated_effort,
            td.detection_date = $detection_date,
            td.status = $status,
            td.description = $description
        MERGE (s)-[:HAS_TECHNICAL_DEBT {
            priority: $severity
        }]->(td)
        RETURN td
        """
        
        result = session.run(query, {
            "server_name": server_name,
            "debt_type": debt.debt_type.value,
            "severity": debt.severity,
            "estimated_effort": debt.estimated_effort,
            "detection_date": debt.detection_date.isoformat(),
            "status": debt.status,
            "description": debt.description,
            "file_path": debt.file_path
        })
        
        return 1 if result.consume().counters.nodes_created > 0 else 0
    
    def get_enhanced_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the enhanced knowledge graph."""
        with self.driver.session() as session:
            stats = {}
            
            # Node counts
            node_queries = {
                "servers": "MATCH (s:MCPServer) RETURN count(s) as count",
                "tools": "MATCH (t:Tool) RETURN count(t) as count",
                "prompts": "MATCH (p:Prompt) RETURN count(p) as count",
                "resources": "MATCH (r:Resource) RETURN count(r) as count",
                "repositories": "MATCH (repo:Repository) RETURN count(repo) as count",
                "packages": "MATCH (pkg:Package) RETURN count(pkg) as count",
                "categories": "MATCH (c:Category) RETURN count(c) as count",
                "domains": "MATCH (d:Domain) RETURN count(d) as count",
                "languages": "MATCH (l:Language) RETURN count(l) as count",
                "frameworks": "MATCH (f:Framework) RETURN count(f) as count",
                "quality_metrics": "MATCH (qm:QualityMetric) RETURN count(qm) as count",
                "usage_patterns": "MATCH (up:UsagePattern) RETURN count(up) as count",
                "technical_debt": "MATCH (td:TechnicalDebt) RETURN count(td) as count"
            }
            
            for key, query in node_queries.items():
                result = session.run(query)
                stats[key] = result.single()["count"]
            
            # Relationship counts
            rel_query = "MATCH ()-[r]->() RETURN count(r) as count"
            result = session.run(rel_query)
            stats["relationships"] = result.single()["count"]
            
            # Enhanced analytics
            stats["ecosystem_insights"] = self._get_ecosystem_insights(session)
            stats["quality_overview"] = self._get_quality_overview(session)
            stats["technology_landscape"] = self._get_technology_landscape(session)
            
            return stats
    
    def _get_ecosystem_insights(self, session) -> Dict[str, Any]:
        """Get insights about the MCP ecosystem."""
        insights = {}
        
        # Top categories by server count
        top_categories = session.run("""
            MATCH (s:MCPServer)-[:BELONGS_TO_CATEGORY]->(c:Category)
            RETURN c.name as category, count(s) as server_count
            ORDER BY server_count DESC LIMIT 10
        """)
        insights["top_categories"] = [dict(record) for record in top_categories]
        
        # Most tool-rich servers
        tool_rich = session.run("""
            MATCH (s:MCPServer)
            WHERE s.tools_count > 0
            RETURN s.name, s.tools_count, s.description
            ORDER BY s.tools_count DESC LIMIT 10
        """)
        insights["most_tool_rich_servers"] = [dict(record) for record in tool_rich]
        
        # Framework adoption
        framework_adoption = session.run("""
            MATCH (s:MCPServer)-[:USES_FRAMEWORK]->(f:Framework)
            RETURN f.name as framework, count(s) as adoption_count
            ORDER BY adoption_count DESC
        """)
        insights["framework_adoption"] = [dict(record) for record in framework_adoption]
        
        return insights
    
    def _get_quality_overview(self, session) -> Dict[str, Any]:
        """Get quality metrics overview."""
        quality = {}
        
        # Average quality scores
        avg_quality = session.run("""
            MATCH (s:MCPServer)
            WHERE s.complexity_score IS NOT NULL OR s.maturity_score IS NOT NULL
            RETURN avg(s.complexity_score) as avg_complexity,
                   avg(s.maturity_score) as avg_maturity,
                   avg(s.popularity_score) as avg_popularity
        """)
        quality["averages"] = dict(avg_quality.single())
        
        # Technical debt distribution
        debt_dist = session.run("""
            MATCH (s:MCPServer)-[:HAS_TECHNICAL_DEBT]->(td:TechnicalDebt)
            RETURN td.debt_type as type, count(td) as count
            ORDER BY count DESC
        """)
        quality["technical_debt_distribution"] = [dict(record) for record in debt_dist]
        
        return quality
    
    def _get_technology_landscape(self, session) -> Dict[str, Any]:
        """Get technology landscape overview."""
        tech = {}
        
        # Language distribution
        lang_dist = session.run("""
            MATCH (s:MCPServer)-[:IMPLEMENTED_IN]->(l:Language)
            RETURN l.name as language, count(s) as server_count
            ORDER BY server_count DESC
        """)
        tech["language_distribution"] = [dict(record) for record in lang_dist]
        
        # Package ecosystem distribution
        pkg_dist = session.run("""
            MATCH (s:MCPServer)-[:PACKAGED_AS]->(pkg:Package)
            RETURN pkg.ecosystem as ecosystem, count(s) as server_count
            ORDER BY server_count DESC
        """)
        tech["package_ecosystem_distribution"] = [dict(record) for record in pkg_dist]
        
        return tech
    
    def find_similar_servers_enhanced(self, server_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find similar servers using enhanced similarity metrics."""
        with self.driver.session() as session:
            query = """
            MATCH (s1:MCPServer {name: $server_name})
            MATCH (s2:MCPServer) WHERE s1 <> s2
            
            // Calculate similarity based on multiple factors
            OPTIONAL MATCH (s1)-[:BELONGS_TO_CATEGORY]->(c:Category)<-[:BELONGS_TO_CATEGORY]-(s2)
            WITH s1, s2, count(DISTINCT c) as shared_categories
            
            OPTIONAL MATCH (s1)-[:IMPLEMENTED_IN]->(l:Language)<-[:IMPLEMENTED_IN]-(s2)
            WITH s1, s2, shared_categories, count(DISTINCT l) as shared_languages
            
            OPTIONAL MATCH (s1)-[:USES_FRAMEWORK]->(f:Framework)<-[:USES_FRAMEWORK]-(s2)
            WITH s1, s2, shared_categories, shared_languages, count(DISTINCT f) as shared_frameworks
            
            // Calculate composite similarity score
            WITH s2, (shared_categories * 3 + shared_languages * 2 + shared_frameworks * 1) as similarity_score
            WHERE similarity_score > 0
            
            RETURN s2.name as name,
                   s2.description as description,
                   s2.github_url as github_url,
                   s2.tools_count as tools_count,
                   s2.complexity_score as complexity_score,
                   similarity_score
            ORDER BY similarity_score DESC, s2.tools_count DESC
            LIMIT $limit
            """
            
            result = session.run(query, {"server_name": server_name, "limit": limit})
            return [dict(record) for record in result]
    
    def get_server_recommendations(self, categories: List[str], min_tools: int = 1) -> List[Dict[str, Any]]:
        """Get server recommendations based on categories and requirements."""
        with self.driver.session() as session:
            query = """
            MATCH (s:MCPServer)-[:BELONGS_TO_CATEGORY]->(c:Category)
            WHERE c.name IN $categories AND s.tools_count >= $min_tools
            
            WITH s, count(DISTINCT c) as category_matches
            ORDER BY category_matches DESC, s.tools_count DESC, s.popularity_score DESC
            
            RETURN s.name as name,
                   s.description as description,
                   s.github_url as github_url,
                   s.tools_count as tools_count,
                   s.complexity_score as complexity_score,
                   s.maturity_score as maturity_score,
                   category_matches,
                   collect(DISTINCT c.name) as matching_categories
            LIMIT 20
            """
            
            result = session.run(query, {
                "categories": categories,
                "min_tools": min_tools
            })
            return [dict(record) for record in result]


def store_enhanced_mcp_data_in_neo4j(results: EnhancedScrapingResults, 
                                    neo4j_uri: str = "bolt://localhost:7687",
                                    neo4j_username: str = "neo4j",
                                    neo4j_password: str = "password") -> Dict[str, Any]:
    """
    Store enhanced MCP scraping results in Neo4j knowledge graph.
    
    Args:
        results: EnhancedScrapingResults from the MCP scraper
        neo4j_uri: Neo4j connection URI
        neo4j_username: Neo4j username
        neo4j_password: Neo4j password
    
    Returns:
        Dictionary with comprehensive storage statistics
    """
    graph = EnhancedMCPKnowledgeGraph(neo4j_uri, neo4j_username, neo4j_password)
    
    try:
        print("🔗 Connecting to Enhanced Neo4j Knowledge Graph...")
        
        # Store the enhanced data
        print("💾 Storing enhanced MCP server data...")
        storage_stats = graph.store_enhanced_results(results)
        
        # Get comprehensive graph statistics
        graph_stats = graph.get_enhanced_graph_statistics()
        
        # Combine stats
        combined_stats = {
            "storage": storage_stats,
            "graph": graph_stats,
            "neo4j_uri": neo4j_uri,
            "enhancement_features": [
                "Comprehensive node types (12+ entity types)",
                "Rich relationship properties with metadata",
                "Quality metrics and technical debt tracking",
                "Advanced similarity algorithms",
                "Ecosystem insights and analytics",
                "Technology landscape mapping"
            ]
        }
        
        print("✅ Successfully stored enhanced MCP data in Neo4j!")
        return combined_stats
        
    finally:
        graph.close()