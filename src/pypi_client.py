"""
PyPI Client module for interacting with the Python Package Index API.
Handles package information retrieval, version checking, and API communication.
"""

import requests
import colorlog
import time
import json
from typing import Dict, List, Optional, Any
from urllib.parse import quote
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = colorlog.getLogger(__name__)

class PyPIClient:
    """
    Client for interacting with PyPI (Python Package Index) API.
    
    Provides methods for:
    - Fetching package information
    - Batch processing of package queries
    - Rate limiting and caching
    - Error handling and retries
    """
    
    BASE_URL = "https://pypi.org/pypi"
    
    def __init__(self, timeout: int = 30, batch_size: int = 10, 
                 max_retries: int = 3, rate_limit_delay: float = 0.1):
        """
        Initialize PyPI client.
        
        Args:
            timeout: Request timeout in seconds
            batch_size: Number of concurrent requests
            max_retries: Maximum number of retries for failed requests
            rate_limit_delay: Delay between requests in seconds
        """
        self.timeout = timeout
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        
        # Setup session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PyUpdater/1.0.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })
        
        # Cache for package information
        self._cache = {}
        self._cache_expiry = {}
        self._cache_lock = threading.Lock()
        self._cache_ttl = timedelta(hours=1)  # Cache for 1 hour
        
        # Rate limiting
        self._last_request_time = 0
        self._rate_limit_lock = threading.Lock()
        
    def get_package_info(self, package_name: str, version: str = None) -> Optional[Dict[str, Any]]:
        """
        Get package information from PyPI.
        
        Args:
            package_name: Name of the package
            version: Specific version (if None, gets latest)
            
        Returns:
            Optional[Dict]: Package information or None if not found
        """
        # Check cache first
        cache_key = f"{package_name}:{version or 'latest'}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
            
        # Apply rate limiting
        self._apply_rate_limit()
        
        try:
            # Construct URL
            safe_package_name = quote(package_name)
            if version:
                url = f"{self.BASE_URL}/{safe_package_name}/{quote(version)}/json"
            else:
                url = f"{self.BASE_URL}/{safe_package_name}/json"
                
            logger.debug(f"Fetching package info for {package_name} from {url}")
            
            # Make request with retries
            response = self._make_request_with_retry(url)
            
            if response and response.status_code == 200:
                data = response.json()
                package_info = self._extract_package_info(data)
                
                # Cache the result
                self._store_in_cache(cache_key, package_info)
                
                return package_info
            elif response and response.status_code == 404:
                logger.debug(f"Package {package_name} not found on PyPI")
                return None
            else:
                logger.warning(f"Error fetching {package_name}: HTTP {response.status_code if response else 'No response'}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting package info for {package_name}: {e}")
            return None
    
    def get_package_versions(self, package_name: str) -> List[str]:
        """
        Get all available versions for a package.
        
        Args:
            package_name: Name of the package
            
        Returns:
            List[str]: List of available versions
        """
        try:
            safe_package_name = quote(package_name)
            url = f"{self.BASE_URL}/{safe_package_name}/json"
            
            self._apply_rate_limit()
            response = self._make_request_with_retry(url)
            
            if response and response.status_code == 200:
                data = response.json()
                return list(data.get('releases', {}).keys())
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting versions for {package_name}: {e}")
            return []
    
    def batch_get_package_info(self, package_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get package information for multiple packages concurrently.
        
        Args:
            package_names: List of package names
            
        Returns:
            Dict[str, Optional[Dict]]: Package information mapped by name
        """
        results = {}
        
        # Split into batches
        batches = [package_names[i:i + self.batch_size] 
                  for i in range(0, len(package_names), self.batch_size)]
        
        for batch in batches:
            logger.debug(f"Processing batch of {len(batch)} packages")
            
            with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
                # Submit all requests in the batch
                future_to_package = {
                    executor.submit(self.get_package_info, package_name): package_name
                    for package_name in batch
                }
                
                # Collect results
                for future in as_completed(future_to_package):
                    package_name = future_to_package[future]
                    try:
                        result = future.result()
                        results[package_name] = result
                    except Exception as e:
                        logger.error(f"Error in batch request for {package_name}: {e}")
                        results[package_name] = None
                        
            # Rate limiting between batches
            if len(batches) > 1:
                time.sleep(self.rate_limit_delay * self.batch_size)
                
        return results
    
    def _extract_package_info(self, pypi_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant information from PyPI API response.
        
        Args:
            pypi_data: Raw PyPI API response
            
        Returns:
            Dict[str, Any]: Cleaned package information
        """
        info = pypi_data.get('info', {})
        
        # Get latest version info
        version = info.get('version', '')
        
        # Get upload time from releases
        upload_time = None
        releases = pypi_data.get('releases', {})
        if version in releases:
            release_files = releases[version]
            if release_files and isinstance(release_files, list):
                # Use the first file's upload time
                upload_time = release_files[0].get('upload_time', '')
        
        return {
            'name': info.get('name', ''),
            'version': version,
            'summary': info.get('summary', ''),
            'description': info.get('description', ''),
            'author': info.get('author', ''),
            'author_email': info.get('author_email', ''),
            'maintainer': info.get('maintainer', ''),
            'home_page': info.get('home_page', ''),
            'download_url': info.get('download_url', ''),
            'project_urls': info.get('project_urls', {}),
            'classifiers': info.get('classifiers', []),
            'keywords': info.get('keywords', ''),
            'license': info.get('license', ''),
            'platform': info.get('platform', ''),
            'requires_dist': info.get('requires_dist', []),
            'requires_python': info.get('requires_python', ''),
            'upload_time': upload_time,
            'yanked': info.get('yanked', False),
            'yanked_reason': info.get('yanked_reason', '')
        }
    
    def _make_request_with_retry(self, url: str) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: URL to request
            
        Returns:
            Optional[requests.Response]: Response object or None
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                
                return response
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                last_exception = "Request timeout"
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt + 1} for {url}")
                last_exception = "Connection error"
                
            except Exception as e:
                logger.warning(f"Request error on attempt {attempt + 1} for {url}: {e}")
                last_exception = str(e)
                
            # Wait before retry
            if attempt < self.max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                time.sleep(wait_time)
                
        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts. Last error: {last_exception}")
        return None
    
    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                time.sleep(sleep_time)
                
            self._last_request_time = time.time()
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get item from cache if not expired."""
        with self._cache_lock:
            if key in self._cache:
                expiry_time = self._cache_expiry.get(key)
                if expiry_time and datetime.now() < expiry_time:
                    logger.debug(f"Cache hit for {key}")
                    return self._cache[key]
                else:
                    # Remove expired entry
                    del self._cache[key]
                    if key in self._cache_expiry:
                        del self._cache_expiry[key]
                        
        return None
    
    def _store_in_cache(self, key: str, value: Dict[str, Any]):
        """Store item in cache with expiry time."""
        with self._cache_lock:
            self._cache[key] = value
            self._cache_expiry[key] = datetime.now() + self._cache_ttl
            logger.debug(f"Cached result for {key}")
    
    def clear_cache(self):
        """Clear the cache."""
        with self._cache_lock:
            self._cache.clear()
            self._cache_expiry.clear()
            logger.debug("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._cache_lock:
            return {
                'total_entries': len(self._cache),
                'expired_entries': sum(1 for expiry in self._cache_expiry.values() 
                                     if datetime.now() >= expiry)
            }
