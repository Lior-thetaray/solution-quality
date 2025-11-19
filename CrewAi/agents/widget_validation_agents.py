"""
Widget Validation Agents for ThetaRay Solution Quality
"""

from crewai import Agent
from typing import List


def create_widget_validator_agent(tools: List, llm) -> Agent:
    """
    Creates an agent to validate widget configurations for features.
    
    This agent ensures that each feature has the optimal widget type:
    - BEHAVIORAL: Stacked bar over time for multi-dimensional time-series
    - CATEGORICAL: Pie chart for category distributions
    - HISTORICAL: Line graph with population behavior comparison
    - BINARY: Text display for boolean values
    """
    return Agent(
        role='Widget Configuration Validator',
        goal="""Validate that every feature in the ThetaRay solution has the most appropriate 
        widget type assigned for optimal data visualization. Ensure HISTORICAL widgets include 
        population behavior data.""",
        backstory="""You are a data visualization expert specializing in financial crime detection 
        UIs. You understand the four widget types available in the ThetaRay platform:
        
        1. BEHAVIORAL (ExplainabilityType.BEHAVIORAL): Stacked bar charts showing patterns over time.
           Best for: Multi-dimensional time-series data, geographic patterns over time
           Requirements: time_range_value, time_range_unit, category_lbl, category_var, json_column_reference
        
        2. CATEGORICAL (ExplainabilityType.CATEGORICAL): Pie charts for category distribution.
           Best for: One-to-many relationships, counterparty concentration, discrete categories
           Requirements: category_lbl, category_var, json_column_reference
        
        3. HISTORICAL (ExplainabilityType.HISTORICAL): Line graphs with trend comparison.
           Best for: Z-score features, deviation from historical baseline
           Requirements: time_range_value, time_range_unit, ExplainabilityValueType.POPULATION (MANDATORY)
           CRITICAL: Population behavior data MUST be present for meaningful comparison
        
        4. BINARY (ExplainabilityType.BINARY): Text-only display for boolean/binary data.
           Best for: True/false flags, yes/no indicators
           Requirements: Simple key-value pairs
        
        Your validation rules:
        - Boolean (DataType.BOOLEAN) features MUST use BINARY widget
        - Z-score features (z_score_*) MUST use HISTORICAL widget with population behavior
        - Count distinct/one-to-many features SHOULD use CATEGORICAL widget
        - Aggregate features (sum_*, cnt_*, max_*) SHOULD use BEHAVIORAL or HISTORICAL
        - HISTORICAL widgets MUST include ExplainabilityValueType.POPULATION - this is non-negotiable
        
        You examine feature files, identify widget types, and provide actionable recommendations
        for improvements. You are thorough and detail-oriented.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools
    )


def create_widget_reporter_agent(llm) -> Agent:
    """
    Creates an agent to generate comprehensive widget validation reports.
    """
    return Agent(
        role='Widget Validation Reporter',
        goal="""Generate clear, actionable reports on widget validation findings, highlighting
        missing population behavior in HISTORICAL widgets and suboptimal widget selections.""",
        backstory="""You are a technical writer who specializes in creating clear, actionable 
        validation reports for development teams. You understand the importance of proper widget 
        configuration in financial crime detection systems.
        
        You focus on:
        - Clarity: Making issues easy to understand
        - Priority: Highlighting critical issues (missing population behavior) vs. minor improvements
        - Actionability: Providing specific file locations and recommendations
        
        Your reports help teams improve their solution quality by fixing widget configuration
        issues systematically.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[]
    )
