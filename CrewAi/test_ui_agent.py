#!/usr/bin/env python3
"""
Quick test to run UI validation agent standalone
Usage: python3 test_ui_agent.py demo_fuib
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.sdlc_agents import create_agent
from tasks.sdlc_tasks import create_validation_task
from tools.tool_registry import ToolRegistry
from crewai import Crew, Process
from langchain_openai import AzureChatOpenAI

def main():
    domain = sys.argv[1] if len(sys.argv) > 1 else "demo_fuib"
    
    print(f"\n{'='*80}")
    print(f"  UI VALIDATION TEST - Domain: {domain}")
    print(f"{'='*80}\n")
    
    # Initialize LLM
    llm = AzureChatOpenAI(
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
        model_name="gpt-4o",
        temperature=0,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    )
    
    # Get tools
    registry = ToolRegistry()
    tools = registry.get_tools_for_agent("ui_validation")
    
    print(f"🔧 Tools loaded: {len(tools)}")
    for tool in tools:
        print(f"   - {tool.name}")
    
    # Create agent
    agent = create_agent("agent_ui_validation", tools, llm)
    print(f"\n🤖 Agent created: {agent.role}")
    
    # Create task
    task = create_validation_task(agent, domain, "ui_validation")
    print(f"📋 Task created\n")
    
    # Create crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    
    # Execute
    print(f"{'='*80}")
    print(f"  STARTING VALIDATION")
    print(f"{'='*80}\n")
    
    result = crew.kickoff()
    
    print(f"\n{'='*80}")
    print(f"  VALIDATION COMPLETE")
    print(f"{'='*80}\n")
    print(result)
    
    # Save report
    output_dir = Path("reports") / "ui_validation_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"ui_validation_{domain}.json"
    
    with open(output_file, 'w') as f:
        f.write(str(result))
    
    print(f"\n✅ Report saved: {output_file}")

if __name__ == "__main__":
    main()
