#!/usr/bin/env python3
"""Streamlit dashboard for ThetaRay SDLC Validation."""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

from main import setup_environment, create_sdlc_crew

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

# Get previous reports
reports_path = Path("reports")
previous_reports = []
if reports_path.exists():
    previous_reports = sorted(
        [f for f in reports_path.glob(f"sdlc_report_{domain}_*.json")],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

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
        with st.spinner("Running SDLC validation... This may take a few minutes."):
            try:
                # Setup and run
                llm = setup_environment()
                crew = create_sdlc_crew(domain, llm)
                result = crew.kickoff()
                
                # Save to session state
                st.session_state['latest_result'] = str(result)
                st.session_state['validation_time'] = datetime.now()
                st.success("✅ Validation complete!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Validation failed: {str(e)}")

# Display results
st.markdown("---")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 Current Report", "📈 History", "📋 Raw Data"])

with tab1:
    # Load report (from session state or latest file)
    report_data = None
    
    if 'latest_result' in st.session_state:
        try:
            report_data = json.loads(st.session_state['latest_result'])
            st.info(f"🕒 Report generated: {st.session_state['validation_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            pass
    
    if report_data is None and previous_reports:
        with open(previous_reports[0], 'r') as f:
            report_data = json.load(f)
        st.info(f"📁 Showing latest saved report: {previous_reports[0].name}")
    
    if report_data:
        # Quality Score
        st.markdown("### Quality Score")
        score = report_data.get('quality_score', 0)
        
        # Color coding
        if score >= 90:
            color = "green"
            status = "✅ Excellent - Production Ready"
        elif score >= 75:
            color = "lightgreen"
            status = "✅ Good - Minor Improvements Needed"
        elif score >= 60:
            color = "orange"
            status = "⚠️ Acceptable - Several Issues to Address"
        else:
            color = "red"
            status = "❌ Needs Work - Major Issues Found"
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.metric("Score", f"{score}/100")
        with col2:
            st.progress(score / 100)
            st.markdown(f"**{status}**")
        with col3:
            summary = report_data.get('summary', {})
            st.metric("Passed", f"{summary.get('passed', 0)}/{summary.get('total_checks', 0)}")
        
        st.markdown("---")
        
        # Validations
        st.markdown("### Validation Results")
        
        validations = report_data.get('validations', [])
        
        # Summary metrics
        cols = st.columns(len(validations))
        for idx, validation in enumerate(validations):
            with cols[idx]:
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
            
            with st.expander(f"{icon} {validation['name']}", expanded=not validation['pass']):
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
    
    if previous_reports:
        history_data = []
        for report_file in previous_reports[:10]:  # Last 10 reports
            try:
                with open(report_file, 'r') as f:
                    data = json.load(f)
                    history_data.append({
                        'Date': datetime.fromtimestamp(report_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                        'Score': data.get('quality_score', 0),
                        'Passed': data.get('summary', {}).get('passed', 0),
                        'Failed': data.get('summary', {}).get('failed', 0),
                        'File': report_file.name
                    })
            except:
                continue
        
        if history_data:
            df = pd.DataFrame(history_data)
            
            # Line chart
            st.line_chart(df.set_index('Date')['Score'])
            
            # Table
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No historical data available")
    else:
        st.info("No previous reports found. Run your first validation to start tracking history.")

with tab3:
    st.markdown("### Raw JSON Report")
    
    if report_data:
        st.json(report_data)
    else:
        st.info("No report data available")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    ThetaRay SDLC Quality Validator | Powered by CrewAI & Azure OpenAI
    </div>
    """,
    unsafe_allow_html=True
)
