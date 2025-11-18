"""
Network Visualization Page Object.
Handles interactions with network visualization tab including date and depth filters.
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from playwright.sync_api import Page
from pages.base_page import BasePage
from config.config import Selectors, TestData
from utils.performance_tracker import CoreWebVitals, MemoryMetrics, ResourceTimingMetrics, UIResponsivenessMetrics

logger = logging.getLogger(__name__)


class NetworkVisualizationPage(BasePage):
    """Page Object for Network Visualization page"""

    def __init__(self, page: Page):
        """
        Initialize NetworkVisualizationPage.

        Args:
            page: Playwright Page instance
        """
        super().__init__(page)
        self.open_network_viz_selector = Selectors.OPEN_NETWORK_VIZ
        self.date_range_selector = Selectors.DATE_RANGE_FIELD
        self.depth_selector = Selectors.DEPTH_FIELD

    def _wait_for_network_viz_loaded(self, timeout_ms: int = 10000) -> bool:
        """
        Wait for network visualization to finish loading.

        Checks that:
        1. .tools-wrapper exists (container appeared)
        2. .tools-wrapper does NOT have .loading class (loading complete)
        3. Either data is displayed OR tr-empty-state appears (empty but loaded)

        Args:
            timeout_ms: Maximum time to wait in milliseconds

        Returns:
            True if loaded, False if timeout
        """
        import time

        start_time = time.time()
        elapsed_ms = 0

        logger.debug("Waiting for network visualization to finish loading...")

        # Phase 1: Wait for tools-wrapper to exist
        tools_wrapper_found = False
        while elapsed_ms < timeout_ms and not tools_wrapper_found:
            try:
                tools_wrapper = self.page.locator('.tools-wrapper')
                if tools_wrapper.count() > 0:
                    logger.debug("Found .tools-wrapper container")
                    tools_wrapper_found = True
                    break
            except Exception as e:
                logger.debug(f"Error finding tools-wrapper: {e}")

            time.sleep(0.1)
            elapsed_ms = (time.time() - start_time) * 1000

        if not tools_wrapper_found:
            logger.warning("tools-wrapper container not found - continuing anyway")
            return False

        # Phase 2: Wait for .loading class to be removed
        while elapsed_ms < timeout_ms:
            try:
                # Check if tools-wrapper has loading class
                loading_elements = self.page.locator('.tools-wrapper.loading')
                loading_count = loading_elements.count()

                if loading_count == 0:
                    # Loading class is gone - now check for content
                    # Check if we have empty state or data
                    empty_state = self.page.locator('tr-empty-state')

                    if empty_state.count() > 0:
                        logger.debug("Network visualization loaded (empty state)")
                        return True
                    else:
                        # Just assume data is there if no empty state
                        logger.debug("Network visualization loaded (data displayed)")
                        return True

            except Exception as e:
                logger.debug(f"Error checking network viz loading state: {e}")

            # Wait for poll interval
            time.sleep(0.1)
            elapsed_ms = (time.time() - start_time) * 1000

        logger.warning(f"Network visualization loading check timeout after {timeout_ms}ms - continuing anyway")
        return False

    def open_network_visualization(self, timeout: int = 30000) -> bool:
        """
        Open network visualization tab and wait for initial loading to complete.
        Does NOT measure performance - just opens and waits for ready state.

        Args:
            timeout: Maximum time to wait in milliseconds

        Returns:
            True if successfully opened and loaded
        """
        import time

        logger.debug("Opening network visualization")

        # Wait for network viz button to appear with retry
        self.wait_for_element_with_retry(
            self.open_network_viz_selector,
            timeout_ms=5000,
            screenshot_name="network_viz_button_not_found",
            take_screenshot_on_failure=True
        )

        # Click network visualization button (try multiple methods)
        click_success = False

        # Method 1: Try JavaScript click first (fastest)
        try:
            logger.debug("Attempting JavaScript click on network viz button...")
            self.page.locator(self.open_network_viz_selector).evaluate("el => el.click()")
            click_success = True
            logger.debug("Network visualization button clicked via JavaScript")
        except Exception as e1:
            logger.warning(f"JavaScript click failed: {e1}")

            # Method 2: Try force click as fallback
            try:
                logger.debug("Attempting force click...")
                self.page.locator(self.open_network_viz_selector).click(force=True)
                click_success = True
                logger.debug("Network visualization button force-clicked")
            except Exception as e2:
                logger.error(f"All click methods failed: {e2}")
                # Take screenshot for debugging
                try:
                    self.page.screenshot(path="output/network_viz_button_error.png")
                except:
                    pass
                raise Exception("Could not click network visualization button")

        if not click_success:
            raise Exception("Failed to click network visualization button")

        # Wait 300ms for navigation to start
        time.sleep(0.3)

        # Wait for visualization container to appear
        self.wait_for_element_with_retry(
            ".network-graph, .visualization-container",
            timeout_ms=5000,
            screenshot_name=None,
            raise_on_failure=False,
            take_screenshot_on_failure=False
        )

        # Wait for initial loading to complete (no .tools-wrapper.loading)
        loading_complete = self._wait_for_network_viz_loaded(timeout_ms=10000)
        if not loading_complete:
            logger.warning("Network visualization loading may not have completed properly")

        # Wait for network to become idle
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
            logger.debug("Network idle after network viz initial load")
        except Exception as e:
            logger.warning(f"Network idle timeout: {e}")

        # Wait for filter controls to be ready (date range, depth fields)
        time.sleep(0.5)

        logger.debug("Network visualization opened and ready for filters")
        return True
    
    def measure_chart_rendering_performance(self) -> Dict[str, Any]:
        """
        Measure chart/visualization rendering performance focusing on canvas elements only.
        
        Returns:
            Dictionary with rendering metrics
        """
        try:
            rendering_metrics = self.page.evaluate("""
            () => {
                const startTime = performance.now();
                
                // Focus only on canvas elements for chart rendering
                const canvasElements = document.querySelectorAll('canvas');
                
                let canvasWithContent = 0;
                let canvasDetails = [];
                
                canvasElements.forEach((canvas, index) => {
                    try {
                        // Check canvas dimensions first
                        const hasValidDimensions = canvas.width > 0 && canvas.height > 0;
                        
                        let hasContent = false;
                        let contentMethod = 'none';
                        
                        if (hasValidDimensions) {
                            // Method 2: Try WebGL context if 2D failed
                            if (!hasContent) {
                                const ctxWebGL = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                                if (ctxWebGL && hasValidDimensions) {
                                    hasContent = true;
                                    contentMethod = 'webgl';
                                }
                            }
                        }
                        
                        canvasDetails.push({
                            index: index,
                            width: canvas.width,
                            height: canvas.height,
                            hasContent: hasContent,
                            contentMethod: contentMethod,
                            className: canvas.className,
                            id: canvas.id || 'no-id'
                        });
                        
                        if (hasContent) {
                            canvasWithContent++;
                        }
                        
                    } catch (e) {
                        canvasDetails.push({
                            index: index,
                            width: canvas.width || 0,
                            height: canvas.height || 0,
                            hasContent: false,
                            contentMethod: 'error',
                            error: e.message,
                            className: canvas.className,
                            id: canvas.id || 'no-id'
                        });
                    }
                });
                
                const renderTime = performance.now() - startTime;
                
                return {
                    canvas_elements_found: canvasElements.length,
                    canvas_elements_with_content: canvasWithContent,
                    canvas_details: canvasDetails,
                    render_detection_time_ms: renderTime,
                    rendering_likely_complete: canvasWithContent > 0
                };
            }
            """)
            
            logger.debug(f"Chart rendering metrics: {rendering_metrics}")
            return rendering_metrics
            
        except Exception as e:
            logger.warning(f"Chart rendering measurement failed: {e}")
            return {
                "canvas_elements_found": 0,
                "canvas_elements_with_content": 0,
                "rendering_likely_complete": False,
                "render_detection_time_ms": 0
            }
    
    def measure_filter_application_performance(
        self, 
        filter_action: callable,
        filter_name: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Measure performance of applying a specific filter.
        
        Args:
            filter_action: Function that applies the filter
            filter_name: Name of the filter being applied
            
        Returns:
            Tuple of (application_time_ms, metrics)
        """
        logger.info(f"Measuring {filter_name} filter application performance")
        
        # Record state before filter application
        pre_filter_state = self.page.evaluate("""
        () => {
            return {
                dom_nodes: document.querySelectorAll('*').length,
                network_requests_count: performance.getEntriesByType('resource').length,
                timestamp: performance.now()
            };
        }
        """)
        
        start_time = time.time()
        
        # Apply the filter
        try:
            filter_action()
            
            # Wait for loading to complete
            self._wait_for_network_viz_loaded(timeout_ms=15000)
            
        except Exception as e:
            logger.error(f"Filter application failed: {e}")
            return 0.0, {}
        
        end_time = time.time()
        application_time_ms = (end_time - start_time) * 1000
        
        # Record state after filter application
        post_filter_state = self.page.evaluate("""
        () => {
            return {
                dom_nodes: document.querySelectorAll('*').length,
                network_requests_count: performance.getEntriesByType('resource').length,
                timestamp: performance.now()
            };
        }
        """)
        
        # Calculate metrics
        metrics = {
            "filter_name": filter_name,
            "application_time_ms": application_time_ms,
            "dom_nodes_added": post_filter_state['dom_nodes'] - pre_filter_state['dom_nodes'],
            "network_requests_added": post_filter_state['network_requests_count'] - pre_filter_state['network_requests_count'],
            "browser_processing_time_ms": post_filter_state['timestamp'] - pre_filter_state['timestamp']
        }
        
        logger.info(f"{filter_name} filter applied in {application_time_ms:.1f}ms")
        return application_time_ms, metrics
    
    def measure_data_processing_performance(self) -> Dict[str, Any]:
        """
        Measure data processing performance by analyzing network activity and DOM changes.
        
        Returns:
            Dictionary with data processing metrics
        """
        try:
            processing_metrics = self.page.evaluate("""
            () => {
                const resources = performance.getEntriesByType('resource');
                const navigation = performance.getEntriesByType('navigation')[0];
                
                // Analyze recent network activity
                const recentResources = resources.filter(resource => {
                    const age = performance.now() - resource.startTime;
                    return age < 30000; // Last 30 seconds
                });
                
                let totalDataSize = 0;
                let apiCallCount = 0;
                let totalProcessingTime = 0;
                
                recentResources.forEach(resource => {
                    if (resource.transferSize) {
                        totalDataSize += resource.transferSize;
                    }
                    
                    // Check if it's likely an API call
                    if (resource.name.includes('/api/') || 
                        resource.name.includes('.json') ||
                        resource.initiatorType === 'fetch' ||
                        resource.initiatorType === 'xmlhttprequest') {
                        apiCallCount++;
                    }
                    
                    // Calculate processing time (responseEnd - responseStart)
                    if (resource.responseEnd && resource.responseStart) {
                        totalProcessingTime += (resource.responseEnd - resource.responseStart);
                    }
                });
                
                // Estimate DOM complexity
                const totalElements = document.querySelectorAll('*').length;
                const visualizationElements = document.querySelectorAll(
                    '.network-graph *, .visualization-container *, svg *, canvas *'
                ).length;
                
                return {
                    recent_resources_count: recentResources.length,
                    total_data_transferred_bytes: totalDataSize,
                    api_calls_count: apiCallCount,
                    avg_processing_time_ms: recentResources.length > 0 ? 
                        totalProcessingTime / recentResources.length : 0,
                    total_dom_elements: totalElements,
                    visualization_dom_elements: visualizationElements,
                    dom_complexity_ratio: totalElements > 0 ? 
                        visualizationElements / totalElements : 0
                };
            }
            """)
            
            logger.debug(f"Data processing metrics: {processing_metrics}")
            return processing_metrics
            
        except Exception as e:
            logger.warning(f"Data processing measurement failed: {e}")
            return {
                "recent_resources_count": 0,
                "total_data_transferred_bytes": 0,
                "api_calls_count": 0
            }

    def measure_network_visualization_comprehensive_performance(
        self,
        action_callback: callable,
        action_name: str,
        wait_for_completion: bool = True
    ) -> Tuple[float, Dict[str, Any], CoreWebVitals, MemoryMetrics, ResourceTimingMetrics, UIResponsivenessMetrics]:
        """
        Comprehensive performance measurement specifically for network visualization actions.
        
        Args:
            action_callback: Function that performs the visualization action
            action_name: Name of the action being measured
            wait_for_completion: Whether to wait for visualization loading to complete
            
        Returns:
            Tuple of comprehensive performance metrics
        """
        logger.info(f"Starting comprehensive measurement of {action_name}")
        
        # Measure basic performance with comprehensive metrics
        load_time_ms, basic_metrics, core_web_vitals, memory_metrics, resource_timing, ui_responsiveness = \
            self.measure_comprehensive_performance(
                action_callback=action_callback,
                wait_selector=".tools-wrapper" if wait_for_completion else None,
                measure_frame_rate=True,
                measure_memory=True,
                measure_resources=True,
                measure_responsiveness=True
            )
        
        # Add visualization-specific metrics
        chart_metrics = self.measure_chart_rendering_performance()
        data_processing_metrics = self.measure_data_processing_performance()
        
        # Combine all metrics
        enhanced_metrics = {
            **basic_metrics,
            "visualization_specific": {
                "chart_rendering": chart_metrics,
                "data_processing": data_processing_metrics,
                "action_name": action_name
            }
        }
        
        logger.info(f"Comprehensive measurement of {action_name} completed: {load_time_ms:.1f}ms")
        
        return load_time_ms, enhanced_metrics, core_web_vitals, memory_metrics, resource_timing, ui_responsiveness
    
    def set_date_range(
        self,
        date_from: str = None,
        date_to: str = None,
        timeout: int = 30000
    ) -> bool:
        """
        Set date range filter without measuring performance.
        Just applies the filter and waits for completion.

        Args:
            date_from: Start date in format DD/MM/YYYY (default from TestData)
            date_to: End date in format DD/MM/YYYY (default from TestData)
            timeout: Maximum time to wait in milliseconds

        Returns:
            True if successfully set
        """
        if date_from is None:
            date_from = TestData.DATE_FROM
        if date_to is None:
            date_to = TestData.DATE_TO

        logger.debug(f"Setting date range: {date_from} to {date_to}")

        import time

        # Retry logic - try twice (initial attempt + 1 retry)
        max_attempts = 2
        last_error = None

        for attempt in range(max_attempts):
            if attempt > 0:
                logger.debug(f"Retrying date range filter (attempt {attempt + 1}/{max_attempts})")
                time.sleep(1)  # Wait before retry

            try:
                # Step 1: Wait for date range field to appear with retry
                self.wait_for_element_with_retry(
                    Selectors.DATE_RANGE_FIELD,
                    timeout_ms=5000,
                    screenshot_name="date_range_field_not_found" if attempt == max_attempts - 1 else None,
                    take_screenshot_on_failure=(attempt == max_attempts - 1)
                )

                # Click on data-fieldname="dateRange" (with force click)
                date_range_field = self.page.locator(Selectors.DATE_RANGE_FIELD)
                try:
                    date_range_field.click(force=True)
                    logger.debug("Clicked on date range field (force)")
                except Exception as e:
                    logger.warning(f"Force click failed, trying JavaScript: {e}")
                    date_range_field.evaluate("el => el.click()")
                    logger.debug("Clicked on date range field (JavaScript)")

                # Wait 300ms for dropdown to open
                time.sleep(0.3)

                # Wait for date filter container to appear with retry
                self.wait_for_element_with_retry(
                    Selectors.DATE_FILTER_CONTAINER,
                    timeout_ms=5000,
                    screenshot_name="date_filter_container_not_found" if attempt == max_attempts - 1 else None,
                    take_screenshot_on_failure=(attempt == max_attempts - 1)
                )

                # Step 2: Find the .date-filter container
                date_filter = self.page.locator(Selectors.DATE_FILTER_CONTAINER)
                logger.debug("Found date filter container")

                # Step 3: Wait for p-calendar elements to appear
                calendar_selector = f"{Selectors.DATE_FILTER_CONTAINER} {Selectors.P_CALENDAR}"
                self.wait_for_element_with_retry(
                    calendar_selector,
                    timeout_ms=5000,
                    screenshot_name="p_calendar_not_found" if attempt == max_attempts - 1 else None,
                    take_screenshot_on_failure=(attempt == max_attempts - 1)
                )

                # Find all p-calendar elements (first is from, second is to)
                calendars = date_filter.locator(Selectors.P_CALENDAR)
                calendar_count = calendars.count()
                logger.debug(f"Found {calendar_count} p-calendar elements")

                if calendar_count < 2:
                    raise Exception(f"Expected at least 2 p-calendar elements, found {calendar_count}")

                # Step 4: Fill the "From" date (first p-calendar)
                from_calendar = calendars.nth(0)
                from_input = from_calendar.locator('input')
                logger.debug("Setting 'From' date...")
                from_input.click()
                from_input.fill("")
                from_input.type(date_from, delay=50)
                logger.debug(f"Set 'From' date: {date_from}")

                # Press Enter after "From" date
                from_input.press("Enter")
                logger.debug("Pressed Enter after 'From' date")

                # Wait for "From" date to be processed
                time.sleep(0.8)  # Increased wait time

                # Step 5: Fill the "To" date (second p-calendar)
                to_calendar = calendars.nth(1)
                to_input = to_calendar.locator('input')
                logger.debug("Setting 'To' date...")
                to_input.click()
                to_input.fill("")
                to_input.type(date_to, delay=50)
                logger.debug(f"Set 'To' date: {date_to}")

                # Press Enter after "To" date to apply the filter
                to_input.press("Enter")
                logger.debug("Pressed Enter after 'To' date")

                # Wait for date inputs to be processed
                time.sleep(0.5)

                # Check if there's an Apply button and click it
                apply_button_selectors = [
                    'button:has-text("Apply")',
                    '.apply-button',
                    '[data-cy="apply"]',
                    'button[type="submit"]',
                    '.btn-apply'
                ]
                
                apply_button_found = False
                for selector in apply_button_selectors:
                    try:
                        apply_button = self.page.locator(selector)
                        if apply_button.count() > 0 and apply_button.first.is_visible():
                            logger.debug(f"Found Apply button with selector: {selector}")
                            try:
                                apply_button.first.click()
                                logger.debug("Apply button clicked")
                                apply_button_found = True
                                break
                            except Exception as e:
                                logger.warning(f"Failed to click Apply button: {e}")
                    except Exception as e:
                        logger.debug(f"Apply button selector '{selector}' failed: {e}")

                if not apply_button_found:
                    logger.debug("No Apply button found - dates should be applied automatically")

                # Wait longer for date filter to be fully applied
                time.sleep(1.0)

                # Wait for network to become idle (date filter applied)
                try:
                    self.page.wait_for_load_state("networkidle", timeout=15000)
                    logger.debug("Date range filter applied successfully")

                except Exception as e:
                    logger.warning(f"Network idle timeout after date filter: {e}")
                    # Continue anyway

                logger.debug(f"Date range filter set: {date_from} to {date_to}")
        
                return True

            except Exception as e:
                last_error = e
                logger.error(f"Error setting date range (attempt {attempt + 1}/{max_attempts}): {e}")
                # Take screenshot for debugging on last attempt
                if attempt == max_attempts - 1:
                    try:
                        self.page.screenshot(path="output/date_range_error.png")
                    except:
                        pass
                # Continue to next attempt if not last

        # All attempts failed
        logger.error(f"Failed to set date range after {max_attempts} attempts")
        if last_error:
            raise last_error
        return False

    def set_depth(
        self,
        depth_value: str = None,
        timeout: int = 30000
    ) -> bool:
        """
        Set depth filter without measuring performance.
        Just applies the filter and waits for completion.

        Args:
            depth_value: Depth value to select (default from TestData)
            timeout: Maximum time to wait in milliseconds

        Returns:
            True if filter set successfully
        """
        if depth_value is None:
            depth_value = TestData.DEPTH_VALUE

        logger.debug(f"Setting depth filter: {depth_value}")

        import time

        # Retry logic - try twice (initial attempt + 1 retry)
        max_attempts = 2
        last_error = None

        for attempt in range(max_attempts):
            if attempt > 0:
                logger.debug(f"Retrying depth filter (attempt {attempt + 1}/{max_attempts})")
                time.sleep(1)  # Wait before retry

            try:
                # Step 1: Wait for depth field to appear with retry
                self.wait_for_element_with_retry(
                    Selectors.DEPTH_FIELD,
                    timeout_ms=5000,
                    screenshot_name="depth_field_not_found" if attempt == max_attempts - 1 else None,
                    take_screenshot_on_failure=(attempt == max_attempts - 1)
                )

                # Click on data-fieldname="depth" (with force click)
                depth_field = self.page.locator(Selectors.DEPTH_FIELD)
                try:
                    depth_field.click(force=True)
                    logger.debug("Clicked on depth field (force)")
                except Exception as e:
                    logger.warning(f"Force click failed, trying JavaScript: {e}")
                    depth_field.evaluate("el => el.click()")
                    logger.debug("Clicked on depth field (JavaScript)")

                # Wait 300ms for dropdown to open
                time.sleep(0.3)

                # Step 2: Wait for dropdown overlay to appear with retry
                self.wait_for_element_with_retry(
                    Selectors.FILTER_DROPDOWN_OVERLAY,
                    timeout_ms=5000,
                    screenshot_name="depth_dropdown_not_found" if attempt == max_attempts - 1 else None,
                    take_screenshot_on_failure=(attempt == max_attempts - 1)
                )

                dropdown_overlay = self.page.locator(Selectors.FILTER_DROPDOWN_OVERLAY)
                logger.debug("Filter dropdown overlay is visible")

                # Step 3: Try to find depth options with multiple selectors
                # Don't wait - just try each selector quickly
                option = None
                selectors_to_try = [
                    # Try basic dropdown selectors first
                    f'.p-dropdown-item:has-text("{depth_value}")',
                    f'.p-dropdown-panel .p-dropdown-item:has-text("{depth_value}")',
                    f'[role="option"]:has-text("{depth_value}")',
                    f'.dropdown-item:has-text("{depth_value}")',
                    # Try with filter dropdown overlay
                    f'{Selectors.FILTER_DROPDOWN_OVERLAY} .p-dropdown-item:has-text("{depth_value}")',
                    f'{Selectors.FILTER_DROPDOWN_OVERLAY} [role="option"]:has-text("{depth_value}")',
                    # Try generic text matching
                    f'{Selectors.FILTER_DROPDOWN_OVERLAY} >> text={depth_value}',
                    f'>> text={depth_value}',
                ]

                logger.debug(f"Trying to find depth option with value '{depth_value}'...")

                for i, selector in enumerate(selectors_to_try):
                    try:
                        candidate = self.page.locator(selector)
                        count = candidate.count()
                        logger.debug(f"  Selector {i+1}: '{selector}' -> {count} elements")

                        if count > 0:
                            # Check if first element is visible
                            if candidate.first.is_visible():
                                option = candidate.first
                                logger.debug(f"Found visible option using selector: {selector}")
                                break
                    except Exception as e:
                        logger.debug(f"  Selector {i+1} failed: {e}")
                        continue

                if not option:
                    # Last resort - try to click any visible element containing the depth value
                    logger.warning("Standard selectors failed, trying last resort approach...")
                    try:
                        # Wait a bit for dropdown to fully load
                        time.sleep(1)
                        # Try to find ANY element containing the depth value
                        all_elements = self.page.locator(f'*:has-text("{depth_value}")')
                        count = all_elements.count()
                        logger.debug(f"Found {count} elements containing text '{depth_value}'")

                        for i in range(count):
                            try:
                                element = all_elements.nth(i)
                                if element.is_visible():
                                    option = element
                                    logger.debug(f"Using element {i} as fallback option")
                                    break
                            except:
                                continue
                    except Exception as e:
                        logger.error(f"Last resort approach failed: {e}")

                if not option:
                    raise Exception(f"Could not find any clickable option with text '{depth_value}' in dropdown")

                # Click the option (with force click)
                try:
                    option.click(force=True)
                    logger.debug(f"Selected depth option: {depth_value} (force)")
                except Exception as e:
                    logger.warning(f"Force click failed, trying JavaScript: {e}")
                    option.evaluate("el => el.click()")
                    logger.debug(f"Selected depth option: {depth_value} (JavaScript)")

                # Wait 300ms for filter to start processing
                time.sleep(0.3)

                # Wait for loading class to be removed (depth filter processing complete)
                logger.debug("Waiting for depth filter loading to complete...")
                loading_complete = self._wait_for_network_viz_loaded(timeout_ms=10000)
                if not loading_complete:
                    logger.warning("Depth filter loading may not have completed properly")
                else:
                    logger.debug("Depth filter loading completed (loading class removed)")

                # Wait for network to become idle (filter applied)
                try:
                    self.page.wait_for_load_state("networkidle", timeout=15000)
                    logger.debug("Depth filter applied successfully")
                except Exception as e:
                    logger.warning(f"Network idle timeout after depth filter: {e}")
                    # Continue anyway

                logger.debug(f"Depth filter set to: {depth_value}")
                return True

            except Exception as e:
                last_error = e
                logger.error(f"Error setting depth (attempt {attempt + 1}/{max_attempts}): {e}")
                # Take screenshot for debugging on last attempt
                if attempt == max_attempts - 1:
                    try:
                        self.page.screenshot(path="output/depth_filter_error.png")
                    except:
                        pass
                # Continue to next attempt if not last

        # All attempts failed
        logger.error(f"Failed to set depth filter after {max_attempts} attempts")
        if last_error:
            raise last_error
        return False

    def measure_final_load_after_filters(self, timeout: int = 30000) -> tuple[float, Dict[str, Any]]:
        """
        Measure the final load time after both filters have been applied.
        
        This method should be called AFTER both date range and depth filters have been set.
        It starts a timer, waits for the loading class to be removed from tools-wrapper,
        then measures the load time.

        Args:
            timeout: Maximum time to wait in milliseconds

        Returns:
            Tuple of (load_time_ms, metrics_dict)
        """
        import time
        
        logger.info("Starting measurement of final load after all filters applied")
        
        # START TIMER
        start_time = time.time()
        
        # Wait 300ms for any final network requests to start
        time.sleep(0.3)
        
        # Wait for loading class to be removed (final data loading complete)
        loading_complete = self._wait_for_network_viz_loaded(timeout_ms=10000)
        if not loading_complete:
            logger.warning("Network visualization final loading may not have completed properly")
        
        # Wait for network to become idle (all requests finished)
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
            logger.info("Network idle after final filter loading")
        except Exception as e:
            logger.warning(f"Network idle timeout during final load: {e}")
            # Continue anyway
        
        # END TIMER
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000
        
        logger.info(f"Final load time after all filters: {load_time_ms:.2f}ms")
        
        # No browser metrics for SPA filter updates
        return load_time_ms, {}
