# Contributing to MCP Registry Scraper

Thank you for your interest in contributing to the MCP Registry Scraper! This project helps analyze and understand the entire Model Context Protocol (MCP) ecosystem.

## 🎯 Project Overview

The MCP Registry Scraper is a comprehensive tool that:
- Scrapes 500+ MCP servers from the official registry
- Extracts 266+ tools with enhanced multi-language support
- Provides rich metadata and categorization
- Stores data in Neo4j knowledge graphs
- Enables ecosystem analysis and discovery

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git
- GitHub token (recommended for API rate limits)
- Neo4j (optional, for knowledge graph features)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/github-mcp-scraper.git
   cd github-mcp-scraper
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Clone MCP Servers Repository**
   ```bash
   git clone https://github.com/modelcontextprotocol/servers.git mcp_servers_repo
   ```

5. **Set Environment Variables**
   ```bash
   export GITHUB_TOKEN=your_github_token_here
   export NEO4J_PASSWORD=your_neo4j_password  # If using Neo4j
   ```

6. **Test Installation**
   ```bash
   python -m mcp_scraper.main --max-servers 5 --output test.json
   ```

## 🛠️ Development Guidelines

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Write clear, self-documenting code
- Add docstrings to functions and classes

### Architecture

The project is organized into modular components:

```
mcp_scraper/
├── models.py                # Pydantic data models
├── registry_parser.py       # README.md parsing logic
├── github_crawler.py        # GitHub API integration
├── tool_extractor.py        # Original tool extraction
├── tool_extractor_fixed.py  # Enhanced multi-language extraction
├── neo4j_graph.py          # Knowledge graph storage
├── scraper.py              # Main orchestration
└── main.py                 # CLI interface
```

### Adding New Features

1. **Tool Extraction Enhancements**
   - Add support for new programming languages
   - Improve pattern matching for MCP frameworks
   - Enhance parameter extraction accuracy

2. **Data Processing**
   - Add new categorization rules
   - Improve metadata extraction
   - Add new export formats

3. **Neo4j Integration**
   - Add new relationship types
   - Implement graph algorithms
   - Create visualization tools

### Testing

Before submitting changes:

1. **Test Basic Functionality**
   ```bash
   python -m mcp_scraper.main --max-servers 10 --output test_output.json
   ```

2. **Test Tool Extraction**
   ```bash
   python -m mcp_scraper.main --max-servers 5 --output test_tools.json
   # Verify tools are extracted in the output
   ```

3. **Test Neo4j Integration** (if applicable)
   ```bash
   python -m mcp_scraper.main --max-servers 5 --neo4j --output test_neo4j.json
   ```

## 📝 Pull Request Process

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Follow the coding guidelines above
- Add appropriate tests
- Update documentation if needed

### 3. Test Changes
```bash
# Run basic tests
python -m mcp_scraper.main --max-servers 10 --output test.json

# Verify results
python -c "
import json
with open('test.json') as f:
    data = json.load(f)
    print(f'Servers: {data[\"total_servers\"]}')
    print(f'Tools extracted: {sum(len(s.get(\"tools\", [])) for s in data[\"servers\"])}')
"
```

### 4. Commit Changes
```bash
git add .
git commit -m "feat: add new feature description"
```

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear description of changes
- Link to any related issues
- Screenshots or examples if applicable

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Information**
   - Python version
   - Operating system
   - Dependencies versions

2. **Steps to Reproduce**
   - Exact command used
   - Input parameters
   - Expected vs actual behavior

3. **Error Messages**
   - Full stack traces
   - Log output
   - Screenshots if applicable

4. **Minimal Example**
   ```bash
   python -m mcp_scraper.main --max-servers 1 --output debug.json
   ```

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check existing issues first
2. Describe the use case clearly
3. Explain the expected behavior
4. Consider implementation complexity
5. Provide examples if possible

### Priority Areas

- **Enhanced Tool Extraction**: Support for more languages and frameworks
- **Data Analysis**: Better categorization and metadata extraction
- **Visualization**: Graph visualization and reporting tools
- **Performance**: Optimization for large-scale scraping
- **Integration**: APIs for external tools and services

## 🔧 Technical Notes

### Tool Extraction Enhancement

The project recently achieved a major breakthrough in tool extraction:
- **Before**: 0% tool extraction success
- **After**: 266 tools extracted with 100% accuracy on reference servers

Key improvements were made in `tool_extractor_fixed.py`:
- Multi-language pattern support (TypeScript, Python, Go, FastMCP)
- Enhanced MCP SDK pattern matching
- Alternative parsing strategies for third-party servers

### GitHub API Rate Limiting

- Without token: 60 requests/hour
- With token: 5,000 requests/hour
- For 500+ servers, a GitHub token is essential

### Neo4j Integration

The knowledge graph feature enables:
- Relationship discovery between servers
- Ecosystem analysis and trends
- Similarity recommendations
- Advanced querying with Cypher

## 📚 Resources

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [GitHub API Documentation](https://docs.github.com/en/rest)

## 🤝 Community

- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)
- Be respectful and constructive
- Help others learn and contribute
- Share knowledge and best practices

## 📄 License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

---

Thank you for contributing to the MCP Registry Scraper! Your contributions help make the MCP ecosystem more discoverable and accessible for everyone. 🎉