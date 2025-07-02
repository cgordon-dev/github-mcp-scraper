"""Enhanced tool extractor for MCP server tool definitions."""

import ast
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from github import Github, GithubException, RateLimitExceededException

from .models import MCPTool, MCPPrompt, MCPResource, ToolParameter, MCPServer


class EnhancedToolExtractor:
    """Enhanced extractor for MCP tool, prompt, and resource definitions."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize tool extractor."""
        self.github = Github(github_token) if github_token else Github()
        self.rate_limit_delay = 1.0  # Delay between API calls
        self.max_retries = 3
        self.extraction_stats = {
            'total_files_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'rate_limit_hits': 0
        }
    
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
        
        # Look for TypeScript and JavaScript files (all reference servers are TS-based)
        ts_files = list(server_path.glob("**/*.ts"))
        js_files = list(server_path.glob("**/*.js"))
        
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
        """Extract tools from GitHub repository with recursive search."""
        try:
            # Parse GitHub URL
            repo_info = self._parse_github_url(str(server.github_url))
            if not repo_info:
                return server
            
            owner, repo_name, subpath = repo_info
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Recursive search through repository
            all_files = self._get_all_files_recursive(repo, subpath)
            
            extraction_log = []
            files_processed = 0
            
            # Process files with enhanced language support
            for file_info in all_files:
                if self._is_relevant_file(file_info['name']):
                    try:
                        file_content = file_info['content']
                        file_extension = Path(file_info['name']).suffix
                        
                        tools, prompts, resources = [], [], []
                        
                        if file_extension == '.py':
                            tools, prompts, resources = self._parse_python_content(file_content)
                        elif file_extension in ['.js', '.ts']:
                            tools, prompts, resources = self._parse_typescript_content(file_content)
                        elif file_extension == '.go':
                            tools, prompts, resources = self._parse_go_content(file_content)
                        elif file_extension == '.rs':
                            tools, prompts, resources = self._parse_rust_content(file_content)
                        elif file_extension in ['.cs', '.csx']:
                            tools, prompts, resources = self._parse_csharp_content(file_content)
                        elif file_extension == '.java':
                            tools, prompts, resources = self._parse_java_content(file_content)
                        
                        if tools or prompts or resources:
                            extraction_log.append(f"Extracted from {file_info['path']}: {len(tools)} tools, {len(prompts)} prompts, {len(resources)} resources")
                        
                        server.tools.extend(tools)
                        server.prompts.extend(prompts)
                        server.resources.extend(resources)
                        files_processed += 1
                        
                    except Exception as e:
                        extraction_log.append(f"Error parsing {file_info['path']}: {str(e)}")
            
            # Add extraction summary to server metadata
            if extraction_log:
                server.extraction_log = extraction_log
            
            # Calculate extraction confidence score
            confidence_score = self._calculate_extraction_confidence(server, files_processed)
            extraction_log.append(f"Extraction confidence score: {confidence_score:.2f}/1.0")
            
            # If no tools found, try README parsing as fallback
            if not server.tools and not server.prompts and not server.resources:
                server = self._extract_from_readme_fallback(server, repo, subpath)
            
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
    
    def _parse_typescript_file(self, file_path: Path) -> tuple:
        """Parse TypeScript file for MCP definitions."""
        try:
            content = file_path.read_text(encoding='utf-8')
            return self._parse_typescript_content(content)
        except Exception:
            return [], [], []
    
    def _parse_typescript_content(self, content: str) -> tuple:
        """Parse TypeScript content for MCP definitions using actual SDK patterns."""
        tools = []
        prompts = []
        resources = []
        
        # Extract MCP definitions using the actual patterns found in reference servers
        tools.extend(self._extract_mcp_tools(content))
        prompts.extend(self._extract_mcp_prompts(content))
        resources.extend(self._extract_mcp_resources(content))
        
        return tools, prompts, resources
    
    def _parse_python_content(self, content: str) -> tuple:
        """Parse Python content for MCP definitions."""
        tools = []
        prompts = []
        resources = []
        
        # Pattern 1: FastMCP framework @mcp.tool() decorator
        fastmcp_pattern = r'@mcp\.tool\(\)\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\):\s*(?:\n\s*"""([^"]*?)""")?'
        fastmcp_matches = re.findall(fastmcp_pattern, content, re.DOTALL)
        
        for name, description in fastmcp_matches:
            tools.append(MCPTool(
                name=name,
                description=description.strip() if description else None,
                parameters=[]
            ))
        
        # Pattern 2: @server.tool decorator (original pattern)
        server_tool_pattern = r'@server\.tool\s*(?:\([^)]*\))?\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\):\s*(?:\n\s*"""([^"]*?)""")?'
        server_tool_matches = re.findall(server_tool_pattern, content, re.DOTALL)
        
        for name, description in server_tool_matches:
            tools.append(MCPTool(
                name=name,
                description=description.strip() if description else None,
                parameters=[]
            ))
        
        # Pattern 3: @tool decorator (simple pattern)
        tool_pattern = r'@tool\s*(?:\([^)]*\))?\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\):\s*(?:\n\s*"""([^"]*?)""")?'
        tool_matches = re.findall(tool_pattern, content, re.DOTALL)
        
        for name, description in tool_matches:
            tools.append(MCPTool(
                name=name,
                description=description.strip() if description else None,
                parameters=[]
            ))
        
        # Pattern 4: server.add_tool() calls
        add_tool_pattern = r'server\.add_tool\s*\(\s*["\']([^"\']+)["\']'
        add_tool_matches = re.findall(add_tool_pattern, content)
        
        for name in add_tool_matches:
            tools.append(MCPTool(
                name=name,
                description=None,
                parameters=[]
            ))
        
        return tools, prompts, resources
    
    def _parse_go_content(self, content: str) -> tuple:
        """Parse Go content for MCP definitions."""
        tools = []
        prompts = []
        resources = []
        
        # Pattern 1: Tool constant definitions + AddTool registration
        const_pattern = r'const\s+(\w+Tool)\s*=\s*["\']([^"\']+)["\']'
        const_matches = re.findall(const_pattern, content)
        
        # Look for corresponding AddTool calls
        for const_name, tool_name in const_matches:
            add_tool_pattern = rf's\.AddTool\s*\(\s*\w*\.?{re.escape(const_name)}'
            if re.search(add_tool_pattern, content):
                tools.append(MCPTool(
                    name=tool_name,
                    description=None,
                    parameters=[]
                ))
        
        # Pattern 2: Direct AddTool calls with string literals
        direct_add_pattern = r's\.AddTool\s*\(\s*["\']([^"\']+)["\']'
        direct_matches = re.findall(direct_add_pattern, content)
        
        for tool_name in direct_matches:
            tools.append(MCPTool(
                name=tool_name,
                description=None,
                parameters=[]
            ))
        
        # Pattern 3: Tool struct definitions (if any)
        struct_pattern = r'type\s+\w*Tool\w*\s+struct\s*{[^}]*Name\s*:\s*["\']([^"\']+)["\'][^}]*}'
        struct_matches = re.findall(struct_pattern, content, re.DOTALL)
        
        for tool_name in struct_matches:
            tools.append(MCPTool(
                name=tool_name,
                description=None,
                parameters=[]
            ))
        
        return tools, prompts, resources
    
    def _extract_mcp_tools(self, content: str) -> List[MCPTool]:
        """Extract MCP tools from TypeScript content using actual SDK patterns."""
        tools = []
        
        # Pattern 1: Look for ListToolsRequestSchema handler with const tools: Tool[] = [...] and return { tools }
        # This pattern is used in everything.ts
        const_tools_pattern = r'server\.setRequestHandler\(ListToolsRequestSchema.*?const\s+tools:\s*Tool\[\]\s*=\s*\[(.*?)\].*?return\s*{\s*tools\s*}'
        const_match = re.search(const_tools_pattern, content, re.DOTALL)
        
        if const_match:
            tools_array = const_match.group(1)
            
            # Extract individual tool objects with enum names
            tool_pattern = r'{\s*name:\s*([^,\s]+)[^{}]*description:\s*["\']([^"\']*)["\']'
            tool_matches = re.findall(tool_pattern, tools_array, re.DOTALL)
            
            for name_expr, description in tool_matches:
                # Extract the actual tool name (could be ToolName.ECHO or "echo")
                tool_name = self._extract_name_value(content, name_expr)
                
                if tool_name:
                    # Extract parameters from inputSchema if present
                    parameters = self._extract_tool_parameters(tools_array, name_expr)
                    
                    tools.append(MCPTool(
                        name=tool_name,
                        description=description.strip() if description else None,
                        parameters=parameters
                    ))
        
        # Pattern 2: Look for tools defined directly in the return statement (like memory/filesystem servers)
        # Use a more flexible approach that finds individual tool objects within tools arrays
        tools_in_handler_pattern = r'server\.setRequestHandler\(ListToolsRequestSchema.*?return\s*{.*?tools:\s*\['
        handler_match = re.search(tools_in_handler_pattern, content, re.DOTALL)
        
        if handler_match:
            # Find all tool objects within the handler function
            handler_start = handler_match.end()
            # Find the matching closing bracket for the tools array
            bracket_count = 1
            i = handler_start
            while i < len(content) and bracket_count > 0:
                if content[i] == '[':
                    bracket_count += 1
                elif content[i] == ']':
                    bracket_count -= 1
                i += 1
            
            if bracket_count == 0:
                tools_section = content[handler_start:i-1]
                
                # Extract individual tool objects with improved pattern
                tool_obj_pattern = r'{\s*name:\s*["\']([^"\']+)["\'].*?description:\s*([^}]+?)(?=\s*,\s*inputSchema|\s*})'
                tool_defs = re.findall(tool_obj_pattern, tools_section, re.DOTALL)
                
                for match in tool_defs:
                    name = match[0]
                    # Clean up the description - handle string concatenation and quotes
                    description = match[1]
                    if description:
                        # Remove string concatenation operators and normalize
                        description = re.sub(r'\s*\+\s*', ' ', description)
                        description = re.sub(r'["\']', '', description)
                        description = ' '.join(description.split())  # Normalize whitespace
                    
                    # Extract parameters from inputSchema
                    parameters = self._extract_input_schema_parameters(tools_section, name)
                    
                    tools.append(MCPTool(
                        name=name.strip(),
                        description=description.strip() if description else None,
                        parameters=parameters
                    ))
        
        # Pattern 3: Look for tools defined as constants (like sequentialthinking server)
        # This pattern handles `tools: [TOOL_CONSTANT]` in arrow function returns
        const_ref_pattern = r'async\s*\(\s*\)\s*=>\s*\(\s*{\s*tools:\s*\[([A-Z_]+)\]'
        const_ref_match = re.search(const_ref_pattern, content, re.DOTALL)
        
        if const_ref_match:
            const_name = const_ref_match.group(1)
            # Look for the constant definition
            const_def_pattern = rf'const\s+{const_name}:\s*Tool\s*=\s*{{\s*name:\s*["\']([^"\']+)["\'].*?description:\s*`([^`]*)`'
            const_def_match = re.search(const_def_pattern, content, re.DOTALL)
            
            if const_def_match:
                name = const_def_match.group(1)
                description = const_def_match.group(2).strip()
                
                tools.append(MCPTool(
                    name=name.strip(),
                    description=description if description else None,
                    parameters=[]  # Could extract from inputSchema if needed
                ))
        
        # Pattern 4: Look for TOOLS constant arrays (common third-party pattern)
        tools_array_pattern = r'const\s+TOOLS\s*:\s*Tool\[\]\s*=\s*\[(.*?)\]'
        tools_array_match = re.search(tools_array_pattern, content, re.DOTALL)
        
        if tools_array_match:
            tools_content = tools_array_match.group(1)
            
            # Extract tool definitions from the array
            tool_obj_pattern = r'{\s*name:\s*["\']([^"\']+)["\'].*?description:\s*["\']([^"\']*)["\']'
            tool_objs = re.findall(tool_obj_pattern, tools_content, re.DOTALL)
            
            for name, description in tool_objs:
                tools.append(MCPTool(
                    name=name.strip(),
                    description=description.strip() if description else None,
                    parameters=[]
                ))
        
        # Pattern 5: Look for direct tool object exports
        export_tools_pattern = r'export\s+const\s+(\w+)\s*=\s*{\s*name:\s*["\']([^"\']+)["\'].*?description:\s*["\']([^"\']*)["\']'
        export_matches = re.findall(export_tools_pattern, content, re.DOTALL)
        
        for const_name, tool_name, description in export_matches:
            tools.append(MCPTool(
                name=tool_name.strip(),
                description=description.strip() if description else None,
                parameters=[]
            ))
        
        return tools
    
    def _extract_mcp_prompts(self, content: str) -> List[MCPPrompt]:
        """Extract MCP prompts from TypeScript content."""
        prompts = []
        
        # Look for ListPromptsRequestSchema handler with prompts array
        prompts_pattern = r'server\.setRequestHandler\(ListPromptsRequestSchema.*?prompts:\s*\[(.*?)\]'
        prompts_match = re.search(prompts_pattern, content, re.DOTALL)
        
        if prompts_match:
            prompts_array = prompts_match.group(1)
            
            # Extract individual prompt objects - handle multi-line and enum names
            prompt_pattern = r'{\s*name:\s*([^,\s]+)[^{}]*?description:\s*["\']([^"\']*?)["\']'
            prompt_matches = re.findall(prompt_pattern, prompts_array, re.DOTALL)
            
            for name_expr, description in prompt_matches:
                # Extract the actual prompt name
                prompt_name = self._extract_name_value(content, name_expr)
                
                if prompt_name:
                    # Extract arguments if present
                    arguments = self._extract_prompt_arguments(prompts_array, name_expr)
                    
                    prompts.append(MCPPrompt(
                        name=prompt_name,
                        description=description.strip() if description else None,
                        arguments=arguments
                    ))
        
        return prompts
    
    def _extract_mcp_resources(self, content: str) -> List[MCPResource]:
        """Extract MCP resources from TypeScript content."""
        resources = []
        
        # Look for ALL_RESOURCES definition with Array.from pattern
        resources_pattern = r'const\s+ALL_RESOURCES.*?Array\.from\(\{\s*length:\s*(\d+)'
        resources_match = re.search(resources_pattern, content)
        
        if resources_match:
            count = int(resources_match.group(1))
            # Create resource entries based on the pattern found in everything.ts
            for i in range(count):
                resources.append(MCPResource(
                    name=f"Resource {i + 1}",
                    description=f"Test resource {i + 1}",
                    uri=f"test://static/resource/{i + 1}",
                    mime_type="text/plain" if i % 2 == 0 else "application/octet-stream"
                ))
        
        # Look for resource templates
        template_pattern = r'resourceTemplates:\s*\[(.*?)\]'
        template_match = re.search(template_pattern, content, re.DOTALL)
        
        if template_match:
            templates_content = template_match.group(1)
            uri_pattern = r'uriTemplate:\s*["\']([^"\']+)["\']'
            name_pattern = r'name:\s*["\']([^"\']+)["\']'
            desc_pattern = r'description:\s*["\']([^"\']*)["\']'
            
            uri_match = re.search(uri_pattern, templates_content)
            name_match = re.search(name_pattern, templates_content)
            desc_match = re.search(desc_pattern, templates_content)
            
            if uri_match and name_match:
                resources.append(MCPResource(
                    name=name_match.group(1),
                    description=desc_match.group(1) if desc_match else None,
                    uri=uri_match.group(1)
                ))
        
        return resources
    
    def _extract_name_value(self, content: str, name_expr: str) -> Optional[str]:
        """Extract the actual value from an enum expression like ToolName.ECHO or direct string."""
        name_expr = name_expr.strip()
        
        # If it's a direct string, return it
        if name_expr.startswith('"') or name_expr.startswith("'"):
            return name_expr.strip('"\'')
        
        # Handle enum expressions like ToolName.ECHO
        if '.' in name_expr:
            enum_name, value_name = name_expr.split('.', 1)
            
            # Look for enum definition
            enum_pattern = rf'enum\s+{enum_name}\s*{{([^}}]+)}}'
            enum_match = re.search(enum_pattern, content, re.DOTALL)
            
            if enum_match:
                enum_content = enum_match.group(1)
                # Look for the specific value
                value_pattern = rf'{value_name}\s*=\s*["\']([^"\']+)["\']'
                value_match = re.search(value_pattern, enum_content)
                
                if value_match:
                    return value_match.group(1)
            
            # Fallback: convert UPPER_CASE to lowercase
            return value_name.lower()
        
        return name_expr
    
    def _extract_tool_parameters(self, tools_content: str, name_expr: str) -> List[ToolParameter]:
        """Extract parameters from tool inputSchema."""
        parameters = []
        
        # Find the specific tool object
        tool_obj_pattern = rf'{{[^{{}}]*name:\s*{re.escape(name_expr)}[^{{}}]*}}'
        tool_match = re.search(tool_obj_pattern, tools_content, re.DOTALL)
        
        if tool_match:
            tool_obj = tool_match.group(0)
            
            # Look for inputSchema
            schema_pattern = r'inputSchema:\s*([^,}}]+)'
            schema_match = re.search(schema_pattern, tool_obj, re.DOTALL)
            
            if schema_match:
                # This is complex - for now, just indicate that parameters exist
                parameters.append(ToolParameter(
                    name="input",
                    type="object",
                    description="Tool input parameters",
                    required=True
                ))
        
        return parameters
    
    def _extract_input_schema_parameters(self, tools_content: str, tool_name: str) -> List[ToolParameter]:
        """Extract parameters from inputSchema properties."""
        parameters = []
        
        # Find the tool with the given name
        tool_pattern = rf'{{[^{{}}]*name:\s*["\']?{re.escape(tool_name)}["\']?[^{{}}]*}}'
        tool_match = re.search(tool_pattern, tools_content, re.DOTALL)
        
        if tool_match:
            tool_content = tool_match.group(0)
            
            # Look for properties in inputSchema
            properties_pattern = r'properties:\s*{([^{}]+)}'
            properties_match = re.search(properties_pattern, tool_content, re.DOTALL)
            
            if properties_match:
                properties_content = properties_match.group(1)
                
                # Extract parameter definitions
                param_pattern = r'(\w+):\s*{[^{}]*type:\s*["\']([^"\']+)["\'][^{}]*}'
                param_matches = re.findall(param_pattern, properties_content)
                
                for param_name, param_type in param_matches:
                    parameters.append(ToolParameter(
                        name=param_name,
                        type=param_type,
                        required=True  # Simplified
                    ))
        
        return parameters
    
    def _extract_prompt_arguments(self, prompts_content: str, name_expr: str) -> List[ToolParameter]:
        """Extract arguments from a prompt definition."""
        arguments = []
        
        # Find the specific prompt object
        prompt_obj_pattern = rf'{{[^{{}}]*name:\s*{re.escape(name_expr)}[^{{}}]*}}'
        prompt_match = re.search(prompt_obj_pattern, prompts_content, re.DOTALL)
        
        if prompt_match:
            prompt_obj = prompt_match.group(0)
            
            # Look for arguments array
            args_pattern = r'arguments:\s*\[(.*?)\]'
            args_match = re.search(args_pattern, prompt_obj, re.DOTALL)
            
            if args_match:
                args_content = args_match.group(1)
                
                # Extract individual argument objects
                arg_pattern = r'{{[^{{}}]*name:\s*["\']([^"\']+)["\'][^{{}}]*description:\s*["\']([^"\']*)["\'][^{{}}]*required:\s*(true|false)'
                arg_matches = re.findall(arg_pattern, args_content, re.DOTALL)
                
                for name, description, required in arg_matches:
                    arguments.append(ToolParameter(
                        name=name,
                        type="string",  # Default type
                        description=description if description else None,
                        required=required.lower() == 'true'
                    ))
        
        return arguments
    
    def _get_all_files_recursive(self, repo, base_path: Optional[str] = None, max_depth: int = 3) -> List[Dict]:
        """Recursively get all relevant files from repository."""
        files = []
        
        def _traverse_directory(path: str, current_depth: int = 0):
            if current_depth > max_depth:
                return
                
            for retry in range(self.max_retries):
                try:
                    # Rate limiting
                    time.sleep(self.rate_limit_delay)
                    
                    contents = repo.get_contents(path)
                    if not isinstance(contents, list):
                        contents = [contents]
                        
                    for content in contents:
                        if content.type == "file" and self._is_relevant_file(content.name):
                            try:
                                # Additional rate limiting for file content
                                time.sleep(self.rate_limit_delay / 2)
                                file_content = content.decoded_content.decode('utf-8')
                                files.append({
                                    'name': content.name,
                                    'path': content.path,
                                    'content': file_content,
                                    'size': content.size
                                })
                                self.extraction_stats['total_files_processed'] += 1
                            except Exception as e:
                                print(f"Error reading file {content.path}: {e}")
                                self.extraction_stats['failed_extractions'] += 1
                        elif content.type == "dir" and not self._should_skip_directory(content.name):
                            _traverse_directory(content.path, current_depth + 1)
                    
                    break  # Success, exit retry loop
                    
                except RateLimitExceededException:
                    self.extraction_stats['rate_limit_hits'] += 1
                    if retry < self.max_retries - 1:
                        wait_time = (2 ** retry) * 60  # Exponential backoff
                        print(f"Rate limit hit, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"Max retries exceeded for path {path}")
                        break
                except GithubException as e:
                    if retry < self.max_retries - 1:
                        time.sleep(2 ** retry)  # Exponential backoff
                    else:
                        print(f"Error accessing path {path}: {e}")
                        break
        
        start_path = base_path if base_path else ""
        _traverse_directory(start_path)
        
        return files
    
    def _is_relevant_file(self, filename: str) -> bool:
        """Check if file is relevant for MCP extraction."""
        relevant_extensions = {
            '.py', '.ts', '.js', '.go', '.rs', '.cs', '.csx', '.java',
            '.tsx', '.jsx', '.mjs', '.cjs'
        }
        
        # Skip test files, build files, and other irrelevant files
        skip_patterns = {
            'test', 'spec', '__test__', '.test.', '.spec.',
            'build', 'dist', 'node_modules', '.git',
            'webpack', 'babel', 'eslint', 'prettier'
        }
        
        filename_lower = filename.lower()
        
        # Check if file has relevant extension
        if not any(filename_lower.endswith(ext) for ext in relevant_extensions):
            return False
            
        # Skip files matching skip patterns
        if any(pattern in filename_lower for pattern in skip_patterns):
            return False
            
        return True
    
    def _should_skip_directory(self, dirname: str) -> bool:
        """Check if directory should be skipped."""
        skip_dirs = {
            'node_modules', '.git', 'build', 'dist', '__pycache__',
            '.pytest_cache', 'coverage', '.nyc_output', 'target',
            'bin', 'obj', 'vendor', '.vscode', '.idea'
        }
        
        return dirname.lower() in skip_dirs
    
    def _parse_rust_content(self, content: str) -> tuple:
        """Parse Rust content for MCP definitions."""
        tools = []
        prompts = []
        resources = []
        
        # Pattern 1: Tool struct definitions with name field
        struct_pattern = r'#\[derive\([^)]*\)]\s*(?:pub\s+)?struct\s+(\w+)\s*{[^}]*name:\s*String[^}]*}'
        struct_matches = re.findall(struct_pattern, content, re.DOTALL)
        
        for struct_name in struct_matches:
            # Look for implementation or usage
            impl_pattern = rf'impl.*{struct_name}.*{{.*?fn\s+(\w+)'  
            impl_matches = re.findall(impl_pattern, content, re.DOTALL)
            
            for method_name in impl_matches:
                tools.append(MCPTool(
                    name=method_name,
                    description=f"Tool from {struct_name} struct",
                    parameters=[]
                ))
        
        # Pattern 2: Function definitions with mcp attributes
        fn_pattern = r'#\[mcp::(tool|prompt)\]\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)'
        fn_matches = re.findall(fn_pattern, content)
        
        for attr_type, fn_name in fn_matches:
            if attr_type == 'tool':
                tools.append(MCPTool(
                    name=fn_name,
                    description=None,
                    parameters=[]
                ))
            elif attr_type == 'prompt':
                prompts.append(MCPPrompt(
                    name=fn_name,
                    description=None,
                    arguments=[]
                ))
        
        return tools, prompts, resources
    
    def _parse_csharp_content(self, content: str) -> tuple:
        """Parse C# content for MCP definitions."""
        tools = []
        prompts = []
        resources = []
        
        # Pattern 1: Methods with [Tool] attribute
        tool_pattern = r'\[Tool(?:\([^)]*\))?\]\s*(?:public\s+)?(?:async\s+)?(?:Task<?[^>]*>?\s+)?(\w+)\s*\('
        tool_matches = re.findall(tool_pattern, content)
        
        for method_name in tool_matches:
            tools.append(MCPTool(
                name=method_name,
                description=None,
                parameters=[]
            ))
        
        # Pattern 2: Methods with [McpTool] attribute
        mcp_tool_pattern = r'\[McpTool(?:\([^)]*\))?\]\s*(?:public\s+)?(?:async\s+)?(?:Task<?[^>]*>?\s+)?(\w+)\s*\('
        mcp_tool_matches = re.findall(mcp_tool_pattern, content)
        
        for method_name in mcp_tool_matches:
            tools.append(MCPTool(
                name=method_name,
                description=None,
                parameters=[]
            ))
        
        return tools, prompts, resources
    
    def _parse_java_content(self, content: str) -> tuple:
        """Parse Java content for MCP definitions."""
        tools = []
        prompts = []
        resources = []
        
        # Pattern 1: Methods with @Tool annotation
        tool_pattern = r'@Tool(?:\([^)]*\))?\s*(?:public\s+)?(?:static\s+)?[\w<>\[\]]+\s+(\w+)\s*\('
        tool_matches = re.findall(tool_pattern, content)
        
        for method_name in tool_matches:
            tools.append(MCPTool(
                name=method_name,
                description=None,
                parameters=[]
            ))
        
        # Pattern 2: Methods with @McpTool annotation
        mcp_tool_pattern = r'@McpTool(?:\([^)]*\))?\s*(?:public\s+)?(?:static\s+)?[\w<>\[\]]+\s+(\w+)\s*\('
        mcp_tool_matches = re.findall(mcp_tool_pattern, content)
        
        for method_name in mcp_tool_matches:
            tools.append(MCPTool(
                name=method_name,
                description=None,
                parameters=[]
            ))
        
        return tools, prompts, resources
    
    def _extract_from_readme_fallback(self, server: MCPServer, repo, subpath: Optional[str]) -> MCPServer:
        """Extract tool information from README as fallback."""
        try:
            readme_content = self._get_readme_content(repo, subpath)
            if not readme_content:
                return server
                
            # Look for tool descriptions in README
            tools = self._extract_tools_from_markdown(readme_content)
            server.tools.extend(tools)
            
            if tools:
                server.extraction_log = server.extraction_log or []
                server.extraction_log.append(f"Extracted {len(tools)} tools from README fallback")
                
        except Exception as e:
            print(f"Error in README fallback extraction: {e}")
            
        return server
        
    def _get_readme_content(self, repo, subpath: Optional[str]) -> Optional[str]:
        """Get README content from repository."""
        readme_files = ['README.md', 'readme.md', 'README.rst', 'README.txt', 'README']
        
        for filename in readme_files:
            try:
                file_path = f"{subpath}/{filename}" if subpath else filename
                file_content = repo.get_contents(file_path)
                return file_content.decoded_content.decode('utf-8')
            except GithubException:
                continue
        
        return None
    
    def _extract_tools_from_markdown(self, content: str) -> List[MCPTool]:
        """Extract tool information from markdown documentation."""
        tools = []
        
        # Pattern 1: Look for tool lists or sections
        tool_sections = re.findall(r'##?\s*Tools?\s*\n(.*?)(?=\n##|$)', content, re.DOTALL | re.IGNORECASE)
        
        for section in tool_sections:
            # Extract bullet points or numbered lists
            tool_patterns = [
                r'[-*+]\s*`?([\w_]+)`?[:\s-]+([^\n]+)',  # - tool_name: description
                r'\d+\.\s*`?([\w_]+)`?[:\s-]+([^\n]+)',  # 1. tool_name: description
                r'`([\w_]+)`[:\s-]+([^\n]+)',           # `tool_name`: description
            ]
            
            for pattern in tool_patterns:
                matches = re.findall(pattern, section)
                for name, description in matches:
                    if len(name) > 2 and not name.lower() in ['tool', 'tools', 'function', 'method']:
                        tools.append(MCPTool(
                            name=name,
                            description=description.strip(),
                            parameters=[]
                        ))
        
        return tools
    
    def _calculate_extraction_confidence(self, server: MCPServer, files_processed: int) -> float:
        """Calculate confidence score for extraction results."""
        confidence = 0.0
        
        # Base score for finding any tools/prompts/resources
        if server.tools or server.prompts or server.resources:
            confidence += 0.5
        
        # Bonus for multiple tools (indicates well-structured MCP server)
        tool_count = len(server.tools)
        if tool_count > 0:
            confidence += min(0.3, tool_count * 0.1)
        
        # Bonus for having descriptions (indicates documentation quality)
        tools_with_descriptions = sum(1 for tool in server.tools if tool.description)
        if tool_count > 0:
            description_ratio = tools_with_descriptions / tool_count
            confidence += description_ratio * 0.2
        
        # Bonus for processing multiple files (indicates comprehensive search)
        if files_processed > 1:
            confidence += min(0.1, files_processed * 0.02)
        
        # Penalty for extraction errors
        if server.error_message:
            confidence *= 0.7
        
        return min(1.0, confidence)
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return self.extraction_stats.copy()