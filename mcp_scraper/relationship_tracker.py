"""Advanced relationship tracking and metadata management for the MCP knowledge graph."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from .enhanced_models import (
    EnhancedMCPServer, MCPTool, Repository, Package,
    SimilarityRelationship, MaintenanceRelationship, 
    ContributionRelationship, CompatibilityRelationship
)


class RelationshipType(str, Enum):
    """Types of relationships in the knowledge graph."""
    # Core relationships
    PROVIDES_TOOL = "PROVIDES_TOOL"
    PROVIDES_PROMPT = "PROVIDES_PROMPT"
    PROVIDES_RESOURCE = "PROVIDES_RESOURCE"
    HOSTED_IN = "HOSTED_IN"
    PACKAGED_AS = "PACKAGED_AS"
    
    # Classification relationships
    BELONGS_TO_CATEGORY = "BELONGS_TO_CATEGORY"
    OPERATES_IN_DOMAIN = "OPERATES_IN_DOMAIN"
    IMPLEMENTED_IN = "IMPLEMENTED_IN"
    USES_FRAMEWORK = "USES_FRAMEWORK"
    LICENSED_UNDER = "LICENSED_UNDER"
    
    # Ecosystem relationships
    MAINTAINS = "MAINTAINS"
    CONTRIBUTES_TO = "CONTRIBUTES_TO"
    HAS_VERSION = "HAS_VERSION"
    DEPENDS_ON = "DEPENDS_ON"
    
    # Network relationships
    SIMILAR_TO = "SIMILAR_TO"
    COMPATIBLE_WITH = "COMPATIBLE_WITH"
    INTEGRATES_WITH = "INTEGRATES_WITH"
    RECOMMENDED_WITH = "RECOMMENDED_WITH"
    
    # Quality relationships
    HAS_QUALITY_METRIC = "HAS_QUALITY_METRIC"
    HAS_USAGE_PATTERN = "HAS_USAGE_PATTERN"
    HAS_TECHNICAL_DEBT = "HAS_TECHNICAL_DEBT"
    
    # Hierarchical relationships
    SUBCATEGORY_OF = "SUBCATEGORY_OF"
    MEMBER_OF = "MEMBER_OF"
    SUCCEEDS = "SUCCEEDS"
    EXTENDS = "EXTENDS"


@dataclass
class RelationshipMetadata:
    """Metadata for graph relationships."""
    relationship_type: RelationshipType
    source_node_id: str
    target_node_id: str
    properties: Dict[str, Any]
    created_at: datetime
    created_by: str = "mcp_scraper"
    confidence: float = 1.0
    source: str = "automatic"
    validation_status: str = "unvalidated"
    last_updated: Optional[datetime] = None


class RelationshipTracker:
    """Advanced relationship tracking and metadata management."""
    
    def __init__(self):
        self.relationships: List[RelationshipMetadata] = []
        self.similarity_cache: Dict[str, List[SimilarityRelationship]] = {}
        self.category_hierarchies: Dict[str, List[str]] = {}
        self.tool_compatibility_matrix: Dict[Tuple[str, str], float] = {}
        
    def track_server_relationships(self, server: EnhancedMCPServer) -> List[RelationshipMetadata]:
        """Track all relationships for a given server."""
        relationships = []
        
        # Core capability relationships
        relationships.extend(self._track_capability_relationships(server))
        
        # Infrastructure relationships
        relationships.extend(self._track_infrastructure_relationships(server))
        
        # Classification relationships
        relationships.extend(self._track_classification_relationships(server))
        
        # Quality relationships
        relationships.extend(self._track_quality_relationships(server))
        
        # Store relationships
        self.relationships.extend(relationships)
        
        return relationships
    
    def _track_capability_relationships(self, server: EnhancedMCPServer) -> List[RelationshipMetadata]:
        """Track tool, prompt, and resource relationships."""
        relationships = []
        
        # Tool relationships
        for tool in server.tools:
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.PROVIDES_TOOL,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"Tool:{tool.name}:{server.name}",
                properties={
                    "tool_complexity": tool.complexity_score,
                    "parameter_count": len(tool.parameters),
                    "category_tags": tool.category_tags,
                    "usage_frequency": tool.usage_frequency
                },
                created_at=datetime.utcnow(),
                confidence=1.0,
                source="tool_extraction"
            )
            relationships.append(rel)
        
        # Prompt relationships
        for prompt in server.prompts:
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.PROVIDES_PROMPT,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"Prompt:{prompt.name}:{server.name}",
                properties={
                    "template_type": prompt.template_type,
                    "argument_count": len(prompt.arguments),
                    "use_cases": prompt.use_cases
                },
                created_at=datetime.utcnow(),
                confidence=1.0,
                source="prompt_extraction"
            )
            relationships.append(rel)
        
        # Resource relationships
        for resource in server.resources:
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.PROVIDES_RESOURCE,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"Resource:{resource.name}:{server.name}",
                properties={
                    "mime_type": resource.mime_type,
                    "access_level": resource.access_level,
                    "supported_operations": resource.supported_operations,
                    "uri_pattern": resource.uri_pattern
                },
                created_at=datetime.utcnow(),
                confidence=1.0,
                source="resource_extraction"
            )
            relationships.append(rel)
        
        return relationships
    
    def _track_infrastructure_relationships(self, server: EnhancedMCPServer) -> List[RelationshipMetadata]:
        """Track repository and package relationships."""
        relationships = []
        
        # Repository relationship
        if server.repository:
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.HOSTED_IN,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"Repository:{server.repository.url}",
                properties={
                    "stars": server.repository.stars,
                    "forks": server.repository.forks,
                    "primary_language": server.repository.primary_language,
                    "is_fork": server.repository.is_fork,
                    "topics": server.repository.topics,
                    "license": server.repository.license_name
                },
                created_at=datetime.utcnow(),
                confidence=1.0,
                source="github_api"
            )
            relationships.append(rel)
        
        # Package relationships
        for package in server.packages:
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.PACKAGED_AS,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"Package:{package.name}:{package.ecosystem}",
                properties={
                    "version": package.version,
                    "ecosystem": package.ecosystem,
                    "author": package.author,
                    "keywords": package.keywords,
                    "download_stats": package.download_stats
                },
                created_at=datetime.utcnow(),
                confidence=1.0,
                source="package_manager"
            )
            relationships.append(rel)
        
        return relationships
    
    def _track_classification_relationships(self, server: EnhancedMCPServer) -> List[RelationshipMetadata]:
        """Track classification relationships with confidence scores."""
        relationships = []
        
        # Category relationships
        for category in server.categories:
            confidence = self._calculate_category_confidence(server, category)
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.BELONGS_TO_CATEGORY,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"Category:{category}",
                properties={
                    "auto_classified": True,
                    "classification_method": "keyword_analysis",
                    "supporting_evidence": self._get_category_evidence(server, category)
                },
                created_at=datetime.utcnow(),
                confidence=confidence,
                source="classification_algorithm"
            )
            relationships.append(rel)
        
        # Domain relationships
        for domain in server.domains:
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.OPERATES_IN_DOMAIN,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"Domain:{domain}",
                properties={
                    "relevance_score": 0.8,  # Could be calculated based on analysis
                    "domain_indicators": self._get_domain_indicators(server, domain)
                },
                created_at=datetime.utcnow(),
                confidence=0.8,
                source="domain_analysis"
            )
            relationships.append(rel)
        
        # Language relationships
        for language in server.languages:
            percentage = self._calculate_language_percentage(server, language)
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.IMPLEMENTED_IN,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"Language:{language}",
                properties={
                    "percentage": percentage,
                    "lines_of_code": self._estimate_loc(server, language),
                    "primary": language == server.repository.primary_language if server.repository else False
                },
                created_at=datetime.utcnow(),
                confidence=1.0,
                source="github_linguist"
            )
            relationships.append(rel)
        
        # Framework relationships
        for framework in server.frameworks:
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.USES_FRAMEWORK,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"Framework:{framework}",
                properties={
                    "adoption_level": self._determine_adoption_level(server, framework),
                    "version": self._extract_framework_version(server, framework),
                    "integration_depth": "full"  # Could be analyzed
                },
                created_at=datetime.utcnow(),
                confidence=0.9,
                source="dependency_analysis"
            )
            relationships.append(rel)
        
        return relationships
    
    def _track_quality_relationships(self, server: EnhancedMCPServer) -> List[RelationshipMetadata]:
        """Track quality and metadata relationships."""
        relationships = []
        
        # Quality metrics
        for metric in server.quality_metrics:
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.HAS_QUALITY_METRIC,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"QualityMetric:{metric.metric_name}:{server.name}",
                properties={
                    "metric_type": metric.metric_type.value,
                    "value": metric.value,
                    "measurement_date": metric.measurement_date.isoformat(),
                    "calculation_method": metric.calculation_method,
                    "threshold_met": metric.threshold_met
                },
                created_at=datetime.utcnow(),
                confidence=1.0,
                source="quality_analysis"
            )
            relationships.append(rel)
        
        # Usage patterns
        for pattern in server.usage_patterns:
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.HAS_USAGE_PATTERN,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"UsagePattern:{pattern.pattern_type}:{server.name}",
                properties={
                    "frequency": pattern.frequency,
                    "success_rate": pattern.success_rate,
                    "setup_time": pattern.estimated_setup_time,
                    "prerequisites": pattern.prerequisites
                },
                created_at=datetime.utcnow(),
                confidence=0.8,
                source="usage_analysis"
            )
            relationships.append(rel)
        
        # Technical debt
        for debt in server.technical_debt:
            rel = RelationshipMetadata(
                relationship_type=RelationshipType.HAS_TECHNICAL_DEBT,
                source_node_id=f"MCPServer:{server.name}",
                target_node_id=f"TechnicalDebt:{debt.debt_type.value}:{server.name}",
                properties={
                    "severity": debt.severity,
                    "estimated_effort": debt.estimated_effort,
                    "status": debt.status,
                    "file_path": debt.file_path,
                    "detection_date": debt.detection_date.isoformat()
                },
                created_at=datetime.utcnow(),
                confidence=1.0,
                source="static_analysis"
            )
            relationships.append(rel)
        
        return relationships
    
    def calculate_server_similarity(self, server1: EnhancedMCPServer, server2: EnhancedMCPServer) -> SimilarityRelationship:
        """Calculate comprehensive similarity between two servers."""
        features_compared = []
        similarity_scores = []
        
        # Category similarity
        category_sim = self._calculate_category_similarity(server1.categories, server2.categories)
        if category_sim > 0:
            features_compared.append("categories")
            similarity_scores.append(category_sim * 0.3)
        
        # Language similarity
        lang_sim = self._calculate_language_similarity(server1.languages, server2.languages)
        if lang_sim > 0:
            features_compared.append("languages")
            similarity_scores.append(lang_sim * 0.2)
        
        # Framework similarity
        framework_sim = self._calculate_framework_similarity(server1.frameworks, server2.frameworks)
        if framework_sim > 0:
            features_compared.append("frameworks")
            similarity_scores.append(framework_sim * 0.2)
        
        # Tool functionality similarity
        tool_sim = self._calculate_tool_similarity(server1.tools, server2.tools)
        if tool_sim > 0:
            features_compared.append("tools")
            similarity_scores.append(tool_sim * 0.3)
        
        # Calculate composite score
        total_score = sum(similarity_scores) if similarity_scores else 0.0
        
        return SimilarityRelationship(
            source_id=server1.name,
            target_id=server2.name,
            similarity_score=total_score,
            algorithm="weighted_composite",
            features_compared=features_compared
        )
    
    def calculate_tool_compatibility(self, tool1: MCPTool, tool2: MCPTool) -> CompatibilityRelationship:
        """Calculate compatibility between two tools."""
        compatibility_score = 0.0
        compatibility_type = "unknown"
        notes = []
        
        # Parameter compatibility
        param_compat = self._assess_parameter_compatibility(tool1.parameters, tool2.parameters)
        if param_compat > 0.5:
            compatibility_score += param_compat * 0.4
            compatibility_type = "data"
            notes.append(f"Parameter compatibility: {param_compat:.2f}")
        
        # Category tag overlap
        tag_overlap = len(set(tool1.category_tags) & set(tool2.category_tags))
        if tag_overlap > 0:
            tag_sim = tag_overlap / max(len(tool1.category_tags), len(tool2.category_tags), 1)
            compatibility_score += tag_sim * 0.3
            if compatibility_type == "unknown":
                compatibility_type = "functional"
            notes.append(f"Category overlap: {tag_overlap} tags")
        
        # Complexity similarity
        if tool1.complexity_score and tool2.complexity_score:
            complexity_diff = abs(tool1.complexity_score - tool2.complexity_score)
            complexity_sim = max(0, 1 - complexity_diff)
            compatibility_score += complexity_sim * 0.3
            notes.append(f"Complexity similarity: {complexity_sim:.2f}")
        
        return CompatibilityRelationship(
            tool1_name=tool1.name,
            tool2_name=tool2.name,
            compatibility_score=compatibility_score,
            compatibility_type=compatibility_type,
            tested=False,
            notes="; ".join(notes)
        )
    
    def get_relationship_statistics(self) -> Dict[str, Any]:
        """Get comprehensive relationship statistics."""
        stats = {
            "total_relationships": len(self.relationships),
            "by_type": {},
            "by_confidence": {},
            "by_source": {},
            "validation_status": {}
        }
        
        for rel in self.relationships:
            # By type
            rel_type = rel.relationship_type.value
            stats["by_type"][rel_type] = stats["by_type"].get(rel_type, 0) + 1
            
            # By confidence
            conf_bucket = self._get_confidence_bucket(rel.confidence)
            stats["by_confidence"][conf_bucket] = stats["by_confidence"].get(conf_bucket, 0) + 1
            
            # By source
            stats["by_source"][rel.source] = stats["by_source"].get(rel.source, 0) + 1
            
            # By validation status
            status = rel.validation_status
            stats["validation_status"][status] = stats["validation_status"].get(status, 0) + 1
        
        # Additional analytics
        stats["high_confidence_relationships"] = len([r for r in self.relationships if r.confidence > 0.8])
        stats["auto_generated_relationships"] = len([r for r in self.relationships if r.source == "automatic"])
        stats["unique_sources"] = len(set(r.source_node_id for r in self.relationships))
        stats["unique_targets"] = len(set(r.target_node_id for r in self.relationships))
        
        return stats
    
    def export_relationships_for_neo4j(self) -> List[Dict[str, Any]]:
        """Export relationships in Neo4j-compatible format."""
        neo4j_relationships = []
        
        for rel in self.relationships:
            neo4j_rel = {
                "type": rel.relationship_type.value,
                "source": rel.source_node_id,
                "target": rel.target_node_id,
                "properties": {
                    **rel.properties,
                    "created_at": rel.created_at.isoformat(),
                    "created_by": rel.created_by,
                    "confidence": rel.confidence,
                    "source": rel.source,
                    "validation_status": rel.validation_status
                }
            }
            
            if rel.last_updated:
                neo4j_rel["properties"]["last_updated"] = rel.last_updated.isoformat()
            
            neo4j_relationships.append(neo4j_rel)
        
        return neo4j_relationships
    
    # Helper methods
    def _calculate_category_confidence(self, server: EnhancedMCPServer, category: str) -> float:
        """Calculate confidence score for category classification."""
        # This would implement actual confidence calculation logic
        # based on keywords, tool types, etc.
        return 0.8  # Placeholder
    
    def _get_category_evidence(self, server: EnhancedMCPServer, category: str) -> List[str]:
        """Get evidence for category classification."""
        # This would return actual evidence like keywords found, tool patterns, etc.
        return ["keyword_match", "tool_pattern"]  # Placeholder
    
    def _get_domain_indicators(self, server: EnhancedMCPServer, domain: str) -> List[str]:
        """Get indicators for domain classification."""
        return ["description_analysis", "tool_functionality"]  # Placeholder
    
    def _calculate_language_percentage(self, server: EnhancedMCPServer, language: str) -> float:
        """Calculate language usage percentage."""
        if server.repository and server.repository.primary_language == language:
            return 100.0
        return 50.0  # Placeholder for secondary languages
    
    def _estimate_loc(self, server: EnhancedMCPServer, language: str) -> Optional[int]:
        """Estimate lines of code for a language."""
        # This would implement actual LOC estimation
        return None  # Placeholder
    
    def _determine_adoption_level(self, server: EnhancedMCPServer, framework: str) -> str:
        """Determine framework adoption level."""
        return "full"  # Placeholder
    
    def _extract_framework_version(self, server: EnhancedMCPServer, framework: str) -> Optional[str]:
        """Extract framework version from dependencies."""
        # This would parse package files for version info
        return None  # Placeholder
    
    def _calculate_category_similarity(self, categories1: List[str], categories2: List[str]) -> float:
        """Calculate similarity between category lists."""
        if not categories1 or not categories2:
            return 0.0
        
        intersection = len(set(categories1) & set(categories2))
        union = len(set(categories1) | set(categories2))
        return intersection / union if union > 0 else 0.0
    
    def _calculate_language_similarity(self, languages1: List[str], languages2: List[str]) -> float:
        """Calculate similarity between language lists."""
        return self._calculate_category_similarity(languages1, languages2)
    
    def _calculate_framework_similarity(self, frameworks1: List[str], frameworks2: List[str]) -> float:
        """Calculate similarity between framework lists."""
        return self._calculate_category_similarity(frameworks1, frameworks2)
    
    def _calculate_tool_similarity(self, tools1: List[MCPTool], tools2: List[MCPTool]) -> float:
        """Calculate functional similarity between tool lists."""
        if not tools1 or not tools2:
            return 0.0
        
        # Compare tool names and category tags
        names1 = set(tool.name for tool in tools1)
        names2 = set(tool.name for tool in tools2)
        name_sim = len(names1 & names2) / len(names1 | names2) if names1 | names2 else 0.0
        
        # Compare category tags
        tags1 = set(tag for tool in tools1 for tag in tool.category_tags)
        tags2 = set(tag for tool in tools2 for tag in tool.category_tags)
        tag_sim = len(tags1 & tags2) / len(tags1 | tags2) if tags1 | tags2 else 0.0
        
        return (name_sim + tag_sim) / 2
    
    def _assess_parameter_compatibility(self, params1: List, params2: List) -> float:
        """Assess parameter compatibility between tools."""
        # This would implement actual parameter compatibility assessment
        return 0.5  # Placeholder
    
    def _get_confidence_bucket(self, confidence: float) -> str:
        """Get confidence bucket for statistics."""
        if confidence >= 0.9:
            return "very_high"
        elif confidence >= 0.7:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"