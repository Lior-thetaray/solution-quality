"""Generic agent factory for creating validation agents from instruction files.

This module provides a simple pattern for creating agents:
- Each agent loads its instructions from agent_instructions/{agent_name}.md
- Full instruction file is passed as agent backstory
- Agent receives specialized tools based on its purpose
"""

import re
from pathlib import Path
from crewai import Agent


def create_agent(agent_name: str, tools: list, llm):
    """Create a validation agent from its instruction file.
    
    Args:
        agent_name: Name of agent (e.g., 'agent_sdlc', 'agent_security')
        tools: List of BaseTool instances for this agent
        llm: Language model instance (AzureChatOpenAI or ChatOpenAI)
        
    Returns:
        Agent configured with instructions and tools
    """
    # Load instruction file
    instructions_path = Path(__file__).parent.parent.parent / "agent_instructions" / f"{agent_name}.md"
    
    if not instructions_path.exists():
        raise FileNotFoundError(
            f"Agent instructions not found at {instructions_path}. "
            f"Please ensure agent_instructions/{agent_name}.md exists."
        )
    
    instructions = instructions_path.read_text()
    
    # Extract role and goal using simple regex
    role_match = re.search(r'\*\*Role\*\*:\s*(.+)', instructions)
    goal_match = re.search(r'\*\*Goal\*\*:\s*(.+)', instructions)
    
    role = role_match.group(1).strip() if role_match else f"{agent_name.replace('agent_', '').upper()} Specialist"
    goal = goal_match.group(1).strip() if goal_match else f"Validate according to {agent_name} requirements"
    
    # Create agent - full instructions as backstory
    return Agent(
        role=role,
        goal=goal,
        backstory=instructions,  # Full .md file provides context
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
