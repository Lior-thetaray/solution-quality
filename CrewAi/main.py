"""Main orchestration script for SDLC validation using CrewAI."""

import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process, LLM

from agents.sdlc_agents import create_agent
from agents.performance_agents import create_performance_agent
from tasks.sdlc_tasks import create_validation_task
from tasks.performance_tasks import create_performance_task
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


def create_performance_crew(target_url: str, test_type: str, llm):
    """Create and configure the performance testing crew.
    
    Simple pattern: 1 agent + 1 task. Agent autonomously decides how to execute.
    """
    
    # Create performance agent with Playwright tools
    performance_agent = create_performance_agent(llm)
    
    # Create comprehensive performance task (runs test_performance.py only)
    performance_task = create_performance_task(
        agent=performance_agent,
        target_url=target_url,
        test_type=test_type
    )
    
    # Create crew - simple sequential execution
    crew = Crew(
        agents=[performance_agent],
        tasks=[performance_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew


def create_combined_crew(domain: str, target_url: str, llm):
    """Create crew that runs both SDLC and performance validation."""
    
    # Create both agents
    sdlc_agent = create_agent(
        agent_name="agent_sdlc",
        tools=get_sdlc_tools(),
        llm=llm
    )
    
    performance_agent = create_performance_agent(llm)
    
    # Create tasks
    sdlc_task = create_validation_task(
        agent=sdlc_agent,
        domain=domain,
        agent_type="SDLC"
    )
    
    performance_task = create_performance_task(
        agent=performance_agent,
        target_url=target_url,
        test_type="comprehensive"
    )
    
    # Create crew with sequential execution (SDLC first, then performance)
    crew = Crew(
        agents=[sdlc_agent, performance_agent],
        tasks=[sdlc_task, performance_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew


def save_report(report: str, identifier: str, report_type: str = "sdlc"):
    """Save the validation report to the reports directory.
    
    Args:
        report: Report content to save
        identifier: Domain name or target URL identifier
        report_type: Type of report ('sdlc', 'performance', 'combined')
    """
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Clean identifier for filename (remove special characters)
    clean_identifier = identifier.replace("://", "_").replace("/", "_").replace(":", "_")
    filename = f"{report_type}_report_{clean_identifier}_{timestamp}.json"
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
    """Main entry point for SDLC and performance validation."""
    print("\n" + "="*80)
    print("ThetaRay Solution Quality - Validation System")
    print("="*80 + "\n")
    
    # Get test type
    print("Select validation type:")
    print("  1. SDLC Validation (code structure, features, DAGs)")
    print("  2. Performance Testing (UI load times, responsiveness)")
    print("  3. Combined (both SDLC + Performance)")
    
    test_choice = input("\nEnter choice (1-3): ").strip()
    
    if test_choice == "1":
        return run_sdlc_validation()
    elif test_choice == "2":
        return run_performance_testing()
    elif test_choice == "3":
        return run_combined_validation()
    else:
        print("Error: Invalid choice. Please enter 1, 2, or 3.")
        return 1


def run_sdlc_validation():
    """Run SDLC validation workflow."""
    print("\n" + "="*80)
    print("SDLC Validation Mode")
    print("="*80 + "\n")
    
    # Get domain to validate
    domain = input("Enter domain name to validate (e.g., 'demo_fuib', 'default'): ").strip()
    
    if not domain:
        print("Error: Domain name cannot be empty")
        return 1
    
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
        return 1
    
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
        filepath = save_report(str(result), domain, "sdlc")
        
        # Print summary
        print("\nSDLC validation complete!")
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
        print(f"\n❌ Error during SDLC validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def run_performance_testing():
    """Run performance testing workflow."""
    print("\n" + "="*80)
    print("Performance Testing Mode")
    print("="*80 + "\n")
    
    # Get target URL
    target_url = input("Enter target URL to test (e.g., 'https://apps-thetalab.sonar.thetaray.cloud'): ").strip()
    
    if not target_url:
        print("Error: Target URL cannot be empty")
        return 1
    
    # The copied Playwright solution runs one comprehensive test with Chromium headless
    test_type = "comprehensive"
    browser_type = "chromium"  # Fixed to Chromium headless only
    
    print("\nExecuting comprehensive performance test:")
    print("- Alert list page load time")
    print("- Feature navigation performance")
    print("- Network visualization rendering")
    print("- Browser: Chromium (headless mode)")
    
    print(f"\nTarget URL: {target_url}")
    print(f"Test Type: Comprehensive (alert list + features + network viz)")
    print(f"Browser: Chromium (headless mode)")
    print("\nInitializing Playwright agents...\n")
    
    try:
        # Setup
        llm = setup_environment()
        
        # Create performance crew
        crew = create_performance_crew(target_url, test_type, llm)
        
        # Execute performance testing
        print(f"\n{'='*80}")
        print("Starting performance testing process...")
        print(f"{'='*80}\n")
        
        result = crew.kickoff()
        
        # Save report
        filepath = save_report(str(result), target_url, "performance")
        
        # Print summary
        print("\nPerformance testing complete!")
        print(f"Full report: {filepath}")
        
        # Try to extract performance metrics
        try:
            report_json = json.loads(str(result))
            
            # Look for performance grade in summary
            if "summary" in report_json and "performance_metrics" in report_json["summary"]:
                perf_metrics = report_json["summary"]["performance_metrics"]
                if "performance_grade" in perf_metrics:
                    grade = perf_metrics["performance_grade"]
                    avg_time = perf_metrics.get("average_load_time_s", 0)
                    print(f"\nPerformance Grade: {grade}")
                    print(f"Average Load Time: {avg_time}s")
                    
                    # Interpret grade for user
                    if grade.startswith("A"):
                        print("Status: ✅ Excellent performance")
                    elif grade.startswith("B"):
                        print("Status: ✅ Good performance")
                    elif grade.startswith("C"):
                        print("Status: ⚠️  Average performance")
                    elif grade.startswith("D"):
                        print("Status: ⚠️  Poor performance")
                    else:
                        print("Status: ❌ Critical performance issues")
        except:
            pass
    
    except Exception as e:
        print(f"\n❌ Error during performance testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def run_combined_validation():
    """Run both SDLC and performance validation."""
    print("\n" + "="*80)
    print("Combined Validation Mode (SDLC + Performance)")
    print("="*80 + "\n")
    
    # Get domain for SDLC validation
    domain = input("Enter domain name to validate (e.g., 'demo_fuib', 'default'): ").strip()
    
    if not domain:
        print("Error: Domain name cannot be empty")
        return 1
    
    # Check if domain exists
    domain_path = Path(f"../Sonar/domains/{domain}")
    if not domain_path.exists():
        print(f"Error: Domain '{domain}' not found at {domain_path}")
        return 1
    
    # Get target URL for performance testing
    target_url = input("Enter target URL for performance testing: ").strip()
    
    if not target_url:
        print("Error: Target URL cannot be empty")
        return 1
    
    print(f"\nDomain: {domain}")
    print(f"Target URL: {target_url}")
    print("\nInitializing combined validation agents...\n")
    
    try:
        # Setup
        llm = setup_environment()
        
        # Create combined crew
        crew = create_combined_crew(domain, target_url, llm)
        
        # Execute combined validation
        print(f"\n{'='*80}")
        print("Starting combined validation process...")
        print(f"{'='*80}\n")
        
        result = crew.kickoff()
        
        # Save report
        identifier = f"{domain}_{target_url.replace('://', '_').replace('/', '_')}"
        filepath = save_report(str(result), identifier, "combined")
        
        # Print summary
        print("\nCombined validation complete!")
        print(f"Full report: {filepath}")
    
    except Exception as e:
        print(f"\n❌ Error during combined validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
