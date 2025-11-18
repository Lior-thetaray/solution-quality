"""
Base page class with common functionality and performance measurement utilities.
All page objects inherit from this class.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, Callable
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.performance_tracker import CoreWebVitals, MemoryMetrics, ResourceTimingMetrics, UIResponsivenessMetrics

logger = logging.getLogger(__name__)


class BasePage:
    """Base class for all page objects with performance measurement capabilities"""

    def __init__(self, page: Page):
        """
        Initialize BasePage.

        Args:
            page: Playwright Page instance
        """
        self.page = page

    def wait_for_page_load(self, timeout: int = 30000) -> None:
        """
        Wait for page to be fully loaded (DOM complete state).

        Args:
            timeout: Maximum time to wait in milliseconds
        """
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
            logger.debug("Page DOM content loaded")
        except PlaywrightTimeoutError:
            logger.warning(f"Page load timeout after {timeout}ms")

    def wait_for_element(self, selector: str, timeout: int = 30000, state: str = "visible") -> None:
        """
        Wait for element to be in specified state.

        Args:
            selector: CSS selector
            timeout: Maximum time to wait in milliseconds
            state: Element state to wait for (visible, attached, hidden, detached)
        """
        try:
            self.page.wait_for_selector(selector, timeout=timeout, state=state)
            logger.debug(f"Element '{selector}' is {state}")
        except PlaywrightTimeoutError:
            logger.warning(f"Element '{selector}' not {state} after {timeout}ms")

    def wait_for_element_with_retry(
        self,
        selector: str,
        timeout_ms: int = 5000,
        poll_interval_ms: int = 100,
        screenshot_name: str = None,
        raise_on_failure: bool = True,
        take_screenshot_on_failure: bool = True
    ) -> bool:
        """
        Wait for element with polling retry mechanism.

        Polls every poll_interval_ms for element to be visible.
        Takes screenshot only on final failure (not on first attempts).

        Args:
            selector: CSS selector to wait for
            timeout_ms: Maximum time to wait in milliseconds (default 5000ms)
            poll_interval_ms: Polling interval in milliseconds (default 100ms)
            screenshot_name: Name for screenshot file if element not found
            raise_on_failure: If True, raises exception on timeout. If False, returns False
            take_screenshot_on_failure: If True, takes screenshot on final failure

        Returns:
            True if element found, False if not found and raise_on_failure=False

        Raises:
            Exception if element not found and raise_on_failure=True
        """
        start_time = time.time()
        elapsed_ms = 0

        logger.debug(f"Waiting for element '{selector}' (polling every {poll_interval_ms}ms, timeout {timeout_ms}ms)")

        while elapsed_ms < timeout_ms:
            try:
                # Check if element exists and is visible
                element = self.page.locator(selector)
                if element.count() > 0 and element.first.is_visible():
                    logger.debug(f"Element '{selector}' found after {elapsed_ms}ms")
                    return True
            except Exception as e:
                logger.debug(f"Element check failed: {e}")

            # Wait for poll interval
            time.sleep(poll_interval_ms / 1000)
            elapsed_ms = (time.time() - start_time) * 1000

        # Element not found after timeout
        logger.warning(f"Element '{selector}' not found after {timeout_ms}ms")

        # Take screenshot only if requested (for final failures after retries)
        if take_screenshot_on_failure:
            if screenshot_name:
                screenshot_path = f"output/{screenshot_name}.png"
            else:
                # Generate screenshot name from selector
                safe_selector = selector.replace('[', '').replace(']', '').replace('"', '').replace("'", '').replace(' ', '_')[:50]
                screenshot_path = f"output/element_not_found_{safe_selector}.png"

            try:
                self.page.screenshot(path=screenshot_path)

            except Exception as e:
                logger.warning(f"Could not save screenshot: {e}")

        # Raise exception or return False
        if raise_on_failure:
            raise Exception(f"Element '{selector}' not found after {timeout_ms}ms")
        else:
            return False

    def measure_performance_metrics(self) -> Dict[str, Any]:
        """
        Measure performance metrics using Performance API.

        Returns:
            Dictionary with performance metrics:
            - dom_interactive: Time when DOM became interactive
            - dom_content_loaded: Time when DOM content was loaded
            - dom_complete: Time when DOM is complete
            - first_contentful_paint: FCP time
            - time_to_interactive: TTI estimation
        """
        try:
            metrics = self.page.evaluate("""
            () => {
                const nav = performance.getEntriesByType('navigation')[0];
                const paint = performance.getEntriesByType('paint');

                // Get paint timing
                const fcp = paint.find(p => p.name === 'first-contentful-paint');

                // Calculate Time to Interactive (simplified)
                // TTI is approximately when there are no long tasks after FCP
                const tti = nav ? nav.domInteractive : performance.now();

                return {
                    dom_interactive: nav ? nav.domInteractive : null,
                    dom_content_loaded: nav ? nav.domContentLoadedEventEnd : null,
                    dom_complete: nav ? nav.domComplete : null,
                    first_contentful_paint: fcp ? fcp.startTime : null,
                    time_to_interactive: tti
                };
            }
            """)

            logger.debug(f"Performance metrics captured: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Failed to measure performance metrics: {e}")
            return {
                "dom_interactive": None,
                "dom_content_loaded": None,
                "dom_complete": None,
                "first_contentful_paint": None,
                "time_to_interactive": None
            }
    
    def start_frame_rate_monitoring(self, duration_seconds: float = 5.0) -> Dict[str, Any]:
        """
        Monitor frame rate using requestAnimationFrame for specified duration.
        
        Args:
            duration_seconds: How long to monitor frame rate
            
        Returns:
            Dictionary with frame rate metrics
        """
        try:
            frame_data = self.page.evaluate(f"""
            () => {{
                return new Promise((resolve) => {{
                    const startTime = performance.now();
                    const duration = {duration_seconds * 1000};
                    let frameCount = 0;
                    let lastFrameTime = startTime;
                    let minFrameTime = Infinity;
                    let maxFrameTime = 0;
                    let frameTimes = [];
                    
                    function countFrame(currentTime) {{
                        frameCount++;
                        
                        if (frameCount > 1) {{
                            const frameTime = currentTime - lastFrameTime;
                            frameTimes.push(frameTime);
                            minFrameTime = Math.min(minFrameTime, frameTime);
                            maxFrameTime = Math.max(maxFrameTime, frameTime);
                        }}
                        
                        lastFrameTime = currentTime;
                        
                        if (currentTime - startTime < duration) {{
                            requestAnimationFrame(countFrame);
                        }} else {{
                            const totalTime = currentTime - startTime;
                            const avgFrameTime = frameTimes.length > 0 ? 
                                frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length : 0;
                            
                            resolve({{
                                total_frames: frameCount,
                                duration_ms: totalTime,
                                avg_fps: frameCount / (totalTime / 1000),
                                avg_frame_time_ms: avgFrameTime,
                                min_frame_time_ms: minFrameTime === Infinity ? null : minFrameTime,
                                max_frame_time_ms: maxFrameTime,
                                dropped_frames: frameTimes.filter(ft => ft > 16.67).length  // > 60fps threshold
                            }});
                        }}
                    }}
                    
                    requestAnimationFrame(countFrame);
                }});
            }}
            """)
            
            logger.debug(f"Frame rate data: {frame_data}")
            return frame_data
            
        except Exception as e:
            logger.warning(f"Frame rate monitoring failed: {e}")
            return {"avg_fps": None, "dropped_frames": None}
    
    def measure_long_tasks(self, duration_seconds: float = 10.0) -> UIResponsivenessMetrics:
        """
        Measure long tasks and UI blocking time for specified duration.
        
        Args:
            duration_seconds: How long to monitor for long tasks
            
        Returns:
            UIResponsivenessMetrics with long task data
        """
        try:
            # Start long task observation
            self.page.evaluate("""
            () => {
                if ('PerformanceObserver' in window && !window._longTaskObserver) {
                    window._longTaskData = [];
                    window._longTaskObserver = new PerformanceObserver((list) => {
                        list.getEntries().forEach(entry => {
                            window._longTaskData.push({
                                duration: entry.duration,
                                startTime: entry.startTime,
                                name: entry.name
                            });
                        });
                    });
                    window._longTaskObserver.observe({entryTypes: ['longtask']});
                }
            }
            """)
            
            # Wait for the specified duration
            time.sleep(duration_seconds)
            
            # Collect long task data
            long_task_data = self.page.evaluate("""
            () => {
                if (window._longTaskData) {
                    const tasks = window._longTaskData;
                    let totalBlockingTime = 0;
                    
                    tasks.forEach(task => {
                        // Tasks longer than 50ms contribute to Total Blocking Time
                        if (task.duration > 50) {
                            totalBlockingTime += (task.duration - 50);
                        }
                    });
                    
                    // Clean up observer
                    if (window._longTaskObserver) {
                        window._longTaskObserver.disconnect();
                        delete window._longTaskObserver;
                    }
                    
                    const result = {
                        long_tasks_count: tasks.length,
                        total_blocking_time: totalBlockingTime,
                        avg_task_duration: tasks.length > 0 ? 
                            tasks.reduce((sum, task) => sum + task.duration, 0) / tasks.length : 0
                    };
                    
                    delete window._longTaskData;
                    return result;
                }
                return {long_tasks_count: 0, total_blocking_time: 0, avg_task_duration: 0};
            }
            """)
            
            return UIResponsivenessMetrics(
                long_tasks_count=long_task_data['long_tasks_count'],
                total_blocking_time_s=long_task_data['total_blocking_time'] / 1000  # Convert ms to seconds
            )
            
        except Exception as e:
            logger.warning(f"Long task measurement failed: {e}")
            return UIResponsivenessMetrics()
    
    def measure_interaction_response_time(self, selector: str, interaction_type: str = "click") -> float:
        """
        Measure time from user interaction to visual response.
        
        Args:
            selector: Element to interact with
            interaction_type: Type of interaction (click, hover, focus)
            
        Returns:
            Response time in milliseconds
        """
        try:
            response_time = self.page.evaluate(f"""
            (selector) => {{
                return new Promise((resolve) => {{
                    const element = document.querySelector(selector);
                    if (!element) {{
                        resolve(null);
                        return;
                    }}
                    
                    const startTime = performance.now();
                    
                    // Set up a MutationObserver to detect DOM changes
                    const observer = new MutationObserver(() => {{
                        const endTime = performance.now();
                        observer.disconnect();
                        resolve(endTime - startTime);
                    }});
                    
                    // Start observing
                    observer.observe(document.body, {{
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeOldValue: true
                    }});
                    
                    // Trigger the interaction
                    element.{interaction_type}();
                    
                    // Fallback timeout
                    setTimeout(() => {{
                        observer.disconnect();
                        resolve(performance.now() - startTime);
                    }}, 5000);
                }});
            }}
            """, selector)
            
            return response_time if response_time else 0.0
            
        except Exception as e:
            logger.warning(f"Interaction response time measurement failed: {e}")
            return 0.0

    def measure_comprehensive_performance(
        self,
        action_callback: Callable,
        wait_selector: Optional[str] = None,
        timeout: int = 30000,
        measure_frame_rate: bool = True,
        measure_memory: bool = True,
        measure_resources: bool = True,
        measure_responsiveness: bool = True
    ) -> tuple[float, Dict[str, Any], CoreWebVitals, MemoryMetrics, ResourceTimingMetrics, UIResponsivenessMetrics]:
        """
        Comprehensive performance measurement including all new metrics.
        
        Args:
            action_callback: Function to execute that triggers the action
            wait_selector: Optional selector to wait for after action
            timeout: Maximum time to wait in milliseconds
            measure_frame_rate: Whether to measure frame rate during action
            measure_memory: Whether to collect memory metrics
            measure_resources: Whether to collect resource timing
            measure_responsiveness: Whether to measure UI responsiveness
            
        Returns:
            Tuple of (load_time_ms, basic_metrics, core_web_vitals, memory_metrics, resource_timing, ui_responsiveness)
        """
        from utils.performance_tracker import PerformanceTracker

        tracker = PerformanceTracker("temp", {})

        # Clear resource timings buffer before measurement to avoid accumulation across actions
        if measure_resources:
            try:
                self.page.evaluate("() => performance.clearResourceTimings()")
                logger.debug("Cleared resource timings buffer before measurement")
            except Exception as e:
                logger.warning(f"Failed to clear resource timings: {e}")

        # Execute the action and measure basic load time first
        load_time_ms, basic_metrics = self.measure_spa_navigation(action_callback, wait_selector, timeout)
        
        # Start frame rate monitoring after main action (to avoid threading issues)
        frame_data = {}
        if measure_frame_rate:
            try:
                frame_data = self.start_frame_rate_monitoring(2.0)  # Reduced duration
            except Exception as e:
                logger.warning(f"Frame rate monitoring failed: {e}")
                frame_data = {}
        
        # Collect comprehensive metrics
        core_web_vitals = tracker.collect_core_web_vitals(self.page) if measure_responsiveness else CoreWebVitals()
        memory_metrics = tracker.collect_memory_metrics(self.page) if measure_memory else MemoryMetrics()
        resource_timing = tracker.collect_resource_timing_metrics(self.page) if measure_resources else ResourceTimingMetrics()
        
        # Collect UI responsiveness (including frame rate data)
        ui_responsiveness = UIResponsivenessMetrics()
        if measure_responsiveness:
            ui_base = tracker.collect_ui_responsiveness_metrics(self.page)
            ui_responsiveness = UIResponsivenessMetrics(
                long_tasks_count=ui_base.long_tasks_count,
                total_blocking_time_s=ui_base.total_blocking_time_s,
                avg_frame_rate=frame_data.get('avg_fps'),
                interaction_response_time_s=None  # Could be measured separately
            )
        
        return load_time_ms, basic_metrics, core_web_vitals, memory_metrics, resource_timing, ui_responsiveness
    
    def measure_spa_navigation(
        self,
        action_callback,
        wait_selector: Optional[str] = None,
        timeout: int = 30000
    ) -> tuple[float, Dict[str, Any]]:
        """
        Measure SPA navigation performance (for Angular routing without full page reload).

        Measures real load time: action → network idle (includes data load + render)
        Does NOT include browser metrics (they're invalid for SPA navigations).

        Args:
            action_callback: Function to execute that triggers navigation
            wait_selector: Optional selector to wait for after navigation
            timeout: Maximum time to wait in milliseconds

        Returns:
            Tuple of (load_time_ms, empty_dict) - metrics not included for SPA
        """
        try:
            # START TIMER before executing action to capture full load time
            start_time = time.time()

            # Execute the action (click, navigate, etc.)
            action_callback()

            # Wait 300ms for dynamic content to start loading
            time.sleep(0.3)

            # Wait for specific element if provided (initial container) with retry
            if wait_selector:
                self.wait_for_element_with_retry(
                    wait_selector,
                    timeout_ms=5000,
                    screenshot_name="spa_navigation_element_not_found",
                    raise_on_failure=False  # Continue even if not found
                )

            # Wait for network to become idle (AJAX/data loading complete)
            # networkidle already waits for 500ms of no network activity
            try:
                self.page.wait_for_load_state("networkidle", timeout=15000)
                logger.debug("Network idle - data loaded and rendered")
            except PlaywrightTimeoutError:
                logger.warning("Network idle timeout - continuing anyway")

            # END TIMER - Calculate real load time
            end_time = time.time()
            load_time_ms = (end_time - start_time) * 1000

            # Don't include browser metrics - they're from original page load, not this SPA navigation
            return load_time_ms, {}

        except PlaywrightTimeoutError as e:
            logger.error(f"SPA navigation timeout: {e}")
            end_time = time.time()
            load_time_ms = (end_time - start_time) * 1000
            return load_time_ms, {}

    def click_and_measure(
        self,
        selector: str,
        wait_selector: Optional[str] = None,
        timeout: int = 30000
    ) -> tuple[float, Dict[str, Any]]:
        """
        Click an element and measure the resulting page load performance.

        Args:
            selector: CSS selector of element to click
            wait_selector: Optional selector to wait for after click
            timeout: Maximum time to wait in milliseconds

        Returns:
            Tuple of (load_time_ms, metrics_dict)
        """
        # Wait for element to be clickable before clicking
        self.wait_for_element_with_retry(
            selector,
            timeout_ms=5000,
            screenshot_name="click_and_measure_element_not_found"
        )

        def click_action():
            self.page.click(selector)

        return self.measure_spa_navigation(click_action, wait_selector, timeout)

    def go_back_and_measure(
        self,
        wait_selector: Optional[str] = None,
        timeout: int = 30000
    ) -> tuple[float, Dict[str, Any]]:
        """
        Navigate back using browser back button and measure performance.

        Args:
            wait_selector: Optional selector to wait for after navigation
            timeout: Maximum time to wait in milliseconds

        Returns:
            Tuple of (load_time_ms, metrics_dict)
        """
        def back_action():
            self.page.go_back()

        return self.measure_spa_navigation(back_action, wait_selector, timeout)

    def get_element_count(self, selector: str) -> int:
        """
        Get count of elements matching selector.

        Args:
            selector: CSS selector

        Returns:
            Number of matching elements
        """
        return self.page.locator(selector).count()

    def get_elements(self, selector: str):
        """
        Get all elements matching selector.

        Args:
            selector: CSS selector

        Returns:
            Playwright Locator object
        """
        return self.page.locator(selector)
