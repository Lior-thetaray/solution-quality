"""
Risk Assessment Alignment Main Script
Validates solution implementation against risk assessment requirements
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from crewai import Crew, Process
from langchain_openai import AzureChatOpenAI

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.risk_assessment_agents import (
    create_risk_assessment_validator_agent,
    create_feature_logic_validator_agent,
    create_config_alignment_agent
)
from tasks.risk_assessment_tasks import (
    create_risk_assessment_validation_task,
    create_feature_logic_validation_task,
    create_config_alignment_task
)
from tools.risk_assessment_tools import (
    ExcelReaderTool,
    FeatureImplementationValidatorTool,
    WranglingConfigValidatorTool,
    TrainingNotebookValidatorTool,
    RiskAssessmentAlignmentReportTool
)


def setup_llm():
    """Setup Azure OpenAI LLM"""
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4o",
        temperature=0.1
    )


def run_risk_assessment_validation(domain: str, excel_path: str = None):
    """
    Run risk assessment alignment validation for a domain
    
    Args:
        domain: Domain name (e.g., 'demo_fuib')
        excel_path: Path to risk assessment Excel file (optional, will use default if not provided)
    """
    
    # Set default Excel path if not provided
    if excel_path is None:
        excel_path = f"Sonar/domains/{domain}/risk_assessment.xlsx"
    
    # Validate inputs
    if not os.path.exists(excel_path):
        print(f"❌ Error: Risk assessment file not found at {excel_path}")
        return
    
    print("=" * 80)
    print("RISK ASSESSMENT ALIGNMENT VALIDATION")
    print("=" * 80)
    print(f"Domain: {domain}")
    print(f"Risk Assessment: {excel_path}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Setup LLM
    llm = setup_llm()
    
    # Initialize tools
    tools = [
        ExcelReaderTool(),
        FeatureImplementationValidatorTool(),
        WranglingConfigValidatorTool(),
        TrainingNotebookValidatorTool(),
        RiskAssessmentAlignmentReportTool()
    ]
    
    # Create agents
    alignment_validator = create_risk_assessment_validator_agent(tools, llm)
    logic_validator = create_feature_logic_validator_agent(tools, llm)
    config_validator = create_config_alignment_agent(tools, llm)
    
    # Create tasks
    alignment_task = create_risk_assessment_validation_task(
        alignment_validator, 
        domain, 
        excel_path
    )
    
    config_task = create_config_alignment_task(
        config_validator,
        domain
    )
    
    # Create crew
    crew = Crew(
        agents=[alignment_validator, config_validator],
        tasks=[alignment_task, config_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Run validation
    print("\n🚀 Starting Risk Assessment Alignment Validation...\n")
    
    try:
        result = crew.kickoff()
        
        # Save report
        report_dir = Path("CrewAi/reports")
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"risk_assessment_alignment_{domain}_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("RISK ASSESSMENT ALIGNMENT VALIDATION REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Domain: {domain}\n")
            f.write(f"Risk Assessment: {excel_path}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            f.write(str(result))
        
        print("\n" + "=" * 80)
        print("✅ VALIDATION COMPLETE")
        print("=" * 80)
        print(f"Report saved to: {report_file}")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error during validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate risk assessment alignment")
    parser.add_argument("domain", help="Domain name (e.g., demo_fuib)")
    parser.add_argument("--excel", "-e", help="Path to risk assessment Excel file", default=None)
    
    args = parser.parse_args()
    
    run_risk_assessment_validation(args.domain, args.excel)


if __name__ == "__main__":
    main()
