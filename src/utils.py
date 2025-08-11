"""
Utility functions for Python Dependency Reader.
Contains helper functions for logging, file operations, and common tasks.
"""

import os
import sys
import colorlog
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import hashlib
import json
from datetime import datetime, timedelta

def setup_logging(verbose: bool = False, log_level: Optional[str] = None):
    """
    Setup colorful logging for the application.
    
    Args:
        verbose: Enable verbose logging
        log_level: Specific log level to use
    """
    # Determine log level
    if log_level:
        level = getattr(logging, log_level.upper(), logging.INFO)
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    # Setup colorlog
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s%(reset)s | %(name)s | %(message)s',
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    ))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for existing_handler in root_logger.handlers[:]:
        root_logger.removeHandler(existing_handler)
    
    root_logger.addHandler(handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    if verbose:
        logger = colorlog.getLogger(__name__)
        logger.debug("Verbose logging enabled")

def validate_file_path(filepath: str, must_exist: bool = True) -> bool:
    """
    Validate a file path.
    
    Args:
        filepath: Path to validate
        must_exist: Whether the file must exist
        
    Returns:
        bool: True if valid
    """
    try:
        path = Path(filepath)
        
        if must_exist:
            return path.exists() and path.is_file()
        else:
            # Check if parent directory exists or can be created
            parent = path.parent
            return parent.exists() or parent.is_dir()
            
    except Exception:
        return False

def ensure_directory(dirpath: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dirpath: Directory path
        
    Returns:
        bool: True if directory exists or was created
    """
    try:
        Path(dirpath).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger = colorlog.getLogger(__name__)
        logger.error(f"Could not create directory {dirpath}: {e}")
        return False

def safe_read_file(filepath: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read a file with error handling.
    
    Args:
        filepath: File path to read
        encoding: File encoding
        
    Returns:
        Optional[str]: File contents or None if error
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger = colorlog.getLogger(__name__)
        logger.error(f"Error reading file {filepath}: {e}")
        return None

def safe_write_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Safely write content to a file.
    
    Args:
        filepath: File path to write
        content: Content to write
        encoding: File encoding
        
    Returns:
        bool: True if successful
    """
    try:
        # Ensure parent directory exists
        ensure_directory(os.path.dirname(filepath))
        
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger = colorlog.getLogger(__name__)
        logger.error(f"Error writing file {filepath}: {e}")
        return False

def calculate_file_hash(filepath: str, algorithm: str = 'sha256') -> Optional[str]:
    """
    Calculate hash of a file.
    
    Args:
        filepath: Path to file
        algorithm: Hash algorithm to use
        
    Returns:
        Optional[str]: File hash or None if error
    """
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
                
        return hash_obj.hexdigest()
    except Exception as e:
        logger = colorlog.getLogger(__name__)
        logger.error(f"Error calculating hash for {filepath}: {e}")
        return None

def parse_version_string(version_str: str) -> Dict[str, Any]:
    """
    Parse a version string into components.
    
    Args:
        version_str: Version string to parse
        
    Returns:
        Dict: Parsed version components
    """
    import re
    
    # Basic pattern for semantic versioning
    pattern = r'^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<micro>\d+)(?P<pre>[-.]?(?P<pre_type>a|b|rc|alpha|beta)\.?(?P<pre_num>\d+))?(?P<post>[-.]?post\.?(?P<post_num>\d+))?(?P<dev>[-.]?dev\.?(?P<dev_num>\d+))?$'
    
    match = re.match(pattern, version_str.lower())
    
    if match:
        return {
            'major': int(match.group('major')),
            'minor': int(match.group('minor')),
            'micro': int(match.group('micro')),
            'is_prerelease': bool(match.group('pre')),
            'prerelease_type': match.group('pre_type'),
            'prerelease_number': int(match.group('pre_num')) if match.group('pre_num') else None,
            'is_postrelease': bool(match.group('post')),
            'postrelease_number': int(match.group('post_num')) if match.group('post_num') else None,
            'is_dev': bool(match.group('dev')),
            'dev_number': int(match.group('dev_num')) if match.group('dev_num') else None,
            'original': version_str
        }
    else:
        # Fallback for non-standard versions
        return {
            'major': 0,
            'minor': 0,
            'micro': 0,
            'is_prerelease': 'dev' in version_str.lower() or 'alpha' in version_str.lower() or 'beta' in version_str.lower(),
            'prerelease_type': None,
            'prerelease_number': None,
            'is_postrelease': False,
            'postrelease_number': None,
            'is_dev': 'dev' in version_str.lower(),
            'dev_number': None,
            'original': version_str,
            'parse_error': True
        }

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size_float = float(size_bytes)
    
    while size_float >= 1024.0 and i < len(size_names) - 1:
        size_float /= 1024.0
        i += 1
    
    return f"{size_float:.1f} {size_names[i]}"

def format_duration(seconds: float) -> str:
    """
    Format duration in human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_terminal_width() -> int:
    """
    Get terminal width, with fallback.
    
    Returns:
        int: Terminal width in characters
    """
    try:
        import shutil
        return shutil.get_terminal_size().columns
    except Exception:
        return 80  # Fallback width

def is_virtual_environment() -> bool:
    """
    Check if running in a virtual environment.
    
    Returns:
        bool: True if in virtual environment
    """
    return (hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

def get_python_info() -> Dict[str, Any]:
    """
    Get Python environment information.
    
    Returns:
        Dict: Python environment details
    """
    return {
        'version': sys.version,
        'executable': sys.executable,
        'platform': sys.platform,
        'prefix': sys.prefix,
        'virtual_env': is_virtual_environment(),
        'path': sys.path[0] if sys.path else ''
    }

def create_cache_key(*args: Any) -> str:
    """
    Create a cache key from arguments.
    
    Args:
        *args: Arguments to include in key
        
    Returns:
        str: Cache key
    """
    # Convert arguments to strings and join
    key_parts = [str(arg) for arg in args]
    key_string = '|'.join(key_parts)
    
    # Create hash for consistent length
    return hashlib.sha256(key_string.encode()).hexdigest()[:16]

def parse_requirements_line(line: str) -> Optional[Dict[str, str]]:
    """
    Parse a single requirements.txt line.
    
    Args:
        line: Requirements line to parse
        
    Returns:
        Optional[Dict]: Parsed requirement or None
    """
    import re
    
    line = line.strip()
    
    # Skip empty lines and comments
    if not line or line.startswith('#'):
        return None
    
    # Skip pip options
    if line.startswith('-'):
        return None
    
    # Basic package name and version pattern
    pattern = r'^([a-zA-Z0-9\-_.]+)(?:\[[^\]]+\])?([><=!~]+.*)?$'
    match = re.match(pattern, line)
    
    if match:
        name = match.group(1)
        version_spec = match.group(2) or ''
        
        return {
            'name': name,
            'version_spec': version_spec,
            'original_line': line
        }
    
    return None

def retry_with_backoff(func, max_retries: int = 3, backoff_factor: float = 2.0):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        backoff_factor: Backoff multiplier
        
    Returns:
        Function result or raises last exception
    """
    import time
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries:
                wait_time = (backoff_factor ** attempt)
                time.sleep(wait_time)
            else:
                break
    
    if last_exception:
        raise last_exception

class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.cache = {}
        self.expiry = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Any:
        """Get item from cache."""
        if key in self.cache:
            if datetime.now() < self.expiry.get(key, datetime.min):
                return self.cache[key]
            else:
                # Remove expired item
                self.cache.pop(key, None)
                self.expiry.pop(key, None)
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set item in cache."""
        ttl = ttl or self.default_ttl
        self.cache[key] = value
        self.expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.expiry.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)

# Global logger for this module
logger = colorlog.getLogger(__name__)
