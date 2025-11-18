"""
Network emulation utilities using Chrome DevTools Protocol (CDP).
Configures network conditions for performance testing.
"""

from playwright.sync_api import Page
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class NetworkEmulator:
    """Handles network condition emulation via CDP"""

    def __init__(self, page: Page, browser_type: str = "chromium"):
        """
        Initialize NetworkEmulator with a Playwright page.

        Args:
            page: Playwright Page instance
            browser_type: Browser type (chromium, firefox, webkit)
        """
        self.page = page
        self.browser_type = browser_type
        self.cdp_session = None

    def setup_network_conditions(self, config: Dict[str, Any], headless: bool = True) -> None:
        """
        Configure network conditions using Chrome DevTools Protocol.

        Args:
            config: Dictionary with keys:
                - download_throughput: bytes per second
                - upload_throughput: bytes per second
                - latency: milliseconds
            headless: Whether browser is running in headless mode

        Example:
            config = {
                "download_throughput": 131072000,  # 1 Gbps
                "upload_throughput": 91750400,     # 700 Mbps
                "latency": 40                       # 40ms
            }
        """
        # CDP only works with Chromium
        if self.browser_type != "chromium":
            logger.warning(
                f"Network emulation not supported for {self.browser_type}. "
                "CDP is only available in Chromium-based browsers."
            )
            return

        # CDP network emulation can cause crashes on macOS in headed mode
        if not headless:
            logger.warning(
                "Network emulation skipped in headed mode due to CDP stability issues on macOS. "
                "Run in headless mode with Chromium for accurate network throttling."
            )
            return

        try:
            # Create CDP session if not exists
            if not self.cdp_session:
                self.cdp_session = self.page.context.new_cdp_session(self.page)

            # Configure network emulation
            self.cdp_session.send("Network.emulateNetworkConditions", {
                "offline": False,
                "downloadThroughput": config["download_throughput"],
                "uploadThroughput": config["upload_throughput"],
                "latency": config["latency"]
            })

            logger.info(
                f"Network conditions set: "
                f"Download={config['download_throughput']/1024/1024:.0f}Mbps, "
                f"Upload={config['upload_throughput']/1024/1024:.0f}Mbps, "
                f"Latency={config['latency']}ms"
            )

        except Exception as e:
            logger.error(f"Failed to set network conditions: {e}")
            raise

    def disable_network_throttling(self) -> None:
        """Disable network throttling and return to normal conditions"""
        try:
            if self.cdp_session:
                self.cdp_session.send("Network.emulateNetworkConditions", {
                    "offline": False,
                    "downloadThroughput": -1,  # -1 disables throttling
                    "uploadThroughput": -1,
                    "latency": 0
                })
                logger.debug("Network throttling disabled")
        except Exception as e:
            logger.error(f"Failed to disable network throttling: {e}")

    def close(self) -> None:
        """Close CDP session"""
        if self.cdp_session:
            try:
                self.cdp_session.detach()
                logger.debug("CDP session closed")
            except Exception as e:
                logger.warning(f"Error closing CDP session: {e}")
