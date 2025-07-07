"""Advanced graph analytics and insights for the MCP knowledge graph."""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import json
from collections import defaultdict, Counter
import networkx as nx
from neo4j import GraphDatabase


class AnalyticsType(str, Enum):
    """Types of analytics available."""
    ECOSYSTEM_OVERVIEW = "ecosystem_overview"
    SIMILARITY_ANALYSIS = "similarity_analysis"
    TECHNOLOGY_LANDSCAPE = "technology_landscape"
    QUALITY_ASSESSMENT = "quality_assessment"
    RECOMMENDATION_ENGINE = "recommendation_engine"
    NETWORK_ANALYSIS = "network_analysis"
    TREND_ANALYSIS = "trend_analysis"
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"


@dataclass
class AnalyticsResult:
    """Result from analytics query."""
    analysis_type: AnalyticsType
    title: str
    description: str
    data: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    generated_at: str
    query_performance: Optional[Dict[str, Any]] = None


class MCPGraphAnalytics:
    """Advanced analytics engine for MCP knowledge graph."""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", 
                 username: str = "neo4j", password: str = "password"):
        """Initialize analytics engine with Neo4j connection."""
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
        
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
    
    def run_comprehensive_analysis(self) -> Dict[str, AnalyticsResult]:
        """Run all available analytics and return comprehensive insights."""
        analyses = {}
        
        # Run each analysis type
        for analysis_type in AnalyticsType:
            try:
                result = self.run_analysis(analysis_type)
                analyses[analysis_type.value] = result
            except Exception as e:
                print(f"Failed to run {analysis_type.value}: {str(e)}")
        
        return analyses
    
    def run_analysis(self, analysis_type: AnalyticsType) -> AnalyticsResult:
        """Run specific analysis type."""
        analysis_methods = {
            AnalyticsType.ECOSYSTEM_OVERVIEW: self._ecosystem_overview_analysis,
            AnalyticsType.SIMILARITY_ANALYSIS: self._similarity_analysis,
            AnalyticsType.TECHNOLOGY_LANDSCAPE: self._technology_landscape_analysis,
            AnalyticsType.QUALITY_ASSESSMENT: self._quality_assessment_analysis,
            AnalyticsType.RECOMMENDATION_ENGINE: self._recommendation_engine_analysis,
            AnalyticsType.NETWORK_ANALYSIS: self._network_analysis,
            AnalyticsType.TREND_ANALYSIS: self._trend_analysis,
            AnalyticsType.COMPETITIVE_INTELLIGENCE: self._competitive_intelligence_analysis
        }
        
        if analysis_type not in analysis_methods:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        return analysis_methods[analysis_type]()
    
    def _ecosystem_overview_analysis(self) -> AnalyticsResult:
        """Comprehensive ecosystem overview analysis."""
        with self.driver.session() as session:
            # Basic ecosystem metrics
            ecosystem_metrics = self._get_ecosystem_metrics(session)
            
            # Category distribution
            category_dist = session.run("""
                MATCH (s:MCPServer)-[:BELONGS_TO_CATEGORY]->(c:Category)
                RETURN c.name as category, 
                       count(s) as server_count,
                       avg(s.tools_count) as avg_tools,
                       avg(s.popularity_score) as avg_popularity,
                       collect(s.name)[0..5] as sample_servers
                ORDER BY server_count DESC
            """)
            
            # Server type distribution
            server_types = session.run("""
                MATCH (s:MCPServer)
                RETURN s.server_type as type, 
                       count(s) as count,
                       avg(s.tools_count) as avg_tools,
                       sum(s.tools_count) as total_tools
            """)
            
            # Tool distribution analysis
            tool_analysis = session.run("""
                MATCH (s:MCPServer)-[:PROVIDES_TOOL]->(t:Tool)
                WITH s, count(t) as tool_count
                RETURN 
                    min(tool_count) as min_tools,
                    max(tool_count) as max_tools,
                    avg(tool_count) as avg_tools,
                    percentileCont(tool_count, 0.5) as median_tools,
                    percentileCont(tool_count, 0.75) as q3_tools,
                    percentileCont(tool_count, 0.95) as p95_tools
            """)
            
            # Growth and activity metrics
            activity_metrics = session.run("""
                MATCH (s:MCPServer)
                WHERE s.updated_at IS NOT NULL
                WITH s, 
                     duration.between(date(s.updated_at), date()).days as days_since_update
                RETURN 
                    count(s) as servers_with_update_data,
                    avg(days_since_update) as avg_days_since_update,
                    count(CASE WHEN days_since_update <= 30 THEN 1 END) as recently_updated,
                    count(CASE WHEN days_since_update <= 90 THEN 1 END) as updated_last_quarter,
                    count(CASE WHEN days_since_update > 365 THEN 1 END) as potentially_stale
            """)
            
            data = {
                "ecosystem_metrics": dict(ecosystem_metrics.single()),
                "category_distribution": [dict(record) for record in category_dist],
                "server_type_distribution": [dict(record) for record in server_types],
                "tool_distribution": dict(tool_analysis.single()),
                "activity_metrics": dict(activity_metrics.single())
            }
            
            insights = self._generate_ecosystem_insights(data)
            recommendations = self._generate_ecosystem_recommendations(data)
            
            return AnalyticsResult(
                analysis_type=AnalyticsType.ECOSYSTEM_OVERVIEW,
                title="MCP Ecosystem Overview",
                description="Comprehensive analysis of the MCP server ecosystem",
                data=data,
                insights=insights,
                recommendations=recommendations,
                generated_at=self._get_timestamp()
            )
    
    def _similarity_analysis(self) -> AnalyticsResult:
        """Advanced similarity and clustering analysis."""
        with self.driver.session() as session:
            # Server similarity clusters
            similarity_clusters = session.run("""
                MATCH (s1:MCPServer)-[:BELONGS_TO_CATEGORY]->(c:Category)<-[:BELONGS_TO_CATEGORY]-(s2:MCPServer)
                WHERE s1 <> s2
                WITH s1, s2, count(c) as shared_categories
                WHERE shared_categories >= 2
                
                OPTIONAL MATCH (s1)-[:IMPLEMENTED_IN]->(l:Language)<-[:IMPLEMENTED_IN]-(s2)
                WITH s1, s2, shared_categories, count(l) as shared_languages
                
                OPTIONAL MATCH (s1)-[:USES_FRAMEWORK]->(f:Framework)<-[:USES_FRAMEWORK]-(s2)
                WITH s1, s2, shared_categories, shared_languages, count(f) as shared_frameworks
                
                WITH s1, s2, (shared_categories * 3 + shared_languages * 2 + shared_frameworks) as similarity_score
                WHERE similarity_score >= 5
                
                RETURN s1.name as server1, s2.name as server2, similarity_score,
                       shared_categories, shared_languages, shared_frameworks
                ORDER BY similarity_score DESC
                LIMIT 50
            """)
            
            # Tool functionality clusters
            tool_clusters = session.run("""
                MATCH (t1:Tool)-[:BELONGS_TO_CATEGORY]->(c:Category)<-[:BELONGS_TO_CATEGORY]-(t2:Tool)
                WHERE t1 <> t2 AND t1.server_name <> t2.server_name
                WITH t1, t2, count(c) as shared_categories
                WHERE shared_categories >= 1
                
                RETURN t1.name as tool1, t1.server_name as server1,
                       t2.name as tool2, t2.server_name as server2,
                       shared_categories,
                       t1.description as desc1, t2.description as desc2
                ORDER BY shared_categories DESC
                LIMIT 30
            """)
            
            # Language ecosystem clusters
            language_ecosystems = session.run("""
                MATCH (s:MCPServer)-[:IMPLEMENTED_IN]->(l:Language)
                WITH l, collect(s) as servers, count(s) as server_count
                WHERE server_count >= 3
                
                UNWIND servers as s1
                UNWIND servers as s2
                WHERE s1 <> s2
                
                OPTIONAL MATCH (s1)-[:BELONGS_TO_CATEGORY]->(c:Category)<-[:BELONGS_TO_CATEGORY]-(s2)
                WITH l, s1, s2, count(c) as shared_categories
                WHERE shared_categories >= 1
                
                RETURN l.name as language,
                       s1.name as server1, s2.name as server2,
                       shared_categories
                ORDER BY l.name, shared_categories DESC
            """)
            
            data = {
                "server_similarity_clusters": [dict(record) for record in similarity_clusters],
                "tool_functionality_clusters": [dict(record) for record in tool_clusters],
                "language_ecosystem_clusters": [dict(record) for record in language_ecosystems]
            }
            
            insights = self._generate_similarity_insights(data)
            recommendations = self._generate_similarity_recommendations(data)
            
            return AnalyticsResult(
                analysis_type=AnalyticsType.SIMILARITY_ANALYSIS,
                title="Similarity and Clustering Analysis",
                description="Analysis of similar servers, tools, and ecosystem patterns",
                data=data,
                insights=insights,
                recommendations=recommendations,
                generated_at=self._get_timestamp()
            )
    
    def _technology_landscape_analysis(self) -> AnalyticsResult:
        """Technology landscape and stack analysis."""
        with self.driver.session() as session:
            # Language popularity and trends
            language_landscape = session.run("""
                MATCH (s:MCPServer)-[:IMPLEMENTED_IN]->(l:Language)
                WITH l, collect(s) as servers, count(s) as adoption_count
                
                UNWIND servers as server
                WITH l, adoption_count, 
                     avg(server.stars) as avg_stars,
                     avg(server.tools_count) as avg_tools,
                     sum(server.tools_count) as total_tools,
                     collect(server.name)[0..5] as top_servers
                
                RETURN l.name as language, adoption_count, avg_stars, avg_tools, 
                       total_tools, top_servers
                ORDER BY adoption_count DESC
            """)
            
            # Framework ecosystem analysis
            framework_analysis = session.run("""
                MATCH (s:MCPServer)-[:USES_FRAMEWORK]->(f:Framework)
                OPTIONAL MATCH (f)-[:IMPLEMENTED_IN]->(l:Language)
                
                WITH f, l, collect(s) as servers, count(s) as adoption_count
                
                UNWIND servers as server
                WITH f, l, adoption_count,
                     avg(server.complexity_score) as avg_complexity,
                     avg(server.maturity_score) as avg_maturity,
                     collect(server.name)[0..5] as example_servers
                
                RETURN f.name as framework, l.name as language, adoption_count,
                       avg_complexity, avg_maturity, example_servers
                ORDER BY adoption_count DESC
            """)
            
            # Technology stack combinations
            tech_stacks = session.run("""
                MATCH (s:MCPServer)-[:IMPLEMENTED_IN]->(l:Language)
                OPTIONAL MATCH (s)-[:USES_FRAMEWORK]->(f:Framework)
                OPTIONAL MATCH (s)-[:PACKAGED_AS]->(p:Package)
                
                WITH l.name as language, 
                     f.name as framework,
                     p.ecosystem as package_ecosystem,
                     count(s) as combination_count,
                     collect(s.name)[0..3] as examples
                WHERE combination_count >= 2
                
                RETURN language, framework, package_ecosystem, combination_count, examples
                ORDER BY combination_count DESC
                LIMIT 20
            """)
            
            # Dependency analysis
            dependency_patterns = session.run("""
                MATCH (s:MCPServer)-[:PACKAGED_AS]->(p:Package)-[:DEPENDS_ON]->(d:Dependency)
                WITH d.name as dependency, 
                     d.ecosystem as ecosystem,
                     count(DISTINCT s) as dependent_servers,
                     collect(DISTINCT s.name)[0..5] as example_servers
                WHERE dependent_servers >= 2
                
                RETURN dependency, ecosystem, dependent_servers, example_servers
                ORDER BY dependent_servers DESC
                LIMIT 15
            """)
            
            data = {
                "language_landscape": [dict(record) for record in language_landscape],
                "framework_analysis": [dict(record) for record in framework_analysis],
                "technology_stack_combinations": [dict(record) for record in tech_stacks],
                "dependency_patterns": [dict(record) for record in dependency_patterns]
            }
            
            insights = self._generate_technology_insights(data)
            recommendations = self._generate_technology_recommendations(data)
            
            return AnalyticsResult(
                analysis_type=AnalyticsType.TECHNOLOGY_LANDSCAPE,
                title="Technology Landscape Analysis",
                description="Analysis of programming languages, frameworks, and technology stacks",
                data=data,
                insights=insights,
                recommendations=recommendations,
                generated_at=self._get_timestamp()
            )
    
    def _quality_assessment_analysis(self) -> AnalyticsResult:
        """Quality assessment and maturity analysis."""
        with self.driver.session() as session:
            # Quality score distribution
            quality_distribution = session.run("""
                MATCH (s:MCPServer)
                WHERE s.complexity_score IS NOT NULL OR s.maturity_score IS NOT NULL
                
                WITH s,
                     CASE 
                         WHEN s.maturity_score >= 0.8 THEN 'High'
                         WHEN s.maturity_score >= 0.6 THEN 'Medium'
                         WHEN s.maturity_score >= 0.4 THEN 'Low'
                         ELSE 'Very Low'
                     END as maturity_level,
                     CASE
                         WHEN s.complexity_score >= 0.8 THEN 'High'
                         WHEN s.complexity_score >= 0.6 THEN 'Medium'
                         WHEN s.complexity_score >= 0.4 THEN 'Low'
                         ELSE 'Very Low'
                     END as complexity_level
                
                RETURN maturity_level, complexity_level, count(s) as count,
                       collect(s.name)[0..3] as examples
                ORDER BY maturity_level, complexity_level
            """)
            
            # Technical debt analysis
            technical_debt = session.run("""
                MATCH (s:MCPServer)-[:HAS_TECHNICAL_DEBT]->(td:TechnicalDebt)
                WITH s, td.debt_type as debt_type, td.severity as severity, count(td) as debt_count
                
                RETURN debt_type, severity, count(DISTINCT s) as affected_servers,
                       sum(debt_count) as total_debt_items,
                       collect(DISTINCT s.name)[0..5] as example_servers
                ORDER BY affected_servers DESC, total_debt_items DESC
            """)
            
            # Repository health metrics
            repo_health = session.run("""
                MATCH (s:MCPServer)-[:HOSTED_IN]->(r:Repository)
                WITH r,
                     CASE 
                         WHEN r.stars >= 1000 THEN 'High'
                         WHEN r.stars >= 100 THEN 'Medium'
                         WHEN r.stars >= 10 THEN 'Low'
                         ELSE 'Very Low'
                     END as popularity,
                     CASE
                         WHEN r.open_issues <= 5 THEN 'Excellent'
                         WHEN r.open_issues <= 15 THEN 'Good'
                         WHEN r.open_issues <= 50 THEN 'Fair'
                         ELSE 'Poor'
                     END as issue_health,
                     duration.between(date(r.updated_at), date()).days as days_since_update
                
                WITH popularity, issue_health,
                     CASE
                         WHEN days_since_update <= 30 THEN 'Very Recent'
                         WHEN days_since_update <= 90 THEN 'Recent'
                         WHEN days_since_update <= 180 THEN 'Moderate'
                         ELSE 'Stale'
                     END as update_freshness,
                     count(r) as repo_count
                
                RETURN popularity, issue_health, update_freshness, repo_count
                ORDER BY popularity, issue_health, update_freshness
            """)
            
            # Quality vs popularity correlation
            quality_popularity = session.run("""
                MATCH (s:MCPServer)-[:HOSTED_IN]->(r:Repository)
                WHERE s.maturity_score IS NOT NULL AND r.stars IS NOT NULL
                
                WITH s, r,
                     CASE 
                         WHEN s.maturity_score >= 0.7 THEN 'High Quality'
                         WHEN s.maturity_score >= 0.5 THEN 'Medium Quality'
                         ELSE 'Low Quality'
                     END as quality_tier,
                     CASE
                         WHEN r.stars >= 100 THEN 'Popular'
                         WHEN r.stars >= 10 THEN 'Moderate'
                         ELSE 'Low Popularity'
                     END as popularity_tier
                
                RETURN quality_tier, popularity_tier, count(s) as server_count,
                       avg(s.maturity_score) as avg_quality,
                       avg(r.stars) as avg_stars
                ORDER BY quality_tier, popularity_tier
            """)
            
            data = {
                "quality_distribution": [dict(record) for record in quality_distribution],
                "technical_debt_analysis": [dict(record) for record in technical_debt],
                "repository_health": [dict(record) for record in repo_health],
                "quality_popularity_correlation": [dict(record) for record in quality_popularity]
            }
            
            insights = self._generate_quality_insights(data)
            recommendations = self._generate_quality_recommendations(data)
            
            return AnalyticsResult(
                analysis_type=AnalyticsType.QUALITY_ASSESSMENT,
                title="Quality Assessment Analysis",
                description="Analysis of code quality, maturity, and technical debt",
                data=data,
                insights=insights,
                recommendations=recommendations,
                generated_at=self._get_timestamp()
            )
    
    def _recommendation_engine_analysis(self) -> AnalyticsResult:
        """Recommendation engine analysis."""
        with self.driver.session() as session:
            # Server recommendations by category
            category_recommendations = session.run("""
                MATCH (c:Category)<-[:BELONGS_TO_CATEGORY]-(s:MCPServer)
                WITH c, s, 
                     s.tools_count * 0.3 + 
                     s.popularity_score * 0.4 + 
                     s.maturity_score * 0.3 as recommendation_score
                WHERE recommendation_score IS NOT NULL
                
                WITH c, collect({
                    server: s.name,
                    score: recommendation_score,
                    tools: s.tools_count,
                    description: s.description
                }) as servers
                
                RETURN c.name as category,
                       [server IN servers WHERE server.score >= 0.6] as top_servers,
                       size([server IN servers WHERE server.score >= 0.6]) as top_count
                ORDER BY top_count DESC
                LIMIT 10
            """)
            
            # Tool recommendations by functionality
            tool_recommendations = session.run("""
                MATCH (t:Tool)<-[:PROVIDES_TOOL]-(s:MCPServer)
                WHERE t.category_tags IS NOT NULL AND size(t.category_tags) > 0
                
                WITH t.category_tags as tags, 
                     collect({
                         tool: t.name,
                         server: s.name,
                         description: t.description,
                         complexity: t.complexity_score,
                         server_popularity: s.popularity_score
                     }) as tools
                
                UNWIND tags as tag
                WITH tag, tools
                
                RETURN tag as functionality,
                       [tool IN tools ORDER BY tool.server_popularity DESC] as recommended_tools
                ORDER BY size(recommended_tools) DESC
                LIMIT 15
            """)
            
            # Complementary server suggestions
            complementary_suggestions = session.run("""
                MATCH (s1:MCPServer)-[:BELONGS_TO_CATEGORY]->(c1:Category)
                MATCH (s2:MCPServer)-[:BELONGS_TO_CATEGORY]->(c2:Category)
                WHERE s1 <> s2 AND c1 <> c2
                
                // Find servers that complement each other (different categories)
                WITH s1, s2, c1, c2,
                     CASE 
                         WHEN c1.name IN ['ai', 'data'] AND c2.name IN ['web', 'filesystem'] THEN 0.8
                         WHEN c1.name IN ['development', 'git'] AND c2.name IN ['productivity', 'communication'] THEN 0.7
                         WHEN c1.name = 'database' AND c2.name IN ['ai', 'web'] THEN 0.9
                         ELSE 0.5
                     END as complementary_score
                WHERE complementary_score >= 0.7
                
                RETURN s1.name as primary_server, s2.name as complementary_server,
                       c1.name as primary_category, c2.name as complementary_category,
                       complementary_score,
                       s1.description as primary_description,
                       s2.description as complementary_description
                ORDER BY complementary_score DESC
                LIMIT 20
            """)
            
            data = {
                "category_recommendations": [dict(record) for record in category_recommendations],
                "tool_recommendations": [dict(record) for record in tool_recommendations],
                "complementary_suggestions": [dict(record) for record in complementary_suggestions]
            }
            
            insights = self._generate_recommendation_insights(data)
            recommendations = self._generate_recommendation_recommendations(data)
            
            return AnalyticsResult(
                analysis_type=AnalyticsType.RECOMMENDATION_ENGINE,
                title="Recommendation Engine Analysis",
                description="Intelligent recommendations for servers, tools, and complementary solutions",
                data=data,
                insights=insights,
                recommendations=recommendations,
                generated_at=self._get_timestamp()
            )
    
    def _network_analysis(self) -> AnalyticsResult:
        """Network analysis of relationships and influence."""
        # This would implement advanced network analysis
        # For now, return placeholder
        return AnalyticsResult(
            analysis_type=AnalyticsType.NETWORK_ANALYSIS,
            title="Network Analysis",
            description="Analysis of network structures and influence patterns",
            data={"status": "not_implemented"},
            insights=["Network analysis implementation pending"],
            recommendations=["Implement PageRank and centrality measures"],
            generated_at=self._get_timestamp()
        )
    
    def _trend_analysis(self) -> AnalyticsResult:
        """Trend analysis over time."""
        # This would implement temporal trend analysis
        # For now, return placeholder
        return AnalyticsResult(
            analysis_type=AnalyticsType.TREND_ANALYSIS,
            title="Trend Analysis",
            description="Analysis of trends and patterns over time",
            data={"status": "not_implemented"},
            insights=["Trend analysis requires historical data"],
            recommendations=["Implement time-series data collection"],
            generated_at=self._get_timestamp()
        )
    
    def _competitive_intelligence_analysis(self) -> AnalyticsResult:
        """Competitive intelligence analysis."""
        # This would implement competitive analysis
        # For now, return placeholder
        return AnalyticsResult(
            analysis_type=AnalyticsType.COMPETITIVE_INTELLIGENCE,
            title="Competitive Intelligence",
            description="Analysis of competitive landscape and market positioning",
            data={"status": "not_implemented"},
            insights=["Competitive analysis implementation pending"],
            recommendations=["Define competitive metrics and benchmarks"],
            generated_at=self._get_timestamp()
        )
    
    # Helper methods for generating insights
    def _get_ecosystem_metrics(self, session):
        """Get basic ecosystem metrics."""
        return session.run("""
            MATCH (s:MCPServer)
            OPTIONAL MATCH (s)-[:PROVIDES_TOOL]->(t:Tool)
            OPTIONAL MATCH (s)-[:PROVIDES_PROMPT]->(p:Prompt)
            OPTIONAL MATCH (s)-[:PROVIDES_RESOURCE]->(r:Resource)
            
            RETURN count(DISTINCT s) as total_servers,
                   count(DISTINCT t) as total_tools,
                   count(DISTINCT p) as total_prompts,
                   count(DISTINCT r) as total_resources,
                   avg(s.tools_count) as avg_tools_per_server,
                   sum(s.tools_count) as total_tool_instances
        """)
    
    def _generate_ecosystem_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights from ecosystem analysis."""
        insights = []
        
        metrics = data["ecosystem_metrics"]
        category_dist = data["category_distribution"]
        
        insights.append(f"The MCP ecosystem contains {metrics['total_servers']} servers providing {metrics['total_tools']} unique tools")
        
        if category_dist:
            top_category = category_dist[0]
            insights.append(f"'{top_category['category']}' is the most popular category with {top_category['server_count']} servers")
        
        tool_dist = data["tool_distribution"]
        insights.append(f"Average {tool_dist['avg_tools']:.1f} tools per server, with top servers providing up to {tool_dist['max_tools']} tools")
        
        activity = data["activity_metrics"]
        if activity["recently_updated"] > 0:
            recent_pct = (activity["recently_updated"] / activity["servers_with_update_data"]) * 100
            insights.append(f"{recent_pct:.1f}% of servers were updated in the last 30 days")
        
        return insights
    
    def _generate_ecosystem_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate recommendations from ecosystem analysis."""
        recommendations = []
        
        activity = data["activity_metrics"]
        if activity["potentially_stale"] > 0:
            stale_pct = (activity["potentially_stale"] / activity["servers_with_update_data"]) * 100
            recommendations.append(f"Consider reviewing {activity['potentially_stale']} servers ({stale_pct:.1f}%) that haven't been updated in over a year")
        
        tool_dist = data["tool_distribution"]
        if tool_dist["min_tools"] == 0:
            recommendations.append("Focus on servers with no tools to identify potential tool extraction opportunities")
        
        recommendations.append("Develop category-specific guidelines to help new servers choose appropriate classifications")
        recommendations.append("Create mentorship programs to pair experienced maintainers with new server developers")
        
        return recommendations
    
    def _generate_similarity_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights from similarity analysis."""
        insights = []
        
        clusters = data["server_similarity_clusters"]
        if clusters:
            insights.append(f"Found {len(clusters)} server pairs with high similarity scores")
            
            # Analyze cluster patterns
            high_similarity = [c for c in clusters if c["similarity_score"] >= 8]
            if high_similarity:
                insights.append(f"{len(high_similarity)} server pairs have very high similarity (score >= 8)")
        
        tool_clusters = data["tool_functionality_clusters"]
        if tool_clusters:
            insights.append(f"Identified {len(tool_clusters)} tool pairs with similar functionality across different servers")
        
        return insights
    
    def _generate_similarity_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate recommendations from similarity analysis."""
        recommendations = []
        
        recommendations.append("Consider consolidating or collaborating on highly similar servers")
        recommendations.append("Use tool similarity data to create standardized interfaces")
        recommendations.append("Develop cross-server compatibility standards based on similarity patterns")
        
        return recommendations
    
    def _generate_technology_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights from technology analysis."""
        insights = []
        
        languages = data["language_landscape"]
        if languages:
            top_lang = languages[0]
            insights.append(f"{top_lang['language']} is the most popular language with {top_lang['adoption_count']} servers")
            
            total_tools = sum(lang["total_tools"] for lang in languages if lang["total_tools"])
            insights.append(f"Language distribution spans {len(languages)} different languages with {total_tools} total tools")
        
        frameworks = data["framework_analysis"]
        if frameworks:
            insights.append(f"Framework adoption varies across {len(frameworks)} different frameworks")
        
        return insights
    
    def _generate_technology_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate recommendations from technology analysis."""
        recommendations = []
        
        recommendations.append("Create language-specific best practices guides")
        recommendations.append("Develop framework-agnostic standards for core MCP functionality")
        recommendations.append("Establish dependency security scanning for popular dependencies")
        
        return recommendations
    
    def _generate_quality_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights from quality analysis."""
        insights = []
        
        debt_analysis = data["technical_debt_analysis"]
        if debt_analysis:
            total_affected = sum(item["affected_servers"] for item in debt_analysis)
            insights.append(f"Technical debt affects {total_affected} server instances across different categories")
        
        quality_dist = data["quality_distribution"]
        if quality_dist:
            high_quality = sum(item["count"] for item in quality_dist if "High" in item.get("maturity_level", ""))
            total_quality = sum(item["count"] for item in quality_dist)
            if total_quality > 0:
                high_pct = (high_quality / total_quality) * 100
                insights.append(f"{high_pct:.1f}% of servers demonstrate high maturity scores")
        
        return insights
    
    def _generate_quality_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate recommendations from quality analysis."""
        recommendations = []
        
        recommendations.append("Implement automated quality checks in the MCP development workflow")
        recommendations.append("Create quality benchmarks and scorecards for server maintainers")
        recommendations.append("Develop technical debt reduction programs with clear priorities")
        
        return recommendations
    
    def _generate_recommendation_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights from recommendation analysis."""
        insights = []
        
        category_recs = data["category_recommendations"]
        if category_recs:
            insights.append(f"Recommendations available across {len(category_recs)} categories")
        
        tool_recs = data["tool_recommendations"]
        if tool_recs:
            insights.append(f"Tool recommendations span {len(tool_recs)} functional areas")
        
        complementary = data["complementary_suggestions"]
        if complementary:
            insights.append(f"Identified {len(complementary)} complementary server pairings")
        
        return insights
    
    def _generate_recommendation_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate meta-recommendations from recommendation analysis."""
        recommendations = []
        
        recommendations.append("Implement a recommendation API for dynamic server suggestions")
        recommendations.append("Create user-facing recommendation interfaces in MCP tooling")
        recommendations.append("Develop feedback mechanisms to improve recommendation accuracy")
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


def export_analytics_report(analytics_results: Dict[str, AnalyticsResult], 
                          output_file: str = "mcp_analytics_report.json"):
    """Export comprehensive analytics report."""
    report = {
        "report_metadata": {
            "generated_at": analytics_results[list(analytics_results.keys())[0]].generated_at if analytics_results else None,
            "analyses_included": list(analytics_results.keys()),
            "total_analyses": len(analytics_results)
        },
        "executive_summary": _generate_executive_summary(analytics_results),
        "detailed_analyses": {}
    }
    
    for analysis_type, result in analytics_results.items():
        report["detailed_analyses"][analysis_type] = {
            "title": result.title,
            "description": result.description,
            "key_insights": result.insights,
            "recommendations": result.recommendations,
            "data": result.data
        }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📊 Analytics report exported to {output_file}")
    return report


def _generate_executive_summary(analytics_results: Dict[str, AnalyticsResult]) -> Dict[str, Any]:
    """Generate executive summary from all analytics."""
    summary = {
        "key_findings": [],
        "strategic_recommendations": [],
        "ecosystem_health": "unknown"
    }
    
    # Aggregate key findings from all analyses
    for result in analytics_results.values():
        summary["key_findings"].extend(result.insights[:2])  # Top 2 insights from each
        summary["strategic_recommendations"].extend(result.recommendations[:1])  # Top recommendation from each
    
    # Determine ecosystem health (simplified)
    if AnalyticsType.ECOSYSTEM_OVERVIEW.value in analytics_results:
        ecosystem_data = analytics_results[AnalyticsType.ECOSYSTEM_OVERVIEW.value].data
        total_servers = ecosystem_data.get("ecosystem_metrics", {}).get("total_servers", 0)
        if total_servers >= 500:
            summary["ecosystem_health"] = "thriving"
        elif total_servers >= 100:
            summary["ecosystem_health"] = "healthy"
        elif total_servers >= 50:
            summary["ecosystem_health"] = "developing"
        else:
            summary["ecosystem_health"] = "emerging"
    
    return summary