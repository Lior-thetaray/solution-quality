"""
Widget Validation Tasks for ThetaRay Solution Quality
"""

from crewai import Task
from typing import List


def create_widget_analysis_task(agent, domain: str) -> Task:
    """
    Task to analyze all feature widgets in a domain.
    """
    return Task(
        description=f"""Analyze all features in the '{domain}' domain to validate widget configurations.
        
        For each feature, you must:
        1. Identify the widget type (BEHAVIORAL, CATEGORICAL, HISTORICAL, or BINARY)
        2. Validate that the widget type is optimal for the feature's data type and purpose
        3. For HISTORICAL widgets, verify population behavior is present (ExplainabilityValueType.POPULATION)
        4. Check that all required fields are specified for each widget type
        
        Use the 'Analyze Feature Widgets' tool to get comprehensive widget analysis.
        
        Critical validations:
        - HISTORICAL widgets MUST have population behavior - this is mandatory
        - Z-score features MUST use HISTORICAL widget
        - Boolean features MUST use BINARY widget
        - Categorical features SHOULD use CATEGORICAL widget
        
        Provide a detailed analysis of:
        - Total features analyzed
        - Features with optimal widgets
        - Features with suboptimal widgets
        - Features missing widgets
        - CRITICAL: Features with HISTORICAL widgets lacking population behavior
        """,
        agent=agent,
        expected_output="""Detailed JSON report containing:
        - Summary statistics (total features, optimal/suboptimal counts)
        - List of features with validation issues
        - Specific recommendations for each suboptimal widget
        - Critical issues highlighted (especially missing population behavior)
        - File paths for all issues found
        """
    )


def create_widget_requirements_check_task(agent, domain: str, features: List[str]) -> Task:
    """
    Task to check specific features for widget requirement compliance.
    """
    features_str = ", ".join(features)
    
    return Task(
        description=f"""Check widget requirements for specific features: {features_str} in domain '{domain}'.
        
        For each feature, verify:
        1. Widget type is specified
        2. All mandatory fields for that widget type are present
        3. For HISTORICAL widgets: Population behavior data is included
        4. Time ranges are specified where required
        5. Category labels and variables are defined for categorical widgets
        
        Use the 'Check Feature Widget Requirements' tool for detailed validation.
        
        Return a comprehensive report on compliance for each feature.
        """,
        agent=agent,
        expected_output="""JSON report for each feature showing:
        - Widget type
        - Requirements met
        - Requirements missing
        - Recommendations for fixes
        """
    )


def create_widget_validation_report_task(agent, domain: str) -> Task:
    """
    Task to generate final widget validation report.
    """
    return Task(
        description=f"""Generate a comprehensive widget validation report for domain '{domain}'.
        
        The report should include:
        1. Executive Summary
           - Total features analyzed
           - Overall widget configuration quality score (0-100)
           - Critical issues count
           - Recommended improvements count
        
        2. Critical Issues (Priority 1)
           - HISTORICAL widgets missing population behavior
           - Boolean features not using BINARY widget
           - Z-score features not using HISTORICAL widget
        
        3. Recommended Improvements (Priority 2)
           - Suboptimal widget selections
           - Missing optional enhancements
        
        4. Detailed Findings
           - Per-feature analysis with file paths
           - Specific recommendations
           - Code examples for fixes
        
        5. Quality Score Calculation
           Score based on:
           - % of features with optimal widgets (40 points)
           - % of HISTORICAL widgets with population behavior (40 points)
           - % of features with widgets defined (20 points)
        
        Format the report in clear, actionable markdown with JSON data embedded.
        """,
        agent=agent,
        expected_output="""Comprehensive markdown report with:
        - Executive summary with quality score
        - Prioritized issue list
        - Detailed findings with file locations
        - Actionable recommendations
        - Embedded JSON data for programmatic parsing
        """
    )


def create_best_practices_task(agent) -> Task:
    """
    Task to document widget best practices.
    """
    return Task(
        description="""Retrieve and document widget selection best practices.
        
        Use the 'Get Widget Best Practices' tool to get comprehensive guidelines.
        
        Present the information in a developer-friendly format with:
        - When to use each widget type
        - Required fields for each type
        - Common mistakes to avoid
        - Code examples
        """,
        agent=agent,
        expected_output="""Developer guide for widget selection including:
        - Widget type decision tree
        - Required vs optional fields
        - Validation rules
        - Common patterns and anti-patterns
        """
    )
