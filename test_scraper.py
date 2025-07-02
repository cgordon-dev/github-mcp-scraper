#!/usr/bin/env python3
"""Test script for the MCP registry scraper."""

import os
import sys
from pathlib import Path

# Add the mcp_scraper module to the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_scraper.scraper import MCPRegistryScraper


def test_scraper():
    """Test the scraper with a limited number of servers."""
    print("🧪 Testing MCP Registry Scraper")
    print("=" * 50)
    
    # Initialize scraper
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("⚠️  No GitHub token found. Using anonymous access (rate limited).")
    
    try:
        scraper = MCPRegistryScraper(
            github_token=github_token,
            repo_path="mcp_servers_repo"
        )
        
        print("✅ Scraper initialized successfully")
        
        # Test with just 5 servers to start
        print("\n🚀 Starting test scrape (max 5 servers)...")
        results = scraper.scrape_all(
            enhance_metadata=True,
            extract_tools=True,
            max_servers=5
        )
        
        print("\n📊 Test Results:")
        print(f"  Total servers processed: {results.total_servers}")
        print(f"  Successful: {results.successful_scrapes}")
        print(f"  Failed: {results.failed_scrapes}")
        print(f"  Reference servers: {results.reference_servers}")
        print(f"  Third-party servers: {results.third_party_servers}")
        
        # Export test results
        scraper.export_to_json(results, "test_results.json")
        scraper.export_to_csv(results, "test_results.csv")
        
        # Show sample data
        if results.servers:
            print(f"\n📋 Sample Server Data:")
            server = results.servers[0]
            print(f"  Name: {server.name}")
            print(f"  URL: {server.github_url}")
            print(f"  Type: {server.server_type.value}")
            print(f"  Tools: {len(server.tools)}")
            print(f"  Accessible: {server.is_accessible}")
            
            if server.repository_stats:
                print(f"  Stars: {server.repository_stats.stars}")
                print(f"  Language: {server.repository_stats.language}")
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_scraper()
    sys.exit(0 if success else 1)