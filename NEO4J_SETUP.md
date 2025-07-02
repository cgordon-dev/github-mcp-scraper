# Neo4j Knowledge Graph Setup Guide

## Overview

The MCP Registry Scraper includes comprehensive Neo4j integration to store the complete MCP ecosystem as a knowledge graph, enabling powerful queries, relationships discovery, and ecosystem analysis.

## Expected Results ACHIEVED ✅

- **505+ MCP servers discovered** ✅
- **Rich metadata** for each server (stars, language, tools, package info) ✅  
- **Categorization by functionality** (AI, database, web, cloud, etc.) ✅
- **Tool definitions extracted** from source code ✅
- **Comprehensive reports** in JSON/CSV format ✅
- **Neo4j knowledge graph storage** ✅

## Knowledge Graph Schema

### Node Types

```cypher
// MCP Server nodes
(:MCPServer {
  name: string,
  github_url: string,
  description: string,
  server_type: "reference" | "third_party",
  stars: integer,
  forks: integer,
  language: string,
  package_name: string,
  package_version: string,
  author: string,
  license: string,
  tools_count: integer,
  is_accessible: boolean,
  is_archived: boolean
})

// Tool nodes
(:Tool {
  name: string,
  server_name: string,
  description: string,
  parameters_count: integer
})

// Category nodes
(:Category {name: string})

// Programming language nodes  
(:Language {name: string})

// Tag nodes
(:Tag {name: string})

// Organization nodes
(:Organization {name: string})
```

### Relationships

```cypher
// Server capabilities
(MCPServer)-[:HAS_TOOL]->(Tool)
(MCPServer)-[:BELONGS_TO_CATEGORY]->(Category)
(MCPServer)-[:HAS_TAG]->(Tag)
(MCPServer)-[:IMPLEMENTED_IN]->(Language)

// Maintainership
(Organization)-[:MAINTAINS]->(MCPServer)
```

## Installation & Setup

### 1. Install Neo4j

**Option A: Neo4j Desktop**
1. Download from [neo4j.com/download](https://neo4j.com/download/)
2. Create a new database project
3. Set password and start database

**Option B: Docker**
```bash
docker run \
    --name neo4j \
    -p7474:7474 -p7687:7687 \
    -d \
    -e NEO4J_AUTH=neo4j/password \
    neo4j:latest
```

**Option C: Neo4j Aura Cloud**
1. Sign up at [neo4j.com/aura](https://neo4j.com/aura/)
2. Create free instance
3. Note connection details

### 2. Set Environment Variables

```bash
export NEO4J_PASSWORD=your_password
export GITHUB_TOKEN=your_github_token  # Optional but recommended
```

### 3. Verify Connection

Visit [http://localhost:7474](http://localhost:7474) and login with:
- Username: `neo4j`
- Password: `password` (or your custom password)

## Usage

### Basic Usage - Store in Neo4j

```bash
# Full scrape with Neo4j storage
python3 -m mcp_scraper.main \
  --output mcp_servers.json \
  --format both \
  --neo4j \
  --neo4j-password your_password

# Quick test with limited servers
python3 -m mcp_scraper.main \
  --max-servers 10 \
  --neo4j \
  --output test.json
```

### Advanced Neo4j Configuration

```bash
# Custom Neo4j instance
python3 -m mcp_scraper.main \
  --neo4j \
  --neo4j-uri bolt://your-server:7687 \
  --neo4j-username admin \
  --neo4j-password secure_password \
  --output results.json

# Neo4j Aura Cloud
python3 -m mcp_scraper.main \
  --neo4j \
  --neo4j-uri neo4j+s://xxxxx.databases.neo4j.io \
  --neo4j-username neo4j \
  --neo4j-password your_aura_password \
  --output results.json
```

## Programmatic Usage

```python
from mcp_scraper.scraper import MCPRegistryScraper
from mcp_scraper.neo4j_graph import store_mcp_data_in_neo4j

# Scrape data
scraper = MCPRegistryScraper()
results = scraper.scrape_all()

# Store in Neo4j
neo4j_stats = store_mcp_data_in_neo4j(
    results,
    neo4j_uri="bolt://localhost:7687",
    neo4j_username="neo4j", 
    neo4j_password="password"
)

print(f"Stored {neo4j_stats['storage']['servers_created']} servers")
```

## Query Examples

### Find Popular Servers by Category

```cypher
// Most popular AI/LLM servers
MATCH (s:MCPServer)-[:BELONGS_TO_CATEGORY]->(c:Category {name: "ai"})
WHERE s.stars IS NOT NULL
RETURN s.name, s.description, s.stars, s.github_url
ORDER BY s.stars DESC
LIMIT 10
```

### Discover Tool Capabilities

```cypher
// Servers with database tools
MATCH (s:MCPServer)-[:HAS_TOOL]->(t:Tool)
WHERE toLower(t.name) CONTAINS "database" 
   OR toLower(t.description) CONTAINS "database"
RETURN s.name, collect(t.name) as database_tools, s.github_url
```

### Find Similar Servers

```cypher
// Servers similar to a specific one
MATCH (target:MCPServer {name: "memory"})-[:BELONGS_TO_CATEGORY]->(c:Category)
MATCH (similar:MCPServer)-[:BELONGS_TO_CATEGORY]->(c)
WHERE target <> similar
WITH similar, count(c) as shared_categories
MATCH (similar)-[:HAS_TOOL]->(t:Tool)
RETURN similar.name, similar.description, shared_categories, count(t) as tool_count
ORDER BY shared_categories DESC, tool_count DESC
LIMIT 5
```

### Language Ecosystem Analysis

```cypher
// Most popular languages in MCP ecosystem
MATCH (s:MCPServer)-[:IMPLEMENTED_IN]->(l:Language)
RETURN l.name, count(s) as server_count, 
       avg(s.stars) as avg_stars,
       collect(s.name)[0..5] as sample_servers
ORDER BY server_count DESC
```

### Organization Insights

```cypher
// Most active organizations
MATCH (o:Organization)-[:MAINTAINS]->(s:MCPServer)
RETURN o.name, count(s) as servers_maintained,
       sum(s.stars) as total_stars,
       collect(s.name) as servers
ORDER BY servers_maintained DESC
LIMIT 10
```

### Capability Search

```cypher
// Search for specific capabilities
MATCH (s:MCPServer)
WHERE toLower(s.description) CONTAINS "database"
   OR exists((s)-[:BELONGS_TO_CATEGORY]->(:Category {name: "database"}))
OPTIONAL MATCH (s)-[:HAS_TOOL]->(t:Tool)
WHERE toLower(t.description) CONTAINS "database"
RETURN s.name, s.description, s.github_url, collect(t.name) as db_tools
```

## Advanced Features

### Server Similarity Search

```python
from mcp_scraper.neo4j_graph import MCPKnowledgeGraph

graph = MCPKnowledgeGraph()

# Find servers similar to "memory" server
similar = graph.find_similar_servers("memory", limit=5)
for server in similar:
    print(f"{server['name']}: {server['shared_categories']} shared categories")

graph.close()
```

### Full-Text Search

```python
# Search across all server metadata
results = graph.search_servers("database management", limit=10)
for result in results:
    print(f"{result['name']}: {result['description']}")
```

### Graph Statistics

```python
stats = graph.get_graph_statistics()
print(f"Total servers: {stats['servers']}")
print(f"Total tools: {stats['tools']}")
print(f"Top categories: {stats['top_categories']}")
```

## Benefits of Knowledge Graph Storage

1. **Relationship Discovery**: Find connections between servers, tools, and organizations
2. **Ecosystem Analysis**: Understand the MCP landscape and trends
3. **Recommendation Engine**: Suggest similar servers based on capabilities
4. **Impact Analysis**: Track dependencies and influences
5. **Search & Discovery**: Powerful queries across all metadata
6. **Visualization**: Create network graphs of the ecosystem
7. **Analytics**: Generate insights about the MCP community

## Troubleshooting

### Connection Issues

```bash
# Test Neo4j connection
python3 -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
with driver.session() as session:
    result = session.run('RETURN 1')
    print('✅ Connection successful')
driver.close()
"
```

### Common Errors

**"Connection refused"**
- Ensure Neo4j is running
- Check port 7687 is accessible
- Verify URI format

**"Authentication failed"**
- Check username/password
- Reset Neo4j password if needed

**"Import errors"**
- Install neo4j driver: `pip install neo4j`
- Check Python environment

### Performance Optimization

```cypher
// Create additional indexes for better query performance
CREATE INDEX server_stars IF NOT EXISTS FOR (s:MCPServer) ON (s.stars)
CREATE INDEX server_language IF NOT EXISTS FOR (s:MCPServer) ON (s.language)
CREATE INDEX tool_description IF NOT EXISTS FOR (t:Tool) ON (t.description)
```

## Example Workflow

```bash
# 1. Start Neo4j
docker run --name neo4j -p7474:7474 -p7687:7687 -d -e NEO4J_AUTH=neo4j/mypassword neo4j

# 2. Scrape and store all MCP servers
export NEO4J_PASSWORD=mypassword
python3 -m mcp_scraper.main --neo4j --format both --output complete_mcp_data

# 3. Explore in Neo4j Browser
open http://localhost:7474

# 4. Run analytics queries
# (Use Cypher examples above)
```

This creates a comprehensive knowledge graph of the entire MCP ecosystem, enabling powerful analysis and discovery of relationships across servers, tools, organizations, and capabilities!