"""
Performance tracking and metrics collection utilities.
Handles measurement collection and JSON report generation.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import psutil
import threading
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CoreWebVitals:
    """Core Web Vitals metrics"""
    largest_contentful_paint_s: Optional[float] = None  # LCP in seconds
    first_input_delay_s: Optional[float] = None         # FID in seconds  
    cumulative_layout_shift_s: Optional[float] = None    # CLS score (unitless)
    first_contentful_paint_s_s: Optional[float] = None   # FCP in seconds
    time_to_interactive_s_s: Optional[float] = None      # TTI in seconds


@dataclass
class MemoryMetrics:
    """Memory usage metrics"""
    js_heap_used_mb: Optional[float] = None      # MB
    js_heap_total_mb: Optional[float] = None     # MB
    js_heap_limit_mb: Optional[float] = None     # MB
    system_memory_used_mb: Optional[float] = None # MB
    system_memory_percent: Optional[float] = None # percentage


@dataclass
class ResourceTimingMetrics:
    """Resource loading performance metrics"""
    resource_count: int = 0
    total_transfer_size_mb: float = 0.0  # MB
    avg_response_time_s: Optional[float] = None  # seconds
    slowest_resource_time_s: Optional[float] = None  # seconds
    fastest_resource_time_s: Optional[float] = None  # seconds


@dataclass
class UIResponsivenessMetrics:
    """UI responsiveness and interaction metrics"""
    long_tasks_count: int = 0
    total_blocking_time_s: float = 0.0  # seconds
    avg_frame_rate: Optional[float] = None  # fps
    interaction_response_time_s: Optional[float] = None  # seconds


class PerformanceTracker:
    """Tracks performance metrics and generates JSON reports"""

    def __init__(self, test_name: str, network_config: Dict[str, Any]):
        """
        Initialize PerformanceTracker.

        Args:
            test_name: Name of the test being executed
            network_config: Network configuration used for the test
        """
        self.test_name = test_name
        self.network_config = network_config
        self.start_time = datetime.now()
        self.measurements: List[Dict[str, Any]] = []
        self.step_counter = 0
        self._memory_monitoring = False
        self._memory_samples: List[Dict[str, Any]] = []
        self._memory_thread = None
        self._memory_monitoring = False
        self._memory_samples: List[Dict[str, Any]] = []
        self._memory_thread = None

    def add_measurement(
        self,
        page: str,
        action: str,
        load_time_ms: float,
        metrics: Dict[str, Any],
        core_web_vitals: Optional[CoreWebVitals] = None,
        memory_metrics: Optional[MemoryMetrics] = None,
        resource_timing: Optional[ResourceTimingMetrics] = None,
        ui_responsiveness: Optional[UIResponsivenessMetrics] = None,
        alert_index: Optional[int] = None,
        **kwargs
    ) -> None:
        """
        Add a performance measurement to the tracker.

        Args:
            page: Page identifier (e.g., "alert_list", "alert_details")
            action: Action performed (e.g., "initial_load", "click_first_alert")
            load_time_ms: Total load time in milliseconds
            metrics: Performance metrics dictionary
            core_web_vitals: Core Web Vitals metrics
            memory_metrics: Memory usage metrics
            resource_timing: Resource loading metrics
            ui_responsiveness: UI responsiveness metrics
            **kwargs: Additional data to include (e.g., feature_index, filters)
        """
        # Handle per-alert step counting
        if alert_index is not None:
            # Group measurements by alert - each alert starts from step 1
            alert_measurements = [m for m in self.measurements if m.get('alert_index') == alert_index]
            alert_step = len(alert_measurements) + 1
        else:
            # For measurements without alert_index, use global counter
            non_alert_measurements = [m for m in self.measurements if m.get('alert_index') is None]
            alert_step = len(non_alert_measurements) + 1
        
        self.step_counter += 1  # Keep global counter for overall tracking

        # Convert ms to seconds
        load_time_s = load_time_ms / 1000

        measurement = {
            "step": alert_step,  # Per-alert step counter
            "global_step": self.step_counter,  # Global step for reference
            "page": page,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "load_time_s": round(load_time_s, 3),
            "metrics": self._convert_metrics_to_seconds(metrics)
        }

        # Add comprehensive performance metrics
        if core_web_vitals:
            measurement["core_web_vitals"] = self._convert_metrics_to_seconds(asdict(core_web_vitals))
        
        if memory_metrics:
            measurement["memory_metrics"] = asdict(memory_metrics)
            
        if resource_timing:
            measurement["resource_timing"] = asdict(resource_timing)
            
        if ui_responsiveness:
            measurement["ui_responsiveness"] = asdict(ui_responsiveness)

        # Add alert_index if provided
        if alert_index is not None:
            measurement["alert_index"] = alert_index

        # Add any additional data
        measurement.update(kwargs)

        self.measurements.append(measurement)
        # Log with both per-alert and global step numbers
        if alert_index is not None:
            logger.info(
                f"Alert {alert_index} - Step {alert_step}: {page} - {action} - {load_time_s:.3f}s (global: {self.step_counter})"
            )
        else:
            logger.info(
                f"Setup - Step {alert_step}: {page} - {action} - {load_time_s:.3f}s (global: {self.step_counter})"
            )
        
        # Log additional metrics if available
        if core_web_vitals and core_web_vitals.largest_contentful_paint_s:
            logger.info(f"  LCP: {core_web_vitals.largest_contentful_paint_s:.3f}s")
        if memory_metrics and memory_metrics.js_heap_used_mb:
            logger.info(f"  Memory: {memory_metrics.js_heap_used_mb:.1f}MB")
        if ui_responsiveness and ui_responsiveness.long_tasks_count > 0:
            logger.info(f"  Long tasks: {ui_responsiveness.long_tasks_count}")

    def _convert_metrics_to_seconds(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert metric values from milliseconds to seconds.

        Args:
            metrics: Performance metrics dictionary with values in ms

        Returns:
            Dictionary with values converted to seconds
        """
        converted = {}
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and value is not None:
                # Convert from ms to seconds and round to 3 decimal places
                converted[key + "_s"] = round(value / 1000, 3)
            else:
                converted[key] = value
        return converted

    def calculate_summary(self) -> Dict[str, Any]:
        """
        Calculate summary statistics from all measurements.

        Returns:
            Dictionary with summary statistics
        """
        if not self.measurements:
            return {}

        load_times = [m["load_time_s"] for m in self.measurements]
        pages = list(set(m["page"] for m in self.measurements))

        slowest = max(self.measurements, key=lambda x: x["load_time_s"])
        fastest = min(self.measurements, key=lambda x: x["load_time_s"])

        return {
            "total_steps": len(self.measurements),
            "pages_measured": pages,
            "average_load_time_s": round(sum(load_times) / len(load_times), 3),
            "min_load_time_s": round(min(load_times), 3),
            "max_load_time_s": round(max(load_times), 3),
            "slowest_step": {
                "step": slowest["step"],
                "global_step": slowest.get("global_step", slowest["step"]),
                "alert_index": slowest.get("alert_index"),
                "page": slowest["page"],
                "action": slowest["action"],
                "load_time_s": slowest["load_time_s"]
            },
            "fastest_step": {
                "step": fastest["step"],
                "global_step": fastest.get("global_step", fastest["step"]),
                "alert_index": fastest.get("alert_index"),
                "page": fastest["page"],
                "action": fastest["action"],
                "load_time_s": fastest["load_time_s"]
            }
        }

    def generate_report(self, output_dir: str = "output", filename: Optional[str] = None) -> str:
        """
        Generate JSON performance report and save to file.

        Args:
            output_dir: Directory to save the report
            filename: Optional custom filename (default: performance_report_TIMESTAMP.json)

        Returns:
            Path to the generated report file
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # Calculate summary statistics
        summary = self.calculate_summary()
        multi_alert_summary = self.calculate_multi_alert_summary()

        # Group measurements by alert_index
        grouped_measurements = self._group_measurements_by_alert()
        
        # Build report structure
        report = {
            "test_metadata": {
                "test_name": self.test_name,
                "test_start": self.start_time.isoformat(),
                "test_end": end_time.isoformat(),
                "total_duration_sec": round(duration, 2),
                "network_config": {
                    "download_mbps": round(self.network_config["download_throughput"] / 1024 / 1024, 2),
                    "upload_mbps": round(self.network_config["upload_throughput"] / 1024 / 1024, 2),
                    "latency_ms": self.network_config["latency"]
                }
            },
            "measurements_by_alert": grouped_measurements,
            "all_measurements": self.measurements,  # Keep original flat structure for reference
            "summary": summary
        }
        
        # Add multi-alert summary if we have multi-alert data
        if multi_alert_summary and multi_alert_summary.get('alert_summaries'):
            report.update(multi_alert_summary)

        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.json"

        filepath = output_path / filename

        # Write report to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Performance report generated: {filepath}")
        return str(filepath)

    def calculate_multi_alert_summary(self) -> Dict[str, Any]:
        """Calculate aggregated statistics across multiple alerts"""
        if not self.measurements:
            return {}

        # Group measurements by alert_index
        alerts_data = {}
        measurements_without_alert = []
        
        for measurement in self.measurements:
            alert_idx = measurement.get('alert_index')
            if alert_idx is not None:
                if alert_idx not in alerts_data:
                    alerts_data[alert_idx] = []
                alerts_data[alert_idx].append(measurement)
            else:
                measurements_without_alert.append(measurement)

        # Calculate per-alert summaries
        alert_summaries = {}
        for alert_idx, alert_measurements in alerts_data.items():
            alert_load_times = [m['load_time_s'] for m in alert_measurements]
            page_breakdown = {}
            
            # Group by page type for this alert
            for measurement in alert_measurements:
                page = measurement['page']
                if page not in page_breakdown:
                    page_breakdown[page] = []
                page_breakdown[page].append(measurement['load_time_s'])
            
            # Calculate averages per page type
            page_averages = {}
            for page, times in page_breakdown.items():
                page_averages[f"{page}_avg_s"] = round(sum(times) / len(times), 3)
                page_averages[f"{page}_count"] = len(times)
            
            alert_summaries[f"alert_{alert_idx}"] = {
                "total_measurements": len(alert_measurements),
                "total_time_s": round(sum(alert_load_times), 3),
                "avg_time_s": round(sum(alert_load_times) / len(alert_load_times), 3) if alert_load_times else 0,
                "min_time_s": round(min(alert_load_times), 3) if alert_load_times else 0,
                "max_time_s": round(max(alert_load_times), 3) if alert_load_times else 0,
                **page_averages
            }

        # Calculate overall multi-alert statistics
        all_alert_avg_times = []
        all_alert_total_times = []
        for summary in alert_summaries.values():
            all_alert_avg_times.append(summary['avg_time_s'])
            all_alert_total_times.append(summary['total_time_s'])

        # Calculate bucket-level aggregations
        bucket_stats = self._calculate_bucket_statistics()

        # Calculate proper multi-alert metrics
        total_cumulative_time = sum(all_alert_total_times)
        avg_step_time = sum(all_alert_avg_times) / len(all_alert_avg_times) if all_alert_avg_times else 0
        avg_alert_duration = total_cumulative_time / len(alerts_data) if alerts_data else 0

        multi_alert_summary = {
            "alerts_tested": len(alerts_data),
            "avg_step_time_s": round(avg_step_time, 3),
            "avg_alert_duration_s": round(avg_alert_duration, 3),
            "total_cumulative_time_s": round(total_cumulative_time, 3),
            "fastest_alert": self._get_fastest_alert(alert_summaries),
            "slowest_alert": self._get_slowest_alert(alert_summaries),
            "bucket_averages": bucket_stats
        }

        return {
            "alert_summaries": alert_summaries,
            "multi_alert_summary": multi_alert_summary,
            "measurements_without_alert": len(measurements_without_alert)
        }

    def _calculate_bucket_statistics(self) -> Dict[str, float]:
        """Calculate average load times for different page buckets across all alerts"""
        buckets = {
            "alert_details_avg_s": [],
            "feature_loading_avg_s": [],
            "network_viz_avg_s": []
        }
        
        for measurement in self.measurements:
            load_time = measurement['load_time_s']
            page = measurement['page']
            
            if page == 'alert_details':
                buckets['alert_details_avg_s'].append(load_time)
            elif page == 'feature':
                buckets['feature_loading_avg_s'].append(load_time)
            elif page == 'network_visualization':
                buckets['network_viz_avg_s'].append(load_time)
        
        # Calculate averages
        bucket_averages = {}
        for bucket_name, times in buckets.items():
            if times:
                bucket_averages[bucket_name] = round(sum(times) / len(times), 3)
                bucket_averages[bucket_name.replace('_avg_s', '_count')] = len(times)
            else:
                bucket_averages[bucket_name] = 0
                bucket_averages[bucket_name.replace('_avg_s', '_count')] = 0
                
        return bucket_averages

    def _get_fastest_alert(self, alert_summaries: Dict[str, Any]) -> Dict[str, Any]:
        """Find the fastest alert by average time"""
        if not alert_summaries:
            return {}
        
        fastest = min(alert_summaries.items(), key=lambda x: x[1]['avg_time_s'])
        return {
            "alert_id": fastest[0],
            "avg_time_s": fastest[1]['avg_time_s'],
            "total_time_s": fastest[1]['total_time_s']
        }

    def _get_slowest_alert(self, alert_summaries: Dict[str, Any]) -> Dict[str, Any]:
        """Find the slowest alert by average time"""
        if not alert_summaries:
            return {}
        
        slowest = max(alert_summaries.items(), key=lambda x: x[1]['avg_time_s'])
        return {
            "alert_id": slowest[0],
            "avg_time_s": slowest[1]['avg_time_s'],
            "total_time_s": slowest[1]['total_time_s']
        }

    def _group_measurements_by_alert(self) -> Dict[str, Any]:
        """Group measurements by alert_index for cleaner report structure"""
        grouped = {}
        
        # Group measurements by alert_index
        for measurement in self.measurements:
            alert_idx = measurement.get('alert_index')
            
            if alert_idx is not None:
                alert_key = f"alert_{alert_idx}"
                if alert_key not in grouped:
                    grouped[alert_key] = []
                grouped[alert_key].append(measurement)
            else:
                # Measurements without alert_index (like initial alert_list load)
                if "setup" not in grouped:
                    grouped["setup"] = []
                grouped["setup"].append(measurement)
        
        # Sort measurements within each alert by step
        for alert_key in grouped:
            grouped[alert_key].sort(key=lambda x: x['step'])
        
        return grouped

    def get_measurements(self) -> List[Dict[str, Any]]:
        """Get all measurements"""
        return self.measurements

    def get_latest_measurement(self) -> Optional[Dict[str, Any]]:
        """Get the most recent measurement"""
        return self.measurements[-1] if self.measurements else None

    def start_memory_monitoring(self, interval_seconds: float = 1.0) -> None:
        """Start continuous memory monitoring in background thread"""
        if self._memory_monitoring:
            return
            
        self._memory_monitoring = True
        self._memory_samples = []
        
        def monitor_memory():
            while self._memory_monitoring:
                try:
                    # Get system memory
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    memory_percent = process.memory_percent()
                    
                    sample = {
                        "timestamp": datetime.now().isoformat(),
                        "system_memory_mb": round(memory_info.rss / 1024 / 1024, 2),
                        "system_memory_percent": round(memory_percent, 2)
                    }
                    
                    self._memory_samples.append(sample)
                    
                except Exception as e:
                    logger.warning(f"Memory monitoring error: {e}")
                    
                time.sleep(interval_seconds)
        
        self._memory_thread = threading.Thread(target=monitor_memory, daemon=True)
        self._memory_thread.start()
        logger.debug("Memory monitoring started")
    
    def stop_memory_monitoring(self) -> List[Dict[str, Any]]:
        """Stop memory monitoring and return collected samples"""
        if not self._memory_monitoring:
            return []
            
        self._memory_monitoring = False
        
        if self._memory_thread:
            self._memory_thread.join(timeout=2)
            
        logger.info(f"Memory monitoring stopped. Collected {len(self._memory_samples)} samples")
        return self._memory_samples.copy()
    
    def collect_core_web_vitals(self, page) -> CoreWebVitals:
        """Collect Core Web Vitals metrics from browser"""
        try:
            vitals = page.evaluate("""
            () => {
                return new Promise((resolve) => {
                    // Collect paint metrics
                    const paintEntries = performance.getEntriesByType('paint');
                    const fcp = paintEntries.find(entry => entry.name === 'first-contentful-paint');
                    
                    // Collect navigation metrics
                    const nav = performance.getEntriesByType('navigation')[0];
                    
                    const result = {
                        first_contentful_paint: fcp ? fcp.startTime : null,
                        time_to_interactive: nav ? nav.domInteractive : null,
                        largest_contentful_paint: null,
                        first_input_delay: null,
                        cumulative_layout_shift: null
                    };
                    
                    // Use PerformanceObserver for LCP and CLS if available
                    if ('PerformanceObserver' in window) {
                        try {
                            // Get LCP
                            const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                            if (lcpEntries.length > 0) {
                                result.largest_contentful_paint = lcpEntries[lcpEntries.length - 1].startTime;
                            }
                            
                            // Get layout shift entries for CLS calculation
                            const clsEntries = performance.getEntriesByType('layout-shift');
                            let clsScore = 0;
                            clsEntries.forEach(entry => {
                                if (!entry.hadRecentInput) {
                                    clsScore += entry.value;
                                }
                            });
                            result.cumulative_layout_shift = clsScore;
                            
                        } catch (e) {
                            console.log('Performance Observer error:', e);
                        }
                    }
                    
                    resolve(result);
                });
            }
            """)
            
            return CoreWebVitals(
                largest_contentful_paint_s=vitals.get('largest_contentful_paint') / 1000 if vitals.get('largest_contentful_paint') else None,
                first_input_delay_s=vitals.get('first_input_delay') / 1000 if vitals.get('first_input_delay') else None,
                cumulative_layout_shift_s=vitals.get('cumulative_layout_shift'),
                first_contentful_paint_s_s=vitals.get('first_contentful_paint') / 1000 if vitals.get('first_contentful_paint') else None,
                time_to_interactive_s_s=vitals.get('time_to_interactive') / 1000 if vitals.get('time_to_interactive') else None
            )
            
        except Exception as e:
            logger.warning(f"Failed to collect Core Web Vitals: {e}")
            return CoreWebVitals()
    
    def start_memory_monitoring(self, interval_seconds: float = 1.0) -> None:
        """Start continuous memory monitoring in background thread"""
        if self._memory_monitoring:
            return
            
        self._memory_monitoring = True
        self._memory_samples = []
        
        def monitor_memory():
            while self._memory_monitoring:
                try:
                    # Get system memory
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    memory_percent = process.memory_percent()
                    
                    sample = {
                        "timestamp": datetime.now().isoformat(),
                        "system_memory_mb": round(memory_info.rss / 1024 / 1024, 2),
                        "system_memory_percent": round(memory_percent, 2)
                    }
                    
                    self._memory_samples.append(sample)
                    
                except Exception as e:
                    logger.warning(f"Memory monitoring error: {e}")
                    
                time.sleep(interval_seconds)
        
        self._memory_thread = threading.Thread(target=monitor_memory, daemon=True)
        self._memory_thread.start()
        logger.debug("Memory monitoring started")
    
    def stop_memory_monitoring(self) -> List[Dict[str, Any]]:
        """Stop memory monitoring and return collected samples"""
        if not self._memory_monitoring:
            return []
            
        self._memory_monitoring = False
        
        # Wait for thread to finish
        if self._memory_thread and self._memory_thread.is_alive():
            self._memory_thread.join(timeout=2.0)
        
        samples = self._memory_samples.copy()
        logger.info(f"Memory monitoring stopped. Collected {len(samples)} samples")
        return samples

    def collect_memory_metrics(self, page) -> MemoryMetrics:
        """Collect memory usage metrics from browser and system"""
        js_metrics = {}
        
        try:
            # Get JavaScript heap info if available (Chromium)
            js_metrics = page.evaluate("""
            () => {
                if (performance.memory) {
                    return {
                        js_heap_used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100,
                        js_heap_total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024 * 100) / 100,
                        js_heap_limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024 * 100) / 100
                    };
                }
                return {};
            }
            """)
        except Exception as e:
            logger.debug(f"JS memory collection failed (may not be Chromium): {e}")
        
        # Get system memory
        system_memory = None
        system_memory_percent = None
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = round(memory_info.rss / 1024 / 1024, 2)
            system_memory_percent = round(process.memory_percent(), 2)
        except Exception as e:
            logger.warning(f"System memory collection failed: {e}")
        
        return MemoryMetrics(
            js_heap_used_mb=js_metrics.get('js_heap_used'),
            js_heap_total_mb=js_metrics.get('js_heap_total'),
            js_heap_limit_mb=js_metrics.get('js_heap_limit'),
            system_memory_used_mb=system_memory,
            system_memory_percent=system_memory_percent
        )
    
    def collect_resource_timing_metrics(self, page) -> ResourceTimingMetrics:
        """Collect performance metrics for API calls only (XHR and Fetch requests).

        Filters resources to measure only API endpoints, excluding static assets
        like images, CSS, JavaScript files, and fonts.
        """
        try:
            resource_data = page.evaluate("""
            () => {
                const allResources = performance.getEntriesByType('resource');

                // Filter for API calls only (XHR and Fetch requests)
                const resources = allResources.filter(resource => {
                    return resource.initiatorType === 'fetch' ||
                           resource.initiatorType === 'xmlhttprequest';
                });

                // If no API calls found, return empty metrics
                if (resources.length === 0) {
                    return {
                        resource_count: 0,
                        total_transfer_size_mb: 0,
                        avg_response_time_s: null,
                        slowest_resource_time_s: null,
                        fastest_resource_time_s: null
                    };
                }

                let totalSize = 0;
                let totalDuration = 0;
                let minDuration = Infinity;
                let maxDuration = 0;
                
                resources.forEach(resource => {
                    if (resource.transferSize) {
                        totalSize += resource.transferSize;
                    }
                    const duration = resource.responseEnd - resource.requestStart;
                    if (duration > 0) {
                        totalDuration += duration;
                        if (duration > maxDuration) {
                            maxDuration = duration;
                        }
                        if (duration < minDuration) {
                            minDuration = duration;
                        }
                    }
                });
                
                return {
                    resource_count: resources.length,
                    total_transfer_size_mb: Math.round(totalSize / 1024 / 1024 * 100) / 100,
                    avg_response_time_s: Math.round((totalDuration / resources.length) / 1000 * 1000) / 1000,
                    slowest_resource_time_s: Math.round(maxDuration / 1000 * 1000) / 1000,
                    fastest_resource_time_s: minDuration === Infinity ? null : Math.round(minDuration / 1000 * 1000) / 1000
                };
            }
            """)
            
            if resource_data:
                return ResourceTimingMetrics(
                    resource_count=resource_data['resource_count'],
                    total_transfer_size_mb=resource_data['total_transfer_size_mb'],
                    avg_response_time_s=resource_data['avg_response_time_s'],
                    slowest_resource_time_s=resource_data['slowest_resource_time_s'],
                    fastest_resource_time_s=resource_data['fastest_resource_time_s']
                )
                
        except Exception as e:
            logger.warning(f"Resource timing collection failed: {e}")
            
        return ResourceTimingMetrics()
    
    def collect_ui_responsiveness_metrics(self, page) -> UIResponsivenessMetrics:
        """Collect UI responsiveness metrics including long tasks"""
        try:
            responsiveness_data = page.evaluate("""
            () => {
                // Get long task entries if available
                const longTasks = performance.getEntriesByType('longtask') || [];
                let totalBlockingTime = 0;
                
                longTasks.forEach(task => {
                    // Tasks longer than 50ms contribute to TBT
                    if (task.duration > 50) {
                        totalBlockingTime += (task.duration - 50);
                    }
                });
                
                return {
                    long_tasks_count: longTasks.length,
                    total_blocking_time: totalBlockingTime
                };
            }
            """)
            
            return UIResponsivenessMetrics(
                long_tasks_count=responsiveness_data['long_tasks_count'],
                total_blocking_time_s=responsiveness_data['total_blocking_time'] / 1000
            )
            
        except Exception as e:
            logger.warning(f"UI responsiveness collection failed: {e}")
            
        return UIResponsivenessMetrics()


class PerformanceMeasurement:
    """Context manager for measuring performance of individual actions"""

    def __init__(self, page, action_name: str):
        """
        Initialize performance measurement context.

        Args:
            page: Playwright Page instance
            action_name: Name of the action being measured
        """
        self.page = page
        self.action_name = action_name
        self.start_time = None
        self.start_perf_time = None
        self.load_time_s = 0

    def __enter__(self):
        """Start measurement"""
        self.start_time = time.time()
        self.start_perf_time = self.page.evaluate("() => performance.now()")
        logger.debug(f"Starting measurement: {self.action_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End measurement"""
        end_time = time.time()
        self.load_time_s = end_time - self.start_time
        logger.debug(f"Completed measurement: {self.action_name} - {self.load_time_s:.3f}s")

    def get_load_time(self) -> float:
        """Get the measured load time in seconds"""
        return self.load_time_s
