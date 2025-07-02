"""Parser for the MCP server registry README.md file."""

import re
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.parse import urlparse

from .models import MCPServer, ServerType


class RegistryParser:
    """Parser for the MCP server registry README.md file."""
    
    def __init__(self, repo_path: str):
        """Initialize parser with repository path."""
        self.repo_path = Path(repo_path)
        self.readme_path = self.repo_path / "README.md"
    
    def parse_registry(self) -> List[MCPServer]:
        """Parse the registry README.md and extract server information."""
        if not self.readme_path.exists():
            raise FileNotFoundError(f"README.md not found at {self.readme_path}")
        
        content = self.readme_path.read_text(encoding='utf-8')
        servers = []
        
        # Parse reference servers
        reference_servers = self._parse_reference_servers()
        servers.extend(reference_servers)
        
        # Parse third-party servers from README
        third_party_servers = self._parse_third_party_servers(content)
        servers.extend(third_party_servers)
        
        return servers
    
    def _parse_reference_servers(self) -> List[MCPServer]:
        """Parse reference servers from the src/ directory."""
        servers = []
        src_path = self.repo_path / "src"
        
        if not src_path.exists():
            return servers
        
        for server_dir in src_path.iterdir():
            if server_dir.is_dir() and not server_dir.name.startswith('.'):
                try:
                    server = self._parse_reference_server(server_dir)
                    if server:
                        servers.append(server)
                except Exception as e:
                    print(f"Error parsing reference server {server_dir.name}: {e}")
        
        return servers
    
    def _parse_reference_server(self, server_dir: Path) -> Optional[MCPServer]:
        """Parse a single reference server directory."""
        # Read README.md for description
        readme_path = server_dir / "README.md"
        description = None
        readme_content = None
        
        if readme_path.exists():
            readme_content = readme_path.read_text(encoding='utf-8')
            # Extract description from first paragraph after title
            lines = readme_content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith('#') and not line.startswith('!'):
                    description = line.strip()
                    break
        
        # Construct GitHub URL
        github_url = f"https://github.com/modelcontextprotocol/servers/tree/main/src/{server_dir.name}"
        
        return MCPServer(
            name=server_dir.name,
            github_url=github_url,
            description=description,
            server_type=ServerType.REFERENCE,
            readme_content=readme_content
        )
    
    def _parse_third_party_servers(self, content: str) -> List[MCPServer]:
        """Parse third-party servers from README.md content."""
        servers = []
        
        # Look for the community servers section
        community_section = self._extract_community_section(content)
        if not community_section:
            return servers
        
        # Parse server entries using regex
        # Pattern: - <img ...> **[Server Name](github-url)** - Description
        # Also handle entries without img tags: - **[Server Name](github-url)** - Description
        
        # First try pattern with img tag
        pattern_with_img = r'- <img[^>]*src="([^"]+)"[^>]*>\s*\*\*\[([^\]]+)\]\(([^)]+)\)\*\*\s*[-–]\s*([^\n]+)'
        matches_with_img = re.findall(pattern_with_img, community_section, re.MULTILINE)
        
        # Then try pattern without img tag
        pattern_without_img = r'- \*\*\[([^\]]+)\]\(([^)]+)\)\*\*\s*[-–]\s*([^\n]+)'
        matches_without_img = re.findall(pattern_without_img, community_section, re.MULTILINE)
        
        # Process matches with img tags
        for match in matches_with_img:
            favicon_url, name, github_url, description = match
            try:
                server = MCPServer(
                    name=name.strip(),
                    github_url=github_url.strip(),
                    description=description.strip(),
                    favicon_url=favicon_url,
                    server_type=ServerType.THIRD_PARTY
                )
                servers.append(server)
            except Exception as e:
                print(f"Error parsing third-party server {name}: {e}")
        
        # Process matches without img tags
        for match in matches_without_img:
            name, github_url, description = match
            try:
                server = MCPServer(
                    name=name.strip(),
                    github_url=github_url.strip(),
                    description=description.strip(),
                    favicon_url=None,
                    server_type=ServerType.THIRD_PARTY
                )
                servers.append(server)
            except Exception as e:
                print(f"Error parsing third-party server {name}: {e}")
        
        return servers
    
    def _extract_community_section(self, content: str) -> Optional[str]:
        """Extract the community servers section from README content."""
        # Look for section starting with "Community servers" or "Third-Party Servers"
        lines = content.split('\n')
        start_idx = None
        end_idx = None
        
        for i, line in enumerate(lines):
            if ('third-party servers' in line.lower() or 
                'community servers' in line.lower() or
                '🤝 Third-Party Servers' in line):
                start_idx = i
            elif start_idx is not None and line.startswith('#') and i > start_idx + 5:
                # Only end if we're well past the start and hit another major section
                end_idx = i
                break
        
        if start_idx is None:
            return None
        
        if end_idx is None:
            end_idx = len(lines)
        
        section = '\n'.join(lines[start_idx:end_idx])
        return section
    
    def get_reference_server_paths(self) -> List[Path]:
        """Get paths to all reference server directories."""
        src_path = self.repo_path / "src"
        if not src_path.exists():
            return []
        
        return [d for d in src_path.iterdir() if d.is_dir() and not d.name.startswith('.')]