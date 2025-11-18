"""
Alert Validation Agent Runner
Uses CrewAI framework to validate alert quality from CSV datasets
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from agents.sdlc_agents import create_agent
from tasks.sdlc_tasks import create_validation_task
from tools.csv_tools import CSVDatasetReaderTool, CSVListTool
from tools.alert_analysis_tools import JoinDatasetsTool, AggregateDatasetTool, CrossTableAnalysisTool


def setup_environment():
    """Load environment variables and create LLM"""
    load_dotenv()
    
    # Azure OpenAI configuration
    llm = LLM(
        model="azure/gpt-4o",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    
    return llm


def get_alert_tools():
    """Get tools for alert validation agent"""
    return [
        CSVListTool(),
        CSVDatasetReaderTool(),
        JoinDatasetsTool(),
        AggregateDatasetTool(),
        CrossTableAnalysisTool(),
    ]


def create_alert_crew(llm):
    """Create alert validation crew with agent and task"""
    
    # Get tools
    tools = get_alert_tools()
    
    # Create agent using generic factory
    alert_agent = create_agent(
        agent_name="agent_alert_validation",
        tools=tools,
        llm=llm
    )
    
    # Create task
    alert_task = create_validation_task(
        agent=alert_agent,
        domain="alert_data",  # CSV data in data/ directory
        agent_type="alert_validation"
    )
    
    # Create crew
    crew = Crew(
        agents=[alert_agent],
        tasks=[alert_task],
        verbose=True
    )
    
    return crew


def save_report(result, output_dir="reports"):
    """Save validation report to JSON file"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"alert_validation_{timestamp}.json"
    filepath = output_path / filename
    
    # Extract report from crew result
    report_content = result.raw if hasattr(result, 'raw') else str(result)
    
    # Try to parse as JSON
    try:
        if isinstance(report_content, str):
            report_data = json.loads(report_content)
        else:
            report_data = report_content
    except json.JSONDecodeError:
        report_data = {
            "raw_output": report_content,
            "timestamp": datetime.now().isoformat()
        }
    
    with open(filepath, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n💾 Report saved: {filepath}")
    return filepath


def main():
    """Main execution"""
    print("=" * 60)
    print("ALERT QUALITY VALIDATION AGENT")
    print("=" * 60)
    
    # Setup
    llm = setup_environment()
    
    # Create and run crew
    crew = create_alert_crew(llm)
    
    print("\n🚀 Starting alert validation...\n")
    result = crew.kickoff()
    
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    
    # Save report
    save_report(result)
    
    print("\n✅ Alert validation complete!")


if __name__ == "__main__":
    main()
