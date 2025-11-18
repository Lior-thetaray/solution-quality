"""
Login page for Keycloak authentication.
Handles authentication flow before accessing the application.
"""

import logging
from typing import Dict, Any
from playwright.sync_api import Page
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Handles Keycloak login page interactions"""

    # Keycloak login selectors
    USERNAME_INPUT = 'input[name="username"]'
    PASSWORD_INPUT = 'input[name="password"]'
    LOGIN_BUTTON = 'input[type="submit"]'

    def __init__(self, page: Page):
        """
        Initialize LoginPage.

        Args:
            page: Playwright Page instance
        """
        super().__init__(page)

    def login(self, username: str, password: str, timeout: int = 30000) -> tuple[float, Dict[str, Any]]:
        """
        Perform login through Keycloak.

        Args:
            username: Username for authentication
            password: Password for authentication
            timeout: Maximum time to wait in milliseconds

        Returns:
            Tuple of (load_time_ms, metrics_dict)
        """
        import time

        logger.debug(f"Logging in as: {username}")
        start_time = time.time()

        try:
            # Wait for login form to appear with retry
            logger.debug("Waiting for login form...")
            self.wait_for_element_with_retry(
                self.USERNAME_INPUT,
                timeout_ms=5000,
                screenshot_name="login_form_username_not_found"
            )

            # Clear and fill username (type slowly for better reliability)
            logger.debug("Filling username...")
            self.page.click(self.USERNAME_INPUT)
            self.page.fill(self.USERNAME_INPUT, "")  # Clear first
            self.page.type(self.USERNAME_INPUT, username, delay=50)  # Type with 50ms delay per character
            time.sleep(0.3)  # Wait for validation

            # Wait for password field with retry
            self.wait_for_element_with_retry(
                self.PASSWORD_INPUT,
                timeout_ms=5000,
                screenshot_name="login_form_password_not_found"
            )

            # Clear and fill password (type slowly for better reliability)
            logger.debug("Filling password...")
            self.page.click(self.PASSWORD_INPUT)
            self.page.fill(self.PASSWORD_INPUT, "")  # Clear first
            self.page.type(self.PASSWORD_INPUT, password, delay=50)  # Type with 50ms delay per character
            time.sleep(0.3)  # Wait for validation

            # Wait for login button with retry
            self.wait_for_element_with_retry(
                self.LOGIN_BUTTON,
                timeout_ms=5000,
                screenshot_name="login_button_not_found"
            )

            # Click login button and wait for navigation
            logger.debug("Clicking login button...")
            self.page.click(self.LOGIN_BUTTON)
            time.sleep(0.5)  # Wait for form submission

            # Wait for redirect after login (wait for URL to change away from Keycloak)
            logger.debug("Waiting for redirect after login...")
            self.page.wait_for_load_state("domcontentloaded", timeout=timeout)

            # Calculate login time
            end_time = time.time()
            load_time_ms = (end_time - start_time) * 1000

            logger.info(f"Login successful (took {load_time_ms:.2f}ms)")
            logger.debug(f"Current URL after login: {self.page.url}")

            # Get performance metrics
            metrics = self.measure_performance_metrics()

            return load_time_ms, metrics

        except Exception as e:
            logger.error(f"Login failed: {e}")
            logger.debug(f"Current URL: {self.page.url}")
            # Take screenshot for debugging
            try:
                self.page.screenshot(path="output/login_error.png")
            except:
                pass
            raise
