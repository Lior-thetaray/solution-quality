"""
Runtime configuration setup for Playwright tests.
Sets up credentials and URLs at runtime for security.
"""

import os
import getpass
from typing import Dict, Any

# Global runtime configuration cache
_runtime_config = {}

def setup_runtime_config() -> Dict[str, Any]:
    """Setup runtime configuration with user input."""
    global _runtime_config
    
    # Check if already configured for this session
    if (_runtime_config.get('USERNAME') and 
        _runtime_config.get('PASSWORD') and 
        _runtime_config.get('BASE_URL')):
        return _runtime_config
    
    # Try environment variables first
    username = os.getenv('THETARAY_USERNAME')
    password = os.getenv('THETARAY_PASSWORD')
    base_url = os.getenv('THETARAY_BASE_URL')
    
    # Prompt for missing values
    if not username or not password or not base_url:
        print("\n🔐 ThetaRay Performance Testing - Runtime Configuration")
        print("Please provide the required configuration:")
        
        if not base_url:
            base_url = input("Base URL (e.g., https://apps-thetalab.sonar.thetaray.cloud): ").strip()
        
        if not username:
            username = input("Username: ").strip()
        
        if not password:
            password = getpass.getpass("Password: ")
    else:
        print("✅ Using configuration from environment variables")
    
    # Validate inputs
    if not username or not password or not base_url:
        raise ValueError("Username, password, and base URL are all required")
    
    if not base_url.startswith(('http://', 'https://')):
        raise ValueError("Base URL must start with http:// or https://")
    
    # Cache configuration
    _runtime_config = {
        'USERNAME': username,
        'PASSWORD': password,
        'BASE_URL': base_url,
        'ALERT_LIST_URL': f"{base_url}/#/investigation-center/alert-list?viewId=4"
    }
    
    return _runtime_config

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value, setting up runtime config if needed."""
    if not _runtime_config:
        setup_runtime_config()
    return _runtime_config.get(key, default)

def clear_runtime_config():
    """Clear runtime configuration for security."""
    global _runtime_config
    _runtime_config = {}

def apply_runtime_config():
    """Apply runtime configuration to the config module."""
    import config.config as config
    
    runtime_config = setup_runtime_config()
    
    # Update the config module with runtime values
    config.USERNAME = runtime_config['USERNAME']
    config.PASSWORD = runtime_config['PASSWORD']  
    config.BASE_URL = runtime_config['BASE_URL']
    config.ALERT_LIST_URL = runtime_config['ALERT_LIST_URL']
    
    print(f"✅ Configuration applied - Base URL: {config.BASE_URL}")
    print(f"✅ Configuration applied - Username: {config.USERNAME}")