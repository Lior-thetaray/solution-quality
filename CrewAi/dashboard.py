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
    page_title="ThetaRay Solution Quality Validator",
    page_icon="🔍",
    layout="wide"
)

# Header
st.title("🔍 ThetaRay Solution Quality Validator")

# Sidebar - Domain selection
st.sidebar.header("Configuration")

# Get available domains
domains_path = Path(__file__).parent.parent / "Sonar" / "domains"
available_domains = []
if domains_path.exists():
    available_domains = [d.name for d in domains_path.iterdir() 
                         if d.is_dir() and not d.name.startswith('.') and d.name != 'common']

domain = None
if available_domains:
    domain = st.sidebar.selectbox(
        "Select Domain",
        options=available_domains,
        index=available_domains.index("demo_fuib") if "demo_fuib" in available_domains else 0
    )
else:
    st.sidebar.warning(f"No domains found in {domains_path}")

# Run Validation Section
st.sidebar.markdown("---")
st.sidebar.header("Run Validation")

if st.sidebar.button("🚀 Run Validation", type="primary", use_container_width=True):
    if domain:
        import subprocess
        with st.spinner("Running validation agents... This may take a few minutes."):
            try:
                # Run only manager with reuse - it will use existing agent reports
                result = subprocess.run(
                    ["python3", "run_with_reuse.py", domain, "manager"],
                    cwd=Path(__file__).parent,
                    capture_output=True,
                    text=True,
                    input="y\n",  # Auto-confirm reuse
                    timeout=300  # 5 minute timeout
                )
                if result.returncode == 0:
                    st.sidebar.success("✅ Validation completed!")
                    st.rerun()
                else:
                    st.sidebar.error(f"❌ Validation failed:\n{result.stderr}")
            except subprocess.TimeoutExpired:
                st.sidebar.error("❌ Validation timed out (>5 minutes)")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")

# Export Section
if domain:
    st.sidebar.markdown("---")
    st.sidebar.header("Export Report")
    
    # Find latest report
    reports_path = Path(__file__).parent / "reports"
    latest_run = None
    if reports_path.exists():
        run_dirs = sorted(
            [d for d in reports_path.iterdir() if d.is_dir() and d.name.startswith("run_") and domain in d.name],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        if run_dirs:
            latest_run = run_dirs[0]
    
    if latest_run:
        manager_file = latest_run / f"manager_consolidated_report_{domain}.json"
        if manager_file.exists():
            with open(manager_file, 'r') as f:
                report_json = f.read()
            
            st.sidebar.download_button(
                label="📥 Download JSON Report",
                data=report_json,
                file_name=f"quality_report_{domain}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
            
            # CSV export for recommendations
            try:
                manager_data = json.loads(report_json)
                recommendations = manager_data.get('recommendations', [])
                if recommendations:
                    df_recs = pd.DataFrame(recommendations)
                    csv = df_recs.to_csv(index=False)
                    st.sidebar.download_button(
                        label="📥 Download Recommendations (CSV)",
                        data=csv,
                        file_name=f"recommendations_{domain}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            except:
                pass

# Get previous reports - look in run directories
reports_path = Path(__file__).parent / "reports"
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
        if domain and domain in run_dir.name:
            previous_runs.append(run_dir)

# Main content
if domain:
    domain_path = Path(__file__).parent.parent / "Sonar" / "domains" / domain
    if not domain_path.exists():
        st.error(f"❌ Domain not found at: {domain_path}")
        st.stop()
else:
    st.warning("⚠️ No domains found. Please check that Sonar/domains exists.")
    st.stop()

# Display results
st.markdown("---")

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📊 Current Report", "📈 History", "🔄 Compare Runs", "📋 Raw Data"])

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
    
    # Display Manager Report if available
    if manager_report and "raw" not in manager_report:
        # 1. EXECUTIVE SUMMARY
        st.markdown("## 📊 Executive Summary")
        
        final_score = manager_report.get('final_quality_score', 0)
        production_readiness = manager_report.get('production_readiness', '')
        is_production_ready = production_readiness == "Production Ready"
        consolidation_summary = manager_report.get('consolidation_summary', {})
        issues_by_severity = manager_report.get('issues_by_severity', {})
        
        # Top row: Score and Status (most important)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.metric("Final Quality Score", f"{final_score:.1f}/100")
            # Color-coded progress bar
            if final_score >= 80:
                st.success(f"✅ Excellent")
            elif final_score >= 70:
                st.warning(f"⚠️ Good")
            else:
                st.error(f"❌ Needs Work")
            st.progress(final_score / 100)
        
        with col2:
            # Production readiness
            if is_production_ready:
                st.metric("Production Status", "✅ Ready")
                st.success("**PRODUCTION READY**")
            else:
                st.metric("Production Status", "❌ Not Ready")
                st.error("**NEEDS WORK**")
            
            # Production readiness rationale (expandable)
            rationale = manager_report.get('production_readiness_rationale', '')
            if rationale:
                with st.expander("📋 View Details", expanded=False):
                    st.markdown(rationale)
        
        st.markdown("---")
        
        # Bottom row: Issues and Validations breakdown
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Count total issues by severity
            high_issues = len(issues_by_severity.get('high', [])) + len(issues_by_severity.get('major', []))
            medium_issues = len(issues_by_severity.get('medium', []))
            low_issues = len(issues_by_severity.get('low', []))
            total_issues = high_issues + medium_issues + low_issues
            
            st.metric("Total Issues", total_issues)
            if high_issues > 0:
                st.error(f"🔴 {high_issues} High")
            if medium_issues > 0:
                st.warning(f"🟡 {medium_issues} Medium")
            if low_issues > 0:
                st.info(f"🟢 {low_issues} Low")
        
        with col2:
            # Validation summary
            total_validations = consolidation_summary.get('total_validations', 0)
            if total_validations > 0:
                # Calculate passed/failed from issues
                passed_validations = total_validations - total_issues
                st.metric("Total Validations", total_validations)
                if passed_validations > 0:
                    st.success(f"✅ {passed_validations} Passed")
                if total_issues > 0:
                    st.error(f"❌ {total_issues} Failed")
        
        with col3:
            # Agents analyzed
            agents_count = consolidation_summary.get('agents_present', 0)
            agents_list = consolidation_summary.get('sub_agents_analyzed', [])
            st.metric("Agents Analyzed", agents_count)
            if agents_list:
                with st.expander("📋 View Agents", expanded=False):
                    for agent in agents_list:
                        st.markdown(f"- {agent}")
        
        st.markdown("---")
        
        # 2. CATEGORIES BREAKDOWN
        st.markdown("## 📈 Categories Breakdown")
        
        category_scores = manager_report.get('category_scores', {})
        
        if category_scores:
            # Define category display info
            category_info = {
                'investigation_experience': {
                    'name': 'Investigation Experience',
                    'icon': '🔍',
                    'weight': 0.40
                },
                'results_quality': {
                    'name': 'Results Quality',
                    'icon': '🎯',
                    'weight': 0.35
                },
                'development_standards': {
                    'name': 'Development Standards',
                    'icon': '📋',
                    'weight': 0.25
                }
            }
            
            # Display each category
            for category_key, category_data in category_scores.items():
                info = category_info.get(category_key, {
                    'name': category_key.replace('_', ' ').title(),
                    'icon': '📊',
                    'weight': category_data.get('weight', 0)
                })
                
                category_score = category_data.get('score', 0)
                weight = category_data.get('weight', 0)
                weighted_contribution = category_data.get('weighted_contribution', 0)
                agents_data = category_data.get('agents', {})
                
                # Category header with score
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.markdown(f"### {info['icon']} {info['name']}")
                
                with col2:
                    st.metric("Score", f"{category_score:.1f}/100")
                
                with col3:
                    st.metric("Weight", f"{weight*100:.0f}%")
                    st.caption(f"Contrib: {weighted_contribution:.1f}")
                
                with col4:
                    # Count issues for this category
                    category_name = info['name']
                    category_issue_count = 0
                    for severity in ['high', 'major', 'medium', 'low']:
                        issues = issues_by_severity.get(severity, [])
                        for issue in issues:
                            if issue.get('category') == category_name:
                                category_issue_count += 1
                    
                    if category_issue_count > 0:
                        st.metric("Issues", category_issue_count)
                    else:
                        st.metric("Issues", "0 ✅")
                
                # Progress bar with color coding
                if category_score >= 80:
                    st.success(f"Score: {category_score:.1f}/100")
                    st.progress(category_score / 100)
                elif category_score >= 60:
                    st.warning(f"Score: {category_score:.1f}/100")
                    st.progress(category_score / 100)
                else:
                    st.error(f"Score: {category_score:.1f}/100")
                    st.progress(category_score / 100)
                
                # Expandable section for agent details and issues
                with st.expander(f"📋 View Details for {info['name']}", expanded=False):
                    # Show agent scores in this category
                    if agents_data:
                        st.markdown("#### Agent Scores")
                        for agent_name, agent_score in agents_data.items():
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{agent_name.replace('_', ' ').title()}**")
                            with col2:
                                icon = "✅" if agent_score >= 80 else "⚠️" if agent_score >= 60 else "❌"
                                st.markdown(f"{icon} {agent_score}/100")
                    
                    # Show issues for this category
                    st.markdown("#### Issues")
                    category_name = info['name']
                    
                    # Collect issues for this category
                    category_issues = {
                        'high': [],
                        'medium': [],
                        'low': []
                    }
                    
                    for severity in ['high', 'major', 'medium', 'low']:
                        issues = issues_by_severity.get(severity, [])
                        for issue in issues:
                            if issue.get('category') == category_name:
                                # Map 'major' to 'high' for display
                                severity_key = 'high' if severity == 'major' else severity
                                category_issues[severity_key].append(issue)
                    
                    # Display issues by severity
                    total_category_issues = sum(len(issues) for issues in category_issues.values())
                    
                    if total_category_issues == 0:
                        st.success("✅ No issues found in this category")
                    else:
                        # Helper function to extract feature details from agent reports
                        def get_affected_features(component, issue_text):
                            """Extract affected features from agent reports based on issue type."""
                            features = []
                            
                            # Widget Validation features
                            if component == "Widget Validation" and "widget_validation" in reports:
                                widget_report = reports["widget_validation"]
                                
                                if "population behavior" in issue_text.lower():
                                    # Extract features with missing population
                                    if "recommendations" in widget_report:
                                        for rec in widget_report["recommendations"]:
                                            if "population" in rec.get("issue", "").lower():
                                                features = rec.get("features", [])
                                                break
                                
                                elif "widget" in issue_text.lower() and "summary" in widget_report:
                                    # Get count of features without widgets
                                    summary = widget_report["summary"]
                                    count = summary.get("features_without_widgets", 0)
                                    if count > 0:
                                        # Try to extract specific features from validations
                                        if "validations" in widget_report:
                                            features = [
                                                v["feature_identifier"] 
                                                for v in widget_report["validations"] 
                                                if v.get("current_widget") is None or v.get("current_widget") == ""
                                            ]
                            
                            # Feature Quality features
                            elif component == "Feature Quality" and "feature_quality" in reports:
                                feature_report = reports["feature_quality"]
                                
                                if "training flag" in issue_text.lower():
                                    # Extract features with training flag mismatch
                                    if "validations" in feature_report:
                                        for validation in feature_report["validations"]:
                                            if validation.get("type") == "UI Validation":
                                                checks = validation.get("checks", [])
                                                features = [
                                                    c["feature_identifier"]
                                                    for c in checks
                                                    if c.get("status") == "fail" and 
                                                       any("training flag" in issue.lower() for issue in c.get("issues", []))
                                                ]
                                                break
                            
                            # SDLC features (trace queries, unit tests)
                            elif component == "SDLC" and "sdlc" in reports:
                                sdlc_report = reports["sdlc"]
                                
                                if "trace query" in issue_text.lower() or "trace queries" in issue_text.lower():
                                    # Try to extract from SDLC report
                                    # Note: SDLC report structure may vary
                                    if isinstance(sdlc_report, dict) and "missing_trace_queries" in sdlc_report:
                                        features = sdlc_report.get("missing_trace_queries", [])
                            
                            return features
                        
                        # High priority issues
                        if category_issues['high']:
                            st.markdown(f"**🔴 High Priority ({len(category_issues['high'])})**")
                            for issue in category_issues['high']:
                                component = issue.get('component', 'Unknown')
                                issue_text = issue.get('issue', '')
                                impact = issue.get('impact', '')
                                
                                st.error(f"**[{component}]** {issue_text}")
                                if impact:
                                    st.caption(f"Impact: {impact}")
                                
                                # Show affected features
                                affected = get_affected_features(component, issue_text)
                                if affected:
                                    if len(affected) <= 5:
                                        st.caption(f"🔹 Affected features: {', '.join(affected)}")
                                    else:
                                        with st.expander(f"🔹 View {len(affected)} affected features"):
                                            st.write(", ".join(affected))
                        
                        # Medium priority issues
                        if category_issues['medium']:
                            st.markdown(f"**🟡 Medium Priority ({len(category_issues['medium'])})**")
                            for issue in category_issues['medium']:
                                component = issue.get('component', 'Unknown')
                                issue_text = issue.get('issue', '')
                                impact = issue.get('impact', '')
                                
                                st.warning(f"**[{component}]** {issue_text}")
                                if impact:
                                    st.caption(f"Impact: {impact}")
                                
                                # Show affected features
                                affected = get_affected_features(component, issue_text)
                                if affected:
                                    if len(affected) <= 5:
                                        st.caption(f"🔹 Affected features: {', '.join(affected)}")
                                    else:
                                        with st.expander(f"🔹 View {len(affected)} affected features"):
                                            st.write(", ".join(affected))
                        
                        # Low priority issues
                        if category_issues['low']:
                            st.markdown(f"**🟢 Low Priority ({len(category_issues['low'])})**")
                            for issue in category_issues['low']:
                                component = issue.get('component', 'Unknown')
                                issue_text = issue.get('issue', '')
                                impact = issue.get('impact', '')
                                
                                st.info(f"**[{component}]** {issue_text}")
                                if impact:
                                    st.caption(f"Impact: {impact}")
                                
                                # Show affected features
                                affected = get_affected_features(component, issue_text)
                                if affected:
                                    if len(affected) <= 5:
                                        st.caption(f"🔹 Affected features: {', '.join(affected)}")
                                    else:
                                        with st.expander(f"🔹 View {len(affected)} affected features"):
                                            st.write(", ".join(affected))
                
                st.markdown("---")
        
        # 3. RECOMMENDATIONS
        st.markdown("## 🎯 Recommendations")
        
        recommendations = manager_report.get('recommendations', [])
        if recommendations:
            # Group by priority
            high_priority = [r for r in recommendations if isinstance(r, dict) and r.get('priority') == 'HIGH']
            medium_priority = [r for r in recommendations if isinstance(r, dict) and r.get('priority') == 'MEDIUM']
            low_priority = [r for r in recommendations if isinstance(r, dict) and r.get('priority') == 'LOW']
            
            # High priority (always shown)
            if high_priority:
                st.markdown("### 🔴 High Priority")
                for idx, rec in enumerate(high_priority, 1):
                    category = rec.get('category', 'N/A')
                    component = rec.get('component', 'N/A')
                    action = rec.get('action', '')
                    effort = rec.get('effort', 'N/A')
                    impact = rec.get('impact', 'N/A')
                    
                    with st.container():
                        st.error(f"**{idx}. [{component}]** {action}")
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.caption(f"📂 Category: {category}")
                        with col2:
                            st.caption(f"⏱️ Effort: {effort}")
                        with col3:
                            st.caption(f"💥 Impact: {impact}")
                st.markdown("---")
            
            # Medium priority (expandable)
            if medium_priority:
                with st.expander(f"🟡 Medium Priority ({len(medium_priority)})", expanded=False):
                    for idx, rec in enumerate(medium_priority, 1):
                        category = rec.get('category', 'N/A')
                        component = rec.get('component', 'N/A')
                        action = rec.get('action', '')
                        effort = rec.get('effort', 'N/A')
                        impact = rec.get('impact', 'N/A')
                        
                        st.warning(f"**{idx}. [{component}]** {action}")
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.caption(f"📂 Category: {category}")
                        with col2:
                            st.caption(f"⏱️ Effort: {effort}")
                        with col3:
                            st.caption(f"💥 Impact: {impact}")
            
            # Low priority (expandable, collapsed by default)
            if low_priority:
                with st.expander(f"🟢 Low Priority ({len(low_priority)})", expanded=False):
                    for idx, rec in enumerate(low_priority, 1):
                        category = rec.get('category', 'N/A')
                        component = rec.get('component', 'N/A')
                        action = rec.get('action', '')
                        effort = rec.get('effort', 'N/A')
                        impact = rec.get('impact', 'N/A')
                        
                        st.info(f"**{idx}. [{component}]** {action}")
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.caption(f"📂 Category: {category}")
                        with col2:
                            st.caption(f"⏱️ Effort: {effort}")
                        with col3:
                            st.caption(f"💥 Impact: {impact}")
        else:
            st.success("✅ No recommendations - all validations passed!")
    
    elif manager_report and "raw" in manager_report:
        st.warning("⚠️ Manager report is in text format, not structured JSON")
        with st.expander("View Raw Manager Report", expanded=False):
            st.text(manager_report["raw"])
    
    else:
        st.info("👆 No validation results available. Run validation to see results.")

with tab3:
    st.markdown("### 🔄 Compare Validation Runs")
    
    if previous_runs and len(previous_runs) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            run1 = st.selectbox(
                "Select First Run",
                options=previous_runs,
                format_func=lambda x: f"{x.name} ({datetime.fromtimestamp(x.stat().st_mtime).strftime('%Y-%m-%d %H:%M')})",
                index=0
            )
        
        with col2:
            run2 = st.selectbox(
                "Select Second Run",
                options=previous_runs,
                format_func=lambda x: f"{x.name} ({datetime.fromtimestamp(x.stat().st_mtime).strftime('%Y-%m-%d %H:%M')})",
                index=min(1, len(previous_runs)-1)
            )
        
        if run1 and run2 and run1 != run2:
            # Load both manager reports
            def load_manager_report(run_dir):
                manager_file = run_dir / f"manager_consolidated_report_{domain}.json"
                if manager_file.exists():
                    try:
                        with open(manager_file, 'r') as f:
                            return json.load(f)
                    except:
                        pass
                return None
            
            report1 = load_manager_report(run1)
            report2 = load_manager_report(run2)
            
            if report1 and report2:
                st.markdown("---")
                
                # Score comparison
                st.markdown("### 📊 Score Comparison")
                
                score1 = report1.get('final_quality_score', 0)
                score2 = report2.get('final_quality_score', 0)
                score_diff = score2 - score1
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "First Run",
                        f"{score1:.1f}/100",
                        delta=None
                    )
                    st.caption(datetime.fromtimestamp(run1.stat().st_mtime).strftime('%Y-%m-%d %H:%M'))
                
                with col2:
                    st.metric(
                        "Second Run",
                        f"{score2:.1f}/100",
                        delta=f"{score_diff:+.1f}"
                    )
                    st.caption(datetime.fromtimestamp(run2.stat().st_mtime).strftime('%Y-%m-%d %H:%M'))
                
                with col3:
                    if score_diff > 0:
                        st.success(f"✅ Improvement: +{score_diff:.1f}")
                    elif score_diff < 0:
                        st.error(f"❌ Regression: {score_diff:.1f}")
                    else:
                        st.info("➖ No change")
                
                st.markdown("---")
                
                # Category comparison
                st.markdown("### 📈 Category Scores")
                
                categories1 = report1.get('category_scores', {})
                categories2 = report2.get('category_scores', {})
                
                for category_key in categories1.keys():
                    cat1 = categories1.get(category_key, {})
                    cat2 = categories2.get(category_key, {})
                    
                    score1_cat = cat1.get('score', 0)
                    score2_cat = cat2.get('score', 0)
                    diff = score2_cat - score1_cat
                    
                    category_name = category_key.replace('_', ' ').title()
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{category_name}**")
                    
                    with col2:
                        st.metric("Run 1", f"{score1_cat:.1f}")
                    
                    with col3:
                        st.metric("Run 2", f"{score2_cat:.1f}", delta=f"{diff:+.1f}")
                
                st.markdown("---")
                
                # Issues comparison
                st.markdown("### 🔍 Issues Comparison")
                
                issues1 = report1.get('issues_by_severity', {})
                issues2 = report2.get('issues_by_severity', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### First Run")
                    for severity in ['major', 'high', 'medium', 'low']:
                        count = len(issues1.get(severity, []))
                        if count > 0:
                            severity_display = 'high' if severity == 'major' else severity
                            emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                            st.metric(f"{emoji.get(severity_display, '⚪')} {severity_display.title()}", count)
                
                with col2:
                    st.markdown("#### Second Run")
                    for severity in ['major', 'high', 'medium', 'low']:
                        count1 = len(issues1.get(severity, []))
                        count2 = len(issues2.get(severity, []))
                        diff = count2 - count1
                        if count2 > 0 or count1 > 0:
                            severity_display = 'high' if severity == 'major' else severity
                            emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                            st.metric(
                                f"{emoji.get(severity_display, '⚪')} {severity_display.title()}",
                                count2,
                                delta=f"{diff:+d}" if diff != 0 else None,
                                delta_color="inverse"
                            )
            else:
                st.warning("⚠️ Could not load one or both manager reports")
    else:
        st.info("Need at least 2 validation runs to compare. Run validation to generate more reports.")

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

with tab4:
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
