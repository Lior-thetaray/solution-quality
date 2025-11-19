"""
Configuration file for Playwright performance testing.
Contains credentials, URLs, selectors, and test settings.
"""

# Runtime Configuration
# These will be set at runtime via user input
USERNAME = ""  # Will be set at runtime
PASSWORD = ""  # Will be set at runtime
BASE_URL = ""  # Will be set at runtime
ALERT_LIST_URL = ""  # Will be constructed at runtime

# Network Configuration (1 Gbps fiber)
NETWORK_CONFIG = {
    "download_throughput": 1024000000,  # 1 Gbps in bytes/sec
    "upload_throughput": 716800000,     # 700 Mbps in bytes/sec
    "latency": 40                       # 40 ms ping
}

# Multi-Alert Testing Configuration
ALERTS_TO_TEST_COUNT = 10  # Number of alerts to test in sequence


# Browser Configuration
VIEWPORT = {
    "width": 1920,
    "height": 1080
}

BROWSER_TYPE = "chrome" 
HEADLESS = True  # Set to False to see browser window

# Performance Monitoring Configuration
PERFORMANCE_CONFIG = {
    "enable_performance_observer": True,
    "enable_resource_timing": True,
    "enable_long_task_api": True,
    "enable_layout_shift_api": True,
    "enable_paint_timing": True,
    "memory_monitoring_interval": 1.0,  # seconds
    "frame_rate_monitoring_duration": 5.0,  # seconds
    "long_task_monitoring_duration": 10.0  # seconds
}

# Browser Launch Arguments for Performance Monitoring
BROWSER_ARGS = {
    "chromium": [
        '--enable-precise-memory-info',  # Enable performance.memory API
        '--enable-performance-observer-tracing',  # Enable Performance Observer
        '--disable-web-security',  # Allow cross-origin performance monitoring
        '--disable-features=TranslateUI',  # Reduce noise
        '--disable-ipc-flooding-protection',  # Better performance measurement
        '--disable-background-timer-throttling',  # Accurate timing
        '--disable-renderer-backgrounding',  # Prevent background throttling
        '--disable-backgrounding-occluded-windows',
        '--disable-background-networking',
        '--disable-extensions',  # Reduce interference
        '--no-default-browser-check',
        '--no-first-run',
        '--disable-dev-shm-usage',
        '--no-sandbox'
    ],
    "firefox": [
        '--no-sandbox',
        '--disable-dev-shm-usage'
    ],
    "webkit": []
}

# Performance Monitoring Thresholds
PERFORMANCE_THRESHOLDS = {
    "good_lcp_ms": 2500,  # Good Largest Contentful Paint
    "good_fid_ms": 100,   # Good First Input Delay
    "good_cls_score": 0.1,  # Good Cumulative Layout Shift
    "good_fcp_ms": 1800,   # Good First Contentful Paint
    "good_tti_ms": 3800,   # Good Time to Interactive
    "long_task_threshold_ms": 50,  # Tasks longer than 50ms
    "acceptable_frame_rate": 30,   # Minimum acceptable FPS
    "memory_warning_mb": 512,      # Memory usage warning threshold
    "resource_count_warning": 100  # Too many resources warning
}

# Test Data Configuration
class TestData:
    """Test data and configuration values"""
    
    # Date range for network visualization tests
    DATE_FROM = "01/01/2025"
    DATE_TO = "30/06/2025"
    
    # Network visualization depth setting
    DEPTH_VALUE = "3"
    
    # Use case selection
    USE_CASE = "dpv:demo_fuib" # should think about make it less hardcoded
    USE_CASE_VALUE = "dpv:demo_fuib"  # Added for backward compatibility
    
    # Performance test parameters
    PERFORMANCE_TEST_ITERATIONS = 1
    WARMUP_ITERATIONS = 0
    
# Selectors
class Selectors:
    """CSS selectors for page elements"""

    # Alert List Page - Use Case Selection
    USE_CASE_CONTAINER = '.use-case-label-container'
    USE_CASE_DROPDOWN = '.use-case-label-container .p-dropdown'
    DROPDOWN_ITEM = '.p-dropdown-item'

    # Alert List Page
    ALERT_TITLE = '[data-cy="alert-title"]'

    # Alert Details Page
    RISK_CHART_WIDGET = 'tr-feature-item'  # Custom element for feature items
    NAV_BUTTON = '.nav-button'  # Nav button within feature item
    NAV_BACK = '.nav-back'

    # Network Visualization
    OPEN_NETWORK_VIZ = '[data-cy="open-network-visualization"]'
    DATE_RANGE_FIELD = '[data-fieldname="dateRange"]'
    DATE_FILTER_CONTAINER = '.date-filter'
    P_CALENDAR = 'p-calendar'
    DEPTH_FIELD = '[data-fieldname="depth"]'

    FILTER_DROPDOWN_OVERLAY = '.filter-dropdown-overlay'
    OPTION = '.p-dropdown-item'

# Performance Settings
WAIT_TIMEOUT = 30000  # 30 seconds
NETWORK_IDLE_TIMEOUT = 5000  # 5 seconds for network idle state

# Output Configuration
OUTPUT_DIR = "output"
REPORT_FILENAME_PREFIX = "performance_report"
