"""Schema validation and performance testing for the MCP Neo4j knowledge graph."""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
from datetime import datetime

from mcp_scraper.enhanced_neo4j_graph import EnhancedMCPKnowledgeGraph
from mcp_scraper.enhanced_models import *


@dataclass
class ValidationResult:
    """Result of schema validation."""
    test_name: str
    passed: bool
    execution_time_ms: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


class Neo4jSchemaValidator:
    """Comprehensive schema validation and performance testing."""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687",
                 username: str = "neo4j", password: str = "password"):
        """Initialize validator with Neo4j connection."""
        self.graph = EnhancedMCPKnowledgeGraph(neo4j_uri, username, password)
        self.validation_results: List[ValidationResult] = []
    
    def close(self):
        """Close Neo4j connection."""
        self.graph.close()
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run comprehensive schema validation and performance tests."""
        print("🔍 Starting comprehensive Neo4j schema validation...")
        
        validation_tests = [
            self._test_constraints_exist,
            self._test_indexes_exist,
            self._test_node_creation,
            self._test_relationship_creation,
            self._test_query_performance,
            self._test_data_integrity,
            self._test_schema_compliance,
            self._test_analytics_queries
        ]
        
        for test in validation_tests:
            try:
                start_time = time.time()
                result = test()
                execution_time = (time.time() - start_time) * 1000
                
                if isinstance(result, ValidationResult):
                    result.execution_time_ms = execution_time
                    self.validation_results.append(result)
                else:
                    # Handle tests that return multiple results
                    for r in result if isinstance(result, list) else [result]:
                        r.execution_time_ms = execution_time / len(result) if isinstance(result, list) else execution_time
                        self.validation_results.append(r)
                        
            except Exception as e:
                self.validation_results.append(ValidationResult(
                    test_name=test.__name__,
                    passed=False,
                    execution_time_ms=0,
                    details={},
                    error_message=str(e)
                ))
        
        return self._generate_validation_report()
    
    def _test_constraints_exist(self) -> ValidationResult:
        """Test that all required constraints exist."""
        with self.graph.driver.session() as session:
            constraints_query = "SHOW CONSTRAINTS"
            result = session.run(constraints_query)
            constraints = [record["name"] for record in result]
            
            required_constraints = [
                "mcp_server_name_unique",
                "tool_composite_unique", 
                "category_name_unique",
                "language_name_unique",
                "repository_url_unique"
            ]
            
            missing_constraints = [c for c in required_constraints if not any(c in constraint for constraint in constraints)]
            
            return ValidationResult(
                test_name="constraints_exist",
                passed=len(missing_constraints) == 0,
                execution_time_ms=0,
                details={
                    "total_constraints": len(constraints),
                    "required_constraints": required_constraints,
                    "missing_constraints": missing_constraints,
                    "existing_constraints": constraints
                },
                error_message=f"Missing constraints: {missing_constraints}" if missing_constraints else None
            )
    
    def _test_indexes_exist(self) -> ValidationResult:
        """Test that performance indexes exist."""
        with self.graph.driver.session() as session:
            indexes_query = "SHOW INDEXES"
            result = session.run(indexes_query)
            indexes = [record["name"] for record in result]
            
            required_indexes = [
                "mcp_server_type_idx",
                "mcp_server_stars_idx",
                "tool_name_idx"
            ]
            
            missing_indexes = [i for i in required_indexes if not any(i in index for index in indexes)]
            
            return ValidationResult(
                test_name="indexes_exist",
                passed=len(missing_indexes) == 0,
                execution_time_ms=0,
                details={
                    "total_indexes": len(indexes),
                    "required_indexes": required_indexes,
                    "missing_indexes": missing_indexes,
                    "existing_indexes": indexes
                },
                error_message=f"Missing indexes: {missing_indexes}" if missing_indexes else None
            )
    
    def _test_node_creation(self) -> List[ValidationResult]:
        """Test creation of different node types."""
        results = []
        
        node_tests = [
            ("MCPServer", self._create_test_server),
            ("Tool", self._create_test_tool),
            ("Repository", self._create_test_repository),
            ("Category", self._create_test_category),
            ("Language", self._create_test_language)
        ]
        
        for node_type, create_func in node_tests:
            try:
                success = create_func()
                results.append(ValidationResult(
                    test_name=f"create_{node_type.lower()}_node",
                    passed=success,
                    execution_time_ms=0,
                    details={"node_type": node_type}
                ))
            except Exception as e:
                results.append(ValidationResult(
                    test_name=f"create_{node_type.lower()}_node",
                    passed=False,
                    execution_time_ms=0,
                    details={"node_type": node_type},
                    error_message=str(e)
                ))
        
        return results
    
    def _test_relationship_creation(self) -> List[ValidationResult]:
        """Test creation of different relationship types."""
        results = []
        
        relationship_tests = [
            ("PROVIDES_TOOL", self._create_test_tool_relationship),
            ("HOSTED_IN", self._create_test_repository_relationship),
            ("BELONGS_TO_CATEGORY", self._create_test_category_relationship),
            ("IMPLEMENTED_IN", self._create_test_language_relationship)
        ]
        
        for rel_type, create_func in relationship_tests:
            try:
                success = create_func()
                results.append(ValidationResult(
                    test_name=f"create_{rel_type.lower()}_relationship",
                    passed=success,
                    execution_time_ms=0,
                    details={"relationship_type": rel_type}
                ))
            except Exception as e:
                results.append(ValidationResult(
                    test_name=f"create_{rel_type.lower()}_relationship",
                    passed=False,
                    execution_time_ms=0,
                    details={"relationship_type": rel_type},
                    error_message=str(e)
                ))
        
        return results
    
    def _test_query_performance(self) -> List[ValidationResult]:
        """Test performance of key queries."""
        results = []
        
        performance_tests = [
            ("server_count_query", "MATCH (s:MCPServer) RETURN count(s) as count"),
            ("tool_count_query", "MATCH (t:Tool) RETURN count(t) as count"),
            ("category_distribution", """
                MATCH (s:MCPServer)-[:BELONGS_TO_CATEGORY]->(c:Category)
                RETURN c.name, count(s) as count ORDER BY count DESC LIMIT 10
            """),
            ("similarity_query", """
                MATCH (s1:MCPServer)-[:BELONGS_TO_CATEGORY]->(c:Category)<-[:BELONGS_TO_CATEGORY]-(s2:MCPServer)
                WHERE s1 <> s2
                RETURN s1.name, s2.name, count(c) as shared_categories
                ORDER BY shared_categories DESC LIMIT 10
            """)
        ]
        
        for test_name, query in performance_tests:
            try:
                with self.graph.driver.session() as session:
                    start_time = time.time()
                    result = session.run(query)
                    records = list(result)
                    execution_time = (time.time() - start_time) * 1000
                    
                    # Performance threshold: queries should complete within 1000ms
                    passed = execution_time < 1000
                    
                    results.append(ValidationResult(
                        test_name=f"performance_{test_name}",
                        passed=passed,
                        execution_time_ms=execution_time,
                        details={
                            "query": query,
                            "records_returned": len(records),
                            "performance_threshold_ms": 1000
                        },
                        error_message=f"Query too slow: {execution_time:.2f}ms" if not passed else None
                    ))
            except Exception as e:
                results.append(ValidationResult(
                    test_name=f"performance_{test_name}",
                    passed=False,
                    execution_time_ms=0,
                    details={"query": query},
                    error_message=str(e)
                ))
        
        return results
    
    def _test_data_integrity(self) -> ValidationResult:
        """Test data integrity constraints."""
        with self.graph.driver.session() as session:
            integrity_checks = []
            
            # Check for orphaned nodes
            orphaned_tools = session.run("""
                MATCH (t:Tool) 
                WHERE NOT (t)<-[:PROVIDES_TOOL]-(:MCPServer)
                RETURN count(t) as count
            """).single()["count"]
            
            integrity_checks.append(("orphaned_tools", orphaned_tools == 0, f"Found {orphaned_tools} orphaned tools"))
            
            # Check for duplicate servers
            duplicate_servers = session.run("""
                MATCH (s:MCPServer)
                WITH s.name as name, count(s) as count
                WHERE count > 1
                RETURN sum(count) as total_duplicates
            """).single()["total_duplicates"] or 0
            
            integrity_checks.append(("duplicate_servers", duplicate_servers == 0, f"Found {duplicate_servers} duplicate servers"))
            
            # Check relationship consistency
            inconsistent_relationships = session.run("""
                MATCH (s:MCPServer)-[r:PROVIDES_TOOL]->(t:Tool)
                WHERE t.server_name <> s.name
                RETURN count(r) as count
            """).single()["count"]
            
            integrity_checks.append(("relationship_consistency", inconsistent_relationships == 0, f"Found {inconsistent_relationships} inconsistent relationships"))
            
            all_passed = all(check[1] for check in integrity_checks)
            issues = [check[2] for check in integrity_checks if not check[1]]
            
            return ValidationResult(
                test_name="data_integrity",
                passed=all_passed,
                execution_time_ms=0,
                details={
                    "checks_performed": len(integrity_checks),
                    "checks_passed": sum(1 for check in integrity_checks if check[1]),
                    "integrity_issues": issues
                },
                error_message="; ".join(issues) if issues else None
            )
    
    def _test_schema_compliance(self) -> ValidationResult:
        """Test compliance with expected schema structure."""
        with self.graph.driver.session() as session:
            # Check node label compliance
            node_labels_query = "CALL db.labels()"
            result = session.run(node_labels_query)
            existing_labels = set(record["label"] for record in result)
            
            expected_labels = {
                "MCPServer", "Tool", "Prompt", "Resource", "Repository", 
                "Package", "Category", "Domain", "Language", "Framework", 
                "License", "Organization", "Developer", "QualityMetric", 
                "UsagePattern", "TechnicalDebt"
            }
            
            missing_labels = expected_labels - existing_labels
            unexpected_labels = existing_labels - expected_labels - {"ScrapingRun"}  # Allow ScrapingRun
            
            # Check relationship type compliance
            rel_types_query = "CALL db.relationshipTypes()"
            result = session.run(rel_types_query)
            existing_rels = set(record["relationshipType"] for record in result)
            
            expected_rels = {
                "PROVIDES_TOOL", "PROVIDES_PROMPT", "PROVIDES_RESOURCE",
                "HOSTED_IN", "PACKAGED_AS", "BELONGS_TO_CATEGORY",
                "OPERATES_IN_DOMAIN", "IMPLEMENTED_IN", "USES_FRAMEWORK",
                "LICENSED_UNDER", "MAINTAINS", "HAS_QUALITY_METRIC",
                "HAS_USAGE_PATTERN", "HAS_TECHNICAL_DEBT"
            }
            
            missing_rels = expected_rels - existing_rels
            
            compliance_score = (
                len(expected_labels - missing_labels) / len(expected_labels) +
                len(expected_rels - missing_rels) / len(expected_rels)
            ) / 2
            
            return ValidationResult(
                test_name="schema_compliance",
                passed=compliance_score >= 0.8,  # 80% compliance threshold
                execution_time_ms=0,
                details={
                    "compliance_score": compliance_score,
                    "expected_labels": len(expected_labels),
                    "existing_labels": len(existing_labels),
                    "missing_labels": list(missing_labels),
                    "unexpected_labels": list(unexpected_labels),
                    "expected_relationships": len(expected_rels),
                    "existing_relationships": len(existing_rels),
                    "missing_relationships": list(missing_rels)
                },
                error_message=f"Schema compliance {compliance_score:.1%} below 80% threshold" if compliance_score < 0.8 else None
            )
    
    def _test_analytics_queries(self) -> ValidationResult:
        """Test that analytics queries execute successfully."""
        try:
            from mcp_scraper.graph_analytics import MCPGraphAnalytics
            
            analytics = MCPGraphAnalytics()
            
            # Test a few key analytics
            test_analyses = [
                analytics._ecosystem_overview_analysis,
                analytics._similarity_analysis,
                analytics._technology_landscape_analysis
            ]
            
            successful_analyses = 0
            total_analyses = len(test_analyses)
            errors = []
            
            for analysis_func in test_analyses:
                try:
                    result = analysis_func()
                    if result and result.data:
                        successful_analyses += 1
                except Exception as e:
                    errors.append(f"{analysis_func.__name__}: {str(e)}")
            
            analytics.close()
            
            success_rate = successful_analyses / total_analyses
            
            return ValidationResult(
                test_name="analytics_queries",
                passed=success_rate >= 0.8,
                execution_time_ms=0,
                details={
                    "total_analyses_tested": total_analyses,
                    "successful_analyses": successful_analyses,
                    "success_rate": success_rate,
                    "errors": errors
                },
                error_message=f"Analytics success rate {success_rate:.1%} below 80%" if success_rate < 0.8 else None
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="analytics_queries",
                passed=False,
                execution_time_ms=0,
                details={},
                error_message=f"Failed to test analytics: {str(e)}"
            )
    
    def _generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        passed_tests = sum(1 for r in self.validation_results if r.passed)
        total_tests = len(self.validation_results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        avg_execution_time = sum(r.execution_time_ms for r in self.validation_results) / total_tests if total_tests > 0 else 0
        
        failed_tests = [r for r in self.validation_results if not r.passed]
        
        report = {
            "validation_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": len(failed_tests),
                "success_rate": success_rate,
                "overall_status": "PASS" if success_rate >= 0.8 else "FAIL",
                "average_execution_time_ms": avg_execution_time
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "execution_time_ms": r.execution_time_ms,
                    "details": r.details,
                    "error_message": r.error_message
                }
                for r in self.validation_results
            ],
            "failed_tests_summary": [
                {
                    "test_name": r.test_name,
                    "error_message": r.error_message,
                    "details": r.details
                }
                for r in failed_tests
            ],
            "recommendations": self._generate_recommendations(failed_tests),
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
        return report
    
    def _generate_recommendations(self, failed_tests: List[ValidationResult]) -> List[str]:
        """Generate recommendations based on failed tests."""
        recommendations = []
        
        if any("constraints" in test.test_name for test in failed_tests):
            recommendations.append("Run the schema setup script to create missing constraints")
        
        if any("indexes" in test.test_name for test in failed_tests):
            recommendations.append("Create missing performance indexes for better query performance")
        
        if any("performance" in test.test_name for test in failed_tests):
            recommendations.append("Consider optimizing slow queries or adding more indexes")
        
        if any("integrity" in test.test_name for test in failed_tests):
            recommendations.append("Clean up data integrity issues before proceeding with analysis")
        
        if any("analytics" in test.test_name for test in failed_tests):
            recommendations.append("Verify that sufficient data exists for meaningful analytics")
        
        if not recommendations:
            recommendations.append("Schema validation passed - system is ready for production use")
        
        return recommendations
    
    # Helper methods for creating test data
    def _create_test_server(self) -> bool:
        """Create a test server node."""
        with self.graph.driver.session() as session:
            query = """
            MERGE (s:MCPServer {name: 'test_server_validation'})
            SET s.description = 'Test server for validation',
                s.server_type = 'reference',
                s.is_accessible = true,
                s.tools_count = 1
            RETURN s
            """
            result = session.run(query)
            return result.consume().counters.nodes_created >= 0
    
    def _create_test_tool(self) -> bool:
        """Create a test tool node."""
        with self.graph.driver.session() as session:
            query = """
            MERGE (t:Tool {name: 'test_tool_validation', server_name: 'test_server_validation'})
            SET t.description = 'Test tool for validation',
                t.parameters_count = 2
            RETURN t
            """
            result = session.run(query)
            return result.consume().counters.nodes_created >= 0
    
    def _create_test_repository(self) -> bool:
        """Create a test repository node."""
        with self.graph.driver.session() as session:
            query = """
            MERGE (r:Repository {url: 'https://github.com/test/validation'})
            SET r.owner = 'test',
                r.name = 'validation',
                r.stars = 100,
                r.primary_language = 'Python'
            RETURN r
            """
            result = session.run(query)
            return result.consume().counters.nodes_created >= 0
    
    def _create_test_category(self) -> bool:
        """Create a test category node."""
        with self.graph.driver.session() as session:
            query = """
            MERGE (c:Category {name: 'test_validation'})
            SET c.description = 'Test category for validation'
            RETURN c
            """
            result = session.run(query)
            return result.consume().counters.nodes_created >= 0
    
    def _create_test_language(self) -> bool:
        """Create a test language node."""
        with self.graph.driver.session() as session:
            query = """
            MERGE (l:Language {name: 'TestScript'})
            SET l.paradigm = 'test'
            RETURN l
            """
            result = session.run(query)
            return result.consume().counters.nodes_created >= 0
    
    def _create_test_tool_relationship(self) -> bool:
        """Create a test tool relationship."""
        with self.graph.driver.session() as session:
            query = """
            MATCH (s:MCPServer {name: 'test_server_validation'})
            MATCH (t:Tool {name: 'test_tool_validation', server_name: 'test_server_validation'})
            MERGE (s)-[:PROVIDES_TOOL]->(t)
            RETURN s, t
            """
            result = session.run(query)
            return result.consume().counters.relationships_created >= 0
    
    def _create_test_repository_relationship(self) -> bool:
        """Create a test repository relationship."""
        with self.graph.driver.session() as session:
            query = """
            MATCH (s:MCPServer {name: 'test_server_validation'})
            MATCH (r:Repository {url: 'https://github.com/test/validation'})
            MERGE (s)-[:HOSTED_IN]->(r)
            RETURN s, r
            """
            result = session.run(query)
            return result.consume().counters.relationships_created >= 0
    
    def _create_test_category_relationship(self) -> bool:
        """Create a test category relationship."""
        with self.graph.driver.session() as session:
            query = """
            MATCH (s:MCPServer {name: 'test_server_validation'})
            MATCH (c:Category {name: 'test_validation'})
            MERGE (s)-[:BELONGS_TO_CATEGORY]->(c)
            RETURN s, c
            """
            result = session.run(query)
            return result.consume().counters.relationships_created >= 0
    
    def _create_test_language_relationship(self) -> bool:
        """Create a test language relationship."""
        with self.graph.driver.session() as session:
            query = """
            MATCH (s:MCPServer {name: 'test_server_validation'})
            MATCH (l:Language {name: 'TestScript'})
            MERGE (s)-[:IMPLEMENTED_IN]->(l)
            RETURN s, l
            """
            result = session.run(query)
            return result.consume().counters.relationships_created >= 0


def run_schema_validation(output_file: str = "neo4j_validation_report.json") -> Dict[str, Any]:
    """
    Run comprehensive Neo4j schema validation and export report.
    
    Args:
        output_file: Output file for validation report
    
    Returns:
        Validation report dictionary
    """
    validator = Neo4jSchemaValidator()
    
    try:
        print("🔍 Starting Neo4j schema validation...")
        report = validator.run_full_validation()
        
        # Export report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        summary = report["validation_summary"]
        print(f"\n📊 Validation Summary:")
        print(f"   Tests: {summary['passed_tests']}/{summary['total_tests']} passed ({summary['success_rate']:.1%})")
        print(f"   Status: {summary['overall_status']}")
        print(f"   Average execution time: {summary['average_execution_time_ms']:.2f}ms")
        
        if summary["failed_tests"] > 0:
            print(f"\n⚠️  Failed tests:")
            for test in report["failed_tests_summary"]:
                print(f"   - {test['test_name']}: {test['error_message']}")
        
        print(f"\n📋 Recommendations:")
        for rec in report["recommendations"]:
            print(f"   - {rec}")
        
        print(f"\n📄 Full report saved to: {output_file}")
        
        return report
        
    finally:
        validator.close()


if __name__ == "__main__":
    """Run validation when script is executed directly."""
    report = run_schema_validation()
    
    # Exit with error code if validation failed
    if report["validation_summary"]["overall_status"] == "FAIL":
        exit(1)
    else:
        print("✅ All validations passed!")
        exit(0)