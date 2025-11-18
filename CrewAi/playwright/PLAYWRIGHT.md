# Playwright Integration

## Actual Playwright Functionality

The copied Playwright solution contains **one comprehensive test** in `test_performance.py` that:

1. **Authenticates** with ThetaRay application
2. **Navigates to alert list** and measures page load time
3. **Selects a use case** (dpv:demo_fuib)
4. **Clicks first alert** and navigates to alert details
5. **Tests all feature widgets** - measures load time for each feature
6. **Opens network visualization** and measures rendering performance
7. **Applies filters** (date range, depth) and measures response time
8. **Generates comprehensive JSON report** with all timing measurements

## Corrected Menu Structure

### Performance Testing Mode
Instead of fake options, now shows:
```
Select browser type:
  1. Chromium (default)
  2. Firefox  
  3. Webkit
```

**Test Type:** Always comprehensive (includes alert list + features + network viz)

## Tools Behavior

### PlaywrightPerformanceTool (Single Tool)
- **Function:** Executes the comprehensive test_performance.py
- **Measures:** Complete analyst workflow with step-by-step timing
- **Output:** JSON report with detailed performance metrics
- **Security:** Prompts for credentials at runtime or uses environment variables
- **Browser:** Uses Chromium headless mode for consistent results

## Test Workflow (What Actually Happens)

```
1. Login Page → Authentication
2. Alert List Page → Load time measurement
3. Use Case Selection → Navigation timing  
4. Alert Details Page → Feature testing
   ├── Feature 0 → Load time
   ├── Feature 1 → Load time
   ├── Feature N → Load time
5. Network Visualization → Graph rendering
   ├── Initial load → Timing
   ├── Date filter → Response time
   ├── Depth filter → Response time
6. Report Generation → JSON output
```

## Performance Metrics Captured

The test generates a **steps array** with detailed timing for each action:
- Step-by-step load times with timestamps
- Action-specific metrics (login, page loads, feature interactions)
- Memory usage data (JS heap, system memory)
- Resource timing (network requests, response times)
- Core Web Vitals (CLS, FCP, TTI)
- UI responsiveness metrics

## Streamlined Playwright JSON Output Format

The test generates a streamlined performance report JSON file with this structure:

```json
{
  "test_metadata": {
    "test_name": "alert_system_performance_test",
    "test_start": "2025-11-19T10:56:07.845180",
    "test_end": "2025-11-19T10:57:01.752593",
    "total_duration_sec": 53.91,
    "network_config": {
      "download_mbps": 9765.62,
      "upload_mbps": 683.59,
      "latency_ms": 40
    }
  },
  "measurements": [
    {
      "step": 1,
      "page": "alert_list",
      "action": "initial_load",
      "timestamp": "2025-11-19T10:56:22.379525",
      "load_time_s": 1.894,
      "core_web_vitals": {
        "largest_contentful_paint_s": null,
        "first_input_delay_s": null,
        "cumulative_layout_shift_s": 0.0,
        "first_contentful_paint_s_s": 0.002,
        "time_to_interactive_s_s": 0.0
      },
      "memory_metrics": {
        "js_heap_used_mb": null,
        "js_heap_total_mb": null,
        "js_heap_limit_mb": null,
        "system_memory_used_mb": 27.0,
        "system_memory_percent": 0.11
      },
      "resource_timing": {
        "resource_count": 9,
        "total_transfer_size_mb": 0.01,
        "avg_response_time_s": 0.174,
        "slowest_resource_time_s": 0.323,
        "fastest_resource_time_s": 0.136
      },
      "ui_responsiveness": {
        "long_tasks_count": 0,
        "total_blocking_time_s": 0.0,
        "avg_frame_rate": 144.28,
        "interaction_response_time_s": null
      }
    },
    {
      "step": 2,
      "page": "alert_details", 
      "action": "initial_load",
      "load_time_s": 0.659,
      "feature_index": 0,
      // ... same streamlined metrics structure
    },
    // ... steps 3-7 for features 0-4
    {
      "step": 8,
      "page": "network_visualization",
      "action": "initial_load", 
      "load_time_s": 1.483,
      "metrics": {
        "visualization_specific": {
          "chart_rendering": {
            "canvas_elements_found": 1,
            "canvas_elements_with_content": 1,
            "rendering_likely_complete": true
          }
        }
      }
    },
    {
      "step": 9,
      "page": "network_visualization",
      "action": "date_filter_application",
      "load_time_s": 4.151,
      "metrics": {
        "filter_name": "date_range",
        "application_time_ms_s": 4.151,
        "dom_nodes_added_s": -0.001,
        "network_requests_added_s": 0.003
      },
      "filters": {
        "date_from": "01/01/2025",
        "date_to": "30/06/2025"
      }
    },
    {
      "step": 10,
      "page": "network_visualization", 
      "action": "depth_filter_application",
      "load_time_s": 1.557,
      "filters": { "depth": "3" }
    }
  ],
  "summary": {
    "total_steps": 10,
    "pages_measured": ["alert_details", "network_visualization", "alert_list", "feature"],
    "average_load_time_s": 2.091,
    "min_load_time_s": 0.659,
    "max_load_time_s": 4.151,
    "slowest_step": {
      "step": 9,
      "page": "network_visualization",
      "action": "date_filter_application",
      "load_time_s": 4.151
    },
    "fastest_step": {
      "step": 2,
      "page": "alert_details", 
      "action": "initial_load",
      "load_time_s": 0.659
    }
  }
}
```

## CrewAI Tool Wrapper Output

When executed via CrewAI's PlaywrightPerformanceTool, the above JSON is wrapped in:

```json
{
  "tool": "playwright_performance",
  "test_type": "comprehensive", 
  "configuration": { "base_url": "...", "browser_type": "chromium" },
  "results": { /* the full Playwright JSON above */ },
  "status": "success",
  "summary": { /* analyzed summary from the tool */ }
}
```

## Configuration

### Runtime Security Implementation
The test now uses **secure runtime configuration** with no hardcoded credentials:
- **Target URL:** Prompted at runtime or from `THETARAY_BASE_URL` environment variable
- **Credentials:** Prompted securely at runtime or from `THETARAY_USERNAME`/`THETARAY_PASSWORD` env vars
- **Browser Settings:** `BROWSER_TYPE`, `HEADLESS`, `VIEWPORT` from config.py
- **Network Emulation:** `NETWORK_CONFIG` (1 Gbps fiber simulation)

### Security Features
- **No hardcoded secrets** anywhere in source code
- **Masked password input** using getpass (password not visible)
- **Session-only caching** - credentials cleared after test
- **Environment variable support** for CI/CD automation

## Usage

### Interactive Mode
```bash
cd CrewAi
python main.py
# Choose option 2 (Performance Testing)
# You'll be prompted for:
#   - Base URL (e.g., https://apps-thetalab.sonar.thetaray.cloud)
#   - Username
#   - Password (hidden input)
# Test executes comprehensive workflow
```

### Environment Variable Mode (CI/CD)
```bash
export THETARAY_BASE_URL="https://your-instance.thetaray.cloud"
export THETARAY_USERNAME="your_username"
export THETARAY_PASSWORD="your_password"
python main.py  # No prompts - uses environment variables
```

## Honest Limitations

1. **Single Test Only:** There is no separate network-only or UI-only test
2. **Fixed Workflow:** Cannot test individual components in isolation
3. **Configuration Dependent:** Test behavior determined by config file
4. **ThetaRay Specific:** Test is designed for specific ThetaRay UI structure

## Benefits of Implementation

- **Accurate Expectations:** Users know exactly what the test does
- **Reliable Results:** No fake functionality that would fail
- **Maintainable Code:** Simple, direct mapping to actual capabilities
- **Clear Reporting:** Results reflect actual test execution

