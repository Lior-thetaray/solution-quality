"""
Main performance test script.
Executes multi-alert performance testing and generates comprehensive report.

Multi-Alert Test Flow (ALERTS_TO_TEST_COUNT=3 alerts):
0. (Keycloak authentication)
1. (Navigate to alert list page)
   1.1. (Select use case from dropdown: dpv:demo_fuib)
   1.2. MEASURE: Alert list page load time

For each alert:
2.X. MEASURE: Click alert X and measure alert details initial load
3.X. Navigate through all feature widgets for alert X:
     MEASURE: Each feature load time (feature_0, feature_1, etc.)
     (Navigate back after each feature)
4.X. MEASURE: Open network visualization for alert X
5.X. MEASURE: Apply date range filter (01/01/2025 - 30/06/2025)
6.X. MEASURE: Apply depth filter (depth=3)
7.X. (Navigate back to alert list using 'All alerts' link - if not last alert)

8. Generate comprehensive JSON report with multi-alert aggregations

Measurements captured per alert (with comprehensive metrics and alert_index):
- alert_list.initial_load (once)
- alert_details.initial_load (per alert)
- feature.feature_0_load, feature.feature_1_load, etc. (per alert)
- network_visualization.initial_load (per alert)
- network_visualization.date_filter_application (per alert)
- network_visualization.depth_filter_application (per alert)

JSON Output includes:
- Individual measurements with alert_index
- alert_summaries: Per-alert performance breakdown
- multi_alert_summary: Aggregated statistics across all alerts
- bucket_averages: Average performance by page type (alert_details, feature_loading, network_viz)
"""

import logging
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
from config.config import (
    NETWORK_CONFIG,
    VIEWPORT,
    BROWSER_TYPE,
    HEADLESS,
    OUTPUT_DIR,
    BROWSER_ARGS,
    PERFORMANCE_CONFIG,
    PERFORMANCE_THRESHOLDS,
    TestData,
    ALERTS_TO_TEST_COUNT,
    Selectors
)
from config.runtime_config import get_config_value, setup_runtime_config
from utils.network_emulator import NetworkEmulator
from utils.performance_tracker import PerformanceTracker
from pages.login_page import LoginPage
from pages.alert_list_page import AlertListPage
from pages.alert_details_page import AlertDetailsPage
from pages.network_viz_page import NetworkVisualizationPage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def log_performance_insights(action_name: str, core_web_vitals, memory_metrics, ui_responsiveness):
    """Log performance insights and warnings based on collected metrics"""
    logger.info(f"\n--- Performance Insights for {action_name} ---")
    
    # Core Web Vitals insights
    if core_web_vitals.largest_contentful_paint_s:
        lcp_s = core_web_vitals.largest_contentful_paint_s
        lcp_threshold_s = PERFORMANCE_THRESHOLDS['good_lcp_ms'] / 1000
        if lcp_s > lcp_threshold_s:
            logger.warning(f"⚠️  LCP is slow: {lcp_s:.3f}s (target: <{lcp_threshold_s:.3f}s)")
        else:
            logger.info(f"✅ LCP is good: {lcp_s:.3f}s")
    
    if core_web_vitals.cumulative_layout_shift_s:
        cls_score = core_web_vitals.cumulative_layout_shift_s
        if cls_score > PERFORMANCE_THRESHOLDS['good_cls_score']:
            logger.warning(f"⚠️  CLS is high: {cls_score:.3f} (target: <{PERFORMANCE_THRESHOLDS['good_cls_score']})")
        else:
            logger.info(f"✅ CLS is good: {cls_score:.3f}")
    
    # Memory insights
    if memory_metrics.js_heap_used_mb:
        heap_mb = memory_metrics.js_heap_used_mb
        if heap_mb > PERFORMANCE_THRESHOLDS['memory_warning_mb']:
            logger.warning(f"⚠️  High memory usage: {heap_mb:.1f}MB (warning: >{PERFORMANCE_THRESHOLDS['memory_warning_mb']}MB)")
        else:
            logger.info(f"✅ Memory usage is acceptable: {heap_mb:.1f}MB")
    
    # UI Responsiveness insights
    if ui_responsiveness.long_tasks_count > 0:
        logger.warning(f"⚠️  Found {ui_responsiveness.long_tasks_count} long tasks (blocking time: {ui_responsiveness.total_blocking_time_s:.3f}s)")
    else:
        logger.info(f"✅ No long tasks detected")
    
    if ui_responsiveness.avg_frame_rate and ui_responsiveness.avg_frame_rate < PERFORMANCE_THRESHOLDS['acceptable_frame_rate']:
        logger.warning(f"⚠️  Low frame rate: {ui_responsiveness.avg_frame_rate:.1f}fps (target: >{PERFORMANCE_THRESHOLDS['acceptable_frame_rate']}fps)")
    elif ui_responsiveness.avg_frame_rate:
        logger.info(f"✅ Frame rate is good: {ui_responsiveness.avg_frame_rate:.1f}fps")


def generate_performance_summary(tracker, memory_samples):
    """Generate and log comprehensive performance summary"""
    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE PERFORMANCE SUMMARY")
    logger.info("=" * 80)
    
    measurements = tracker.get_measurements()
    
    # Analyze Core Web Vitals across all measurements
    lcp_values = [m.get('core_web_vitals', {}).get('largest_contentful_paint_s') 
                  for m in measurements if m.get('core_web_vitals', {}).get('largest_contentful_paint_s')]
    if lcp_values:
        avg_lcp = sum(lcp_values) / len(lcp_values)
        logger.info(f"Average LCP: {avg_lcp:.3f}s (samples: {len(lcp_values)})")
    
    # Analyze memory usage trends
    if memory_samples:
        memory_values = [s['system_memory_mb'] for s in memory_samples]
        min_memory = min(memory_values)
        max_memory = max(memory_values)
        avg_memory = sum(memory_values) / len(memory_values)
        logger.info(f"Memory Usage - Min: {min_memory:.1f}MB, Max: {max_memory:.1f}MB, Avg: {avg_memory:.1f}MB")
    
    # Count total long tasks
    total_long_tasks = sum(m.get('ui_responsiveness', {}).get('long_tasks_count', 0) for m in measurements)
    if total_long_tasks > 0:
        logger.warning(f"Total long tasks detected: {total_long_tasks}")
    else:
        logger.info("✅ No long tasks detected throughout test")
    
    logger.info("=" * 80)


def run_performance_test():
    """Execute the complete performance test flow"""

    logger.info("=" * 80)
    logger.info("Starting Performance Test")
    logger.info("=" * 80)

    # Initialize performance tracker
    tracker = PerformanceTracker(
        test_name="alert_system_performance_test",
        network_config=NETWORK_CONFIG
    )

    with sync_playwright() as playwright:
        # Launch browser with args for stability
        browser_type = getattr(playwright, BROWSER_TYPE)

        # Browser-specific launch args for performance monitoring
        launch_args = {
            "args": BROWSER_ARGS.get(BROWSER_TYPE, [])
        }

        browser = browser_type.launch(
            headless=HEADLESS,
            slow_mo=50 if not HEADLESS else 0,  # Reduced from 100ms for better performance measurement
            **launch_args
        )
        logger.debug(f"Browser launched ({BROWSER_TYPE}, headless={HEADLESS})")
        logger.debug(f"Performance monitoring enabled: {PERFORMANCE_CONFIG}")
        
        # Start memory monitoring for the entire test
        tracker.start_memory_monitoring(interval_seconds=PERFORMANCE_CONFIG['memory_monitoring_interval'])

        # Create context with viewport
        context = browser.new_context(viewport=VIEWPORT)
        logger.debug(f"Browser context created with viewport {VIEWPORT['width']}x{VIEWPORT['height']}")

        # Create page
        page = context.new_page()
        logger.debug("New page created")

        # Setup runtime configuration (will prompt for credentials if needed)
        setup_runtime_config()
        logger.info("Runtime configuration loaded")

        try:
            # Set up network emulation
            network_emulator = NetworkEmulator(page, browser_type=BROWSER_TYPE)
            network_emulator.setup_network_conditions(NETWORK_CONFIG, headless=HEADLESS)

            # Wait for network conditions to stabilize before navigation
            time.sleep(0.5)

            # ================================================================
            # Step 0: Login via Keycloak
            # ================================================================
            logger.info("\n--- Step 0: Keycloak Authentication ---")

            # Navigate to base URL (will redirect to Keycloak)
            base_url = get_config_value('BASE_URL')
            logger.info(f"Navigating to {base_url} (will redirect to Keycloak)...")
            page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            logger.info(f"Current URL: {page.url}")

            # Perform login (not measured)
            login_page = LoginPage(page)
            username = get_config_value('USERNAME')
            password = get_config_value('PASSWORD')
            load_time, metrics = login_page.login(username, password)
            logger.debug(f"Login completed in {load_time/1000:.3f}s")

            # ================================================================
            # Step 1: Navigate to Alert List and measure
            # ================================================================
            logger.info("\n--- Step 1: Loading Alert List Page ---")

            # Navigate with timeout and retry logic
            max_retries = 3
            alert_list_url = get_config_value('ALERT_LIST_URL')
            
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Navigation attempt {attempt + 1}/{max_retries}")
                    page.goto(alert_list_url, wait_until="domcontentloaded", timeout=60000)
                    logger.debug(f"Successfully navigated to {alert_list_url}")
                    break
                except Exception as nav_error:
                    logger.error(f"Navigation error (attempt {attempt + 1}): {nav_error}")
                    logger.debug(f"Current URL: {page.url}")

                    if attempt == max_retries - 1:
                        # Last attempt failed - take screenshot and raise
                        page.screenshot(path="output/navigation_error.png")
                        raise
                    else:
                        # Wait before retrying
                        logger.info(f"Waiting 2 seconds before retry...")
                        time.sleep(2)

            # ================================================================
            # Step 1.1: Select Use Case from Dropdown (not measured)
            # ================================================================
            logger.info("\n--- Step 1.1: Selecting Use Case ---")
            alert_list = AlertListPage(page)

            load_time, metrics = alert_list.select_use_case()
            logger.debug(f"Use case selection completed in {load_time/1000:.3f}s")

            # ================================================================
            # Step 1.2: Measure Alert List Page Load with Comprehensive Metrics
            # ================================================================
            logger.info("\n--- Step 1.2: Measuring Alert List Page Load with Comprehensive Metrics ---")
            
            # Use comprehensive measurement if available, fallback to basic measurement
            try:
                load_time_ms, basic_metrics, core_web_vitals, memory_metrics, resource_timing, ui_responsiveness = \
                    alert_list.measure_comprehensive_performance(
                        action_callback=lambda: alert_list.measure_page_load(),
                        measure_frame_rate=True,
                        measure_memory=True,
                        measure_resources=True,
                        measure_responsiveness=True
                    )
                
                tracker.add_measurement(
                    page="alert_list",
                    action="initial_load",
                    load_time_ms=load_time_ms,
                    metrics=basic_metrics,
                    core_web_vitals=core_web_vitals,
                    memory_metrics=memory_metrics,
                    resource_timing=resource_timing,
                    ui_responsiveness=ui_responsiveness
                )
                
                log_performance_insights("Alert List Load", core_web_vitals, memory_metrics, ui_responsiveness)
                
            except AttributeError:
                # Fallback to basic measurement if comprehensive method not available
                logger.debug("Using basic measurement (comprehensive method not available)")
                load_time, metrics = alert_list.measure_page_load()
                tracker.add_measurement(
                    page="alert_list",
                    action="initial_load",
                    load_time_ms=load_time,
                    metrics=metrics
                )

            # ================================================================
            # Step 2-N: Test Multiple Alerts (Loop through available alerts)
            # ================================================================
            logger.info(f"\n--- Starting Multi-Alert Testing ({ALERTS_TO_TEST_COUNT} alerts) ---")
            
            # Check how many alerts are actually available
            alerts_available = alert_list.get_elements(Selectors.ALERT_TITLE).count()
            logger.info(f"Found {alerts_available} alerts available on the page")
            
            # Test only the number of alerts that are actually available
            alerts_to_test = min(ALERTS_TO_TEST_COUNT, alerts_available)
            if alerts_to_test < ALERTS_TO_TEST_COUNT:
                logger.warning(f"Only {alerts_to_test} alerts available, testing {alerts_to_test} instead of {ALERTS_TO_TEST_COUNT}")

            # Create alert_details page object for measurement
            alert_details = AlertDetailsPage(page)

            # Test each alert in sequence
            for alert_index in range(alerts_to_test):
                logger.info(f"\n=== TESTING ALERT {alert_index + 1}/{alerts_to_test} ===")

                try:
                    # ================================================================
                    # Step 2.X: Click Alert and Measure Alert Details Initial Load
                    # ================================================================
                    logger.info(f"\n--- Alert {alert_index}: Loading Alert Details Page ---")

                    # Use comprehensive measurement if available, fallback to basic measurement
                    try:
                        load_time_ms, basic_metrics, core_web_vitals, memory_metrics, resource_timing, ui_responsiveness = \
                            alert_list.measure_comprehensive_performance(
                                action_callback=lambda idx=alert_index: alert_list.click_alert_by_index(idx),
                                measure_frame_rate=True,
                                measure_memory=True,
                                measure_resources=True,
                                measure_responsiveness=True
                            )

                        tracker.add_measurement(
                            page="alert_details",
                            action="initial_load",
                            load_time_ms=load_time_ms,
                            metrics=basic_metrics,
                            core_web_vitals=core_web_vitals,
                            memory_metrics=memory_metrics,
                            resource_timing=resource_timing,
                            ui_responsiveness=ui_responsiveness,
                            alert_index=alert_index
                        )

                        log_performance_insights(f"Alert {alert_index} Details Load", core_web_vitals, memory_metrics, ui_responsiveness)

                    except AttributeError:
                        # Fallback to basic measurement if comprehensive method not available
                        logger.debug("Using basic measurement (comprehensive method not available)")
                        load_time, metrics = alert_list.click_alert_by_index(alert_index)
                        tracker.add_measurement(
                            page="alert_details",
                            action="initial_load",
                            load_time_ms=load_time,
                            metrics=metrics,
                            alert_index=alert_index
                        )
                        logger.debug(f"Alert {alert_index} clicked in {load_time/1000:.3f}s")

                    # ================================================================
                    # Step 3.X: Navigate through all feature widgets for this alert
                    # ================================================================
                    logger.info(f"\n--- Alert {alert_index}: Navigating Feature Widgets ---")

                    # Get feature count
                    feature_count = alert_details.get_feature_widget_count()
                    logger.debug(f"Found {feature_count} feature widgets to navigate for alert {alert_index}")

                    # Navigate each feature with comprehensive measurement
                    for i in range(feature_count):
                        logger.debug(f"\n  Alert {alert_index}, Feature {i + 1}/{feature_count} with Comprehensive Metrics")

                        # Try comprehensive measurement, fallback to basic
                        try:
                            load_time_ms, basic_metrics, core_web_vitals, memory_metrics, resource_timing, ui_responsiveness = \
                                alert_details.measure_comprehensive_performance(
                                    action_callback=lambda idx=i: alert_details.navigate_to_feature(idx),
                                    measure_frame_rate=True,
                                    measure_memory=True,
                                    measure_resources=True,
                                    measure_responsiveness=True
                                )
                            
                            tracker.add_measurement(
                                page="feature",
                                action=f"feature_{i}_load",
                                load_time_ms=load_time_ms,
                                metrics=basic_metrics,
                                core_web_vitals=core_web_vitals,
                                memory_metrics=memory_metrics,
                                resource_timing=resource_timing,
                                ui_responsiveness=ui_responsiveness,
                                feature_index=i,
                                alert_index=alert_index
                            )
                            
                            log_performance_insights(f"Alert {alert_index} - Feature {i}", core_web_vitals, memory_metrics, ui_responsiveness)
                            
                        except AttributeError:
                            # Fallback to basic measurement
                            nav_load_time, nav_metrics = alert_details.navigate_to_feature(i)
                            tracker.add_measurement(
                                page="feature",
                                action=f"feature_{i}_load",
                                load_time_ms=nav_load_time,
                                metrics=nav_metrics,
                                feature_index=i,
                                alert_index=alert_index
                            )

                        # Navigate back (not measured)
                        back_load_time, back_metrics = alert_details.navigate_back()
                        logger.debug(f"  Navigate back completed in {back_load_time/1000:.3f}s")

                    # ================================================================
                    # Step 4.X: Open Network Visualization and Measure Initial Load
                    # ================================================================
                    logger.info(f"\n--- Alert {alert_index}: Opening Network Visualization ---")
                    network_viz = NetworkVisualizationPage(page)

                    # Use comprehensive measurement if available, fallback to basic measurement
                    try:
                        load_time_ms, enhanced_metrics, core_web_vitals, memory_metrics, resource_timing, ui_responsiveness = \
                            network_viz.measure_network_visualization_comprehensive_performance(
                                action_callback=lambda: network_viz.open_network_visualization(),
                                action_name="initial_network_viz_load",
                                wait_for_completion=True
                            )

                        tracker.add_measurement(
                            page="network_visualization",
                            action="initial_load",
                            load_time_ms=load_time_ms,
                            metrics=enhanced_metrics,
                            core_web_vitals=core_web_vitals,
                            memory_metrics=memory_metrics,
                            resource_timing=resource_timing,
                            ui_responsiveness=ui_responsiveness,
                            alert_index=alert_index
                        )

                        log_performance_insights(f"Alert {alert_index} - Network Visualization Load", core_web_vitals, memory_metrics, ui_responsiveness)

                    except AttributeError:
                        # Fallback to basic measurement if comprehensive method not available
                        logger.debug("Using basic measurement (comprehensive method not available)")
                        success = network_viz.open_network_visualization()
                        if not success:
                            raise Exception(f"Failed to open network visualization for alert {alert_index}")

                    logger.debug(f"Network visualization opened for alert {alert_index}")

                    # ================================================================
                    # Step 5.X: Apply Date Range Filter with Performance Measurement
                    # ================================================================
                    logger.info(f"\n--- Alert {alert_index}: Applying Date Range Filter ---")
                    
                    try:
                        # Measure date filter application performance
                        date_filter_time_ms, date_filter_metrics = network_viz.measure_filter_application_performance(
                            filter_action=lambda: network_viz.set_date_range(),
                            filter_name="date_range"
                        )
                        
                        tracker.add_measurement(
                            page="network_visualization", 
                            action="date_filter_application",
                            load_time_ms=date_filter_time_ms,
                            metrics=date_filter_metrics,
                            filters={"date_from": "01/01/2025", "date_to": "30/06/2025"},
                            alert_index=alert_index
                        )
                        
                    except AttributeError:
                        # Fallback to basic filter application
                        logger.debug("Using basic date filter application")
                        date_success = network_viz.set_date_range()
                        if not date_success:
                            raise Exception(f"Failed to set date range filter for alert {alert_index}")
                            
                    logger.debug(f"Date range filter applied for alert {alert_index}")

                    # ================================================================
                    # Step 6.X: Apply Depth Filter with Performance Measurement
                    # ================================================================  
                    logger.info(f"\n--- Alert {alert_index}: Applying Depth Filter ---")
                    
                    try:
                        # Measure depth filter application performance
                        depth_filter_time_ms, depth_filter_metrics = network_viz.measure_filter_application_performance(
                            filter_action=lambda: network_viz.set_depth(),
                            filter_name="depth"
                        )
                        
                        tracker.add_measurement(
                            page="network_visualization",
                            action="depth_filter_application", 
                            load_time_ms=depth_filter_time_ms,
                            metrics=depth_filter_metrics,
                            filters={"depth": "3"},
                            alert_index=alert_index
                        )
                        
                    except AttributeError:
                        # Fallback to basic filter application
                        logger.debug("Using basic depth filter application")
                        depth_success = network_viz.set_depth()
                        if not depth_success:
                            raise Exception(f"Failed to set depth filter for alert {alert_index}")
                            
                    logger.debug(f"Depth filter applied for alert {alert_index}")

                    # ================================================================
                    # Step 7.X: Navigate back to Alert List (if not the last alert)
                    # ================================================================
                    if alert_index < alerts_to_test - 1:  # Don't navigate back after the last alert
                        logger.info(f"\n--- Alert {alert_index}: Navigating back to Alert List ---")
                        
                        try:
                            # Navigate back to alert list
                            back_load_time, back_metrics = alert_list.navigate_back_to_alert_list()
                            logger.debug(f"Navigation back to alert list completed in {back_load_time/1000:.3f}s")
                            
                            # Small delay to let the page stabilize before next alert
                            time.sleep(1)
                            
                        except Exception as e:
                            logger.error(f"Failed to navigate back to alert list from alert {alert_index}: {e}")
                            raise

                    logger.info(f"=== COMPLETED ALERT {alert_index + 1}/{alerts_to_test} ===")

                except Exception as e:
                    logger.error(f"Error testing alert {alert_index}: {e}", exc_info=True)
                    
                    # Try to navigate back to alert list for next iteration
                    if alert_index < ALERTS_TO_TEST_COUNT - 1:
                        try:
                            logger.info(f"Attempting recovery - navigating back to alert list")
                            alert_list.navigate_back_to_alert_list()
                            time.sleep(2)  # Extra recovery time
                        except Exception as recovery_error:
                            logger.error(f"Recovery failed: {recovery_error}")
                            raise  # Stop the test if recovery fails
                    
                    # Continue to next alert
                    continue

            logger.info(f"\n=== COMPLETED ALL {alerts_to_test} ALERTS ===")

            # ================================================================
            # Final Step: Test completed - no more navigation needed
            # ================================================================

            # ================================================================
            # Generate Report
            # ================================================================
            # Wait 3 seconds before ending test
            time.sleep(3)
            
            logger.info("\n" + "=" * 80)
            logger.info("Test Completed Successfully")
            logger.info("=" * 80)

            # Stop memory monitoring and collect final samples
            memory_samples = tracker.stop_memory_monitoring()
            logger.debug(f"Memory monitoring completed. Collected {len(memory_samples)} samples")

            # Generate comprehensive performance report
            report_path = tracker.generate_report(output_dir=OUTPUT_DIR)
            logger.info(f"\nComprehensive performance report generated: {report_path}")

            # Print enhanced summary
            summary = tracker.calculate_summary()
            multi_alert_summary = tracker.calculate_multi_alert_summary()
            
            logger.info("\n--- Basic Performance Summary ---")
            logger.info(f"Total steps: {summary['total_steps']}")
            logger.info(f"Average load time: {summary['average_load_time_s']:.3f}s")
            logger.info(f"Fastest step: {summary['fastest_step']['page']} - "
                       f"{summary['fastest_step']['action']} "
                       f"({summary['fastest_step']['load_time_s']:.3f}s)")
            logger.info(f"Slowest step: {summary['slowest_step']['page']} - "
                       f"{summary['slowest_step']['action']} "
                       f"({summary['slowest_step']['load_time_s']:.3f}s)")
            
            # Print multi-alert summary if available
            if multi_alert_summary and multi_alert_summary.get('multi_alert_summary'):
                mas = multi_alert_summary['multi_alert_summary']
                logger.info("\n--- Multi-Alert Performance Summary ---")
                logger.info(f"Alerts tested: {mas['alerts_tested']}")
                logger.info(f"Average step time: {mas['avg_step_time_s']:.3f}s")
                logger.info(f"Average alert duration: {mas['avg_alert_duration_s']:.3f}s")
                logger.info(f"Total cumulative time: {mas['total_cumulative_time_s']:.3f}s")
                
                if mas.get('fastest_alert'):
                    fa = mas['fastest_alert']
                    logger.info(f"Fastest alert: {fa['alert_id']} ({fa['avg_time_s']:.3f}s avg)")
                
                if mas.get('slowest_alert'):
                    sa = mas['slowest_alert']
                    logger.info(f"Slowest alert: {sa['alert_id']} ({sa['avg_time_s']:.3f}s avg)")
                
                # Print bucket averages
                if mas.get('bucket_averages'):
                    ba = mas['bucket_averages']
                    logger.info("\n--- Bucket Performance Averages ---")
                    logger.info(f"Alert Details: {ba.get('alert_details_avg_s', 0):.3f}s (count: {ba.get('alert_details_count', 0)})")
                    logger.info(f"Feature Loading: {ba.get('feature_loading_avg_s', 0):.3f}s (count: {ba.get('feature_loading_count', 0)})")
                    logger.info(f"Network Viz: {ba.get('network_viz_avg_s', 0):.3f}s (count: {ba.get('network_viz_count', 0)})")
            
            # Generate comprehensive performance summary
            generate_performance_summary(tracker, memory_samples)

        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            raise

        finally:
            # Cleanup
            try:
                if 'network_emulator' in locals():
                    network_emulator.close()
            except Exception as e:
                logger.warning(f"Error closing network emulator: {e}")

            try:
                context.close()
            except Exception as e:
                logger.warning(f"Error closing context: {e}")

            try:
                browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")

            logger.debug("\nBrowser closed")


if __name__ == "__main__":
    try:
        run_performance_test()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)
