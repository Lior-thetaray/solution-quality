"""Main orchestration script for SDLC validation using CrewAI."""

import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process, LLM

from agents.sdlc_agents import create_agent
from tasks.sdlc_tasks import create_validation_task
from tools.code_analysis_tools import (
    PythonFeatureAnalyzerTool,
    YAMLConfigAnalyzerTool,
    DatasetAnalyzerTool,
    DAGAnalyzerTool,
    NotebookAnalyzerTool
)


def setup_environment():
    """Load environment variables and configure Azure OpenAI for CrewAI."""
    load_dotenv()
    
    # Azure OpenAI credentials
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not api_key:
        raise ValueError(
            "AZURE_OPENAI_API_KEY not found in environment. "
            "Please add it to your .env file."
        )
    if not endpoint:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT not found in environment. "
            "Please add it to your .env file (e.g., https://your-resource.openai.azure.com/)."
        )
    if not deployment:
        raise ValueError(
            "AZURE_OPENAI_DEPLOYMENT not found in environment. "
            "Please add your deployment name to your .env file."
        )
    
    # Use CrewAI's native LLM class with Azure
    return LLM(
        model=f"azure/{deployment}",
        api_key=api_key,
        base_url=endpoint,
        api_version=api_version,
        temperature=0
    )


def get_sdlc_tools():
    """Get tools for SDLC validation agent."""
    return [
        PythonFeatureAnalyzerTool(),
        YAMLConfigAnalyzerTool(),
        DatasetAnalyzerTool(),
        DAGAnalyzerTool(),
        NotebookAnalyzerTool()
    ]


def create_sdlc_crew(domain: str, llm):
    """Create and configure the SDLC validation crew.
    
    Simple pattern: 1 agent + 1 task. Agent autonomously decides how to execute.
    """
    
    # Create SDLC agent with tools
    sdlc_agent = create_agent(
        agent_name="agent_sdlc",
        tools=get_sdlc_tools(),
        llm=llm
    )
    
    # Create single validation task
    validation_task = create_validation_task(
        agent=sdlc_agent,
        domain=domain,
        agent_type="SDLC"
    )
    
    # Create crew - simple sequential execution
    crew = Crew(
        agents=[sdlc_agent],
        tasks=[validation_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew


def save_report(report: str, domain: str):
    """Save the validation report to the reports directory."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sdlc_report_{domain}_{timestamp}.json"
    filepath = reports_dir / filename
    
    # Try to parse as JSON and pretty-print
    try:
        report_json = json.loads(report)
        with open(filepath, 'w') as f:
            json.dump(report_json, f, indent=2)
    except json.JSONDecodeError:
        # If not valid JSON, save as text
        with open(filepath.with_suffix('.txt'), 'w') as f:
            f.write(report)
        filepath = filepath.with_suffix('.txt')
    
    print(f"\n{'='*80}")
    print(f"Report saved to: {filepath}")
    print(f"{'='*80}\n")
    
    return filepath


def main():
    """Main entry point for SDLC validation."""
    print("\n" + "="*80)
    print("ThetaRay Solution Quality - SDLC Validation")
    print("="*80 + "\n")
    
    # Get domain to validate
    domain = input("Enter domain name to validate (e.g., 'demo_fuib', 'default'): ").strip()
    
    if not domain:
        print("Error: Domain name cannot be empty")
        return
    
    # Check if domain exists
    domain_path = Path(f"../Sonar/domains/{domain}")
    if not domain_path.exists():
        print(f"Error: Domain '{domain}' not found at {domain_path}")
        print("\nAvailable domains:")
        domains_dir = Path("../Sonar/domains")
        if domains_dir.exists():
            for d in domains_dir.iterdir():
                if d.is_dir() and not d.name.startswith('.'):
                    print(f"  - {d.name}")
        return
    
    print(f"\nValidating domain: {domain}")
    print(f"Domain path: {domain_path}")
    print("\nInitializing AI agents...\n")
    
    try:
        # Setup
        llm = setup_environment()
        
        # Create crew
        crew = create_sdlc_crew(domain, llm)
        
        # Execute validation
        print(f"\n{'='*80}")
        print("Starting SDLC validation process...")
        print(f"{'='*80}\n")
        
        result = crew.kickoff()
        
        # Save report
        filepath = save_report(str(result), domain)
        
        # Print summary
        print("\nValidation complete!")
        print(f"Full report: {filepath}")
        
        # Try to extract quality score
        try:
            report_json = json.loads(str(result))
            if "quality_score" in report_json:
                score = report_json["quality_score"]
                print(f"\nQuality Score: {score}/100")
                
                if score >= 90:
                    print("Status: ✅ Excellent - Production ready")
                elif score >= 75:
                    print("Status: ✅ Good - Minor improvements needed")
                elif score >= 60:
                    print("Status: ⚠️  Acceptable - Several issues to address")
                else:
                    print("Status: ❌ Needs work - Major issues found")
        except:
            pass
    
    except Exception as e:
        print(f"\n❌ Error during validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
