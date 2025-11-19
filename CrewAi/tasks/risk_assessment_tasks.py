"""
Risk Assessment Tasks
Tasks for validating solution alignment with risk assessment
"""

from typing import List
from crewai import Task
from agents.risk_assessment_agents import (
    create_risk_assessment_validator_agent,
    create_feature_logic_validator_agent,
    create_config_alignment_agent
)


def create_risk_assessment_validation_task(agent, domain: str, excel_path: str) -> Task:
    """Task to validate overall risk assessment alignment"""
    return Task(
        description=f"""
        Perform comprehensive validation of risk assessment alignment for domain '{domain}'.
        
        Steps:
        1. Read the risk assessment Excel file at: {excel_path}
        2. Extract all training and forensic features
        3. For each feature, validate:
           - Feature implementation file exists
           - Feature is in wrangling.yaml with correct train flag
           - Feature appears in training notebook if it's a training feature
        4. Generate alignment score and detailed report
        
        Expected Output:
        - List of all features from risk assessment
        - Implementation status for each feature
        - Configuration alignment status
        - Overall alignment score (0-100)
        - Specific recommendations for fixing issues
        """,
        agent=agent,
        expected_output="""A comprehensive validation report showing:
        1. Total features in risk assessment
        2. Implementation status (implemented/missing)
        3. Configuration alignment (correct train flags)
        4. Alignment score percentage
        5. List of issues and recommendations"""
    )


def create_feature_logic_validation_task(agent, domain: str, feature_list: List[str]) -> Task:
    """Task to validate feature implementation logic"""
    features_str = ", ".join(feature_list) if feature_list else "all features from risk assessment"
    
    return Task(
        description=f"""
        Validate the implementation logic of features: {features_str} in domain '{domain}'.
        
        For each feature, check:
        1. Feature class inherits from AggFeature
        2. Has required methods: identifier, version, description, get_agg_exprs, output_fields
        3. Description property matches risk assessment intent
        4. Aggregation logic (get_agg_exprs) correctly implements the risk measurement
        5. Output fields are properly defined with metadata
        6. Trace query exists for training features
        7. Required columns are appropriate for the feature logic
        
        Compare actual implementation against expected behavior from risk assessment.
        
        Expected Output:
        For each feature, report:
        - Implementation correctness (pass/fail)
        - Logic validation (does it match the risk description?)
        - Missing components
        - Recommendations for fixes
        """,
        agent=agent,
        expected_output="""Detailed feature-by-feature validation report showing:
        1. Feature name and risk assessment description
        2. Implementation status for each required component
        3. Logic validation results
        4. Specific code issues found
        5. Recommendations for each feature"""
    )


def create_config_alignment_task(agent, domain: str) -> Task:
    """Task to validate wrangling configuration alignment"""
    return Task(
        description=f"""
        Validate the wrangling.yaml configuration alignment for domain '{domain}'.
        
        Steps:
        1. Read wrangling.yaml configuration
        2. Extract all requested_features with their train flags
        3. Compare against risk assessment requirements
        4. Identify:
           - Training features with incorrect train: false
           - Forensic features with incorrect train: true
           - Missing features not in config
           - Inactive features that should be active
        5. Generate configuration fix recommendations
        
        Expected Output:
        - List of all features in config with their train flags
        - Misalignment issues (wrong train flags)
        - Missing features
        - Recommended YAML changes
        """,
        agent=agent,
        expected_output="""Configuration validation report with:
        1. Current config summary (total features, train/forensic split)
        2. List of misaligned features with current vs expected flags
        3. Missing features not in config
        4. Specific YAML fix recommendations
        5. Overall config alignment score"""
    )
