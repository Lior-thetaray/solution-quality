"""
Multi-Agent Validation Runner
Unified main file to run SDLC, Alert, and other validation agents
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from crewai import Crew, Process, LLM

from agents.sdlc_agents import create_agent
from tasks.sdlc_tasks import create_validation_task
from tools.tool_registry import get_tool_registry, get_tools_for_agent


def setup_environment():
    """Load environment variables and configure Azure OpenAI for CrewAI."""
    load_dotenv()
    
    # Azure OpenAI credentials
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not api_key or not endpoint or not deployment:
        raise ValueError("Azure OpenAI credentials not found in .env file")
    
    # Use CrewAI's native LLM class with Azure
    return LLM(
        model=f"azure/{deployment}",
        api_key=api_key,
        base_url=endpoint,
        api_version=api_version,
        temperature=0
    )


def get_agent_tools(agent_type: str) -> List:
    """Get tools for specific agent type using the registry"""
    return get_tools_for_agent(agent_type)


def create_crew(agent_type: str, domain: str, llm) -> Crew:
    """Create a crew for the specified agent type"""
    
    # Get appropriate tools
    tools = get_agent_tools(agent_type)
    
    # Create agent using generic factory
    agent = create_agent(
        agent_name=f"agent_{agent_type}",
        tools=tools,
        llm=llm
    )
    
    # Create task
    task = create_validation_task(
        agent=agent,
        domain=domain,
        agent_type=agent_type.upper()
    )
    
    # Create crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew


def save_report(result, agent_type: str, domain: str, output_dir="reports") -> str:
    """Save validation report to JSON file"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{agent_type}_report_{domain}_{timestamp}.json"
    filepath = output_path / filename
    
    # Extract report from crew result
    report_content = str(result)
    
    # Try to parse as JSON
    try:
        report_data = json.loads(report_content)
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)
    except json.JSONDecodeError:
        # Save as text if not valid JSON
        with open(filepath.with_suffix('.txt'), 'w') as f:
            f.write(report_content)
        filepath = filepath.with_suffix('.txt')
    
    print(f"\n💾 Report saved: {filepath}")
    return str(filepath)


def run_agents(agent_types: List[str], domain: str, llm) -> Dict[str, Any]:
    """Run multiple agents and collect results"""
    results = {}
    
    for agent_type in agent_types:
        print("\n" + "=" * 80)
        print(f"RUNNING {agent_type.upper().replace('_', ' ')} AGENT")
        print("=" * 80)
        
        try:
            # Create and run crew
            crew = create_crew(agent_type, domain, llm)
            
            print(f"\n🚀 Starting {agent_type} validation for: {domain}\n")
            result = crew.kickoff()
            
            # Save report
            report_path = save_report(result, agent_type, domain)
            
            results[agent_type] = {
                "status": "success",
                "report_path": report_path,
                "result": str(result)
            }
            
            print(f"\n✅ {agent_type} validation complete!")
            
        except Exception as e:
            print(f"\n❌ Error running {agent_type}: {str(e)}")
            results[agent_type] = {
                "status": "error",
                "error": str(e)
            }
    
    return results


def print_summary(results: Dict[str, Any], agent_types: List[str]):
    """Print summary of all agent results"""
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    for agent_type, result in results.items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"\n{status_icon} {agent_type.upper().replace('_', ' ')}:")
        
        if result["status"] == "success":
            print(f"   Report: {result['report_path']}")
            
            # Try to extract quality score
            try:
                report_data = json.loads(result['result'])
                if "quality_score" in report_data:
                    score = report_data["quality_score"]
                    print(f"   Quality Score: {score}/100")
            except:
                pass
        else:
            print(f"   Error: {result['error']}")
    
    # Show tool usage statistics
    if len(agent_types) > 1:
        print("\n" + "-" * 80)
        print("TOOL USAGE OPTIMIZATION")
        print("-" * 80)
        
        registry = get_tool_registry()
        stats = registry.get_tool_usage_stats(agent_types)
        
        print(f"\nTotal tools in registry: {stats['total_tools']}")
        print(f"Tools used by selected agents: {stats['total_tools_used']}")
        
        if stats['shared_tools']:
            print(f"\n🔄 Shared tools (reused across agents): {len(stats['shared_tools'])}")
            for tool in stats['shared_tools']:
                print(f"   • {tool}")
            print(f"\n💡 Memory savings: {len(stats['shared_tools'])} tool instances reused")
        
        print(f"\nTools per agent:")
        for agent_type, info in stats['tools_by_agent'].items():
            print(f"  {agent_type}: {info['count']} tools")
            if agent_type in stats['unique_tools_per_agent']:
                unique = stats['unique_tools_per_agent'][agent_type]
                if unique:
                    print(f"    Unique to {agent_type}: {', '.join(unique)}")
    
    print("\n" + "=" * 80)


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("THETARAY MULTI-AGENT VALIDATION SYSTEM")
    print("=" * 80)
    
    # Get configuration from user
    print("\nAvailable agents:")
    print("  1. sdlc - Code quality and solution structure validation")
    print("  2. alert_validation - Alert quality and data validation")
    print("  3. all - Run all agents")
    
    agent_choice = input("\nSelect agents (e.g., '1', '2', '1,2', or 'all'): ").strip()
    
    # Parse agent selection
    if agent_choice == "all" or agent_choice == "3":
        agent_types = ["sdlc", "alert_validation"]
    else:
        agent_map = {"1": "sdlc", "2": "alert_validation"}
        selected = [agent_map.get(choice.strip()) for choice in agent_choice.split(",")]
        agent_types = [a for a in selected if a is not None]
    
    if not agent_types:
        print("❌ No valid agents selected")
        return 1
    
    # Get domain/target
    if "sdlc" in agent_types:
        domain = input("\nEnter domain to validate (e.g., demo_fuib): ").strip()
        
        # Check if domain exists
        if domain:
            domain_path = Path(f"../Sonar/domains/{domain}")
            if not domain_path.exists():
                print(f"⚠️  Warning: Domain '{domain}' not found at {domain_path}")
                proceed = input("Continue anyway? (y/n): ").strip().lower()
                if proceed != 'y':
                    return 1
    else:
        domain = input("\nEnter target name (e.g., alert_data): ").strip() or "alert_data"
    
    if not domain:
        print("❌ Domain/target name is required")
        return 1
    
    try:
        # Setup
        llm = setup_environment()
        
        # Run selected agents
        print(f"\n🎯 Running agents: {', '.join(agent_types)}")
        print(f"🎯 Target: {domain}")
        
        results = run_agents(agent_types, domain, llm)
        
        # Print summary
        print_summary(results, agent_types)
        
        print("\n✅ All validations complete!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
