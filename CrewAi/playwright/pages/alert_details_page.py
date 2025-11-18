"""
Alert Details Page Object.
Handles interactions with alert details page including feature navigation.
"""

import logging
from typing import Dict, Any, List
from playwright.sync_api import Page
from pages.base_page import BasePage
from config.config import Selectors

logger = logging.getLogger(__name__)


class AlertDetailsPage(BasePage):
    """Page Object for Alert Details page with feature navigation"""

    def __init__(self, page: Page):
        """
        Initialize AlertDetailsPage.

        Args:
            page: Playwright Page instance
        """
        super().__init__(page)
        self.risk_chart_widget_selector = Selectors.RISK_CHART_WIDGET
        self.nav_button_selector = Selectors.NAV_BUTTON
        self.nav_back_selector = Selectors.NAV_BACK

    def wait_for_details_loaded(self, timeout: int = 30000) -> None:
        """
        Wait for alert details page to be fully loaded.

        Args:
            timeout: Maximum time to wait in milliseconds
        """
        self.wait_for_page_load(timeout)
        # Wait for at least one widget to be present with retry
        self.wait_for_element_with_retry(
            self.risk_chart_widget_selector,
            timeout_ms=5000,
            screenshot_name="risk_chart_widget_not_loaded"
        )
        logger.debug("Alert details page loaded")

    def _wait_for_data_count_loaded(self, timeout_ms: int = 5000) -> bool:
        """
        Wait for dynamic data count to be loaded in the header.

        Looks for .header-left h3 .total element with a number inside () - e.g., (14), (5), or (0).
        This indicates that the data has been loaded and displayed.

        Args:
            timeout_ms: Maximum time to wait in milliseconds

        Returns:
            True if count loaded, False if not found
        """
        import time
        import re

        start_time = time.time()
        elapsed_ms = 0

        logger.debug("Waiting for data count to be loaded in header...")

        while elapsed_ms < timeout_ms:
            try:
                # Look for .header-left h3 .total element
                total_elements = self.page.locator('.header-left h3 .total')

                if total_elements.count() > 0:
                    # Get the text content
                    total_text = total_elements.first.text_content()

                    # Check if it has a number inside parentheses: (14), (0), etc.
                    if total_text and re.search(r'\(\d+\)', total_text):
                        logger.debug(f"Data count loaded: {total_text}")
                        return True
            except Exception as e:
                logger.debug(f"Error checking data count: {e}")

            # Wait for poll interval
            time.sleep(0.1)
            elapsed_ms = (time.time() - start_time) * 1000

        logger.warning(f"Data count not loaded after {timeout_ms}ms - continuing anyway")
        return False

    def get_feature_widget_count(self) -> int:
        """
        Get the number of feature widgets on the page.

        Returns:
            Number of risk chart widgets
        """
        # Wait for feature widgets to appear with retry
        self.wait_for_element_with_retry(
            self.risk_chart_widget_selector,
            timeout_ms=5000,
            screenshot_name="feature_widgets_not_found",
            take_screenshot_on_failure=True
        )

        count = self.get_element_count(self.risk_chart_widget_selector)
        logger.debug(f"Found {count} feature widgets")
        return count

    def navigate_to_feature(
        self,
        feature_index: int,
        timeout: int = 30000
    ) -> tuple[float, Dict[str, Any]]:
        """
        Navigate to a specific feature by hovering and clicking its nav button.

        Args:
            feature_index: Zero-based index of the feature widget
            timeout: Maximum time to wait in milliseconds

        Returns:
            Tuple of (load_time_ms, metrics_dict)
        """
        import time

        # Wait for widgets to appear with retry before getting them
        try:
            self.wait_for_element_with_retry(
                self.risk_chart_widget_selector,
                timeout_ms=10000,  # Increased timeout
                screenshot_name=f"widgets_not_found_before_feature_{feature_index}"
            )
        except Exception as e:
            # Debug: Log available elements on the page
            self.logger.error(f"Could not find {self.risk_chart_widget_selector}. Page URL: {self.page.url}")
            
            # Try alternative selectors
            alternative_selectors = [
                '[data-cy*="feature"]',
                '.feature-item', 
                '.widget',
                '[class*="feature"]',
                'tr-feature-item',
                'feature-item'
            ]
            
            for selector in alternative_selectors:
                try:
                    count = self.get_element_count(selector)
                    if count > 0:
                        self.logger.info(f"Found {count} elements with selector: {selector}")
                        # Use this selector instead
                        self.risk_chart_widget_selector = selector
                        break
                except:
                    continue
            else:
                # If no alternative found, take screenshot and re-raise
                self.page.screenshot(path=f"output/debug_page_feature_{feature_index}.png")
                raise e

        widgets = self.get_elements(self.risk_chart_widget_selector)
        widget_count = widgets.count()

        if feature_index >= widget_count:
            raise IndexError(
                f"Feature index {feature_index} out of range (total widgets: {widget_count})"
            )

        logger.debug(f"Navigating to feature {feature_index}")

        # Get the specific widget
        widget = widgets.nth(feature_index)

        # Hover over the widget to make nav button visible
        logger.debug(f"Hovering over widget {feature_index}")
        widget.hover()
        time.sleep(0.3)  # Wait for hover animation

        # Find the nav button within the widget (no complex selector needed)
        nav_button = widget.locator(self.nav_button_selector)

        # Quick check if button exists
        if nav_button.count() == 0:
            logger.warning(f"Nav button not found in widget {feature_index}")
            # Take screenshot for debugging
            try:
                self.page.screenshot(path=f"output/nav_button_feature_{feature_index}_not_found.png")
            except:
                pass

        # Get current URL before click
        url_before = self.page.url
        logger.debug(f"URL before clicking nav button: {url_before}")

        # Try multiple click methods (faster approach - try JavaScript first)
        click_success = False

        # Method 1: Try JavaScript click directly (fastest, usually works)
        try:
            logger.debug("Attempting JavaScript click on nav button...")
            nav_button.evaluate("el => el.click()")
            click_success = True
            logger.debug(f"Nav button clicked via JavaScript for feature {feature_index}")
        except Exception as e1:
            logger.warning(f"JavaScript click failed: {e1}")

            # Method 2: Try force click as fallback
            try:
                logger.debug("Attempting force click...")
                nav_button.click(force=True, timeout=5000)  # Shorter timeout
                click_success = True
                logger.debug(f"Nav button force-clicked for feature {feature_index}")
            except Exception as e2:
                logger.error(f"All click methods failed: {e2}")
                # Take screenshot for debugging
                try:
                    self.page.screenshot(path=f"output/feature_{feature_index}_nav_button_error.png")
                except:
                    pass
                raise Exception(f"Could not click nav button for feature {feature_index}")

        if not click_success:
            raise Exception(f"Failed to click nav button for feature {feature_index}")

        # START TIMER immediately after click
        start_time = time.time()

        # Wait for URL to change
        try:
            self.page.wait_for_url(lambda url: url != url_before, timeout=timeout)
            logger.debug(f"URL changed to: {self.page.url}")
        except Exception as e:
            logger.warning(f"URL did not change after clicking nav button: {e}")

        # Wait 300ms for dynamic content to start loading
        time.sleep(0.3)

        # Wait for feature page content to load (tr-transactions-table-evolution element)
        self.wait_for_element_with_retry(
            'tr-transactions-table-evolution',
            timeout_ms=5000,
            screenshot_name=f"transactions_table_feature_{feature_index}_not_loaded",
            raise_on_failure=False  # Continue even if not found (some features may have different content)
        )

        # Wait for dynamic data to be loaded and displayed (check for count in header)
        # Look for .header-left h3 .total to have a number inside () - this means data is loaded
        self._wait_for_data_count_loaded(timeout_ms=5000)

        # Wait for network to become idle (data loaded)
        # networkidle already waits for 500ms of no network activity
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
            logger.debug(f"Network idle after loading feature {feature_index}")
        except Exception as e:
            logger.warning(f"Network idle timeout: {e}")

        # END TIMER
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000

        # No metrics for SPA navigation
        logger.info(f"Feature {feature_index} load time: {load_time_ms:.2f}ms")
        return load_time_ms, {}

    def navigate_back(self, timeout: int = 30000) -> tuple[float, Dict[str, Any]]:
        """
        Navigate back to alert details using the back button.

        Args:
            timeout: Maximum time to wait in milliseconds

        Returns:
            Tuple of (load_time_ms, metrics_dict)
        """
        import time

        logger.debug("Navigating back to alert details")

        # Get current URL before click
        url_before = self.page.url
        logger.debug(f"URL before navigate back: {url_before}")

        # Wait for back button to be visible with retry
        back_button_found = self.wait_for_element_with_retry(
            self.nav_back_selector,
            timeout_ms=5000,
            screenshot_name="nav_back_button_not_found",
            raise_on_failure=False  # Don't raise, we'll try browser back as fallback
        )

        # Click the back button
        if back_button_found:
            try:
                self.page.locator(self.nav_back_selector).click()
                logger.debug("Back button clicked")
            except Exception as e:
                logger.warning(f"Could not click back button: {e}")
                # Try browser back as fallback
                logger.debug("Trying browser back as fallback")
                self.page.go_back()
        else:
            # Back button not found, use browser back
            logger.debug("Back button not found, using browser back")
            self.page.go_back()

        # START TIMER immediately after click
        start_time = time.time()

        # Wait for URL to change
        try:
            self.page.wait_for_url(lambda url: url != url_before, timeout=timeout)
            logger.debug(f"URL changed to: {self.page.url}")
        except Exception as e:
            logger.warning(f"URL did not change after navigate back: {e}")

        # Wait 300ms for dynamic content to start loading
        time.sleep(0.3)

        # Wait for risk chart widgets to appear with retry
        self.wait_for_element_with_retry(
            self.risk_chart_widget_selector,
            timeout_ms=5000,
            screenshot_name="risk_chart_widgets_not_found",
            raise_on_failure=False  # Continue even if widgets not found
        )

        # Wait for network to become idle (data loaded)
        # networkidle already waits for 500ms of no network activity
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
            logger.debug("Network idle after navigate back")
        except Exception as e:
            logger.warning(f"Network idle timeout: {e}")

        # END TIMER
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000

        # No metrics for SPA navigation
        logger.info(f"Navigate back load time: {load_time_ms:.2f}ms")
        return load_time_ms, {}

    def navigate_all_features(
        self,
        timeout: int = 30000
    ) -> List[Dict[str, Any]]:
        """
        Navigate through all feature widgets and measure performance for each.

        Args:
            timeout: Maximum time to wait in milliseconds

        Returns:
            List of dictionaries with feature navigation measurements
        """
        feature_count = self.get_feature_widget_count()
        measurements = []

        logger.debug(f"Starting navigation loop for {feature_count} features")

        for i in range(feature_count):
            try:
                # Navigate to feature
                nav_load_time, nav_metrics = self.navigate_to_feature(i, timeout)

                # Navigate back
                back_load_time, back_metrics = self.navigate_back(timeout)

                # Store measurements
                measurements.append({
                    "feature_index": i,
                    "navigate_to_feature": {
                        "load_time_ms": nav_load_time,
                        "metrics": nav_metrics
                    },
                    "navigate_back": {
                        "load_time_ms": back_load_time,
                        "metrics": back_metrics
                    }
                })

                logger.debug(
                    f"Feature {i} completed - "
                    f"Navigate: {nav_load_time:.2f}ms, Back: {back_load_time:.2f}ms"
                )

            except Exception as e:
                logger.error(f"Error navigating feature {i}: {e}")
                measurements.append({
                    "feature_index": i,
                    "error": str(e)
                })

        logger.debug(f"Completed navigation for all {feature_count} features")
        return measurements
