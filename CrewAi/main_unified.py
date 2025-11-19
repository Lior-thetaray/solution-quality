"""
Multi-Agent Validation Runner
Unified main file to run SDLC, Alert, and other validation agents
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from crewai import Crew, Process, LLM, Task

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


def create_manager_agent(llm):
    """Create the manager agent for consolidation"""
    from pathlib import Path
    
    # Load manager instructions
    instructions_path = Path(__file__).parent.parent / "agent_instructions" / "agent_manager.md"
    
    if not instructions_path.exists():
        raise FileNotFoundError(f"Manager instructions not found at {instructions_path}")
    
    instructions = instructions_path.read_text()
    
    # Extract role and goal
    import re
    role_match = re.search(r'\*\*Role\*\*:\s*(.+)', instructions)
    goal_match = re.search(r'\*\*Goal\*\*:\s*(.+)', instructions)
    
    role = role_match.group(1).strip() if role_match else "Quality Assurance Manager"
    goal = goal_match.group(1).strip() if goal_match else "Consolidate validation reports into final assessment"
    
    # Create manager agent with no tools (works with provided data)
    from crewai import Agent
    
    return Agent(
        role=role,
        goal=goal,
        backstory=instructions,
        tools=[],  # No tools - receives data directly in task
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


def create_crew(agent_type: str, domain: str, llm, manager_mode: bool = False) -> Crew:
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


def create_hierarchical_crew(domain: str, llm, run_dir: Path, worker_types: List[str]) -> Crew:
    """Create a hierarchical crew with manager orchestrating worker agents"""
    
    # Create manager agent (no tools needed - consolidates reports)
    manager = create_agent(
        agent_name="agent_manager",
        tools=[],
        llm=llm
    )
    
    # Create worker agents
    workers = []
    tasks = []
    
    for agent_type in worker_types:
        tools = get_agent_tools(agent_type)
        agent = create_agent(
            agent_name=f"agent_{agent_type}",
            tools=tools,
            llm=llm
        )
        workers.append(agent)
        
        # Create task for each worker
        task = create_validation_task(
            agent=agent,
            domain=domain,
            agent_type=agent_type.upper()
        )
        tasks.append(task)
    
    # Create consolidation task for manager
    from tasks.sdlc_tasks import Task
    manager_task = Task(
        description=f"""Consolidate all validation reports for domain '{domain}'.
        
        Review reports from: {', '.join([w.role for w in workers])}
        
        Synthesize findings, categorize issues by severity (Major/Medium/Low),
        calculate weighted quality score, and provide production readiness assessment.
        
        Output a comprehensive consolidated JSON report as specified in your instructions.""",
        expected_output="Consolidated JSON report with final quality score and production readiness assessment",
        agent=manager
    )
    tasks.append(manager_task)
    
    # Create hierarchical crew with manager
    crew = Crew(
        agents=workers,  # Only worker agents, not manager
        tasks=tasks,
        process=Process.hierarchical,
        manager_agent=manager,
        verbose=True
    )
    
    return crew


def save_report(result, agent_type: str, domain: str, run_dir: Path) -> str:
    """Save validation report to JSON file in the run directory"""
    filepath = run_dir / f"{agent_type}_report_{domain}.json"
    
    # Extract report from crew result
    report_content = str(result)
    
    # Try to parse as JSON
    try:
        # Sometimes CrewAI wraps the JSON in extra text, try to extract it
        # Look for JSON object starting with { and ending with }
        start_idx = report_content.find('{')
        end_idx = report_content.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = report_content[start_idx:end_idx]
            report_data = json.loads(json_str)
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"\n💾 Report saved as JSON: {filepath}")
        else:
            raise ValueError("No JSON object found in output")
    except Exception as e:
        # Save as text if not valid JSON
        print(f"\n⚠️  Could not parse as JSON ({e}), saving as text")
        with open(filepath.with_suffix('.txt'), 'w') as f:
            f.write(report_content)
        filepath = filepath.with_suffix('.txt')
        print(f"💾 Report saved as TXT: {filepath}")
    
    return str(filepath)


def run_agents(agent_types: List[str], domain: str, llm, run_dir: Path, use_manager: bool = False, reuse_existing: bool = False) -> Dict[str, Any]:
    """Run multiple agents and collect results
    
    Args:
        agent_types: List of agent types to run
        domain: Domain name
        llm: LLM instance
        run_dir: Directory to save reports
        use_manager: Whether to run manager consolidation
        reuse_existing: If True, skip agents that already have reports in run_dir
    """
    results = {}
    
    # Check for existing reports if reuse_existing is True
    if reuse_existing:
        print("\n🔍 Checking for existing reports to reuse...")
        for agent_type in agent_types:
            json_file = run_dir / f"{agent_type}_report_{domain}.json"
            txt_file = run_dir / f"{agent_type}_report_{domain}.txt"
            
            if json_file.exists() or txt_file.exists():
                report_file = json_file if json_file.exists() else txt_file
                print(f"✓ Found existing {agent_type} report: {report_file.name}")
                
                # Load and add to results
                try:
                    with open(report_file, 'r') as f:
                        if report_file.suffix == '.json':
                            report_content = json.load(f)
                        else:
                            report_content = f.read()
                    
                    results[agent_type] = {
                        "status": "success",
                        "report_path": str(report_file),
                        "result": json.dumps(report_content) if isinstance(report_content, dict) else report_content,
                        "reused": True
                    }
                except Exception as e:
                    print(f"⚠️  Could not load existing {agent_type} report: {e}")
    
    # Run only agents that don't have results yet
    agents_to_run = [a for a in agent_types if a not in results]
    
    if agents_to_run:
        print(f"\n🚀 Running {len(agents_to_run)} agent(s): {', '.join(agents_to_run)}")
    else:
        print("\n✓ All agents have existing reports, nothing to run")
    
    # Sequential mode - run each agent independently
    for agent_type in agents_to_run:
        print("\n" + "=" * 80)
        print(f"RUNNING {agent_type.upper().replace('_', ' ')} AGENT")
        print("=" * 80)
        
        max_retries = 3
        retry_delay = 60  # seconds
        
        for attempt in range(max_retries):
            try:
                # Create and run crew
                crew = create_crew(agent_type, domain, llm)
                
                print(f"\n🚀 Starting {agent_type} validation for: {domain}")
                if attempt > 0:
                    print(f"   (Retry attempt {attempt + 1}/{max_retries})")
                print()
                
                result = crew.kickoff()
                
                # Save report
                report_path = save_report(result, agent_type, domain, run_dir)
                
                results[agent_type] = {
                    "status": "success",
                    "report_path": report_path,
                    "result": str(result)
                }
                
                print(f"\n✅ {agent_type} validation complete!")
                break  # Success, exit retry loop
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if "RateLimitReached" in error_msg or "rate limit" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(f"\n⏱️  Rate limit hit. Waiting {retry_delay} seconds before retry...")
                        print(f"   Attempt {attempt + 1}/{max_retries} failed")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff
                        continue
                    else:
                        print(f"\n❌ Rate limit persists after {max_retries} attempts")
                        results[agent_type] = {
                            "status": "error",
                            "error": f"Rate limit exceeded after {max_retries} retries: {error_msg}"
                        }
                else:
                    # Non-rate-limit error
                    print(f"\n❌ Error running {agent_type}: {error_msg}")
                    results[agent_type] = {
                        "status": "error",
                        "error": error_msg
                    }
                break  # Don't retry for non-rate-limit errors
        
        # Add cooldown between agents to avoid hitting rate limits
        if agent_type != agent_types[-1] and len(agent_types) > 1:
            cooldown = 90  # 90 seconds between agents
            print(f"\n⏱️  Cooldown: Waiting {cooldown} seconds before next agent...")
            print(f"   (Helps avoid Azure rate limits on S0 tier)")
            time.sleep(cooldown)
    
    # Run manager consolidation if requested
    # Manager can consolidate even if some agents failed, as long as we have at least one successful report
    if use_manager:
        print("\n" + "=" * 80)
        print("RUNNING MANAGER CONSOLIDATION")
        print("=" * 80)
        
        # Count successful agents
        successful_agents = [k for k, v in results.items() if v.get('status') == 'success']
        failed_agents = [k for k, v in results.items() if v.get('status') == 'error']
        
        if failed_agents:
            print(f"\n⚠️  Note: {len(failed_agents)} agent(s) failed: {', '.join(failed_agents)}")
        
        print(f"👔 Manager consolidating reports from {len(successful_agents)} successful agent(s): {', '.join(successful_agents)}\n")
        
        try:
            # Read the saved reports (try both .json and .txt)
            agent_reports = {}
            for agent_type in agent_types:
                # Check for JSON file first, then TXT
                json_file = run_dir / f"{agent_type}_report_{domain}.json"
                txt_file = run_dir / f"{agent_type}_report_{domain}.txt"
                
                if json_file.exists():
                    try:
                        with open(json_file, 'r') as f:
                            agent_reports[agent_type] = json.load(f)
                        print(f"✓ Loaded {agent_type} report (JSON)")
                    except Exception as e:
                        print(f"⚠️  Failed to parse {agent_type} JSON: {e}")
                elif txt_file.exists():
                    try:
                        with open(txt_file, 'r') as f:
                            content = f.read()
                            # Try to extract JSON from text content
                            try:
                                agent_reports[agent_type] = json.loads(content)
                                print(f"✓ Loaded {agent_type} report (TXT as JSON)")
                            except:
                                agent_reports[agent_type] = {"raw": content}
                                print(f"✓ Loaded {agent_type} report (TXT raw)")
                    except Exception as e:
                        print(f"⚠️  Failed to read {agent_type} TXT: {e}")
                else:
                    print(f"⚠️  No report found for {agent_type}")
            
            # Only proceed if we have at least one report
            if not agent_reports:
                print("\n❌ No reports available for consolidation")
                results["manager_consolidated"] = {
                    "status": "error",
                    "error": "No agent reports found to consolidate"
                }
                return results
            
            # Create manager agent (no tools needed - will work with provided data)
            manager = create_manager_agent(llm)
            
            # Build detailed context from reports
            reports_summary = ""
            for agent_type, report in agent_reports.items():
                reports_summary += f"\n\n### {agent_type.upper()} REPORT:\n"
                reports_summary += json.dumps(report, indent=2)
            
            # Create consolidation task with full report data embedded
            manager_task = Task(
                description=f"""Consolidate validation reports for domain '{domain}'.

You have received the following validation reports:
{reports_summary}

Analyze these reports and produce a consolidated assessment with:
1. Overall quality score (weighted average)
2. Production readiness determination (score >= 70)
3. Total critical issues, warnings, and passed checks across all agents
4. Agent-by-agent summaries with key issues
5. Top 5 key recommendations prioritized by impact

Follow the output format specified in your instructions.""",
                expected_output="Consolidated JSON report with final quality score and production readiness assessment",
                agent=manager
            )
            
            # Create crew with just manager
            crew = Crew(
                agents=[manager],
                tasks=[manager_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Save consolidated report
            report_path = save_report(result, "manager_consolidated", domain, run_dir)
            
            results["manager_consolidated"] = {
                "status": "success",
                "report_path": report_path,
                "result": str(result)
            }
            
            print(f"\n✅ Manager consolidation complete!")
            
        except Exception as e:
            print(f"\n❌ Error running manager consolidation: {str(e)}")
            import traceback
            traceback.print_exc()
            results["manager_consolidated"] = {
                "status": "error",
                "error": str(e)
            }
    
    return results


def print_summary(results: Dict[str, Any], agent_types: List[str], run_dir: Path, reuse_existing: bool = False):
    """Print summary of all agent results"""
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    print(f"\n📁 All reports saved in: {run_dir}")
    
    for agent_type, result in results.items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        reused_icon = "♻️" if result.get("reused", False) else ""
        print(f"\n{status_icon} {reused_icon} {agent_type.upper().replace('_', ' ')}:")
        
        if result["status"] == "success":
            # Show just the filename, not the full path
            report_filename = Path(result['report_path']).name
            if result.get("reused", False):
                print(f"   Report: {report_filename} (reused from previous run)")
            else:
                print(f"   Report: {report_filename}")
            
            # Try to extract quality score
            try:
                report_data = json.loads(result['result'])
                if "quality_score" in report_data:
                    score = report_data["quality_score"]
                    print(f"   Quality Score: {score}/100")
                elif "final_quality_score" in report_data:
                    score = report_data["final_quality_score"]
                    print(f"   Final Quality Score: {score}/100")
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
    print("  3. all - Run all agents (sequential)")
    print("  4. manager - Run all agents + manager consolidation")
    
    agent_choice = input("\nSelect agents (e.g., '1', '2', '1,2', 'all', or 'manager'): ").strip()
    
    # Parse agent selection
    use_manager = False
    if agent_choice == "manager" or agent_choice == "4":
        agent_types = ["sdlc", "alert_validation"]
        use_manager = True
    elif agent_choice == "all" or agent_choice == "3":
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
        
        # Check for existing runs for this domain
        reports_path = Path("reports")
        existing_runs = []
        if reports_path.exists():
            existing_runs = sorted(
                [d for d in reports_path.iterdir() if d.is_dir() and domain in d.name and d.name.startswith("run_")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
        
        # Ask if user wants to reuse existing run directory
        run_dir = None
        reuse_existing = False
        
        if existing_runs and len(agent_types) > 1:
            latest_run = existing_runs[0]
            existing_reports = list(latest_run.glob("*_report_*"))
            
            if existing_reports:
                print(f"\n📁 Found existing run: {latest_run.name}")
                print(f"   Contains {len(existing_reports)} report(s):")
                for report in existing_reports:
                    print(f"   - {report.name}")
                
                reuse_choice = input("\nReuse this run directory and skip existing reports? (y/n): ").strip().lower()
                if reuse_choice == 'y':
                    run_dir = latest_run
                    reuse_existing = True
                    print(f"\n♻️  Reusing run directory: {run_dir}")
        
        # Create new run directory if not reusing
        if run_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_dir = Path("reports") / f"run_{timestamp}_{domain}"
            run_dir.mkdir(parents=True, exist_ok=True)
            print(f"\n📁 Created new run directory: {run_dir}")
        
        print(f"\n📁 Reports will be saved to: {run_dir}")
        
        # Run selected agents
        mode_text = "with Manager Consolidation" if use_manager else "Sequential"
        print(f"\n🎯 Running agents: {', '.join(agent_types)} ({mode_text})")
        print(f"🎯 Target: {domain}")
        
        results = run_agents(agent_types, domain, llm, run_dir, use_manager, reuse_existing)
        
        # Print summary
        print_summary(results, agent_types, run_dir, reuse_existing)
        
        print("\n✅ All validations complete!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
