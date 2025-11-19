#!/usr/bin/env python3
"""
Generalized runner that detects missing reports and only runs what's needed.

Supported agents:
- sdlc: Code quality and solution structure validation
- alert_validation: Alert quality and data validation  
- manager_consolidated: Manager consolidation of all reports

Usage:
    python3 run_with_reuse.py                    # Interactive: auto-detect missing
    python3 run_with_reuse.py demo_fuib          # Auto: run missing reports only
    python3 run_with_reuse.py demo_fuib --force-all  # Force rerun everything
    python3 run_with_reuse.py demo_fuib sdlc     # Force run specific agent(s)
    python3 run_with_reuse.py demo_fuib alert manager  # Force run alert + manager
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from main_unified import (
    setup_environment,
    run_agents,
    print_summary
)


# All possible agent types
ALL_AGENTS = ['sdlc', 'alert_validation']
MANAGER_AGENT = 'manager_consolidated'


def find_latest_run(domain: str) -> Path:
    """Find the most recent run directory for a domain"""
    reports_path = Path("reports")
    
    if not reports_path.exists():
        return None
    
    runs = sorted(
        [d for d in reports_path.iterdir() 
         if d.is_dir() and domain in d.name and d.name.startswith("run_")],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    return runs[0] if runs else None


def analyze_run(run_dir: Path, domain: str) -> dict:
    """Analyze what reports exist in a run directory
    
    Returns:
        dict: {agent_type: report_file_path or None}
    """
    analysis = {}
    
    # Check worker agents
    for agent_type in ALL_AGENTS:
        json_file = run_dir / f"{agent_type}_report_{domain}.json"
        txt_file = run_dir / f"{agent_type}_report_{domain}.txt"
        
        if json_file.exists():
            analysis[agent_type] = json_file
        elif txt_file.exists():
            analysis[agent_type] = txt_file
        else:
            analysis[agent_type] = None
    
    # Check manager
    manager_json = run_dir / f"{MANAGER_AGENT}_report_{domain}.json"
    manager_txt = run_dir / f"{MANAGER_AGENT}_report_{domain}.txt"
    
    if manager_json.exists():
        analysis[MANAGER_AGENT] = manager_json
    elif manager_txt.exists():
        analysis[MANAGER_AGENT] = manager_txt
    else:
        analysis[MANAGER_AGENT] = None
    
    return analysis


def get_missing_agents(analysis: dict) -> list:
    """Get list of missing worker agent reports"""
    return [agent for agent in ALL_AGENTS if not analysis.get(agent)]


def needs_manager_rerun(analysis: dict, agents_to_run: list) -> bool:
    """Determine if manager needs to run
    
    Manager should run if:
    - It doesn't exist yet
    - We're running new worker agents (needs consolidation)
    - We have multiple worker reports
    """
    # No manager report exists
    if not analysis.get(MANAGER_AGENT):
        return True
    
    # Running new agents that will need consolidation
    if agents_to_run:
        return True
    
    return False


def main():
    print("=" * 80)
    print("GENERALIZED RUNNER: Auto-detect & Run Missing Reports")
    print("=" * 80)
    
    # Parse arguments
    force_all = '--force-all' in sys.argv
    force_agents = []
    domain = None
    
    for arg in sys.argv[1:]:
        if arg.startswith('--'):
            continue
        elif arg in ['sdlc', 'alert', 'alert_validation', 'manager']:
            # Map 'alert' to 'alert_validation', 'manager' to run manager
            if arg == 'alert':
                force_agents.append('alert_validation')
            elif arg == 'manager':
                force_agents.append(MANAGER_AGENT)
            else:
                force_agents.append(arg)
        elif not domain:
            domain = arg
    
    # Get domain
    if not domain:
        domain = input("\nEnter domain (default: demo_fuib): ").strip() or "demo_fuib"
    
    print(f"\n🎯 Domain: {domain}")
    
    # Find or create run directory
    latest_run = find_latest_run(domain)
    
    if latest_run:
        print(f"📁 Found latest run: {latest_run.name}")
        analysis = analyze_run(latest_run, domain)
        run_dir = latest_run
    else:
        print(f"📁 No existing runs found - will create new one")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path("reports") / f"run_{timestamp}_{domain}"
        run_dir.mkdir(parents=True, exist_ok=True)
        analysis = {agent: None for agent in ALL_AGENTS + [MANAGER_AGENT]}
    
    # Display current state
    print("\n📊 Current Reports Status:")
    for agent_type in ALL_AGENTS + [MANAGER_AGENT]:
        status = "✓" if analysis.get(agent_type) else "✗"
        file_name = analysis[agent_type].name if analysis.get(agent_type) else "Missing"
        print(f"   {status} {agent_type}: {file_name}")
    
    # Determine what to run
    if force_all:
        agents_to_run = ALL_AGENTS.copy()
        run_manager = True
        print("\n⚡ Force mode: Running ALL agents + manager")
    elif force_agents:
        # User specified which agents to run
        agents_to_run = [a for a in force_agents if a in ALL_AGENTS]
        run_manager = MANAGER_AGENT in force_agents or needs_manager_rerun(analysis, agents_to_run)
        print(f"\n⚡ Force running: {', '.join(force_agents)}")
    else:
        # Auto-detect missing
        agents_to_run = get_missing_agents(analysis)
        run_manager = needs_manager_rerun(analysis, agents_to_run)
        
        if not agents_to_run and not run_manager:
            print("\n✅ All reports exist! Nothing to run.")
            print(f"📁 Reports location: {run_dir}")
            return 0
        
        print(f"\n🔍 Auto-detected missing reports:")
        if agents_to_run:
            print(f"   Worker agents to run: {', '.join(agents_to_run)}")
        else:
            print(f"   Worker agents: All exist ✓")
        
        if run_manager:
            if not analysis.get(MANAGER_AGENT):
                print(f"   Manager: Missing - will run")
            else:
                print(f"   Manager: Will rerun (new data available)")
    
    # Summary
    print("\n" + "-" * 80)
    print("EXECUTION PLAN:")
    if agents_to_run:
        for idx, agent in enumerate(agents_to_run, 1):
            print(f"  {idx}. Run {agent}")
    else:
        print(f"  - All worker agents exist, will reuse")
    
    if run_manager:
        print(f"  {len(agents_to_run) + 1}. Run manager consolidation")
    
    print(f"\n📁 Output directory: {run_dir}")
    print("-" * 80)
    
    # Confirm
    if not sys.stdin.isatty():
        # Non-interactive (piped input)
        confirm = 'y'
    else:
        confirm = input("\nProceed? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Cancelled.")
        return 0
    
    # Setup
    print("\n" + "=" * 80)
    print("STARTING EXECUTION")
    print("=" * 80)
    
    llm = setup_environment()
    
    # Run agents with reuse enabled
    results = run_agents(
        agent_types=ALL_AGENTS,  # Pass all agents so manager knows what to consolidate
        domain=domain,
        llm=llm,
        run_dir=run_dir,
        use_manager=run_manager,
        reuse_existing=True  # Always reuse existing reports
    )
    
    # Print summary
    print_summary(results, ALL_AGENTS, run_dir, reuse_existing=True)
    
    print("\n✅ Execution complete!")
    print(f"📁 All reports in: {run_dir}")
    
    # Show final status
    final_analysis = analyze_run(run_dir, domain)
    print("\n📊 Final Reports Status:")
    for agent_type in ALL_AGENTS + [MANAGER_AGENT]:
        status = "✓" if final_analysis.get(agent_type) else "✗"
        file_name = final_analysis[agent_type].name if final_analysis.get(agent_type) else "Missing"
        print(f"   {status} {agent_type}: {file_name}")
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

