"""
Configuration module for Python Dependency Reader.
Handles configuration file loading, environment variables, and settings management.
"""

import os
import toml
import colorlog
from typing import Dict, Any, Optional
from pathlib import Path

logger = colorlog.getLogger(__name__)

class Config:
    """
    Configuration manager for the application.
    
    Handles:
    - Loading configuration from TOML files
    - Environment variable overrides
    - Default settings
    - Configuration validation
    """
    
    DEFAULT_CONFIG = {
        'pypi': {
            'base_url': 'https://pypi.org/pypi',
            'timeout': 30,
            'max_retries': 3,
            'batch_size': 10,
            'rate_limit_delay': 0.1,
            'cache_ttl_hours': 1
        },
        'output': {
            'default_format': 'table',
            'colors_enabled': True,
            'max_description_length': 100,
            'show_upload_time': True,
            'show_progress': True
        },
        'version_checking': {
            'include_prerelease': False,
            'strict_semver': True,
            'ignore_yanked': True,
            'skip_dev_versions': True
        },
        'filtering': {
            'default_filter': 'all',
            'exclude_packages': [],
            'include_only': [],
            'min_days_old': 0
        },
        'logging': {
            'level': 'INFO',
            'format': '%(log_color)s%(levelname)s%(reset)s | %(name)s | %(message)s',
            'colors': {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white'
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load configuration from file if provided
        if config_path:
            self._load_config_file(config_path)
        else:
            # Try to find default config file
            self._load_default_config()
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate_config()
        
        logger.debug("Configuration loaded successfully")
    
    def _load_config_file(self, config_path: str):
        """
        Load configuration from a TOML file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            if not os.path.exists(config_path):
                logger.warning(f"Configuration file not found: {config_path}")
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = toml.load(f)
            
            # Deep merge with default config
            self.config = self._deep_merge(self.config, file_config)
            logger.info(f"Loaded configuration from {config_path}")
            
        except Exception as e:
            logger.error(f"Error loading configuration file {config_path}: {e}")
            logger.info("Using default configuration")
    
    def _load_default_config(self):
        """Try to load configuration from default locations."""
        default_locations = [
            '.pdr.toml',
            '~/.pdr.toml',
            '~/.config/pdr/config.toml'
        ]
        
        for location in default_locations:
            expanded_path = os.path.expanduser(location)
            if os.path.exists(expanded_path):
                logger.debug(f"Found default config at {expanded_path}")
                self._load_config_file(expanded_path)
                break
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            'PDR_PYPI_TIMEOUT': ('pypi', 'timeout', int),
            'PDR_PYPI_BATCH_SIZE': ('pypi', 'batch_size', int),
            'PDR_PYPI_MAX_RETRIES': ('pypi', 'max_retries', int),
            'PDR_OUTPUT_FORMAT': ('output', 'default_format', str),
            'PDR_INCLUDE_PRERELEASE': ('version_checking', 'include_prerelease', self._str_to_bool),
            'PDR_LOG_LEVEL': ('logging', 'level', str),
            'PDR_COLORS_ENABLED': ('output', 'colors_enabled', self._str_to_bool),
        }
        
        for env_var, (section, key, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    converted_value = converter(value)
                    if section not in self.config:
                        self.config[section] = {}
                    self.config[section][key] = converted_value
                    logger.debug(f"Applied env override: {env_var}={converted_value}")
                except Exception as e:
                    logger.warning(f"Invalid value for {env_var}: {value} - {e}")
    
    def _str_to_bool(self, value: str) -> bool:
        """Convert string to boolean."""
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            Dict: Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _validate_config(self):
        """Validate configuration values."""
        try:
            # Validate PyPI settings
            pypi_config = self.config.get('pypi', {})
            
            if pypi_config.get('timeout', 0) <= 0:
                logger.warning("Invalid PyPI timeout, using default")
                self.config['pypi']['timeout'] = self.DEFAULT_CONFIG['pypi']['timeout']
            
            if pypi_config.get('batch_size', 0) <= 0:
                logger.warning("Invalid batch size, using default")
                self.config['pypi']['batch_size'] = self.DEFAULT_CONFIG['pypi']['batch_size']
            
            # Validate output format
            output_config = self.config.get('output', {})
            valid_formats = ['table', 'json', 'csv']
            
            if output_config.get('default_format') not in valid_formats:
                logger.warning(f"Invalid output format, using 'table'")
                self.config['output']['default_format'] = 'table'
            
            # Validate logging level
            logging_config = self.config.get('logging', {})
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            
            if logging_config.get('level') not in valid_levels:
                logger.warning("Invalid log level, using 'INFO'")
                self.config['logging']['level'] = 'INFO'
                
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(section, {}).get(key, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Dict: Section configuration
        """
        return self.config.get(section, {})
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire configuration.
        
        Returns:
            Dict: Complete configuration
        """
        return self.config.copy()
    
    def set(self, section: str, key: str, value: Any):
        """
        Set a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def save(self, filepath: Optional[str] = None):
        """
        Save current configuration to file.
        
        Args:
            filepath: Optional file path (uses config_path if not provided)
        """
        save_path = filepath or self.config_path
        
        if not save_path:
            save_path = '.pdr.toml'
        
        try:
            # Ensure directory exists
            save_dir = os.path.dirname(save_path)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                toml.dump(self.config, f)
            
            logger.info(f"Configuration saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration to {save_path}: {e}")
            raise
    
    def create_sample_config(self, filepath: str):
        """
        Create a sample configuration file.
        
        Args:
            filepath: Path for the sample configuration
        """
        try:
            sample_config = self.DEFAULT_CONFIG.copy()
            
            # Add comments and documentation
            sample_content = """# Python Dependency Reader Configuration
# This file contains configuration options for PDR

[pypi]
# PyPI API settings
base_url = "https://pypi.org/pypi"
timeout = 30                    # Request timeout in seconds
max_retries = 3                 # Maximum number of retries
batch_size = 10                 # Number of concurrent requests
rate_limit_delay = 0.1          # Delay between requests
cache_ttl_hours = 1             # Cache time-to-live

[output]
# Output formatting options
default_format = "table"        # table, json, or csv
colors_enabled = true           # Enable colored output
max_description_length = 100    # Maximum description length
show_upload_time = true         # Show package upload time
show_progress = true            # Show progress indicators

[version_checking]
# Version comparison settings
include_prerelease = false      # Include pre-release versions
strict_semver = true            # Strict semantic versioning
ignore_yanked = true            # Ignore yanked packages
skip_dev_versions = true        # Skip development versions

[filtering]
# Package filtering options
default_filter = "all"          # all, major, minor, patch
exclude_packages = []           # Packages to exclude
include_only = []               # Only check these packages
min_days_old = 0                # Minimum days since last update

[logging]
# Logging configuration
level = "INFO"                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
format = "%(log_color)s%(levelname)s%(reset)s | %(name)s | %(message)s"

[logging.colors]
DEBUG = "cyan"
INFO = "green"
WARNING = "yellow"
ERROR = "red"
CRITICAL = "red,bg_white"
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            
            logger.info(f"Sample configuration created at {filepath}")
            
        except Exception as e:
            logger.error(f"Error creating sample configuration: {e}")
            raise
