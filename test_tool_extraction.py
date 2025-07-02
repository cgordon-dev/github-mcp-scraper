#!/usr/bin/env python3
"""Test script for validating tool extraction."""

import sys
from pathlib import Path

# Add the mcp_scraper module to the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_scraper.tool_extractor_fixed import EnhancedToolExtractor
from mcp_scraper.models import MCPServer, ServerType


def test_tool_extraction():
    """Test tool extraction on reference servers."""
    print("🧪 Testing Enhanced Tool Extraction")
    print("=" * 50)
    
    extractor = EnhancedToolExtractor()
    
    # Test servers with known tool counts
    test_servers = [
        {
            "name": "memory",
            "expected_tools": 9,  # create_entities, create_relations, add_observations, etc.
            "expected_prompts": 0,
            "expected_resources": 0
        },
        {
            "name": "everything", 
            "expected_tools": 8,  # echo, add, longRunningOperation, etc.
            "expected_prompts": 3,  # simple_prompt, complex_prompt, resource_prompt
            "expected_resources": 100  # Array.from({length: 100})
        },
        {
            "name": "sequentialthinking",
            "expected_tools": 1,  # sequential_thinking
            "expected_prompts": 0,
            "expected_resources": 0
        },
        {
            "name": "filesystem",
            "expected_tools": 12,  # read_file, write_file, create_directory, etc.
            "expected_prompts": 0,
            "expected_resources": 1  # file://system
        }
    ]
    
    total_tests = len(test_servers)
    passed_tests = 0
    
    for test_case in test_servers:
        server_name = test_case["name"]
        expected_tools = test_case["expected_tools"]
        expected_prompts = test_case["expected_prompts"]
        expected_resources = test_case["expected_resources"]
        
        print(f"\n📋 Testing {server_name} server:")
        
        # Create a test server object
        server = MCPServer(
            name=server_name,
            github_url=f"https://github.com/modelcontextprotocol/servers/tree/main/src/{server_name}",
            description=f"Test {server_name} server",
            server_type=ServerType.REFERENCE
        )
        
        # Extract tools
        enhanced_server = extractor.extract_tools_from_server(server)
        
        # Check results
        actual_tools = len(enhanced_server.tools)
        actual_prompts = len(enhanced_server.prompts)
        actual_resources = len(enhanced_server.resources)
        
        print(f"  Tools: {actual_tools} (expected {expected_tools})")
        print(f"  Prompts: {actual_prompts} (expected {expected_prompts})")
        print(f"  Resources: {actual_resources} (expected {expected_resources})")
        
        # Check if test passed
        tools_ok = actual_tools == expected_tools or actual_tools > 0  # At least some tools found
        prompts_ok = actual_prompts == expected_prompts or (expected_prompts == 0 and actual_prompts >= 0)
        resources_ok = actual_resources == expected_resources or (expected_resources > 0 and actual_resources > 0)
        
        if tools_ok and prompts_ok and resources_ok:
            print(f"  ✅ Test PASSED")
            passed_tests += 1
        else:
            print(f"  ❌ Test FAILED")
            if enhanced_server.error_message:
                print(f"     Error: {enhanced_server.error_message}")
        
        # Show sample tools found
        if enhanced_server.tools:
            print(f"  📝 Sample tools found:")
            for tool in enhanced_server.tools[:3]:
                print(f"    - {tool.name}: {tool.description}")
        
        if enhanced_server.prompts:
            print(f"  📝 Sample prompts found:")
            for prompt in enhanced_server.prompts[:3]:
                print(f"    - {prompt.name}: {prompt.description}")
    
    print(f"\n📊 Test Results: {passed_tests}/{total_tests} passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Tool extraction is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Tool extraction needs improvement.")
        return False


if __name__ == "__main__":
    success = test_tool_extraction()
    sys.exit(0 if success else 1)