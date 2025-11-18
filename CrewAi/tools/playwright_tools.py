"""Playwright-based performance testing tools for CrewAI integration."""

import json
import sys
import os
import logging
import importlib.util
import getpass
from pathlib import Path
from typing import Type, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# Set up logging
logger = logging.getLogger(__name__)

# Runtime credential input configuration
# Credentials will be requested at runtime for security

# Cache for runtime credentials (cleared after each test run)
_runtime_credentials = {}

def get_runtime_credentials():
    """Securely prompt for credentials and URL at runtime."""
    global _runtime_credentials
    
    # Check if all required info is already cached for this session
    if (_runtime_credentials.get('username') and 
        _runtime_credentials.get('password') and 
        _runtime_credentials.get('base_url')):
        return _runtime_credentials
    
    # Try environment variables first (optional)
    username = os.getenv('THETARAY_USERNAME')
    password = os.getenv('THETARAY_PASSWORD')
    base_url = os.getenv('THETARAY_BASE_URL')
    
    # If not found in environment, prompt user
    if not username or not password or not base_url:
        print("\n🔐 ThetaRay Performance Testing - Configuration Input")
        print("Please provide your ThetaRay configuration:")
        
        if not base_url:
            base_url = input("Base URL (e.g., https://apps-thetalab.sonar.thetaray.cloud): ").strip()
        
        if not username:
            username = input("Username: ").strip()
        
        if not password:
            password = getpass.getpass("Password: ")
    else:
        print(f"Using configuration from environment variables")
    
    # Validate inputs
    if not username or not password or not base_url:
        raise ValueError("Username, password, and base URL are all required")
    
    # Validate URL format
    if not base_url.startswith(('http://', 'https://')):
        raise ValueError("Base URL must start with http:// or https://")
    
    # Cache for this session
    _runtime_credentials = {
        'username': username,
        'password': password,
        'base_url': base_url
    }
    
    return _runtime_credentials

def clear_runtime_credentials():
    """Clear cached credentials for security."""
    global _runtime_credentials
    _runtime_credentials = {}

# Default configuration (without sensitive data)
DEFAULT_CONFIG = {
    "NETWORK_CONFIG": {
        "download_throughput": 1024000000,
        "upload_throughput": 716800000,
        "latency": 40  
    },
    "VIEWPORT": {"width": 1920, "height": 1080},
    "BROWSER_TYPE": "chromium",
    "HEADLESS": True
}

def load_playwright_config():
    """Dynamically load Playwright configuration."""
    playwright_path = Path(__file__).parent.parent / "playwright"
    config_path = playwright_path / "config" / "config.py"
    
    if config_path.exists():
        try:
            spec = importlib.util.spec_from_file_location("playwright_config", config_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            
            # Get runtime credentials
            try:
                creds = get_runtime_credentials()
            except ValueError as e:
                logger.error(f"Credential error: {e}")
                creds = {'username': '', 'password': ''}
            
            return {
                "BASE_URL": getattr(config_module, "BASE_URL", creds['base_url']),
                "USERNAME": getattr(config_module, "USERNAME", creds['username']),
                "PASSWORD": getattr(config_module, "PASSWORD", creds['password']),
                "NETWORK_CONFIG": getattr(config_module, "NETWORK_CONFIG", DEFAULT_CONFIG["NETWORK_CONFIG"]),
                "VIEWPORT": getattr(config_module, "VIEWPORT", DEFAULT_CONFIG["VIEWPORT"]),
                "BROWSER_TYPE": getattr(config_module, "BROWSER_TYPE", DEFAULT_CONFIG["BROWSER_TYPE"]),
                "HEADLESS": getattr(config_module, "HEADLESS", DEFAULT_CONFIG["HEADLESS"])
            }
        except Exception as e:
            logger.warning(f"Could not load Playwright config: {e}")
            return DEFAULT_CONFIG
    else:
        logger.info("Playwright config not found, using defaults with runtime credentials")
        # Get runtime credentials
        try:
            creds = get_runtime_credentials()
        except ValueError as e:
            logger.error(f"Credential error: {e}")
            creds = {'username': '', 'password': ''}
        
        config = DEFAULT_CONFIG.copy()
        config.update({
            "BASE_URL": creds['base_url'],
            "USERNAME": creds['username'],
            "PASSWORD": creds['password']
        })
        return config

# Load configuration
PLAYWRIGHT_CONFIG = load_playwright_config()
BASE_URL = PLAYWRIGHT_CONFIG["BASE_URL"]
USERNAME = PLAYWRIGHT_CONFIG["USERNAME"]
PASSWORD = PLAYWRIGHT_CONFIG["PASSWORD"]
NETWORK_CONFIG = PLAYWRIGHT_CONFIG["NETWORK_CONFIG"]
VIEWPORT = PLAYWRIGHT_CONFIG["VIEWPORT"]
BROWSER_TYPE = PLAYWRIGHT_CONFIG["BROWSER_TYPE"]
HEADLESS = PLAYWRIGHT_CONFIG["HEADLESS"]


class PlaywrightTestInput(BaseModel):
    """Input schema for Playwright testing tools."""
    target_url: Optional[str] = Field(None, description="Target URL to test (will be prompted at runtime if not provided)")
    browser_type: Optional[str] = Field("chromium", description="Browser type: chromium (default), firefox, webkit")
    headless: Optional[bool] = Field(True, description="Run browser in headless mode (default: True)")
    network_config: Optional[Dict[str, Any]] = Field(None, description="Network configuration overrides")
    custom_selectors: Optional[Dict[str, str]] = Field(None, description="Custom CSS selectors")


class PlaywrightPerformanceTool(BaseTool):
    """Executes the comprehensive Playwright test (test_performance.py) against ThetaRay UI."""
    
    name: str = "Playwright Performance Tester"
    description: str = (
        "Executes test_performance.py which runs the complete ThetaRay user workflow: "
        "login, alert list loading, feature navigation, and network visualization. "
        "Uses Chromium browser in headless mode. Returns comprehensive JSON report with "
        "step-by-step performance metrics, core web vitals, memory usage, resource timing, "
        "UI responsiveness data, and detailed analysis of each action's load time."
    )
    args_schema: Type[BaseModel] = PlaywrightTestInput
    
    def _run(
        self, 
        target_url: Optional[str] = None,
        browser_type: Optional[str] = "chromium",
        headless: Optional[bool] = True,
        network_config: Optional[Dict[str, Any]] = None,
        custom_selectors: Optional[Dict[str, str]] = None
    ) -> str:
        """Execute Playwright performance tests."""
        
        try:
            # Override configuration if provided
            config_overrides = {
                "base_url": target_url or BASE_URL,
                "browser_type": browser_type or BROWSER_TYPE,
                "headless": headless if headless is not None else HEADLESS,
                "network_config": network_config or NETWORK_CONFIG
            }
            
            # Dynamically import and run the original test function
            results = _execute_performance_test(config_overrides)
            
            # Format results for CrewAI
            performance_report = {
                "tool": "playwright_performance",
                "test_type": "comprehensive",  # Always comprehensive since there's only one test
                "configuration": config_overrides,
                "results": results,
                "status": "success",
                "summary": self._generate_summary(results)
            }
            
            # Clear credentials after successful test for security
            clear_runtime_credentials()
            
            return json.dumps(performance_report, indent=2)
            
        except Exception as e:
            # Clear credentials after failed test for security
            clear_runtime_credentials()
            
            error_report = {
                "tool": "playwright_performance",
                "test_type": "comprehensive",  # Always comprehensive since there's only one test
                "error": str(e),
                "status": "failed"
            }
            return json.dumps(error_report, indent=2)
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive performance summary from test results."""
        if not results:
            return {"error": "No valid results found"}
        
        # Handle both old format (measurements) and new format (steps array)
        steps = results.get("measurements", results.get("steps", []))
        
        if not steps:
            return {"error": "No test steps found"}
        
        # Extract load times and detailed metrics
        load_times = [step.get("load_time_s", 0) for step in steps if step.get("load_time_s")]
        
        if not load_times:
            return {"error": "No load time measurements found"}
        
        # Analyze step types and pages
        pages_tested = list(set(step.get("page", "unknown") for step in steps))
        actions_performed = list(set(step.get("action", "unknown") for step in steps))
        
        # Extract memory and resource metrics from the last comprehensive step
        memory_info = None
        resource_info = None
        web_vitals = None
        
        for step in reversed(steps):
            if "memory_metrics" in step:
                memory_info = step["memory_metrics"]
            if "resource_timing" in step:
                resource_info = step["resource_timing"]
            if "core_web_vitals" in step:
                web_vitals = step["core_web_vitals"]
            if memory_info and resource_info and web_vitals:
                break
        
        summary = {
            "test_execution": {
                "total_steps": len(steps),
                "pages_tested": pages_tested,
                "actions_performed": actions_performed,
                "total_duration_s": round(sum(load_times), 3)
            },
            "performance_metrics": {
                "average_load_time_s": round(sum(load_times) / len(load_times), 3),
                "max_load_time_s": round(max(load_times), 3),
                "min_load_time_s": round(min(load_times), 3),
                "performance_grade": self._calculate_grade(load_times)
            }
        }
        
        # Add memory metrics if available
        if memory_info:
            summary["memory_usage"] = {
                "js_heap_used_mb": memory_info.get("js_heap_used_mb", 0),
                "js_heap_total_mb": memory_info.get("js_heap_total_mb", 0),
                "system_memory_used_mb": memory_info.get("system_memory_used_mb", 0),
                "memory_efficiency": self._calculate_memory_efficiency(memory_info)
            }
        
        # Add resource timing if available
        if resource_info:
            summary["resource_performance"] = {
                "total_resources": resource_info.get("resource_count", 0),
                "avg_response_time_s": resource_info.get("avg_response_time_s", 0),
                "slowest_resource_time_s": resource_info.get("slowest_resource_time_s", 0),
                "fastest_resource_time_s": resource_info.get("fastest_resource_time_s", 0)
            }
        
        # Add web vitals if available
        if web_vitals:
            summary["core_web_vitals"] = {
                "cumulative_layout_shift_s": web_vitals.get("cumulative_layout_shift_s", 0),
                "first_contentful_paint_s_s": web_vitals.get("first_contentful_paint_s_s", 0),
                "time_to_interactive_s_s": web_vitals.get("time_to_interactive_s_s", 0)
            }
        
        return summary
    
    def _calculate_grade(self, load_times: List[float]) -> str:
        """Calculate performance grade based on load times.
        
        Thresholds aligned with agent_performance.md standards:
        - Excellent (A): ≤ 1.0s 
        - Good (B): ≤ 2.0s
        - Average (C): ≤ 4.0s  
        - Poor (D): ≤ 6.0s
        - Critical (F): > 6.0s
        """
        avg_time = sum(load_times) / len(load_times)
        if avg_time <= 1.0:
            return "A - Excellent"
        elif avg_time <= 2.0:
            return "B - Good"
        elif avg_time <= 4.0:
            return "C - Average"
        elif avg_time <= 6.0:
            return "D - Poor"
        else:
            return "F - Critical"
    
    def _calculate_memory_efficiency(self, memory_info: Dict[str, Any]) -> str:
        """Calculate memory efficiency grade."""
        heap_used = memory_info.get("js_heap_used_mb", 0)
        heap_total = memory_info.get("js_heap_total_mb", 1)  # Avoid division by zero
        
        usage_ratio = heap_used / heap_total
        
        if usage_ratio <= 0.6:
            return "Efficient"
        elif usage_ratio <= 0.8:
            return "Moderate"
        else:
            return "High Usage"


# Note: Only PlaywrightPerformanceTool is used since the solution 
# contains one comprehensive test (test_performance.py) that covers
# all aspects: alert list, features, and network visualization.


# Helper methods for dynamic test execution
def _execute_performance_test(config_overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Execute performance test with dynamic import."""
    try:
        playwright_path = Path(__file__).parent.parent / "playwright"
        test_path = playwright_path / "tests" / "test_performance.py"
        
        if test_path.exists():
            # Temporarily modify the config if needed
            config_path = playwright_path / "config" / "config.py"
            original_config = None
            
            # Read original config
            if config_path.exists():
                with open(config_path, 'r') as f:
                    original_config = f.read()
            
            spec = importlib.util.spec_from_file_location("test_performance", test_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            
            # Try to call the main test function
            if hasattr(test_module, "run_performance_test"):
                result = test_module.run_performance_test()
                # Add configuration info to result
                if isinstance(result, dict):
                    result["configuration_used"] = config_overrides
                return result
            else:
                return {"error": "run_performance_test function not found"}
        else:
            return {"error": "Performance test file not found"}
    except Exception as e:
        return {"error": f"Failed to execute performance test: {str(e)}"}


# Note: Only one comprehensive test exists (test_performance.py)