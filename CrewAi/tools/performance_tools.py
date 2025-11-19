"""
Performance Analysis Tools
Tools for reading and analyzing raw performance test reports
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from crewai.tools import BaseTool


class ReadPerformanceReportTool(BaseTool):
    name: str = "Read Performance Report"
    description: str = """
    Reads raw performance test report JSON file for a given domain.
    
    Input: domain name (e.g., 'demo_fuib')
    Output: JSON object with test_metadata, measurements_by_alert, and summary including bucket_averages
    
    The report contains:
    - test_metadata: Test configuration and timing
    - measurements_by_alert: Detailed timing for each alert
    - summary.bucket_averages: Average times for alert_details, feature_loading, network_viz
    """
    
    def _run(self, domain: str) -> str:
        """Read the performance report for the specified domain"""
        try:
            # Get workspace root and find performance report in data directory
            workspace_root = Path(__file__).parent.parent.parent
            perf_data_dir = workspace_root / "CrewAi" / "data" / "performance"
            
            # Look for performance report
            perf_report_path = perf_data_dir / f"performance_report_{domain}.json"
            
            if not perf_report_path.exists():
                return json.dumps({
                    "error": f"Performance report not found",
                    "expected_path": str(perf_report_path),
                    "note": "Raw performance reports should be in data/performance/ directory"
                })
            
            # Read and return the report
            with open(perf_report_path, 'r') as f:
                data = json.load(f)
            
            return json.dumps(data, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Failed to read performance report: {str(e)}",
                "domain": domain
            })


class CalculatePerformanceScoreTool(BaseTool):
    name: str = "Calculate Performance Score"
    description: str = """
    Calculates quality scores for performance metrics based on thresholds.
    
    Input: JSON object with bucket_averages containing:
    - alert_details_avg_s: average time for alert details loading
    - feature_loading_avg_s: average time for feature loading
    - network_viz_avg_s: average time for network visualization
    
    Output: JSON with individual metric scores and overall quality_score (0-100)
    
    Thresholds:
    - alert_details: <1s=100, 1-2s=80, 2-3s=60, >3s=40
    - feature_loading: <2s=100, 2-3s=80, 3-5s=60, >5s=40
    - network_viz: <2s=100, 2-4s=80, 4-6s=60, >6s=40
    """
    
    def _run(self, bucket_averages_json: str) -> str:
        """Calculate scores from bucket averages"""
        try:
            bucket_averages = json.loads(bucket_averages_json)
            
            alert_details = bucket_averages.get('alert_details_avg_s', 0)
            feature_loading = bucket_averages.get('feature_loading_avg_s', 0)
            network_viz = bucket_averages.get('network_viz_avg_s', 0)
            
            # Calculate scores based on thresholds
            def score_alert_details(time_s: float) -> int:
                if time_s < 1.0:
                    return 100
                elif time_s < 2.0:
                    return 80
                elif time_s < 3.0:
                    return 60
                else:
                    return 40
            
            def score_feature_loading(time_s: float) -> int:
                if time_s < 2.0:
                    return 100
                elif time_s < 3.0:
                    return 80
                elif time_s < 5.0:
                    return 60
                else:
                    return 40
            
            def score_network_viz(time_s: float) -> int:
                if time_s < 2.0:
                    return 100
                elif time_s < 4.0:
                    return 80
                elif time_s < 6.0:
                    return 60
                else:
                    return 40
            
            alert_score = score_alert_details(alert_details)
            feature_score = score_feature_loading(feature_loading)
            viz_score = score_network_viz(network_viz)
            
            overall_score = round((alert_score + feature_score + viz_score) / 3)
            
            result = {
                "metric_scores": {
                    "alert_details": {
                        "value": alert_details,
                        "score": alert_score,
                        "pass": alert_score >= 60
                    },
                    "feature_loading": {
                        "value": feature_loading,
                        "score": feature_score,
                        "pass": feature_score >= 60
                    },
                    "network_viz": {
                        "value": network_viz,
                        "score": viz_score,
                        "pass": viz_score >= 60
                    }
                },
                "quality_score": overall_score,
                "passed_count": sum(1 for s in [alert_score, feature_score, viz_score] if s >= 60),
                "failed_count": sum(1 for s in [alert_score, feature_score, viz_score] if s < 60)
            }
            
            return json.dumps(result, indent=2)
            
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Invalid JSON input: {str(e)}"
            })
        except Exception as e:
            return json.dumps({
                "error": f"Failed to calculate scores: {str(e)}"
            })
