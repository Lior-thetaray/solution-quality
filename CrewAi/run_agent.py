#!/usr/bin/env python3
"""
Unified Agent Runner
Consistent structure for running all validation agents
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process, LLM, Task

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.sdlc_agents import create_agent
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


def create_validation_task(agent, domain: str, agent_type: str):
    """Create generic validation task"""
    
    workspace_root = Path(__file__).parent.parent
    domain_path = workspace_root / "Sonar" / "domains" / domain
    
    if not domain_path.exists():
        raise ValueError(f"Domain not found: {domain}")
    
    # Task descriptions by agent type
    task_configs = {
        "sdlc": {
            "description": f"Perform SDLC validation for domain: {domain}. Validate: features, datasets, evaluation flows, risks, DAGs, notebooks.",
            "expected_output": "JSON report with validations, summary, quality_score (0-100), recommendations"
        },
        "alert_validation": {
            "description": f"Validate alert publication quality for domain: {domain}. Check: alert counts, duplicates, cross-table consistency, monthly trends, consolidation effectiveness.",
            "expected_output": "JSON report with alert_validations, monthly_analysis, quality_score (0-100), consolidation_metrics"
        },
        "widget_validation": {
            "description": f"Validate widget configurations for domain: {domain}. Check: widget types match feature types, HISTORICAL widgets have population behavior, boolean features use BINARY widgets.",
            "expected_output": "JSON report with widget_validations, summary, quality_score (0-100), critical_issues, recommendations"
        },
        "feature_quality": {
            "description": f"Validate feature quality for domain: {domain}. Part 1: UI validation (12 guidelines). Part 2: Risk assessment alignment (Excel vs implementation).",
            "expected_output": "JSON report with ui_validation, risk_assessment_alignment, final_quality_score (0-100), production_readiness, recommendations"
        }
    }
    
    config = task_configs.get(agent_type)
    if not config:
        # Generic fallback
        config = {
            "description": f"Perform {agent_type} validation for domain: {domain}",
            "expected_output": "JSON report with validation results"
        }
    
    return Task(
        description=config["description"],
        expected_output=config["expected_output"],
        agent=agent
    )


def run_validation(agent_type: str, domain: str, output_dir: str = None):
    """
    Run validation for specified agent type
    
    Args:
        agent_type: Type of agent ('sdlc', 'alert_validation', 'widget_validation', 'feature_quality')
        domain: Domain name to validate (e.g., 'demo_fuib')
        output_dir: Optional output directory for report
    """
    
    print("=" * 80)
    print(f"{agent_type.upper().replace('_', ' ')} Validation - {domain}")
    print("=" * 80)
    
    # Setup
    llm = setup_llm()
    
    # Get tools from registry
    tools = get_tools_for_agent(agent_type)
    print(f"\n📊 Agent has {len(tools)} tools available")
    
    # Create agent using generic factory
    agent = create_agent(
        agent_name=f"agent_{agent_type}",
        tools=tools,
        llm=llm
    )
    
    # Create task
    task = create_validation_task(agent, domain, agent_type)
    
    # Create crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    
    # Run validation
    print(f"\n🚀 Starting {agent_type} validation for {domain}...")
    print(f"   This may take several minutes...\n")
    
    start_time = datetime.now()
    
    try:
        result = crew.kickoff()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Validation completed in {duration:.1f} seconds")
        
        # Determine output directory
        if output_dir is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path(__file__).parent / "reports" / f"run_{timestamp}_{domain}"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"{agent_type}_report_{domain}.json"
        
        # Parse result
        result_text = str(result)
        
        # Try to extract JSON from result
        try:
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                report_data = json.loads(json_match.group(1))
            else:
                report_data = json.loads(result_text)
        except json.JSONDecodeError:
            # If not valid JSON, wrap it
            report_data = {
                "domain": domain,
                "timestamp": datetime.now().isoformat(),
                "validation_type": agent_type,
                "status": "completed",
                "raw_output": result_text
            }
        
        # Save report
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_path}")
        
        # Print summary
        if isinstance(report_data, dict):
            if "quality_score" in report_data:
                print(f"\n📊 Quality Score: {report_data['quality_score']}/100")
            if "final_quality_score" in report_data:
                print(f"📊 Final Quality Score: {report_data['final_quality_score']}/100")
            if "production_readiness" in report_data:
                print(f"🎯 Production Readiness: {report_data['production_readiness']}")
        
        return report_path
        
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description="Run ThetaRay Validation Agents")
    parser.add_argument(
        "agent_type",
        choices=["sdlc", "alert_validation", "widget_validation", "feature_quality", "all"],
        help="Type of validation to run"
    )
    parser.add_argument("domain", help="Domain to validate (e.g., demo_fuib)")
    parser.add_argument("--output-dir", help="Output directory for reports")
    
    args = parser.parse_args()
    
    try:
        if args.agent_type == "all":
            # Run all agents sequentially
            agent_types = ["sdlc", "widget_validation", "feature_quality"]
            # Note: alert_validation excluded due to rate limit issues
            
            print(f"\n🎯 Running ALL validation agents for {args.domain}")
            print("=" * 80)
            
            reports = {}
            for agent_type in agent_types:
                try:
                    report_path = run_validation(agent_type, args.domain, args.output_dir)
                    reports[agent_type] = str(report_path)
                    print(f"\n✅ {agent_type} completed\n")
                except Exception as e:
                    print(f"\n❌ {agent_type} failed: {e}\n")
                    reports[agent_type] = f"FAILED: {e}"
            
            print("\n" + "=" * 80)
            print("Summary of All Validations")
            print("=" * 80)
            for agent_type, result in reports.items():
                status = "✅" if "FAILED" not in result else "❌"
                print(f"{status} {agent_type}: {result}")
        else:
            run_validation(args.agent_type, args.domain, args.output_dir)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
