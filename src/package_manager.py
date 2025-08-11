"""
Package Manager module for handling Python package operations.
Responsible for discovering installed packages and parsing requirements files.
"""

import pkg_resources
import subprocess
import sys
import re
import colorlog
from typing import List, Optional, NamedTuple, Dict
from pathlib import Path

logger = colorlog.getLogger(__name__)

class Package(NamedTuple):
    """Represents a Python package with name and version."""
    name: str
    version: str
    location: Optional[str] = None
    editable: bool = False

class PackageManager:
    """
    Manages Python package operations including:
    - Discovery of installed packages
    - Parsing requirements.txt files
    - Handling different installation methods (pip, conda, etc.)
    """
    
    def __init__(self):
        """Initialize the PackageManager."""
        self.installed_packages_cache = None
        
    def get_installed_packages(self) -> List[Package]:
        """
        Get list of all installed Python packages.
        
        Returns:
            List[Package]: List of installed packages with name, version, and metadata
        """
        if self.installed_packages_cache is not None:
            return self.installed_packages_cache
            
        packages = []
        
        try:
            # Use pkg_resources to get installed packages
            logger.info("Scanning installed packages using pkg_resources")
            
            for dist in pkg_resources.working_set:
                # Skip packages without proper version info
                if not dist.version or not dist.project_name:
                    continue
                    
                # Check if package is editable (development install)
                editable = self._is_editable_install(dist)
                
                package = Package(
                    name=dist.project_name,
                    version=dist.version,
                    location=str(dist.location) if dist.location else None,
                    editable=editable
                )
                packages.append(package)
                
            # Also try pip list as fallback/supplement
            pip_packages = self._get_pip_list_packages()
            
            # Merge results, preferring pkg_resources for version info
            packages = self._merge_package_lists(packages, pip_packages)
            
            logger.info(f"Found {len(packages)} installed packages")
            
        except Exception as e:
            logger.error(f"Error getting installed packages: {e}")
            # Fallback to pip list only
            packages = self._get_pip_list_packages()
            
        self.installed_packages_cache = packages
        return packages
    
    def _is_editable_install(self, dist) -> bool:
        """
        Check if a package is an editable install.
        
        Args:
            dist: pkg_resources distribution object
            
        Returns:
            bool: True if the package is editable
        """
        try:
            if hasattr(dist, 'egg_info') and dist.egg_info:
                egg_info_path = Path(dist.egg_info)
                # Check for .egg-link file which indicates editable install
                if egg_info_path.name.endswith('.egg-link'):
                    return True
                    
            # Check if location contains 'site-packages' - if not, likely editable
            if dist.location and 'site-packages' not in str(dist.location):
                return True
                
        except Exception:
            pass
            
        return False
    
    def _get_pip_list_packages(self) -> List[Package]:
        """
        Get packages using pip list command as fallback.
        
        Returns:
            List[Package]: List of packages from pip list
        """
        packages = []
        
        try:
            logger.debug("Getting packages from pip list")
            
            # Run pip list --format=json for structured output
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                import json
                pip_data = json.loads(result.stdout)
                
                for item in pip_data:
                    package = Package(
                        name=item['name'],
                        version=item['version'],
                        editable=False  # pip list doesn't easily show editable flag
                    )
                    packages.append(package)
                    
        except Exception as e:
            logger.debug(f"Could not get pip list packages: {e}")
            
        return packages
    
    def _merge_package_lists(self, pkg_resources_list: List[Package], 
                           pip_list: List[Package]) -> List[Package]:
        """
        Merge package lists from different sources, avoiding duplicates.
        
        Args:
            pkg_resources_list: Packages from pkg_resources
            pip_list: Packages from pip list
            
        Returns:
            List[Package]: Merged list with no duplicates
        """
        # Create a dict with package name as key for quick lookup
        merged = {}
        
        # Add pkg_resources packages first (more detailed info)
        for pkg in pkg_resources_list:
            merged[pkg.name.lower()] = pkg
            
        # Add pip packages if not already present
        for pkg in pip_list:
            name_key = pkg.name.lower()
            if name_key not in merged:
                merged[name_key] = pkg
                
        return list(merged.values())
    
    def read_requirements_file(self, requirements_path: str) -> List[Package]:
        """
        Parse a requirements.txt file and extract package information.
        
        Args:
            requirements_path: Path to requirements.txt file
            
        Returns:
            List[Package]: List of packages from requirements file
        """
        packages = []
        
        try:
            logger.info(f"Reading requirements file: {requirements_path}")
            
            with open(requirements_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                    
                # Skip lines with -r (recursive requirements)
                if line.startswith('-r ') or line.startswith('--requirement'):
                    continue
                    
                # Skip other pip options
                if line.startswith('-'):
                    continue
                    
                # Parse package specification
                package_info = self._parse_requirement_line(line, line_num)
                if package_info:
                    packages.append(package_info)
                    
            logger.info(f"Parsed {len(packages)} packages from requirements file")
            
        except FileNotFoundError:
            logger.error(f"Requirements file not found: {requirements_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading requirements file: {e}")
            raise
            
        return packages
    
    def _parse_requirement_line(self, line: str, line_num: int) -> Optional[Package]:
        """
        Parse a single line from requirements.txt.
        
        Args:
            line: Single line from requirements file
            line_num: Line number for error reporting
            
        Returns:
            Optional[Package]: Parsed package or None if invalid
        """
        try:
            # Handle different requirement formats:
            # - package==1.0.0
            # - package>=1.0.0
            # - package~=1.0.0
            # - git+https://github.com/user/repo.git
            # - -e git+https://github.com/user/repo.git
            # - /path/to/local/package
            
            # Remove editable flag
            is_editable = line.startswith('-e ')
            if is_editable:
                line = line[3:].strip()
                
            # Handle VCS URLs
            if any(vcs in line for vcs in ['git+', 'hg+', 'svn+', 'bzr+']):
                return self._parse_vcs_requirement(line, is_editable)
                
            # Handle local paths
            if line.startswith('/') or line.startswith('./') or line.startswith('../'):
                return self._parse_local_requirement(line, is_editable)
                
            # Handle standard package requirements
            return self._parse_standard_requirement(line, is_editable)
            
        except Exception as e:
            logger.warning(f"Could not parse requirement line {line_num}: '{line}' - {e}")
            return None
    
    def _parse_standard_requirement(self, line: str, is_editable: bool) -> Optional[Package]:
        """Parse standard package requirement (e.g., package==1.0.0)."""
        # Pattern to match package[extras]==version, package>=version, etc.
        pattern = r'^([a-zA-Z0-9\-_\.]+)(?:\[[^\]]+\])?(?:[><=!~]+.*)?$'
        match = re.match(pattern, line)
        
        if not match:
            return None
            
        package_name = match.group(1)
        
        # Try to extract version if specified
        version = 'unknown'
        version_match = re.search(r'[><=!~]+([0-9\.]+[a-zA-Z0-9]*)', line)
        if version_match:
            version = version_match.group(1)
            
        return Package(
            name=package_name,
            version=version,
            editable=is_editable
        )
    
    def _parse_vcs_requirement(self, line: str, is_editable: bool) -> Optional[Package]:
        """Parse VCS requirement (e.g., git+https://github.com/user/repo.git)."""
        # Extract package name from VCS URL
        # Pattern: git+https://github.com/user/repo.git#egg=package_name
        egg_match = re.search(r'#egg=([a-zA-Z0-9\-_\.]+)', line)
        if egg_match:
            package_name = egg_match.group(1)
        else:
            # Try to extract from URL
            url_match = re.search(r'/([a-zA-Z0-9\-_\.]+)\.git', line)
            if url_match:
                package_name = url_match.group(1)
            else:
                package_name = 'unknown_vcs_package'
                
        return Package(
            name=package_name,
            version='vcs',
            editable=is_editable
        )
    
    def _parse_local_requirement(self, line: str, is_editable: bool) -> Optional[Package]:
        """Parse local path requirement."""
        # Extract package name from local path
        path = Path(line)
        package_name = path.name
        
        return Package(
            name=package_name,
            version='local',
            editable=is_editable
        )
    
    def get_package_dependencies(self, package_name: str) -> List[str]:
        """
        Get dependencies for a specific package.
        
        Args:
            package_name: Name of the package
            
        Returns:
            List[str]: List of dependency names
        """
        dependencies = []
        
        try:
            dist = pkg_resources.get_distribution(package_name)
            if dist.requires():
                dependencies = [str(req).split()[0] for req in dist.requires()]
                
        except Exception as e:
            logger.debug(f"Could not get dependencies for {package_name}: {e}")
            
        return dependencies
    
    def clear_cache(self):
        """Clear the installed packages cache."""
        self.installed_packages_cache = None
