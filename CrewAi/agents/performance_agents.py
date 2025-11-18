"""Performance testing agent factory following the same pattern as SDLC agents.

Creates performance validation agents from instruction files with Playwright tools.
"""

from .sdlc_agents import create_agent
from ..tools import (
    PlaywrightPerformanceTool
)


def create_performance_agent(llm):
    """Create performance testing agent with Playwright tools.
    
    Args:
        llm: Language model instance (AzureChatOpenAI or ChatOpenAI)
        
    Returns:
        Agent configured for performance testing with Playwright tools
    """
    performance_tools = [
        PlaywrightPerformanceTool()
    ]
    
    return create_agent(
        agent_name="agent_performance",  # Loads agent_instructions/agent_performance.md
        tools=performance_tools,
        llm=llm
    )


def get_performance_tools():
    """Get list of performance testing tools.
    
    Returns:
        List containing the single Playwright performance testing tool
    """
    return [
        PlaywrightPerformanceTool()
    ]