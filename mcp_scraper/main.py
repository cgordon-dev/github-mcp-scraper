"""Main entry point for the MCP registry scraper."""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from .scraper import MCPRegistryScraper
from .neo4j_graph import store_mcp_data_in_neo4j


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scraper for the Model Context Protocol (MCP) server registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scraping with all features
  mcp-scraper --output results/mcp_servers.json

  # Quick scrape without tool extraction
  mcp-scraper --no-tools --output results/basic.json

  # Scrape only first 10 servers for testing
  mcp-scraper --max-servers 10 --output results/test.json

  # Use GitHub token for higher rate limits
  export GITHUB_TOKEN=your_token_here
  mcp-scraper --output results/mcp_servers.json
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        default='mcp_servers.json',
        help='Output file path (default: mcp_servers.json)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'csv', 'both'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--github-token',
        help='GitHub token for API access (can also use GITHUB_TOKEN env var)'
    )
    
    parser.add_argument(
        '--repo-path',
        default='mcp_servers_repo',
        help='Path to MCP servers repository (default: mcp_servers_repo)'
    )
    
    parser.add_argument(
        '--max-servers',
        type=int,
        help='Maximum number of servers to process (useful for testing)'
    )
    
    parser.add_argument(
        '--no-metadata',
        action='store_true',
        help='Skip GitHub metadata enhancement'
    )
    
    parser.add_argument(
        '--no-tools',
        action='store_true',
        help='Skip tool extraction'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    # Neo4j arguments
    parser.add_argument(
        '--neo4j',
        action='store_true',
        help='Store results in Neo4j knowledge graph'
    )
    
    parser.add_argument(
        '--neo4j-uri',
        default='bolt://localhost:7687',
        help='Neo4j connection URI (default: bolt://localhost:7687)'
    )
    
    parser.add_argument(
        '--neo4j-username',
        default='neo4j',
        help='Neo4j username (default: neo4j)'
    )
    
    parser.add_argument(
        '--neo4j-password',
        help='Neo4j password (can also use NEO4J_PASSWORD env var)'
    )
    
    args = parser.parse_args()
    
    # Get GitHub token
    github_token = args.github_token or os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        print("⚠️  No GitHub token provided. Rate limits may apply.")
        print("   Set GITHUB_TOKEN environment variable or use --github-token")
        print("   to avoid rate limiting issues.\n")
    
    # Initialize scraper
    try:
        scraper = MCPRegistryScraper(
            github_token=github_token,
            repo_path=args.repo_path
        )
    except Exception as e:
        print(f"❌ Error initializing scraper: {e}")
        sys.exit(1)
    
    # Run scraping
    try:
        print("🚀 Starting MCP registry scraping...")
        print(f"📁 Repository path: {args.repo_path}")
        print(f"📄 Output file: {args.output}")
        print(f"🔧 Enhance metadata: {not args.no_metadata}")
        print(f"⚙️  Extract tools: {not args.no_tools}")
        if args.max_servers:
            print(f"🔢 Max servers: {args.max_servers}")
        print()
        
        results = scraper.scrape_all(
            enhance_metadata=not args.no_metadata,
            extract_tools=not args.no_tools,
            max_servers=args.max_servers
        )
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        sys.exit(1)
    
    # Export results
    try:
        output_path = Path(args.output)
        
        if args.format in ['json', 'both']:
            json_path = output_path.with_suffix('.json')
            scraper.export_to_json(results, str(json_path))
        
        if args.format in ['csv', 'both']:
            csv_path = output_path.with_suffix('.csv')
            scraper.export_to_csv(results, str(csv_path))
        
    except Exception as e:
        print(f"❌ Error exporting results: {e}")
        sys.exit(1)
    
    # Store in Neo4j if requested
    if args.neo4j:
        try:
            neo4j_password = args.neo4j_password or os.getenv('NEO4J_PASSWORD', 'password')
            
            print(f"\n🔗 Storing data in Neo4j knowledge graph...")
            print(f"📍 URI: {args.neo4j_uri}")
            print(f"👤 Username: {args.neo4j_username}")
            
            neo4j_stats = store_mcp_data_in_neo4j(
                results,
                neo4j_uri=args.neo4j_uri,
                neo4j_username=args.neo4j_username,
                neo4j_password=neo4j_password
            )
            
            print(f"\n📈 NEO4J STORAGE SUMMARY:")
            print(f"🏗️  Nodes created: {neo4j_stats['storage']['servers_created']} servers, "
                  f"{neo4j_stats['storage']['tools_created']} tools, "
                  f"{neo4j_stats['storage']['categories_created']} categories")
            print(f"🔗 Relationships created: {neo4j_stats['storage']['relationships_created']}")
            print(f"📊 Total graph size: {neo4j_stats['graph']['servers']} servers, "
                  f"{neo4j_stats['graph']['relationships']} relationships")
            
        except Exception as e:
            print(f"❌ Error storing in Neo4j: {e}")
            print("💡 Make sure Neo4j is running and credentials are correct")
    
    # Print summary
    if not args.quiet:
        scraper.print_summary(results)
    
    print(f"\n🎉 Scraping completed successfully!")
    print(f"📊 {results.successful_scrapes}/{results.total_servers} servers processed")
    
    if args.neo4j:
        print(f"🔗 Data stored in Neo4j knowledge graph at {args.neo4j_uri}")


if __name__ == '__main__':
    main()