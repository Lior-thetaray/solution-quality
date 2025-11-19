"""Generic task factory for creating validation tasks.

Simple pattern: One task per agent that lets the LLM decide how to execute.
"""

from crewai import Task


def create_validation_task(agent, domain: str, agent_type: str = "validation") -> Task:
    """Create a simple validation task for any agent.
    
    Args:
        agent: The agent that will execute this task
        domain: Domain name to validate (e.g., 'demo_fuib')
        agent_type: Type of validation (e.g., 'SDLC', 'security', 'performance')
        
    Returns:
        Task that lets the agent autonomously execute validation
    """
    
    # For alert validation, provide explicit step-by-step workflow to minimize LLM calls
    if 'alert' in agent.role.lower():
        description = f"""Validate alert quality for domain '{domain}' following these steps IN ORDER:

STEP 1: Use CSV File Lister to discover CSV files
STEP 2: Use CSV Dataset Reader on tr_alert_table.csv  
STEP 3: Use CSV Dataset Reader on evaluated_activities.csv
STEP 4: Use Cross-Table Analysis to validate trigger relationships
STEP 5: Use Monthly Alert Percentage Calculator for monthly metrics
STEP 6: Use Consolidation Effectiveness Checker (if applicable)

After ALL steps complete, compile a final JSON report with your findings.

Domain: Sonar/domains/{domain}/

Output JSON with validations array, summary, quality_score (0-100), and recommendations."""
    else:
        description = f"""Validate the ThetaRay solution in domain '{domain}' according to your instructions.

Use your available tools to analyze the codebase and produce a comprehensive validation report.
Follow all guidelines, requirements, and validation steps specified in your backstory.

The domain is located at: Sonar/domains/{domain}/

Produce a detailed JSON report with your findings."""
    
    return Task(
        description=description,
        
        expected_output="""JSON report with:
- domain: string (domain name)
- timestamp: ISO datetime string
- validations: array of validation checks with pass/fail status and issues
- summary: object with total_checks, passed, failed counts
- quality_score: number from 0-100
- recommendations: array of actionable improvement suggestions""",
        
        agent=agent
    )
