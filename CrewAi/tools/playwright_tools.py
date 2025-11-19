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
        """Generate comprehensive performance summary with weighted quality scoring.
        
        Quality Score Breakdown (agent_performance.md):
        - Load Time Performance (45%): Page load times across critical workflows
        - UI Responsiveness (25%): Click response, frame rates, interaction smoothness
        - Network Performance (20%): API response times, resource loading efficiency
        - Stability (10%): Memory usage, performance consistency
        """
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
        
        # Calculate comprehensive performance grades
        load_time_grade = self._calculate_grade(load_times)
        load_time_score = self._metric_to_score(load_time_grade.split(" - ")[1])  # Extract grade part
        
        ui_responsiveness = self._calculate_ui_responsiveness_grade(steps)
        network_performance = self._calculate_network_performance_grade(steps)
        stability = self._calculate_stability_grade(steps, load_times)
        
        # Calculate weighted quality score (45%/25%/20%/10%)
        weighted_score = (
            load_time_score * 0.45 +
            ui_responsiveness["overall_score"] * 0.25 +
            network_performance["overall_score"] * 0.20 +
            stability["overall_score"] * 0.10
        )
        
        overall_quality_grade = self._score_to_grade(weighted_score)
        
        # Extract memory and resource metrics for backward compatibility
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
            "quality_score": {
                "overall_score": round(weighted_score, 1),
                "overall_grade": overall_quality_grade,
                "category_breakdown": {
                    "load_time_performance": {
                        "weight": "45%",
                        "score": round(load_time_score, 1),
                        "grade": load_time_grade,
                        "avg_load_time_s": round(sum(load_times) / len(load_times), 3),
                        "max_load_time_s": round(max(load_times), 3),
                        "min_load_time_s": round(min(load_times), 3)
                    },
                    "ui_responsiveness": {
                        "weight": "25%",
                        "score": ui_responsiveness["overall_score"],
                        "grade": ui_responsiveness["overall_grade"],
                        "details": ui_responsiveness["metrics"]
                    },
                    "network_performance": {
                        "weight": "20%",
                        "score": network_performance["overall_score"],
                        "grade": network_performance["overall_grade"],
                        "details": network_performance["metrics"]
                    },
                    "stability": {
                        "weight": "10%",
                        "score": stability["overall_score"],
                        "grade": stability["overall_grade"],
                        "details": stability["metrics"]
                    }
                }
            },
            # Legacy compatibility sections
            "performance_metrics": {
                "average_load_time_s": round(sum(load_times) / len(load_times), 3),
                "max_load_time_s": round(max(load_times), 3),
                "min_load_time_s": round(min(load_times), 3),
                "performance_grade": load_time_grade
            }
        }
        
        # Add memory metrics if available (backward compatibility)
        if memory_info:
            summary["memory_usage"] = {
                "js_heap_used_mb": memory_info.get("js_heap_used_mb", 0),
                "js_heap_total_mb": memory_info.get("js_heap_total_mb", 0),
                "system_memory_used_mb": memory_info.get("system_memory_used_mb", 0),
                "memory_efficiency": self._calculate_memory_efficiency(memory_info)
            }
        
        # Add resource timing if available (backward compatibility)
        if resource_info:
            summary["resource_performance"] = {
                "total_resources": resource_info.get("resource_count", 0),
                "avg_response_time_s": resource_info.get("avg_response_time_s", 0),
                "slowest_resource_time_s": resource_info.get("slowest_resource_time_s", 0),
                "fastest_resource_time_s": resource_info.get("fastest_resource_time_s", 0)
            }
        
        # Add web vitals if available (backward compatibility)
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
    
    def _calculate_ui_responsiveness_grade(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate UI responsiveness grade based on user-provided benchmarks.
        
        Benchmarks:
        - Average Frame Rate: ≥60fps=Excellent, 45-59fps=Good, 30-44fps=Fair, <30fps=Poor
        - Total Blocking Time: <200ms=Excellent, 200-600ms=Good, 600-1000ms=Fair, >1000ms=Poor
        - Long Tasks Count: 0=Excellent, 1-2=Good, 3-5=Fair, >5=Poor
        """
        # Collect UI responsiveness metrics from all steps
        frame_rates = []
        blocking_times = []
        long_tasks_counts = []
        
        for step in steps:
            ui_resp = step.get("ui_responsiveness", {})
            if ui_resp.get("avg_frame_rate"):
                frame_rates.append(ui_resp["avg_frame_rate"])
            if ui_resp.get("total_blocking_time_s") is not None:
                blocking_times.append(ui_resp["total_blocking_time_s"] * 1000)  # Convert to ms
            if ui_resp.get("long_tasks_count") is not None:
                long_tasks_counts.append(ui_resp["long_tasks_count"])
        
        # Calculate averages
        avg_fps = sum(frame_rates) / len(frame_rates) if frame_rates else 0
        avg_blocking_time_ms = sum(blocking_times) / len(blocking_times) if blocking_times else 0
        total_long_tasks = sum(long_tasks_counts) if long_tasks_counts else 0
        
        # Grade each metric
        fps_grade = self._grade_fps(avg_fps)
        blocking_grade = self._grade_blocking_time(avg_blocking_time_ms)
        long_tasks_grade = self._grade_long_tasks(total_long_tasks)
        
        # Calculate overall UI responsiveness score (0-100)
        fps_score = self._metric_to_score(fps_grade)
        blocking_score = self._metric_to_score(blocking_grade)
        long_tasks_score = self._metric_to_score(long_tasks_grade)
        
        overall_score = (fps_score + blocking_score + long_tasks_score) / 3
        overall_grade = self._score_to_grade(overall_score)
        
        return {
            "overall_grade": overall_grade,
            "overall_score": round(overall_score, 1),
            "metrics": {
                "avg_frame_rate": round(avg_fps, 1),
                "fps_grade": fps_grade,
                "avg_blocking_time_ms": round(avg_blocking_time_ms, 1),
                "blocking_grade": blocking_grade,
                "total_long_tasks": total_long_tasks,
                "long_tasks_grade": long_tasks_grade
            }
        }
    
    def _calculate_network_performance_grade(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate network performance grade based on user-provided benchmarks.
        
        Benchmarks:
        - Average Response Time: <0.2s=Excellent, 0.2-0.4s=Good, 0.4-0.6s=Fair, >0.6s=Poor
        - Slowest Resource Time: <0.5s=Excellent, 0.5-1.0s=Good, 1.0-2.0s=Fair, >2.0s=Poor
        - Total Transfer Size: <0.5MB=Excellent, 0.5-2.0MB=Good, 2.0-5.0MB=Fair, >5.0MB=Poor
        """
        # Collect network metrics from all steps
        response_times = []
        slowest_times = []
        transfer_sizes = []
        
        for step in steps:
            resource_timing = step.get("resource_timing", {})
            if resource_timing.get("avg_response_time_s"):
                response_times.append(resource_timing["avg_response_time_s"])
            if resource_timing.get("slowest_resource_time_s"):
                slowest_times.append(resource_timing["slowest_resource_time_s"])
            if resource_timing.get("total_transfer_size_mb"):
                transfer_sizes.append(resource_timing["total_transfer_size_mb"])
        
        # Calculate averages/totals
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_slowest_time = max(slowest_times) if slowest_times else 0
        total_transfer_mb = sum(transfer_sizes) if transfer_sizes else 0
        
        # Grade each metric
        response_grade = self._grade_response_time(avg_response_time)
        slowest_grade = self._grade_slowest_resource(max_slowest_time)
        transfer_grade = self._grade_transfer_size(total_transfer_mb)
        
        # Calculate overall network performance score (0-100)
        response_score = self._metric_to_score(response_grade)
        slowest_score = self._metric_to_score(slowest_grade)
        transfer_score = self._metric_to_score(transfer_grade)
        
        overall_score = (response_score + slowest_score + transfer_score) / 3
        overall_grade = self._score_to_grade(overall_score)
        
        return {
            "overall_grade": overall_grade,
            "overall_score": round(overall_score, 1),
            "metrics": {
                "avg_response_time_s": round(avg_response_time, 3),
                "response_grade": response_grade,
                "max_slowest_time_s": round(max_slowest_time, 3),
                "slowest_grade": slowest_grade,
                "total_transfer_mb": round(total_transfer_mb, 2),
                "transfer_grade": transfer_grade
            }
        }
    
    def _calculate_stability_grade(self, steps: List[Dict[str, Any]], load_times: List[float]) -> Dict[str, Any]:
        """Calculate stability grade based on performance consistency and memory usage.
        
        Benchmarks:
        - Memory Usage: <50MB=Excellent, 50-100MB=Good, 100-200MB=Fair, >200MB=Poor
        - Performance Consistency: Based on coefficient of variation of load times
        """
        # Memory usage assessment
        memory_usages = []
        for step in steps:
            memory_metrics = step.get("memory_metrics", {})
            if memory_metrics.get("js_heap_used_mb"):
                memory_usages.append(memory_metrics["js_heap_used_mb"])
        
        avg_memory_mb = sum(memory_usages) / len(memory_usages) if memory_usages else 0
        memory_grade = self._grade_memory_usage(avg_memory_mb)
        
        # Performance consistency (coefficient of variation)
        if len(load_times) > 1:
            import statistics
            mean_time = statistics.mean(load_times)
            std_time = statistics.stdev(load_times)
            cv = std_time / mean_time if mean_time > 0 else 0
        else:
            cv = 0
        
        consistency_grade = self._grade_consistency(cv)
        
        # Calculate overall stability score (0-100)
        memory_score = self._metric_to_score(memory_grade)
        consistency_score = self._metric_to_score(consistency_grade)
        
        overall_score = (memory_score + consistency_score) / 2
        overall_grade = self._score_to_grade(overall_score)
        
        return {
            "overall_grade": overall_grade,
            "overall_score": round(overall_score, 1),
            "metrics": {
                "avg_memory_mb": round(avg_memory_mb, 1),
                "memory_grade": memory_grade,
                "performance_cv": round(cv, 3),
                "consistency_grade": consistency_grade
            }
        }
    
    # Helper methods for individual metric grading
    def _grade_fps(self, fps: float) -> str:
        if fps >= 60: return "Excellent"
        elif fps >= 45: return "Good"
        elif fps >= 30: return "Fair"
        else: return "Poor"
    
    def _grade_blocking_time(self, ms: float) -> str:
        if ms < 200: return "Excellent"
        elif ms < 600: return "Good"
        elif ms < 1000: return "Fair"
        else: return "Poor"
    
    def _grade_long_tasks(self, count: int) -> str:
        if count == 0: return "Excellent"
        elif count <= 2: return "Good"
        elif count <= 5: return "Fair"
        else: return "Poor"
    
    def _grade_response_time(self, seconds: float) -> str:
        if seconds < 0.2: return "Excellent"
        elif seconds < 0.4: return "Good"
        elif seconds < 0.6: return "Fair"
        else: return "Poor"
    
    def _grade_slowest_resource(self, seconds: float) -> str:
        if seconds < 0.5: return "Excellent"
        elif seconds < 1.0: return "Good"
        elif seconds < 2.0: return "Fair"
        else: return "Poor"
    
    def _grade_transfer_size(self, mb: float) -> str:
        if mb < 0.5: return "Excellent"
        elif mb < 2.0: return "Good"
        elif mb < 5.0: return "Fair"
        else: return "Poor"
    
    def _grade_memory_usage(self, mb: float) -> str:
        if mb < 50: return "Excellent"
        elif mb < 100: return "Good"
        elif mb < 200: return "Fair"
        else: return "Poor"
    
    def _grade_consistency(self, cv: float) -> str:
        """Grade performance consistency based on coefficient of variation."""
        if cv < 0.1: return "Excellent"  # Very consistent
        elif cv < 0.3: return "Good"     # Reasonably consistent
        elif cv < 0.5: return "Fair"     # Moderate variation
        else: return "Poor"              # High variation
    
    def _metric_to_score(self, grade: str) -> float:
        """Convert grade to numeric score (0-100)."""
        scores = {
            "Excellent": 95.0,
            "Good": 80.0,
            "Fair": 65.0,
            "Poor": 40.0
        }
        return scores.get(grade, 0.0)
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90: return "A - Excellent"
        elif score >= 80: return "B - Good"
        elif score >= 70: return "C - Average"
        elif score >= 60: return "D - Poor"
        else: return "F - Critical"


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