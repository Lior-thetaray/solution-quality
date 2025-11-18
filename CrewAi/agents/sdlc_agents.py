"""Agent definitions for the SDLC validation crew.

All agent role definitions are now loaded from agent_instructions/agent_sdlc.md
This ensures a single source of truth for both the agent's role and validation rules.
"""

from crewai import Agent
from typing import List, Optional, Dict
from tools.code_analysis_tools import (
    PythonFeatureAnalyzerTool,
    YAMLConfigAnalyzerTool,
    DatasetAnalyzerTool,
    DAGAnalyzerTool,
    NotebookAnalyzerTool
)
from tools.instruction_loader import (
    AgentInstructionLoaderTool,
    SDLCValidationRulesExtractorTool
)
from pathlib import Path
import re


def parse_agent_role_from_instructions() -> Dict[str, str]:
    """Parse agent role, goal, and backstory from agent_instructions/agent_sdlc.md"""
    instructions_path = Path(__file__).parent.parent.parent / "agent_instructions" / "agent_sdlc.md"
    
    with open(instructions_path, 'r') as f:
        content = f.read()
    
    # Extract role
    role_match = re.search(r'\*\*Role:\*\*\s*(.+?)(?=\n\n|\*\*)', content, re.DOTALL)
    role = role_match.group(1).strip() if role_match else "ThetaRay SDLC Quality Assurance Validator"
    
    # Extract goal
    goal_match = re.search(r'\*\*Goal:\*\*\s*(.+?)(?=\n\n|\*\*)', content, re.DOTALL)
    goal = goal_match.group(1).strip() if goal_match else "Validate ThetaRay solutions for production readiness"
    
    # Extract backstory
    backstory_match = re.search(r'\*\*Backstory:\*\*\s*(.+?)(?=\n\n|\*\*)', content, re.DOTALL)
    backstory = backstory_match.group(1).strip() if backstory_match else "Expert QA engineer for ThetaRay platform"
    
    return {
        "role": role,
        "goal": goal,
        "backstory": backstory
    }


def create_sdlc_validator_agent(llm) -> Agent:
    """Create the SDLC Validator agent.
    
    Role, goal, and backstory are dynamically loaded from agent_instructions/agent_sdlc.md
    which serves as the single source of truth for validation rules and agent behavior.
    """
    agent_config = parse_agent_role_from_instructions()
    
    return Agent(
        role=agent_config["role"],
        goal=agent_config["goal"],
        backstory=agent_config["backstory"],
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[
            AgentInstructionLoaderTool(),
            SDLCValidationRulesExtractorTool(),
            PythonFeatureAnalyzerTool(),
            YAMLConfigAnalyzerTool(),
            DatasetAnalyzerTool(),
            DAGAnalyzerTool(),
            NotebookAnalyzerTool()
        ]
    )
