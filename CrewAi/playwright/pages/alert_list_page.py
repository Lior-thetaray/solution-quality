"""
Alert List Page Object.
Handles interactions with the alert list page.
"""

import logging
from typing import Dict, Any
from playwright.sync_api import Page
from pages.base_page import BasePage
from config.config import Selectors, TestData

logger = logging.getLogger(__name__)


class AlertListPage(BasePage):
    """Page Object for Alert List page"""

    def __init__(self, page: Page):
        """
        Initialize AlertListPage.

        Args:
            page: Playwright Page instance
        """
        super().__init__(page)
        self.use_case_container_selector = Selectors.USE_CASE_CONTAINER
        self.use_case_dropdown_selector = Selectors.USE_CASE_DROPDOWN
        self.dropdown_item_selector = Selectors.DROPDOWN_ITEM
        self.alert_title_selector = Selectors.ALERT_TITLE

    def select_use_case(self, use_case_value: str = None, timeout: int = 30000) -> tuple[float, Dict[str, Any]]:
        """
        Select a use case from the dropdown and measure performance.

        Args:
            use_case_value: The text value to select (defaults to TestData.USE_CASE_VALUE)
            timeout: Maximum time to wait in milliseconds

        Returns:
            Tuple of (load_time_ms, metrics_dict)
        """
        if use_case_value is None:
            use_case_value = TestData.USE_CASE_VALUE

        logger.debug(f"Selecting use case: {use_case_value}")

        # Wait for use case container to appear with retry
        self.wait_for_element_with_retry(
            Selectors.USE_CASE_CONTAINER,
            timeout_ms=5000,
            screenshot_name="use_case_container_not_found",
            take_screenshot_on_failure=True  # Only screenshot if this is the final failure
        )

        # Click dropdown to open it and measure performance
        import time
        start_time = time.time()

        # Wait for dropdown selector to be clickable with retry
        self.wait_for_element_with_retry(
            self.use_case_dropdown_selector,
            timeout_ms=5000,
            screenshot_name="use_case_dropdown_not_clickable"
        )

        # Click the dropdown
        self.page.click(self.use_case_dropdown_selector)
        logger.debug("Use case dropdown opened")

        # Wait 300ms for dropdown to open and populate
        time.sleep(0.3)

        # Wait for dropdown items to appear with retry
        self.wait_for_element_with_retry(
            self.dropdown_item_selector,
            timeout_ms=5000,
            screenshot_name="use_case_dropdown_items_not_found"
        )

        # Find and click the item with matching text
        dropdown_items = self.page.locator(self.dropdown_item_selector)
        item_count = dropdown_items.count()
        logger.debug(f"Found {item_count} dropdown items")

        item_found = False
        for i in range(item_count):
            item_text = dropdown_items.nth(i).text_content()
            if item_text and use_case_value in item_text:
                logger.debug(f"Found matching item: {item_text}")
                dropdown_items.nth(i).click()
                item_found = True
                break

        if not item_found:
            raise ValueError(f"Use case '{use_case_value}' not found in dropdown")

        # Wait for page to reload/update after selection
        self.page.wait_for_load_state("domcontentloaded", timeout=timeout)

        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000

        # Get performance metrics
        metrics = self.measure_performance_metrics()

        logger.debug(f"Use case selection completed in {load_time_ms:.2f}ms")
        return load_time_ms, metrics

    def wait_for_alert_list_loaded(self, timeout: int = 30000) -> None:
        """
        Wait for alert list to be fully loaded.

        Args:
            timeout: Maximum time to wait in milliseconds
        """
        self.wait_for_page_load(timeout)
        self.wait_for_element(self.alert_title_selector, timeout)
        logger.debug("Alert list page loaded")

    def measure_page_load(self) -> tuple[float, Dict[str, Any]]:
        """
        Measure alert list page load performance.

        Measures real load time including network requests and rendering.
        This is the ONLY place where browser metrics are valid (actual page navigation).

        Returns:
            Tuple of (load_time_ms, metrics_dict)
        """
        import time

        # START TIMER
        start_time = time.time()

        # Wait for alerts to appear with retry
        self.wait_for_element_with_retry(
            self.alert_title_selector,
            timeout_ms=5000,
            screenshot_name="alert_list_load_timeout"
        )

        # Wait 300ms for any additional network requests to start
        time.sleep(0.3)

        # Wait for network to become idle
        # networkidle already waits for 500ms of no network activity
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
            logger.debug("Network idle after alert list load")
        except:
            logger.warning("Network idle timeout for alert list")

        # END TIMER
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000

        # Get browser metrics (valid for actual page navigation)
        metrics = self.measure_performance_metrics()

        logger.info(f"Alert list page load time: {load_time_ms:.2f}ms")
        return load_time_ms, metrics

    def get_alert_count(self) -> int:
        """
        Get the number of alerts displayed on the page.

        Returns:
            Number of alert elements
        """
        # Wait for alerts to appear with retry before counting
        self.wait_for_element_with_retry(
            self.alert_title_selector,
            timeout_ms=5000,
            screenshot_name="alerts_not_found_for_count"
        )

        count = self.get_element_count(self.alert_title_selector)
        logger.debug(f"Found {count} alerts on page")
        return count

    def click_first_alert(self, timeout: int = 30000) -> tuple[float, Dict[str, Any]]:
        """
        Click the first alert in the list and measure navigation performance.

        Args:
            timeout: Maximum time to wait in milliseconds

        Returns:
            Tuple of (load_time_ms, metrics_dict)
        """
        import time

        logger.debug("Clicking first alert")

        # Wait for alerts to be visible with retry
        self.wait_for_element_with_retry(
            self.alert_title_selector,
            timeout_ms=5000,
            screenshot_name="alert_not_found"
        )

        # Get current URL before click
        url_before = self.page.url
        logger.debug(f"URL before click: {url_before}")

        # Click the first alert
        self.page.locator(self.alert_title_selector).first.click()
        logger.debug("First alert clicked")

        # START TIMER immediately after click
        start_time = time.time()

        # Wait for URL to change (SPA navigation)
        try:
            self.page.wait_for_url(lambda url: url != url_before, timeout=timeout)
            logger.debug(f"URL changed to: {self.page.url}")
        except Exception as e:
            logger.warning(f"URL did not change after click: {e}")

        # Wait 300ms for dynamic content to start loading
        time.sleep(0.3)

        # Wait for network to become idle (data loaded)
        # networkidle already waits for 500ms of no network activity
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
            logger.debug("Network idle after clicking alert")
        except Exception as e:
            logger.warning(f"Network idle timeout: {e}")

        # END TIMER
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000

        # No metrics for SPA navigation
        logger.info(f"Alert details page load time: {load_time_ms:.2f}ms")
        return load_time_ms, {}

    def click_alert_by_index(self, index: int, timeout: int = 30000) -> tuple[float, Dict[str, Any]]:
        """
        Click a specific alert by index and measure navigation performance.

        Args:
            index: Zero-based index of the alert to click
            timeout: Maximum time to wait in milliseconds

        Returns:  
            Tuple of (load_time_ms, metrics_dict)
        """
        # First check how many alerts are available
        alerts = self.get_elements(self.alert_title_selector)
        alert_count = alerts.count()
        logger.debug(f"Found {alert_count} alerts on the page")

        if index >= alert_count:
            raise IndexError(f"Alert index {index} out of range (total alerts: {alert_count})")

        logger.debug(f"Clicking alert at index {index}")

        # Get current URL before click
        url_before = self.page.url
        logger.debug(f"URL before click: {url_before}")

        # Click the specific alert using Playwright's nth() method
        import time
        start_time = time.time()
        
        alerts.nth(index).click()
        logger.debug(f"Alert at index {index} clicked")

        # Wait for URL to change (SPA navigation)
        try:
            self.page.wait_for_url(lambda url: url != url_before, timeout=timeout)
            logger.debug(f"URL changed to: {self.page.url}")
        except Exception as e:
            logger.warning(f"URL did not change after click: {e}")

        # Wait 300ms for dynamic content to start loading
        time.sleep(0.3)

        # Wait for network to become idle (data loaded)
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
            logger.debug("Network idle after clicking alert")
        except Exception as e:
            logger.warning(f"Network idle timeout: {e}")

        # END TIMER
        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000

        logger.info(f"Alert details page load time: {load_time_ms}ms")
        return load_time_ms, {}

    def navigate_back_to_alert_list(self, timeout: int = 30000) -> tuple[float, Dict[str, Any]]:
        """
        Navigate back to alert list using the 'All alerts' link and measure performance.

        Args:
            timeout: Maximum time to wait in milliseconds

        Returns:
            Tuple of (load_time_ms, metrics_dict)
        """
        logger.debug("Navigating back to alert list")

        # Look for the 'All alerts' link using data-cy attributes
        all_alerts_selector = '[data-cy="alerts-view-item"][data-cy-view="All alerts"]'

        # Wait for the element to be available
        self.wait_for_element_with_retry(
            all_alerts_selector,
            timeout_ms=5000,
            screenshot_name="all_alerts_link_not_found"
        )

        # Click and measure navigation performance
        load_time_ms, metrics = self.click_and_measure(
            selector=all_alerts_selector,
            wait_selector=self.alert_title_selector,  # Wait for alert list to load
            timeout=timeout
        )

        logger.info(f"Navigation back to alert list completed in {load_time_ms}ms")
        return load_time_ms, metrics
