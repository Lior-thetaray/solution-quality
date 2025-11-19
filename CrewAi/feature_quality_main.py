#!/usr/bin/env python3
"""
Feature Quality Validation Runner
Runs the combined UI + Risk Assessment validation agent
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process, LLM, Agent, Task

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.tool_registry import get_tools_for_agent


def setup_llm():
    """Setup Azure OpenAI LLM"""
    load_dotenv()
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not api_key or not endpoint:
        raise ValueError("Azure OpenAI credentials not found in .env file")
    
    return LLM(
        model=f"azure/{deployment}",
        api_key=api_key,
        base_url=endpoint,
        api_version=api_version,
        temperature=0.1
    )


def create_feature_quality_agent(llm):
    """Create the Feature Quality Validator agent"""
    
    # Load agent instructions
    instructions_path = Path(__file__).parent.parent / "agent_instructions" / "agent_ui_validation.md"
    
    if not instructions_path.exists():
        raise FileNotFoundError(f"Agent instructions not found at {instructions_path}")
    
    instructions = instructions_path.read_text()
    
    # Extract role and goal
    import re
    role_match = re.search(r'\*\*Role\*\*:\s*(.+)', instructions)
    goal_match = re.search(r'\*\*Goal\*\*:\s*(.+)', instructions)
    
    role = role_match.group(1).strip() if role_match else "Feature Quality Validator"
    goal = goal_match.group(1).strip() if goal_match else "Validate UI and risk assessment quality"
    
    # Get tools from registry
    tools = get_tools_for_agent('feature_quality')
    
    print(f"\n📊 Creating Feature Quality Validator with {len(tools)} tools:")
    for tool in tools:
        print(f"   - {tool.__class__.__name__}")
    
    return Agent(
        role=role,
        goal=goal,
        backstory=instructions,
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_validation_task(agent, domain: str):
    """Create the validation task"""
    
    workspace_root = Path(__file__).parent.parent
    sonar_path = workspace_root / "Sonar"
    domain_path = sonar_path / "domains" / domain
    
    if not domain_path.exists():
        raise ValueError(f"Domain not found: {domain}")
    
    features_path = domain_path / "features"
    excel_path = domain_path / "risk_assessment.xlsx"
    config_path = domain_path / "config" / "core"
    
    description = f"""
Perform comprehensive Feature Quality Validation for domain: {domain}

**Part 1: UI Validation**
1. Extract feature metadata from: {features_path}
2. Validate all features against 12 UI guidelines
3. Calculate ui_quality_score (0-100)

**Part 2: Risk Assessment Alignment**
4. Read risk assessment Excel: {excel_path}
5. Validate feature implementation (files, methods, descriptions)
6. Check wrangling config alignment: {config_path}
7. Verify training notebook alignment
8. Calculate risk_assessment_score (0-100)

**Final Report**
9. Combine both validations
10. Calculate final_quality_score = (ui_score * 0.4) + (risk_assessment_score * 0.6)
11. Determine production_readiness (>=85 ready, 70-84 minor fixes, <70 major work)
12. Generate prioritized recommendations

Output comprehensive JSON report with all validation results.
"""
    
    expected_output = """
A comprehensive JSON report containing:
- ui_validation: validations per feature, summary, ui_quality_score
- risk_assessment_alignment: feature_checks, summary, risk_assessment_score
- final_quality_score: weighted combination
- production_readiness: status
- recommendations: prioritized list with effort/impact
"""
    
    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent
    )


def run_feature_quality_validation(domain: str, output_dir: str = None):
    """
    Run feature quality validation for a domain
    
    Args:
        domain: Domain name to validate (e.g., 'demo_fuib')
        output_dir: Optional output directory for report
    """
    
    print("=" * 80)
    print(f"Feature Quality Validation - {domain}")
    print("=" * 80)
    
    # Setup
    llm = setup_llm()
    agent = create_feature_quality_agent(llm)
    task = create_validation_task(agent, domain)
    
    # Create crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    
    # Run validation
    print(f"\n🚀 Starting Feature Quality Validation for {domain}...")
    print(f"   This may take several minutes...\n")
    
    start_time = datetime.now()
    
    try:
        result = crew.kickoff()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Validation completed in {duration:.1f} seconds")
        
        # Save report
        if output_dir is None:
            output_dir = Path(__file__).parent / "reports" / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{domain}"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"feature_quality_report_{domain}.json"
        
        # Parse result
        result_text = str(result)
        
        # Try to extract JSON from result
        try:
            # Look for JSON block in markdown
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                report_data = json.loads(json_match.group(1))
            else:
                # Try to parse directly
                report_data = json.loads(result_text)
        except json.JSONDecodeError:
            # If not valid JSON, wrap it
            report_data = {
                "domain": domain,
                "timestamp": datetime.now().isoformat(),
                "validation_type": "feature_quality",
                "status": "completed",
                "raw_output": result_text
            }
        
        # Save report
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_path}")
        
        # Print summary if available
        if isinstance(report_data, dict):
            if "final_quality_score" in report_data:
                print(f"\n📊 Final Quality Score: {report_data['final_quality_score']}/100")
            if "production_readiness" in report_data:
                print(f"🎯 Production Readiness: {report_data['production_readiness']}")
            
            if "ui_validation" in report_data:
                ui_score = report_data["ui_validation"].get("ui_quality_score", "N/A")
                print(f"   UI Quality Score: {ui_score}/100")
            
            if "risk_assessment_alignment" in report_data:
                risk_score = report_data["risk_assessment_alignment"].get("risk_assessment_score", "N/A")
                print(f"   Risk Assessment Score: {risk_score}/100")
        
        return report_data
        
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Feature Quality Validation")
    parser.add_argument("domain", help="Domain to validate (e.g., demo_fuib)")
    parser.add_argument("--output-dir", help="Output directory for report")
    
    args = parser.parse_args()
    
    try:
        run_feature_quality_validation(args.domain, args.output_dir)
        return 0
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
