"""Main MCP registry scraper."""

import json
import csv
from pathlib import Path
from typing import Optional, List
from tqdm import tqdm

from .models import MCPServer, ScrapingResults
from .registry_parser import RegistryParser
from .github_crawler import GitHubCrawler
from .tool_extractor_fixed import EnhancedToolExtractor


class MCPRegistryScraper:
    """Main scraper for the MCP server registry."""
    
    def __init__(self, github_token: Optional[str] = None, repo_path: str = "mcp_servers_repo"):
        """Initialize the scraper."""
        self.repo_path = repo_path
        self.parser = RegistryParser(repo_path)
        self.crawler = GitHubCrawler(github_token)
        self.extractor = EnhancedToolExtractor(github_token)
    
    def scrape_all(self, 
                   enhance_metadata: bool = True,
                   extract_tools: bool = True,
                   max_servers: Optional[int] = None) -> ScrapingResults:
        """Scrape all MCP servers from the registry."""
        print("🔍 Parsing MCP server registry...")
        
        # Parse basic server information from registry
        servers = self.parser.parse_registry()
        
        if max_servers:
            servers = servers[:max_servers]
        
        print(f"📋 Found {len(servers)} servers in registry")
        
        successful_scrapes = 0
        failed_scrapes = 0
        errors = []
        
        # Process each server with progress bar
        for server in tqdm(servers, desc="Processing servers"):
            try:
                # Enhance with GitHub metadata
                if enhance_metadata:
                    server = self.crawler.enhance_server(server)
                
                # Extract tool definitions
                if extract_tools:
                    server = self.extractor.extract_tools_from_server(server)
                
                # Categorize server
                server = self._categorize_server(server)
                
                if server.is_accessible and not server.error_message:
                    successful_scrapes += 1
                else:
                    failed_scrapes += 1
                    if server.error_message:
                        errors.append(f"{server.name}: {server.error_message}")
                
            except Exception as e:
                failed_scrapes += 1
                error_msg = f"{server.name}: {str(e)}"
                errors.append(error_msg)
                server.error_message = str(e)
                server.is_accessible = False
        
        # Count server types
        reference_servers = sum(1 for s in servers if s.server_type.value == "reference")
        third_party_servers = sum(1 for s in servers if s.server_type.value == "third_party")
        
        results = ScrapingResults(
            total_servers=len(servers),
            successful_scrapes=successful_scrapes,
            failed_scrapes=failed_scrapes,
            reference_servers=reference_servers,
            third_party_servers=third_party_servers,
            servers=servers,
            errors=errors
        )
        
        print(f"✅ Scraping completed: {successful_scrapes} successful, {failed_scrapes} failed")
        
        return results
    
    def _categorize_server(self, server: MCPServer) -> MCPServer:
        """Categorize server based on its functionality."""
        categories = set()
        tags = set()
        
        # Analyze server name and description
        text = f"{server.name} {server.description or ''}".lower()
        
        # Define category keywords
        category_keywords = {
            'database': ['database', 'db', 'sql', 'postgres', 'mysql', 'mongodb', 'sqlite'],
            'web': ['web', 'http', 'api', 'fetch', 'browser', 'scraping'],
            'filesystem': ['file', 'filesystem', 'directory', 'path'],
            'git': ['git', 'github', 'version control', 'repository'],
            'ai': ['ai', 'llm', 'openai', 'anthropic', 'model', 'chat'],
            'data': ['data', 'csv', 'json', 'xml', 'excel'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 's3', 'lambda'],
            'development': ['dev', 'development', 'build', 'test', 'ci/cd'],
            'communication': ['slack', 'discord', 'email', 'notification'],
            'productivity': ['calendar', 'todo', 'task', 'note'],
            'time': ['time', 'date', 'timezone', 'schedule'],
            'memory': ['memory', 'cache', 'storage', 'knowledge']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                categories.add(category)
        
        # Extract tags from repository topics
        if server.repository_stats and server.repository_stats.topics:
            tags.update(server.repository_stats.topics)
        
        # Add programming language as tag
        if server.repository_stats and server.repository_stats.language:
            tags.add(server.repository_stats.language.lower())
        
        server.categories = list(categories)
        server.tags = list(tags)
        
        return server
    
    def export_to_json(self, results: ScrapingResults, output_path: str):
        """Export results to JSON file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict for JSON serialization
        data = results.model_dump(mode='json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Results exported to JSON: {output_file}")
    
    def export_to_csv(self, results: ScrapingResults, output_path: str):
        """Export results to CSV file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            'name', 'github_url', 'description', 'server_type', 'is_accessible',
            'is_archived', 'stars', 'forks', 'language', 'topics', 'categories',
            'tools_count', 'prompts_count', 'resources_count', 'tool_names',
            'package_name', 'package_version', 'author', 'license',
            'created_at', 'updated_at', 'error_message'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for server in results.servers:
                row = {
                    'name': server.name,
                    'github_url': str(server.github_url),
                    'description': server.description,
                    'server_type': server.server_type.value,
                    'is_accessible': server.is_accessible,
                    'is_archived': server.is_archived,
                    'stars': server.repository_stats.stars if server.repository_stats else 0,
                    'forks': server.repository_stats.forks if server.repository_stats else 0,
                    'language': server.repository_stats.language if server.repository_stats else '',
                    'topics': ', '.join(server.repository_stats.topics) if server.repository_stats else '',
                    'categories': ', '.join(server.categories),
                    'tools_count': len(server.tools),
                    'prompts_count': len(server.prompts),
                    'resources_count': len(server.resources),
                    'tool_names': ', '.join([tool.name for tool in server.tools]),
                    'package_name': server.package_info.name if server.package_info else '',
                    'package_version': server.package_info.version if server.package_info else '',
                    'author': server.package_info.author if server.package_info else '',
                    'license': server.package_info.license if server.package_info else '',
                    'created_at': server.repository_stats.created_at if server.repository_stats else '',
                    'updated_at': server.repository_stats.updated_at if server.repository_stats else '',
                    'error_message': server.error_message or ''
                }
                writer.writerow(row)
        
        print(f"📊 Results exported to CSV: {output_file}")
    
    def print_summary(self, results: ScrapingResults):
        """Print summary statistics."""
        print("\n" + "="*60)
        print("📈 MCP REGISTRY SCRAPING SUMMARY")
        print("="*60)
        print(f"Total servers found: {results.total_servers}")
        print(f"Successfully scraped: {results.successful_scrapes}")
        print(f"Failed to scrape: {results.failed_scrapes}")
        print(f"Reference servers: {results.reference_servers}")
        print(f"Third-party servers: {results.third_party_servers}")
        print(f"Scraped at: {results.scraped_at}")
        
        # Tool statistics
        total_tools = sum(len(server.tools) for server in results.servers)
        total_prompts = sum(len(server.prompts) for server in results.servers)
        total_resources = sum(len(server.resources) for server in results.servers)
        
        print(f"\n🔧 CAPABILITIES DISCOVERED:")
        print(f"Total tools: {total_tools}")
        print(f"Total prompts: {total_prompts}")
        print(f"Total resources: {total_resources}")
        
        # Top categories
        category_counts = {}
        for server in results.servers:
            for category in server.categories:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        if category_counts:
            print(f"\n📂 TOP CATEGORIES:")
            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {category}: {count}")
        
        # Languages
        language_counts = {}
        for server in results.servers:
            if server.repository_stats and server.repository_stats.language:
                lang = server.repository_stats.language
                language_counts[lang] = language_counts.get(lang, 0) + 1
        
        if language_counts:
            print(f"\n💻 PROGRAMMING LANGUAGES:")
            for lang, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {lang}: {count}")
        
        # Errors
        if results.errors:
            print(f"\n❌ ERRORS ({len(results.errors)}):")
            for error in results.errors[:10]:  # Show first 10 errors
                print(f"  {error}")
            if len(results.errors) > 10:
                print(f"  ... and {len(results.errors) - 10} more errors")
        
        print("="*60)