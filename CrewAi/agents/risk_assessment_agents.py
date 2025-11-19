"""
Risk Assessment Agents
Agents for validating solution alignment with risk assessment requirements
"""

from crewai import Agent
from typing import List


def create_risk_assessment_validator_agent(tools: List, llm) -> Agent:
    """
    Creates an agent to validate risk assessment alignment
    """
    return Agent(
        role='Risk Assessment Alignment Validator',
        goal='Validate that the solution implementation fully aligns with the risk assessment requirements',
        backstory="""You are an expert compliance and QA specialist who ensures that AML/fraud detection 
        solutions are implemented exactly as specified in the risk assessment documentation. You meticulously 
        verify that every feature defined in the risk assessment is properly implemented, configured, and 
        used in model training. You check for:
        - Feature implementation completeness
        - Correct feature descriptions and logic
        - Proper configuration in wrangling YAML
        - Correct train/forensic flag settings
        - Alignment between risk assessment and actual code
        
        You provide detailed validation reports with specific recommendations for fixing any misalignments.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools
    )


def create_feature_logic_validator_agent(tools: List, llm) -> Agent:
    """
    Creates an agent to validate feature implementation logic
    """
    return Agent(
        role='Feature Logic Validator',
        goal='Validate that each feature is implemented with correct logic matching its risk assessment description',
        backstory="""You are a senior ML engineer and financial crime expert who understands the intent 
        behind each risk indicator. You validate that:
        - Feature aggregation logic matches the described risk measurement
        - SQL/PySpark transformations correctly implement the feature
        - Trace queries properly filter transactions for investigation
        - Output fields are correctly defined with proper metadata
        - Features use appropriate columns and transformations
        
        You can read Python code and understand PySpark aggregations, window functions, and feature engineering 
        patterns. You compare implementation against expected behavior described in risk assessments.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools
    )


def create_config_alignment_agent(tools: List, llm) -> Agent:
    """
    Creates an agent to validate YAML configuration alignment
    """
    return Agent(
        role='Configuration Alignment Specialist',
        goal='Ensure wrangling configuration perfectly aligns with risk assessment feature requirements',
        backstory="""You are a configuration management expert who ensures that YAML configurations 
        correctly reflect the risk assessment specifications. You validate:
        - All training features have train: true
        - All forensic features have train: false
        - All features are marked as active: true
        - No missing features from risk assessment
        - No extra features that shouldn't be there
        - Correct version configurations
        
        You understand the relationship between risk assessment, feature implementation, and YAML configuration.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools
    )
