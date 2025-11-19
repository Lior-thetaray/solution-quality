#!/usr/bin/env python3
"""
Widget Validation Main Script
Validates widget configurations for ThetaRay solution features
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

from crewai import Crew
from langchain_openai import AzureChatOpenAI

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from agents.widget_validation_agents import create_widget_validator_agent, create_widget_reporter_agent
from tasks.widget_validation_tasks import (
    create_widget_analysis_task,
    create_widget_validation_report_task
)
from tools.widget_validation_tools import (
    AnalyzeFeatureWidgetsTool,
    GetWidgetBestPracticesTool,
    CheckFeatureWidgetRequirementsTool
)


def setup_llm():
    """Setup Azure OpenAI LLM"""
    return AzureChatOpenAI(
        deployment_name="gpt-4o",
        model="gpt-4o",
        api_version="2024-08-01-preview",
        temperature=0.1
    )


def run_widget_validation(domain: str, output_dir: str = "reports"):
    """
    Run widget validation for a domain.
    
    Args:
        domain: Domain name to validate (e.g., 'demo_fuib')
        output_dir: Directory to save reports
    """
    print(f"\n{'='*80}")
    print(f"Widget Validation for Domain: {domain}")
    print(f"{'='*80}\n")
    
    # Setup LLM
    llm = setup_llm()
    
    # Create tools list
    tools = [
        AnalyzeFeatureWidgetsTool(),
        GetWidgetBestPracticesTool(),
        CheckFeatureWidgetRequirementsTool()
    ]
    
    # Create agents
    print("Creating agents...")
    validator_agent = create_widget_validator_agent(tools, llm)
    reporter_agent = create_widget_reporter_agent(llm)
    
    # Create tasks
    print("Creating tasks...")
    analysis_task = create_widget_analysis_task(validator_agent, domain)
    report_task = create_widget_validation_report_task(reporter_agent, domain)
    
    # Create crew
    print("Assembling crew...")
    crew = Crew(
        agents=[validator_agent, reporter_agent],
        tasks=[analysis_task, report_task],
        verbose=True
    )
    
    # Execute
    print(f"\nStarting widget validation for domain '{domain}'...")
    print("-" * 80)
    
    result = crew.kickoff()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(output_dir) / f"widget_validation_{domain}_{timestamp}"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Save main report
    report_file = report_dir / "widget_validation_report.md"
    report_file.write_text(str(result))
    print(f"\nReport saved to: {report_file}")
    
    # Also run the tool directly and save raw JSON
    print("\nGenerating raw JSON analysis...")
    analyze_tool = AnalyzeFeatureWidgetsTool()
    raw_analysis = analyze_tool._run(domain)
    raw_json_file = report_dir / "widget_analysis_raw.json"
    raw_json_file.write_text(raw_analysis)
    print(f"Raw JSON saved to: {raw_json_file}")
    
    # Parse and display summary
    try:
        analysis_data = json.loads(raw_analysis)
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        summary = analysis_data.get("summary", {})
        print(f"\nTotal Features: {summary.get('total_features', 0)}")
        print(f"With Widgets: {summary.get('with_widgets', 0)}")
        print(f"Without Widgets: {summary.get('without_widgets', 0)}")
        print(f"Optimal Widgets: {summary.get('optimal_widgets', 0)}")
        print(f"Suboptimal Widgets: {summary.get('suboptimal_widgets', 0)}")
        print(f"HISTORICAL Missing Population: {summary.get('missing_population_in_historical', 0)}")
        
        # Calculate quality score
        total = summary.get('total_features', 1)
        with_widgets = summary.get('with_widgets', 0)
        optimal = summary.get('optimal_widgets', 0)
        missing_pop = summary.get('missing_population_in_historical', 0)
        
        widget_coverage_score = (with_widgets / total * 20) if total > 0 else 0
        optimal_score = (optimal / with_widgets * 40) if with_widgets > 0 else 0
        population_score = ((with_widgets - missing_pop) / with_widgets * 40) if with_widgets > 0 else 0
        
        quality_score = widget_coverage_score + optimal_score + population_score
        
        print(f"\n{'='*80}")
        print(f"QUALITY SCORE: {quality_score:.1f}/100")
        print(f"{'='*80}")
        print(f"  Widget Coverage: {widget_coverage_score:.1f}/20")
        print(f"  Optimal Selection: {optimal_score:.1f}/40")
        print(f"  Population Behavior: {population_score:.1f}/40")
        
        # Show critical issues
        errors = analysis_data.get("validation_errors", [])
        critical_errors = [e for e in errors if e.get("severity") == "high"]
        
        if critical_errors:
            print(f"\n{'='*80}")
            print(f"CRITICAL ISSUES ({len(critical_errors)})")
            print(f"{'='*80}")
            for error in critical_errors[:5]:  # Show first 5
                print(f"\n  Feature: {error.get('feature', 'unknown')}")
                print(f"  Issue: {error.get('issue', 'unknown')}")
                print(f"  File: {error.get('file', 'unknown')}")
        
    except json.JSONDecodeError:
        print("\nCould not parse JSON for summary display")
    
    print(f"\n{'='*80}")
    print(f"Widget validation complete! Reports saved to: {report_dir}")
    print(f"{'='*80}\n")
    
    return report_dir


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate widget configurations in ThetaRay solutions"
    )
    parser.add_argument(
        "domain",
        help="Domain to validate (e.g., demo_fuib)"
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Output directory for reports (default: reports)"
    )
    
    args = parser.parse_args()
    
    try:
        run_widget_validation(args.domain, args.output_dir)
    except Exception as e:
        print(f"\n❌ Error during widget validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
