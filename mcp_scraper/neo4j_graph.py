"""Neo4j knowledge graph integration for MCP server data."""

import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from neo4j import GraphDatabase, Driver
from .models import MCPServer, ScrapingResults


class MCPKnowledgeGraph:
    """Neo4j knowledge graph for MCP server ecosystem."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 username: str = "neo4j", 
                 password: str = "password"):
        """Initialize Neo4j connection."""
        self.driver: Driver = GraphDatabase.driver(uri, auth=(username, password))
        self._create_constraints()
    
    def close(self):
        """Close the driver connection."""
        if self.driver:
            self.driver.close()
    
    def _create_constraints(self):
        """Create constraints and indexes for better performance."""
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT server_name_unique IF NOT EXISTS FOR (s:MCPServer) REQUIRE s.name IS UNIQUE",
                "CREATE CONSTRAINT tool_name_unique IF NOT EXISTS FOR (t:Tool) REQUIRE (t.name, t.server_name) IS UNIQUE",
                "CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
                "CREATE CONSTRAINT language_name_unique IF NOT EXISTS FOR (l:Language) REQUIRE l.name IS UNIQUE",
                "CREATE CONSTRAINT tag_name_unique IF NOT EXISTS FOR (tag:Tag) REQUIRE tag.name IS UNIQUE",
                "CREATE CONSTRAINT org_name_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"Note: {constraint.split()[2]} may already exist")
    
    def clear_graph(self):
        """Clear all data from the graph (use with caution!)."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("🗑️  Graph cleared")
    
    def store_scraping_results(self, results: ScrapingResults) -> Dict[str, int]:
        """Store complete scraping results in Neo4j."""
        stats = {
            "servers_created": 0,
            "tools_created": 0,
            "categories_created": 0,
            "languages_created": 0,
            "tags_created": 0,
            "organizations_created": 0,
            "relationships_created": 0
        }
        
        with self.driver.session() as session:
            # Store scraping metadata
            self._store_scraping_metadata(session, results)
            
            # Process each server
            for server in results.servers:
                server_stats = self._store_server(session, server)
                for key, value in server_stats.items():
                    stats[key] += value
        
        return stats
    
    def _store_scraping_metadata(self, session, results: ScrapingResults):
        """Store scraping run metadata."""
        query = """
        MERGE (run:ScrapingRun {
            scraped_at: $scraped_at,
            total_servers: $total_servers,
            successful_scrapes: $successful_scrapes,
            failed_scrapes: $failed_scrapes,
            reference_servers: $reference_servers,
            third_party_servers: $third_party_servers
        })
        RETURN run
        """
        
        session.run(query, {
            "scraped_at": results.scraped_at.isoformat(),
            "total_servers": results.total_servers,
            "successful_scrapes": results.successful_scrapes,
            "failed_scrapes": results.failed_scrapes,
            "reference_servers": results.reference_servers,
            "third_party_servers": results.third_party_servers
        })
    
    def _store_server(self, session, server: MCPServer) -> Dict[str, int]:
        """Store a single MCP server and its relationships."""
        stats = {
            "servers_created": 0,
            "tools_created": 0,
            "categories_created": 0,
            "languages_created": 0,
            "tags_created": 0,
            "organizations_created": 0,
            "relationships_created": 0
        }
        
        # Create server node
        server_query = """
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
            s.resources_count = $resources_count
        """
        
        # Repository stats
        repo_stats = {}
        if server.repository_stats:
            repo_stats = {
                "stars": server.repository_stats.stars,
                "forks": server.repository_stats.forks,
                "watchers": server.repository_stats.watchers,
                "open_issues": server.repository_stats.open_issues,
                "size_kb": server.repository_stats.size_kb,
                "created_at": server.repository_stats.created_at.isoformat() if server.repository_stats.created_at else None,
                "updated_at": server.repository_stats.updated_at.isoformat() if server.repository_stats.updated_at else None,
                "pushed_at": server.repository_stats.pushed_at.isoformat() if server.repository_stats.pushed_at else None
            }
        
        # Package info
        package_info = {}
        if server.package_info:
            package_info = {
                "package_name": server.package_info.name,
                "package_version": server.package_info.version,
                "package_description": server.package_info.description,
                "author": server.package_info.author,
                "license": server.package_info.license
            }
        
        # Combine all server properties
        server_props = {
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
            **repo_stats,
            **package_info
        }
        
        result = session.run(server_query, server_props)
        if result.consume().counters.nodes_created > 0:
            stats["servers_created"] += 1
        
        # Store tools
        for tool in server.tools:
            tool_stats = self._store_tool(session, tool, server.name)
            stats["tools_created"] += tool_stats
        
        # Store categories
        for category in server.categories:
            cat_stats = self._store_category_relationship(session, server.name, category)
            stats["categories_created"] += cat_stats["categories_created"]
            stats["relationships_created"] += cat_stats["relationships_created"]
        
        # Store tags
        for tag in server.tags:
            tag_stats = self._store_tag_relationship(session, server.name, tag)
            stats["tags_created"] += tag_stats["tags_created"]
            stats["relationships_created"] += tag_stats["relationships_created"]
        
        # Store language relationship
        if server.repository_stats and server.repository_stats.language:
            lang_stats = self._store_language_relationship(session, server.name, server.repository_stats.language)
            stats["languages_created"] += lang_stats["languages_created"]
            stats["relationships_created"] += lang_stats["relationships_created"]
        
        # Store organization relationship (extracted from author)
        if server.package_info and server.package_info.author:
            org_stats = self._store_organization_relationship(session, server.name, server.package_info.author)
            stats["organizations_created"] += org_stats["organizations_created"]
            stats["relationships_created"] += org_stats["relationships_created"]
        
        return stats
    
    def _store_tool(self, session, tool, server_name: str) -> int:
        """Store a tool and link it to its server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (t:Tool {name: $tool_name, server_name: $server_name})
        SET t.description = $description,
            t.parameters_count = $parameters_count
        MERGE (s)-[:HAS_TOOL]->(t)
        RETURN t
        """
        
        result = session.run(query, {
            "server_name": server_name,
            "tool_name": tool.name,
            "description": tool.description,
            "parameters_count": len(tool.parameters)
        })
        
        return 1 if result.consume().counters.nodes_created > 0 else 0
    
    def _store_category_relationship(self, session, server_name: str, category: str) -> Dict[str, int]:
        """Store category and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (c:Category {name: $category})
        MERGE (s)-[:BELONGS_TO_CATEGORY]->(c)
        RETURN c
        """
        
        result = session.run(query, {
            "server_name": server_name,
            "category": category
        })
        
        counters = result.consume().counters
        return {
            "categories_created": counters.nodes_created,
            "relationships_created": counters.relationships_created
        }
    
    def _store_tag_relationship(self, session, server_name: str, tag: str) -> Dict[str, int]:
        """Store tag and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (t:Tag {name: $tag})
        MERGE (s)-[:HAS_TAG]->(t)
        RETURN t
        """
        
        result = session.run(query, {
            "server_name": server_name,
            "tag": tag
        })
        
        counters = result.consume().counters
        return {
            "tags_created": counters.nodes_created,
            "relationships_created": counters.relationships_created
        }
    
    def _store_language_relationship(self, session, server_name: str, language: str) -> Dict[str, int]:
        """Store programming language and link to server."""
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (l:Language {name: $language})
        MERGE (s)-[:IMPLEMENTED_IN]->(l)
        RETURN l
        """
        
        result = session.run(query, {
            "server_name": server_name,
            "language": language
        })
        
        counters = result.consume().counters
        return {
            "languages_created": counters.nodes_created,
            "relationships_created": counters.relationships_created
        }
    
    def _store_organization_relationship(self, session, server_name: str, author: str) -> Dict[str, int]:
        """Store organization and link to server."""
        # Extract organization name from author string
        org_name = author.split(',')[0].strip() if ',' in author else author.strip()
        
        query = """
        MATCH (s:MCPServer {name: $server_name})
        MERGE (o:Organization {name: $org_name})
        MERGE (o)-[:MAINTAINS]->(s)
        RETURN o
        """
        
        result = session.run(query, {
            "server_name": server_name,
            "org_name": org_name
        })
        
        counters = result.consume().counters
        return {
            "organizations_created": counters.nodes_created,
            "relationships_created": counters.relationships_created
        }
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        with self.driver.session() as session:
            stats = {}
            
            # Node counts
            node_queries = {
                "servers": "MATCH (s:MCPServer) RETURN count(s) as count",
                "tools": "MATCH (t:Tool) RETURN count(t) as count",
                "categories": "MATCH (c:Category) RETURN count(c) as count",
                "languages": "MATCH (l:Language) RETURN count(l) as count",
                "tags": "MATCH (tag:Tag) RETURN count(tag) as count",
                "organizations": "MATCH (o:Organization) RETURN count(o) as count"
            }
            
            for key, query in node_queries.items():
                result = session.run(query)
                stats[key] = result.single()["count"]
            
            # Relationship counts
            rel_query = "MATCH ()-[r]->() RETURN count(r) as count"
            result = session.run(rel_query)
            stats["relationships"] = result.single()["count"]
            
            # Top categories
            top_categories = session.run("""
                MATCH (s:MCPServer)-[:BELONGS_TO_CATEGORY]->(c:Category)
                RETURN c.name as category, count(s) as server_count
                ORDER BY server_count DESC
                LIMIT 10
            """)
            stats["top_categories"] = [dict(record) for record in top_categories]
            
            # Top languages
            top_languages = session.run("""
                MATCH (s:MCPServer)-[:IMPLEMENTED_IN]->(l:Language)
                RETURN l.name as language, count(s) as server_count
                ORDER BY server_count DESC
                LIMIT 10
            """)
            stats["top_languages"] = [dict(record) for record in top_languages]
            
            # Most popular servers (by stars)
            popular_servers = session.run("""
                MATCH (s:MCPServer)
                WHERE s.stars IS NOT NULL
                RETURN s.name as name, s.stars as stars, s.description as description
                ORDER BY s.stars DESC
                LIMIT 10
            """)
            stats["popular_servers"] = [dict(record) for record in popular_servers]
            
            return stats
    
    def find_similar_servers(self, server_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find servers similar to the given server based on categories and tools."""
        with self.driver.session() as session:
            query = """
            MATCH (s1:MCPServer {name: $server_name})-[:BELONGS_TO_CATEGORY]->(c:Category)<-[:BELONGS_TO_CATEGORY]-(s2:MCPServer)
            WHERE s1 <> s2
            WITH s2, count(c) as shared_categories
            MATCH (s2)-[:HAS_TOOL]->(t:Tool)
            WITH s2, shared_categories, count(t) as tool_count
            RETURN s2.name as name, 
                   s2.description as description,
                   s2.github_url as github_url,
                   shared_categories,
                   tool_count,
                   s2.stars as stars
            ORDER BY shared_categories DESC, tool_count DESC, stars DESC
            LIMIT $limit
            """
            
            result = session.run(query, {"server_name": server_name, "limit": limit})
            return [dict(record) for record in result]
    
    def search_servers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search servers by name, description, or tools."""
        with self.driver.session() as session:
            search_query = """
            MATCH (s:MCPServer)
            WHERE toLower(s.name) CONTAINS toLower($query)
               OR toLower(s.description) CONTAINS toLower($query)
            OPTIONAL MATCH (s)-[:HAS_TOOL]->(t:Tool)
            WHERE toLower(t.name) CONTAINS toLower($query)
               OR toLower(t.description) CONTAINS toLower($query)
            WITH s, count(t) as matching_tools
            RETURN DISTINCT s.name as name,
                          s.description as description,
                          s.github_url as github_url,
                          s.server_type as server_type,
                          s.stars as stars,
                          matching_tools
            ORDER BY matching_tools DESC, s.stars DESC
            LIMIT $limit
            """
            
            result = session.run(search_query, {"query": query, "limit": limit})
            return [dict(record) for record in result]


def store_mcp_data_in_neo4j(results: ScrapingResults, 
                           neo4j_uri: str = "bolt://localhost:7687",
                           neo4j_username: str = "neo4j",
                           neo4j_password: str = "password") -> Dict[str, Any]:
    """
    Store MCP scraping results in Neo4j knowledge graph.
    
    Args:
        results: ScrapingResults from the MCP scraper
        neo4j_uri: Neo4j connection URI
        neo4j_username: Neo4j username
        neo4j_password: Neo4j password
    
    Returns:
        Dictionary with storage statistics
    """
    graph = MCPKnowledgeGraph(neo4j_uri, neo4j_username, neo4j_password)
    
    try:
        print("🔗 Connecting to Neo4j...")
        
        # Store the data
        print("💾 Storing MCP server data in Neo4j knowledge graph...")
        storage_stats = graph.store_scraping_results(results)
        
        # Get graph statistics
        graph_stats = graph.get_graph_statistics()
        
        # Combine stats
        combined_stats = {
            "storage": storage_stats,
            "graph": graph_stats,
            "neo4j_uri": neo4j_uri
        }
        
        print("✅ Successfully stored MCP data in Neo4j!")
        return combined_stats
        
    finally:
        graph.close()