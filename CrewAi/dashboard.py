#!/usr/bin/env python3
"""Streamlit dashboard for ThetaRay Multi-Agent Validation."""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import os
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from crewai import LLM

from agents.sdlc_agents import create_agent as create_sdlc_agent
from tasks.sdlc_tasks import create_validation_task
from tools.tool_registry import ToolRegistry
from crewai import Crew, Process

# Page config
st.set_page_config(
    page_title="ThetaRay SDLC Validator",
    page_icon="🔍",
    layout="wide"
)

# Header
st.title("🔍 ThetaRay SDLC Quality Validator")
st.markdown("Automated validation of ThetaRay solutions against production-readiness requirements")

# Sidebar - Domain selection
st.sidebar.header("Configuration")

# Agent selection
agent_mode = st.sidebar.radio(
    "Validation Mode",
    ["SDLC Only", "Alert Validation Only", "Both (Sequential)", "Both with Manager"],
    help="Choose which validation agents to run"
)

# Map selection to agent types
agent_type_map = {
    "SDLC Only": ["sdlc"],
    "Alert Validation Only": ["alert_validation"],
    "Both (Sequential)": ["sdlc", "alert_validation"],
    "Both with Manager": ["sdlc", "alert_validation"]
}
use_manager = "Manager" in agent_mode

# Get available domains
domains_path = Path("../Sonar/domains")
available_domains = []
if domains_path.exists():
    available_domains = [d.name for d in domains_path.iterdir() 
                         if d.is_dir() and not d.name.startswith('.') and d.name != 'common']

domain = st.sidebar.selectbox(
    "Select Domain",
    options=available_domains,
    index=available_domains.index("demo_fuib") if "demo_fuib" in available_domains else 0
)

# Get previous reports - look in run directories
reports_path = Path("reports")
previous_runs = []
if reports_path.exists():
    # Find all run directories
    run_dirs = sorted(
        [d for d in reports_path.iterdir() if d.is_dir() and d.name.startswith("run_")],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    for run_dir in run_dirs[:20]:  # Last 20 runs
        # Extract domain from directory name
        if domain in run_dir.name:
            previous_runs.append(run_dir)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Domain: {domain}")
    domain_path = Path(f"../Sonar/domains/{domain}")
    if domain_path.exists():
        st.success(f"✅ Domain found at: {domain_path}")
    else:
        st.error(f"❌ Domain not found at: {domain_path}")

with col2:
    if st.button("🚀 Run Validation", type="primary", use_container_width=True):
        with st.spinner(f"Running {agent_mode}... This may take several minutes."):
            try:
                # Load environment
                load_dotenv()
                
                # Setup Azure OpenAI
                endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                api_key = os.getenv("AZURE_OPENAI_API_KEY")
                deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
                
                llm = LLM(
                    model=f"azure/{deployment}",
                    api_key=api_key,
                    base_url=endpoint
                )
                
                # Create run directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                run_dir = reports_path / f"run_{timestamp}_{domain}"
                run_dir.mkdir(parents=True, exist_ok=True)
                
                # Get agent types
                agent_types = agent_type_map[agent_mode]
                
                # Initialize tool registry
                registry = ToolRegistry()
                
                # Run agents
                results = {}
                
                # Run worker agents
                for agent_type in agent_types:
                    progress_text = f"Running {agent_type.replace('_', ' ').upper()} agent..."
                    st.info(progress_text)
                    
                    # Get tools for agent
                    tools = registry.get_tools_for_agent(agent_type)
                    
                    # Create agent
                    agent = create_sdlc_agent(f"agent_{agent_type}", tools, llm)
                    
                    # Create task
                    task = create_validation_task(agent, domain, agent_type)
                    
                    # Create and run crew
                    crew = Crew(
                        agents=[agent],
                        tasks=[task],
                        process=Process.sequential,
                        verbose=False
                    )
                    
                    result = crew.kickoff()
                    
                    # Save report
                    report_path = run_dir / f"{agent_type}_report_{domain}.json"
                    try:
                        report_data = json.loads(str(result))
                        with open(report_path, 'w') as f:
                            json.dump(report_data, f, indent=2)
                    except:
                        with open(report_path.with_suffix('.txt'), 'w') as f:
                            f.write(str(result))
                    
                    results[agent_type] = str(result)
                
                # Run manager consolidation if requested
                if use_manager and len(agent_types) > 1:
                    st.info("Running Manager consolidation...")
                    # Manager consolidation logic would go here
                    # For now, just note that it's requested
                    pass
                
                # Save to session state
                st.session_state['latest_results'] = results
                st.session_state['latest_run_dir'] = run_dir
                st.session_state['validation_time'] = datetime.now()
                st.session_state['agent_types'] = agent_types
                
                st.success("✅ Validation complete!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Validation failed: {str(e)}")
                st.exception(e)

# Display results
st.markdown("---")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 Current Report", "📈 History", "📋 Raw Data"])

with tab1:
    # Load reports (from session state or latest run directory)
    reports = {}
    manager_report = None
    run_info = None
    
    if 'latest_results' in st.session_state:
        # Use session state results
        for agent_type in st.session_state.get('agent_types', []):
            try:
                reports[agent_type] = json.loads(st.session_state['latest_results'][agent_type])
            except:
                pass
        
        # Check for manager report
        if 'manager_consolidated' in st.session_state.get('latest_results', {}):
            try:
                manager_report = json.loads(st.session_state['latest_results']['manager_consolidated'])
            except:
                pass
        
        run_info = f"🕒 Report generated: {st.session_state['validation_time'].strftime('%Y-%m-%d %H:%M:%S')}"
    
    elif previous_runs:
        # Load from latest run directory
        latest_run = previous_runs[0]
        
        # Check for manager report first (try both .json and .txt)
        manager_file_json = latest_run / f"manager_consolidated_report_{domain}.json"
        manager_file_txt = latest_run / f"manager_consolidated_report_{domain}.txt"
        
        if manager_file_json.exists():
            try:
                with open(manager_file_json, 'r') as f:
                    manager_report = json.load(f)
            except Exception as e:
                st.warning(f"Failed to load manager JSON: {e}")
        elif manager_file_txt.exists():
            try:
                with open(manager_file_txt, 'r') as f:
                    content = f.read()
                    # Try to parse as JSON
                    try:
                        manager_report = json.loads(content)
                    except:
                        # Keep as raw text
                        manager_report = {"raw": content}
            except Exception as e:
                st.warning(f"Failed to load manager TXT: {e}")
        
        # Load agent reports (try both .json and .txt)
        for report_file in list(latest_run.glob("*_report_*.json")) + list(latest_run.glob("*_report_*.txt")):
            if "manager_consolidated" not in report_file.name:
                agent_type = report_file.stem.replace(f"_report_{domain}", "")
                try:
                    with open(report_file, 'r') as f:
                        if report_file.suffix == '.json':
                            reports[agent_type] = json.load(f)
                        else:  # .txt file
                            content = f.read()
                            try:
                                reports[agent_type] = json.loads(content)
                            except:
                                reports[agent_type] = {"raw": content}
                except Exception as e:
                    st.warning(f"Failed to load {agent_type} report: {e}")
        
        run_info = f"📁 Showing latest run: {latest_run.name}"
    
    if run_info:
        st.info(run_info)
    
    # Display Manager Report First (if available)
    if manager_report:
        st.markdown("# 🎯 Manager Consolidated Report")
        
        # Check if it's raw text
        if "raw" in manager_report and len(manager_report) == 1:
            st.warning("⚠️ Manager report is in text format, not structured JSON")
            with st.expander("View Raw Manager Report", expanded=False):
                st.text(manager_report["raw"])
        else:
            st.markdown("### Executive Summary")
            
            # Overall Quality Score (handle both field names for compatibility)
            final_score = manager_report.get('final_quality_score', manager_report.get('overall_quality_score', 0))
            production_readiness = manager_report.get('production_readiness', '')
            
            # Parse production readiness (handle both formats)
            is_production_ready = (
                production_readiness == "Production Ready" or 
                manager_report.get('production_ready', False) or
                final_score >= 70
            )
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                st.metric("Final Score", f"{final_score}/100")
            
            with col2:
                st.progress(final_score / 100)
                if is_production_ready:
                    st.success("✅ **PRODUCTION READY**")
                else:
                    st.error("❌ **ADDITIONAL CYCLE REQUIRED**")
            
            with col3:
                # Count total issues from issues_by_severity
                issues_by_severity = manager_report.get('issues_by_severity', {})
                total_issues = (
                    len(issues_by_severity.get('major', [])) +
                    len(issues_by_severity.get('medium', [])) +
                    len(issues_by_severity.get('low', []))
                )
                st.metric("Total Issues", total_issues)
            
            st.markdown("---")
            
            # Issue Breakdown by Severity
            st.markdown("### Issues by Severity")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                major = len(issues_by_severity.get('major', []))
                st.metric("🔴 Major", major, delta=f"-{major}" if major > 0 else None, delta_color="inverse")
            
            with col2:
                medium = len(issues_by_severity.get('medium', []))
                st.metric("🟡 Medium", medium, delta=f"-{medium}" if medium > 0 else None, delta_color="inverse")
            
            with col3:
                low = len(issues_by_severity.get('low', []))
                st.metric("🟢 Low", low, delta=f"-{low}" if low > 0 else None, delta_color="inverse")
            
            # Show detailed issues by severity
            if total_issues > 0:
                with st.expander("📋 View All Issues by Severity", expanded=False):
                    for severity_level, severity_name, icon in [('major', 'Major Issues', '🔴'), ('medium', 'Medium Issues', '🟡'), ('low', 'Low Issues', '🟢')]:
                        issues = issues_by_severity.get(severity_level, [])
                        if issues:
                            st.markdown(f"#### {icon} {severity_name} ({len(issues)})")
                            for issue in issues:
                                component = issue.get('component', 'unknown')
                                issue_desc = issue.get('issue', '')
                                impact = issue.get('impact', '')
                                st.markdown(f"- **[{component}]** {issue_desc}")
                                if impact:
                                    st.markdown(f"  *Impact: {impact}*")
            
            st.markdown("---")
            
            # Component Scores Breakdown
            component_scores = manager_report.get('component_scores', {})
            if component_scores:
                st.markdown("### Component Quality Breakdown")
                
                # Sort components by score (lowest first to highlight issues)
                sorted_components = sorted(component_scores.items(), key=lambda x: x[1])
                
                for component, score in sorted_components:
                    # Color code based on score
                    if score >= 75:
                        color = "green"
                    elif score >= 50:
                        color = "orange"
                    else:
                        color = "red"
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.progress(score / 100)
                        st.markdown(f"**{component.replace('_', ' ').title()}**: {score}/100")
                    with col2:
                        if score >= 75:
                            st.success("✅ Good")
                        elif score >= 50:
                            st.warning("⚠️ Needs Work")
                        else:
                            st.error("❌ Critical")
                
                st.markdown("---")
            
            # Prioritized Recommendations
            recommendations = manager_report.get('recommendations', [])
            if recommendations:
                st.markdown("### 🎯 Prioritized Recommendations")
                
                # Group by priority
                high_priority = [r for r in recommendations if isinstance(r, dict) and r.get('priority') == 'HIGH']
                medium_priority = [r for r in recommendations if isinstance(r, dict) and r.get('priority') == 'MEDIUM']
                low_priority = [r for r in recommendations if isinstance(r, dict) and r.get('priority') == 'LOW']
                
                # High priority (always expanded)
                if high_priority:
                    st.markdown("#### 🔴 HIGH Priority")
                    for idx, rec in enumerate(high_priority, 1):
                        component = rec.get('component', 'N/A')
                        action = rec.get('action', '')
                        effort = rec.get('effort', 'N/A')
                        impact = rec.get('impact', 'N/A')
                        
                        st.error(f"**{idx}. [{component.upper()}]** {action}")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"⏱️ Effort: **{effort}**")
                        with col2:
                            st.markdown(f"📈 Impact: **{impact}**")
                
                # Medium priority (expandable)
                if medium_priority:
                    with st.expander(f"🟡 MEDIUM Priority ({len(medium_priority)})", expanded=False):
                        for idx, rec in enumerate(medium_priority, 1):
                            component = rec.get('component', 'N/A')
                            action = rec.get('action', '')
                            effort = rec.get('effort', 'N/A')
                            impact = rec.get('impact', 'N/A')
                            
                            st.warning(f"**{idx}. [{component.upper()}]** {action}")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"⏱️ Effort: **{effort}**")
                            with col2:
                                st.markdown(f"📈 Impact: **{impact}**")
                
                # Low priority (expandable, collapsed by default)
                if low_priority:
                    with st.expander(f"🟢 LOW Priority ({len(low_priority)})", expanded=False):
                        for idx, rec in enumerate(low_priority, 1):
                            component = rec.get('component', 'N/A')
                            action = rec.get('action', '')
                            effort = rec.get('effort', 'N/A')
                            impact = rec.get('impact', 'N/A')
                            
                            st.info(f"**{idx}. [{component.upper()}]** {action}")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"⏱️ Effort: **{effort}**")
                            with col2:
                                st.markdown(f"📈 Impact: **{impact}**")
                
                # Handle simple string recommendations (fallback for compatibility)
                simple_recs = [r for r in recommendations if isinstance(r, str)]
                if simple_recs:
                    st.markdown("#### Additional Recommendations")
                    for idx, rec in enumerate(simple_recs, 1):
                        st.info(f"{idx}. {rec}")
            
            st.markdown("---")
            
            # Consolidation Summary
            consolidation_summary = manager_report.get('consolidation_summary', {})
            if consolidation_summary:
                with st.expander("📊 Consolidation Details", expanded=False):
                    sub_agents = consolidation_summary.get('sub_agents_analyzed', [])
                    total_validations = consolidation_summary.get('total_validations', 0)
                    cross_component_issues = consolidation_summary.get('cross_component_issues', [])
                    
                    st.markdown(f"**Sub-Agents Analyzed:** {', '.join(sub_agents)}")
                    st.markdown(f"**Total Validations:** {total_validations}")
                    
                    if cross_component_issues:
                        st.markdown("**Cross-Component Issues:**")
                        for issue in cross_component_issues:
                            st.warning(f"- {issue}")
            
            st.markdown("---")
            st.markdown("---")
            
            # Sub-Agent Reports Summary
            st.markdown("## 📊 Sub-Agent Reports Summary")
            st.markdown("*Click to expand and see individual agent reports*")
            
            # Show component scores as quick overview
            if component_scores or reports:
                for agent_type in reports.keys():
                    agent_score = reports[agent_type].get('quality_score', 0)
                    agent_summary = reports[agent_type].get('summary', {})
                    passed = agent_summary.get('passed', 0)
                    total = agent_summary.get('total_checks', 0)
                    
                    status_icon = "✅" if agent_score >= 70 else "⚠️" if agent_score >= 50 else "❌"
                    
                    with st.expander(f"{status_icon} {agent_type.replace('_', ' ').title()} Agent - {agent_score}/100 ({passed}/{total} passed)", expanded=False):
                        st.markdown(f"**Quality Score:** {agent_score}/100")
                        st.progress(agent_score / 100)
                        st.markdown(f"**Tests Passed:** {passed} out of {total}")
                        st.markdown("*Full report available in 'Full Agent Reports' section below*")
    
    elif reports:
        st.markdown("# 📊 Validation Reports")
    
    # Display Individual Agent Reports (Expandable)
    if reports:
        if manager_report:
            st.markdown("---")
            st.markdown("## 📋 Full Agent Reports")
            st.markdown("*Click to expand and see complete validation details*")
        
        # Display each agent's report in expandable sections
        for agent_type, report_data in reports.items():
            score = report_data.get('quality_score', 0)
            summary = report_data.get('summary', {})
            status_icon = "✅" if summary.get('passed', 0) == summary.get('total_checks', 0) else "❌"
            
            with st.expander(
                f"{status_icon} {agent_type.replace('_', ' ').title()} - {score}/100 ({summary.get('passed', 0)}/{summary.get('total_checks', 0)} passed)",
                expanded=not manager_report  # Expand if no manager report
            ):
                # Quality Score
                st.markdown("### Quality Score")
                
                # Color coding
                if score >= 90:
                    status = "✅ Excellent - Production Ready"
                elif score >= 75:
                    status = "✅ Good - Minor Improvements Needed"
                elif score >= 60:
                    status = "⚠️ Acceptable - Several Issues to Address"
                else:
                    status = "❌ Needs Work - Major Issues Found"
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    st.metric("Score", f"{score}/100")
                with col2:
                    st.progress(score / 100)
                    st.markdown(f"**{status}**")
                with col3:
                    st.metric("Passed", f"{summary.get('passed', 0)}/{summary.get('total_checks', 0)}")
                
                st.markdown("---")
                
                # Validations
                st.markdown("### Validation Results")
                
                validations = report_data.get('validations', [])
                
                if validations:
                    # Summary metrics
                    cols = st.columns(min(len(validations), 4))
                    for idx, validation in enumerate(validations):
                        with cols[idx % 4]:
                            icon = "✅" if validation['pass'] else "❌"
                            st.metric(
                                validation['name'].replace(' Validation', ''),
                                icon,
                                delta=f"{len(validation.get('issues', []))} issues" if not validation['pass'] else None,
                                delta_color="inverse"
                            )
                    
                    st.markdown("---")
                    
                    # Detailed issues
                    for validation in validations:
                        icon = "✅" if validation['pass'] else "❌"
                        issues = validation.get('issues', [])
                        
                        with st.expander(f"{icon} {validation['name']}", expanded=False):
                            if issues:
                                st.warning(f"Found {len(issues)} issue(s):")
                                for issue in issues:
                                    st.markdown(f"- {issue}")
                            else:
                                st.success("All checks passed!")
                
                st.markdown("---")
                
                # Recommendations
                recommendations = report_data.get('recommendations', [])
                if recommendations:
                    st.markdown("### 📋 Recommendations")
                    for idx, rec in enumerate(recommendations, 1):
                        st.info(f"{idx}. {rec}")
    
    else:
        st.info("👆 Click 'Run Validation' to start analyzing the domain")

with tab2:
    st.markdown("### Validation History")
    
    if previous_runs:
        history_data = []
        for run_dir in previous_runs:
            # Find all reports in this run (both .json and .txt)
            reports_in_run = list(run_dir.glob("*_report_*.json")) + list(run_dir.glob("*_report_*.txt"))
            if not reports_in_run:
                continue
                
            # Calculate average score across all reports in run
            scores = []
            passed_total = 0
            failed_total = 0
            
            for report_file in reports_in_run:
                try:
                    with open(report_file, 'r') as f:
                        if report_file.suffix == '.json':
                            data = json.load(f)
                        else:  # .txt file
                            content = f.read()
                            try:
                                data = json.loads(content)
                            except:
                                continue  # Skip non-JSON txt files
                        scores.append(data.get('quality_score', 0))
                        passed_total += data.get('summary', {}).get('passed', 0)
                        failed_total += data.get('summary', {}).get('failed', 0)
                except:
                    continue
            
            if scores:
                avg_score = sum(scores) / len(scores)
                history_data.append({
                    'Date': datetime.fromtimestamp(run_dir.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'Agents': len(scores),
                    'Avg Score': round(avg_score, 1),
                    'Passed': passed_total,
                    'Failed': failed_total,
                    'Run': run_dir.name
                })
        
        if history_data:
            df = pd.DataFrame(history_data)
            
            # Line chart
            st.line_chart(df.set_index('Date')['Avg Score'])
            
            # Table
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No historical data available")
    else:
        st.info("No previous runs found. Run your first validation to start tracking history.")

with tab3:
    st.markdown("### Raw JSON Reports")
    
    # Show manager report first if available
    if manager_report:
        st.markdown("#### Manager Consolidated Report")
        st.json(manager_report)
        st.markdown("---")
    
    if reports:
        for agent_type, report_data in reports.items():
            st.markdown(f"#### {agent_type.replace('_', ' ').title()}")
            st.json(report_data)
            st.markdown("---")
    
    if not manager_report and not reports:
        st.info("No report data available")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    ThetaRay Multi-Agent Quality Validator | Powered by CrewAI & Azure OpenAI
    </div>
    """,
    unsafe_allow_html=True
)
