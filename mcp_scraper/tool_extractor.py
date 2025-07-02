"""Tool extractor for MCP server tool definitions."""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from github import Github, GithubException

from .models import MCPTool, MCPPrompt, MCPResource, ToolParameter, MCPServer


class ToolExtractor:
    """Extractor for MCP tool, prompt, and resource definitions."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize tool extractor."""
        self.github = Github(github_token) if github_token else Github()
    
    def extract_tools_from_server(self, server: MCPServer) -> MCPServer:
        """Extract tools, prompts, and resources from MCP server."""
        try:
            if server.server_type.value == "reference":
                # For reference servers, parse from local files
                server = self._extract_from_reference_server(server)
            else:
                # For third-party servers, extract from GitHub repository
                server = self._extract_from_github_repo(server)
            
            return server
            
        except Exception as e:
            if not server.error_message:
                server.error_message = f"Error extracting tools: {str(e)}"
            return server
    
    def _extract_from_reference_server(self, server: MCPServer) -> MCPServer:
        """Extract tools from reference server in local repository."""
        # Get the server directory from the cloned repo
        server_name = server.name
        server_path = Path("mcp_servers_repo/src") / server_name
        
        if not server_path.exists():
            server.error_message = f"Reference server directory not found: {server_path}"
            return server
        
        # Look for Python and TypeScript files
        python_files = list(server_path.glob("**/*.py"))
        ts_files = list(server_path.glob("**/*.ts"))
        js_files = list(server_path.glob("**/*.js"))
        
        # Extract from Python files
        for py_file in python_files:
            try:
                tools, prompts, resources = self._parse_python_file(py_file)
                server.tools.extend(tools)
                server.prompts.extend(prompts)
                server.resources.extend(resources)
            except Exception as e:
                print(f"Error parsing Python file {py_file}: {e}")
        
        # Extract from TypeScript/JavaScript files
        for ts_file in ts_files + js_files:
            try:
                tools, prompts, resources = self._parse_typescript_file(ts_file)
                server.tools.extend(tools)
                server.prompts.extend(prompts)
                server.resources.extend(resources)
            except Exception as e:
                print(f"Error parsing TypeScript file {ts_file}: {e}")
        
        return server
    
    def _extract_from_github_repo(self, server: MCPServer) -> MCPServer:
        """Extract tools from GitHub repository."""
        try:
            # Parse GitHub URL
            repo_info = self._parse_github_url(str(server.github_url))
            if not repo_info:
                return server
            
            owner, repo_name, subpath = repo_info
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Get repository contents
            contents = repo.get_contents("")
            if subpath:
                try:
                    contents = repo.get_contents(subpath)
                except GithubException:
                    contents = []
            
            # Process files
            for content in contents:
                if content.type == "file" and content.name.endswith(('.py', '.ts', '.js')):
                    try:
                        file_content = content.decoded_content.decode('utf-8')
                        if content.name.endswith('.py'):
                            tools, prompts, resources = self._parse_python_content(file_content)
                        else:
                            tools, prompts, resources = self._parse_typescript_content(file_content)
                        
                        server.tools.extend(tools)
                        server.prompts.extend(prompts)
                        server.resources.extend(resources)
                        
                    except Exception as e:
                        print(f"Error parsing file {content.name}: {e}")
            
            return server
            
        except Exception as e:
            if not server.error_message:
                server.error_message = f"Error extracting from GitHub: {str(e)}"
            return server
    
    def _parse_github_url(self, url: str) -> Optional[tuple]:
        """Parse GitHub URL to extract owner, repo, and subpath."""
        import re
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            if parsed.netloc != 'github.com':
                return None
            
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return None
            
            owner = path_parts[0]
            repo_name = path_parts[1]
            
            # Handle subpaths
            subpath = None
            if len(path_parts) > 4 and path_parts[2] == 'tree':
                subpath = '/'.join(path_parts[4:])
            
            return owner, repo_name, subpath
            
        except Exception:
            return None
    
    def _parse_python_file(self, file_path: Path) -> tuple:
        """Parse Python file for MCP definitions."""
        try:
            content = file_path.read_text(encoding='utf-8')
            return self._parse_python_content(content)
        except Exception:
            return [], [], []
    
    def _parse_python_content(self, content: str) -> tuple:
        """Parse Python content for MCP definitions."""
        tools = []
        prompts = []
        resources = []
        
        try:
            # Try to parse AST
            tree = ast.parse(content)
            
            # Look for tool decorators and function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for @server.tool decorator
                    tool_info = self._extract_tool_from_function(node, content)
                    if tool_info:
                        tools.append(tool_info)
                    
                    # Check for prompt definitions
                    prompt_info = self._extract_prompt_from_function(node, content)
                    if prompt_info:
                        prompts.append(prompt_info)
        except SyntaxError:
            # If AST parsing fails, use regex patterns
            tools.extend(self._extract_tools_with_regex(content, 'python'))
            prompts.extend(self._extract_prompts_with_regex(content, 'python'))
        
        return tools, prompts, resources
    
    def _parse_typescript_file(self, file_path: Path) -> tuple:
        """Parse TypeScript file for MCP definitions."""
        try:
            content = file_path.read_text(encoding='utf-8')
            return self._parse_typescript_content(content)
        except Exception:
            return [], [], []
    
    def _parse_typescript_content(self, content: str) -> tuple:
        """Parse TypeScript content for MCP definitions."""
        tools = []
        prompts = []
        resources = []
        
        # Use regex patterns to extract MCP definitions
        tools.extend(self._extract_tools_with_regex(content, 'typescript'))
        prompts.extend(self._extract_prompts_with_regex(content, 'typescript'))
        resources.extend(self._extract_resources_with_regex(content, 'typescript'))
        
        return tools, prompts, resources
    
    def _extract_tool_from_function(self, node: ast.FunctionDef, content: str) -> Optional[MCPTool]:
        """Extract tool information from Python function node."""
        # Check for @server.tool decorator
        for decorator in node.decorator_list:
            if (isinstance(decorator, ast.Attribute) and 
                isinstance(decorator.value, ast.Name) and
                decorator.value.id == 'server' and
                decorator.attr == 'tool'):
                
                # Extract function name and docstring
                name = node.name
                description = ast.get_docstring(node)
                
                # Extract parameters
                parameters = []
                for arg in node.args.args:
                    if arg.arg != 'self':
                        param = ToolParameter(
                            name=arg.arg,
                            type="string",  # Default type
                            required=True
                        )
                        parameters.append(param)
                
                return MCPTool(
                    name=name,
                    description=description,
                    parameters=parameters
                )
        
        return None
    
    def _extract_prompt_from_function(self, node: ast.FunctionDef, content: str) -> Optional[MCPPrompt]:
        """Extract prompt information from Python function node."""
        # Check for @server.prompt decorator
        for decorator in node.decorator_list:
            if (isinstance(decorator, ast.Attribute) and 
                isinstance(decorator.value, ast.Name) and
                decorator.value.id == 'server' and
                decorator.attr == 'prompt'):
                
                name = node.name
                description = ast.get_docstring(node)
                
                # Extract arguments
                arguments = []
                for arg in node.args.args:
                    if arg.arg != 'self':
                        param = ToolParameter(
                            name=arg.arg,
                            type="string",
                            required=True
                        )
                        arguments.append(param)
                
                return MCPPrompt(
                    name=name,
                    description=description,
                    arguments=arguments
                )
        
        return None
    
    def _extract_tools_with_regex(self, content: str, language: str) -> List[MCPTool]:
        """Extract tools using regex patterns."""
        tools = []
        
        if language == 'python':
            # Look for @server.tool decorated functions
            pattern = r'@server\.tool\s*(?:\([^)]*\))?\s*def\s+(\w+)\s*\([^)]*\):\s*"""([^"]*?)"""'
        else:
            # TypeScript/JavaScript patterns
            pattern = r'server\.tools\.register\s*\(\s*{\s*name:\s*["\']([^"\']+)["\'].*?description:\s*["\']([^"\']+)["\']'
        
        matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            if len(match) >= 2:
                name, description = match[0], match[1]
                tools.append(MCPTool(
                    name=name.strip(),
                    description=description.strip() if description else None
                ))
        
        return tools
    
    def _extract_prompts_with_regex(self, content: str, language: str) -> List[MCPPrompt]:
        """Extract prompts using regex patterns."""
        prompts = []
        
        if language == 'python':
            pattern = r'@server\.prompt\s*(?:\([^)]*\))?\s*def\s+(\w+)\s*\([^)]*\):\s*"""([^"]*?)"""'
        else:
            pattern = r'server\.prompts\.register\s*\(\s*{\s*name:\s*["\']([^"\']+)["\'].*?description:\s*["\']([^"\']+)["\']'
        
        matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            if len(match) >= 2:
                name, description = match[0], match[1]
                prompts.append(MCPPrompt(
                    name=name.strip(),
                    description=description.strip() if description else None
                ))
        
        return prompts
    
    def _extract_resources_with_regex(self, content: str, language: str) -> List[MCPResource]:
        """Extract resources using regex patterns."""
        resources = []
        
        if language == 'typescript':
            pattern = r'server\.resources\.register\s*\(\s*{\s*name:\s*["\']([^"\']+)["\'].*?description:\s*["\']([^"\']+)["\']'
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            
            for match in matches:
                if len(match) >= 2:
                    name, description = match[0], match[1]
                    resources.append(MCPResource(
                        name=name.strip(),
                        description=description.strip() if description else None
                    ))
        
        return resources