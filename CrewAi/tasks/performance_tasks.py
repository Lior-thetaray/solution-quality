"""Performance testing task factory following the same pattern as SDLC tasks.

Creates performance validation tasks for Playwright testing agents.
"""

from crewai import Task


def create_performance_task(agent, target_url: str = None) -> Task:
    """Create a performance testing task for Playwright agents.
    
    Args:
        agent: The performance testing agent that will execute this task
        target_url: Target URL to test (will be prompted at runtime if not provided)
        
    Returns:
        Task that lets the agent autonomously execute comprehensive performance testing
    """
    return Task(
        description=f"""Execute comprehensive performance testing against a ThetaRay application using Chromium browser in headless mode.

The test will execute tests/test_performance.py which runs the complete user workflow:
1. Runtime configuration setup (URL, username, password will be requested securely)
2. Login and authentication
3. Alert list page load time measurement  
4. Alert details navigation and feature testing (feature_0, feature_1, etc.)
5. Network visualization performance testing
6. Filter application (date range, depth filters) and interaction responsiveness

Use your PlaywrightPerformanceTool to execute test_performance.py and wait for results.
The test measures actual load times for critical analyst workflows using step-by-step timing.

Analyze the results and provide performance recommendations to improve user experience.
Focus on identifying bottlenecks, slow-loading components, and areas for optimization.""",
        
        expected_output="""JSON report from PlaywrightPerformanceTool containing streamlined Playwright test results:

CrewAI Tool Wrapper Structure:
- tool: "playwright_performance"
- test_type: "comprehensive" 
- configuration: {base_url, browser_type, headless, network_config}
- results: {test_metadata, measurements[], summary}
- status: "success" or "failed"
- summary: analyzed performance metrics

The 'results' field contains the streamlined Playwright JSON with:
- test_metadata: test timing, network config
- measurements[]: array of 10 steps with detailed timing:
  - Step 1: alert_list.initial_load
  - Steps 2-6: feature_0_load through feature_4_load
  - Step 7: network_visualization.initial_load
  - Step 8: network_visualization.date_filter_application  
  - Step 9: network_visualization.depth_filter_application
- Each step includes: load_time_s, core_web_vitals, memory_metrics, resource_timing, ui_responsiveness
- Core web vitals: simplified metrics without redundant format indicators
- Resource timing: summary metrics only (no detailed resource objects)
- Memory metrics: consolidated system and JS heap measurements
- summary: total_steps, pages_measured, average/min/max load times, slowest/fastest steps

Analyze the streamlined performance data and provide specific optimization recommendations.""",
        
        agent=agent
    )


# Note: The Playwright solution contains one comprehensive test (test_performance.py) that:
# - Prompts for runtime configuration (URL, credentials) securely
# - Executes complete analyst workflow with step-by-step timing
# - Measures: alert list, feature widgets, network visualization, filter interactions
# - Generates detailed JSON report with performance metrics and browser data