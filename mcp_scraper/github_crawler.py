"""GitHub repository crawler for enhanced MCP server metadata."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import requests
from github import Github, GithubException

try:
    import toml
except ImportError:
    import tomllib as toml

from .models import MCPServer, RepositoryStats, PackageInfo, MCPTool, ToolParameter


class GitHubCrawler:
    """Crawler for GitHub repositories to extract enhanced metadata."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize GitHub crawler."""
        self.github = Github(github_token) if github_token else Github()
        self.session = requests.Session()
        
    def enhance_server(self, server: MCPServer) -> MCPServer:
        """Enhance server metadata with GitHub repository data."""
        try:
            repo_info = self._parse_github_url(str(server.github_url))
            if not repo_info:
                server.error_message = "Invalid GitHub URL"
                server.is_accessible = False
                return server
            
            owner, repo_name, subpath = repo_info
            
            # Get repository object
            try:
                repo = self.github.get_repo(f"{owner}/{repo_name}")
            except GithubException as e:
                server.error_message = f"Repository not accessible: {e.data.get('message', str(e))}"
                server.is_accessible = False
                return server
            
            # Extract repository statistics
            server.repository_stats = self._extract_repo_stats(repo)
            
            # Get package information
            server.package_info = self._extract_package_info(repo, subpath)
            
            # Get README content if not already present
            if not server.readme_content:
                server.readme_content = self._get_readme_content(repo, subpath)
            
            # Extract installation instructions and usage examples
            if server.readme_content:
                server.installation_instructions = self._extract_installation_instructions(server.readme_content)
                server.usage_examples = self._extract_usage_examples(server.readme_content)
            
            # Check if repository is archived
            server.is_archived = repo.archived
            
            return server
            
        except Exception as e:
            server.error_message = f"Error enhancing server metadata: {str(e)}"
            server.is_accessible = False
            return server
    
    def _parse_github_url(self, url: str) -> Optional[tuple]:
        """Parse GitHub URL to extract owner, repo, and subpath."""
        try:
            parsed = urlparse(url)
            if parsed.netloc != 'github.com':
                return None
            
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return None
            
            owner = path_parts[0]
            repo_name = path_parts[1]
            
            # Handle subpaths (e.g., /tree/main/src/servername)
            subpath = None
            if len(path_parts) > 4 and path_parts[2] == 'tree':
                # Remove 'tree' and branch name, keep the rest as subpath
                subpath = '/'.join(path_parts[4:])
            
            return owner, repo_name, subpath
            
        except Exception:
            return None
    
    def _extract_repo_stats(self, repo) -> RepositoryStats:
        """Extract repository statistics."""
        return RepositoryStats(
            stars=repo.stargazers_count,
            forks=repo.forks_count,
            watchers=repo.watchers_count,
            open_issues=repo.open_issues_count,
            size_kb=repo.size,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
            pushed_at=repo.pushed_at,
            language=repo.language,
            topics=list(repo.get_topics())
        )
    
    def _extract_package_info(self, repo, subpath: Optional[str]) -> Optional[PackageInfo]:
        """Extract package information from package.json or pyproject.toml."""
        package_info = None
        
        # Try to find package files
        package_files = ['package.json', 'pyproject.toml', 'setup.py']
        
        for filename in package_files:
            try:
                file_path = f"{subpath}/{filename}" if subpath else filename
                file_content = repo.get_contents(file_path)
                
                if filename == 'package.json':
                    package_info = self._parse_package_json(file_content.decoded_content.decode('utf-8'))
                elif filename == 'pyproject.toml':
                    package_info = self._parse_pyproject_toml(file_content.decoded_content.decode('utf-8'))
                
                if package_info:
                    break
                    
            except GithubException:
                continue
        
        return package_info
    
    def _parse_package_json(self, content: str) -> Optional[PackageInfo]:
        """Parse package.json content."""
        try:
            data = json.loads(content)
            
            return PackageInfo(
                name=data.get('name'),
                version=data.get('version'),
                description=data.get('description'),
                author=self._extract_author(data.get('author')),
                license=data.get('license'),
                keywords=data.get('keywords', []),
                dependencies=data.get('dependencies', {}),
                dev_dependencies=data.get('devDependencies', {}),
                scripts=data.get('scripts', {})
            )
        except (json.JSONDecodeError, Exception):
            return None
    
    def _parse_pyproject_toml(self, content: str) -> Optional[PackageInfo]:
        """Parse pyproject.toml content."""
        try:
            data = toml.loads(content)
            project = data.get('project', {})
            
            author = None
            if project.get('authors'):
                author = project['authors'][0].get('name')
            
            return PackageInfo(
                name=project.get('name'),
                version=project.get('version'),
                description=project.get('description'),
                author=author,
                license=self._extract_license(project.get('license')),
                keywords=project.get('keywords', []),
                dependencies=self._extract_dependencies(project.get('dependencies', [])),
                scripts=data.get('project', {}).get('scripts', {})
            )
        except Exception:
            return None
    
    def _extract_author(self, author_data) -> Optional[str]:
        """Extract author string from various formats."""
        if isinstance(author_data, str):
            return author_data
        elif isinstance(author_data, dict):
            return author_data.get('name')
        return None
    
    def _extract_license(self, license_data) -> Optional[str]:
        """Extract license string from various formats."""
        if isinstance(license_data, str):
            return license_data
        elif isinstance(license_data, dict):
            return license_data.get('text')
        return None
    
    def _extract_dependencies(self, deps_list: List[str]) -> Dict[str, str]:
        """Extract dependencies from list format to dict."""
        deps = {}
        for dep in deps_list:
            if isinstance(dep, str):
                # Simple dependency string
                if '>=' in dep or '==' in dep or '~=' in dep:
                    parts = re.split(r'[><=~!]+', dep, 1)
                    if len(parts) == 2:
                        deps[parts[0].strip()] = dep.split(parts[0])[-1].strip()
                    else:
                        deps[dep] = "*"
                else:
                    deps[dep] = "*"
        return deps
    
    def _get_readme_content(self, repo, subpath: Optional[str]) -> Optional[str]:
        """Get README content from repository."""
        readme_files = ['README.md', 'readme.md', 'README.rst', 'README.txt']
        
        for filename in readme_files:
            try:
                file_path = f"{subpath}/{filename}" if subpath else filename
                file_content = repo.get_contents(file_path)
                return file_content.decoded_content.decode('utf-8')
            except GithubException:
                continue
        
        return None
    
    def _extract_installation_instructions(self, readme_content: str) -> Optional[str]:
        """Extract installation instructions from README content."""
        # Look for installation section
        lines = readme_content.split('\n')
        installation_section = []
        in_installation = False
        
        for line in lines:
            if re.search(r'##?\s*(install|setup|getting started)', line, re.IGNORECASE):
                in_installation = True
                installation_section.append(line)
            elif in_installation and line.startswith('#'):
                break
            elif in_installation:
                installation_section.append(line)
        
        return '\n'.join(installation_section).strip() if installation_section else None
    
    def _extract_usage_examples(self, readme_content: str) -> Optional[str]:
        """Extract usage examples from README content."""
        # Look for usage/example sections
        lines = readme_content.split('\n')
        usage_section = []
        in_usage = False
        
        for line in lines:
            if re.search(r'##?\s*(usage|example|how to use)', line, re.IGNORECASE):
                in_usage = True
                usage_section.append(line)
            elif in_usage and line.startswith('#'):
                break
            elif in_usage:
                usage_section.append(line)
        
        return '\n'.join(usage_section).strip() if usage_section else None