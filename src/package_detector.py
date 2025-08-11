"""
Package detection and version extraction module.
"""

import pkg_resources
import subprocess
import sys
import re
import os
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import colorlog

from .config import Config
from .utils import normalize_package_name, parse_requirement_line

logger = colorlog.getLogger(__name__)

class PackageDetector:
    """Detects installed Python packages and their versions."""
    
    def __init__(self, config: Config):
        self.config = config
        self._installed_cache = None
        
    def from_installed_packages(self) -> List[Dict[str, Any]]:
        """
        Get list of all installed packages with their versions.
        
        Returns:
            List of package dictionaries with 'name', 'version', and metadata
        """
        if self._installed_cache is not None:
            return self._installed_cache
            
        packages = []
        
        try:
            # Use pkg_resources to get installed packages
            installed_packages = [d for d in pkg_resources.working_set]
            
            for package in installed_packages:
                # Skip system packages and development installs if configured
                if self._should_skip_package(package):
                    continue
                    
                package_info = {
                    'name': normalize_package_name(package.project_name),
                    'version': package.version,
                    'location': package.location,
                    'editable': self._is_editable_install(package),
                    'metadata': self._get_package_metadata(package)
                }
                
                packages.append(package_info)
                
        except Exception as e:
            logger.error(f"Error detecting installed packages: {e}")
            # Fallback to pip list
            packages = self._fallback_pip_list()
        
        # Sort packages by name
        packages.sort(key=lambda x: x['name'].lower())
        
        self._installed_cache = packages
        logger.info(f"Detected {len(packages)} installed packages")
        
        return packages
    
    def from_requirements_file(self, requirements_path: str) -> List[Dict[str, Any]]:
        """
        Parse packages from requirements.txt file.
        
        Args:
            requirements_path: Path to requirements.txt file
            
        Returns:
            List of package dictionaries
        """
        packages = []
        requirements_path = Path(requirements_path)
        
        if not requirements_path.exists():
            raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
        
        try:
            with open(requirements_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Handle line continuations
                if line.endswith('\\'):
                    line = line[:-1]
                    # TODO: Handle multi-line requirements
                
                try:
                    req_info = parse_requirement_line(line)
                    if req_info:
                        # Check if package is installed and get current version
                        installed_info = self._get_installed_version(req_info['name'])
                        
                        package_info = {
                            'name': req_info['name'],
                            'version': installed_info['version'] if installed_info else 'not-installed',
                            'requirement_spec': req_info['spec'],
                            'source': 'requirements.txt',
                            'line_number': line_num,
                            'editable': req_info.get('editable', False),
                            'vcs': req_info.get('vcs', None),
                            'url': req_info.get('url', None)
                        }
                        
                        packages.append(package_info)
                        
                except Exception as e:
                    logger.warning(f"Error parsing requirement line {line_num}: {line} - {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error reading requirements file: {e}")
            raise
        
        logger.info(f"Parsed {len(packages)} packages from {requirements_path}")
        return packages
    
    def from_package_names(self, package_names: List[str]) -> List[Dict[str, Any]]:
        """
        Get information for specific package names.
        
        Args:
            package_names: List of package names to check
            
        Returns:
            List of package dictionaries
        """
        packages = []
        
        for name in package_names:
            # Handle requirement specifications like "requests>=2.0.0"
            req_info = parse_requirement_line(name)
            if not req_info:
                logger.warning(f"Invalid package specification: {name}")
                continue
            
            package_name = req_info['name']
            installed_info = self._get_installed_version(package_name)
            
            if installed_info:
                package_info = {
                    'name': package_name,
                    'version': installed_info['version'],
                    'requirement_spec': req_info.get('spec', ''),
                    'source': 'command-line',
                    'location': installed_info.get('location', ''),
                    'editable': installed_info.get('editable', False)
                }
                packages.append(package_info)
            else:
                # Package not installed, but we can still check PyPI
                package_info = {
                    'name': package_name,
                    'version': 'not-installed',
                    'requirement_spec': req_info.get('spec', ''),
                    'source': 'command-line'
                }
                packages.append(package_info)
        
        return packages
    
    def _should_skip_package(self, package: pkg_resources.Distribution) -> bool:
        """Check if package should be skipped from analysis."""
        package_name = package.project_name.lower()
        
        # Skip common system packages
        system_packages = {
            'pip', 'setuptools', 'wheel', 'distribute', 'pkg-resources'
        }
        
        if package_name in system_packages and not self.config.include_system_packages:
            return True
        
        # Skip packages installed in system directories (if configured)
        if not self.config.include_system_packages and package.location:
            system_paths = [sys.prefix, sys.exec_prefix]
            for sys_path in system_paths:
                if package.location.startswith(sys_path):
                    return True
        
        return False
    
    def _is_editable_install(self, package: pkg_resources.Distribution) -> bool:
        """Check if package is an editable install."""
        if hasattr(package, '_link') and package._link:
            return package._link.editable
        
        # Check for .egg-link files (older pip versions)
        if package.location and package.location.endswith('.egg-link'):
            return True
            
        return False
    
    def _get_package_metadata(self, package: pkg_resources.Distribution) -> Dict[str, Any]:
        """Extract metadata from package."""
        metadata = {}
        
        try:
            if hasattr(package, 'get_metadata'):
                # Try to get summary/description
                pkg_info = package.get_metadata('PKG-INFO') or package.get_metadata('METADATA')
                if pkg_info:
                    for line in pkg_info.split('\n'):
                        if line.startswith('Summary:'):
                            metadata['summary'] = line.split(':', 1)[1].strip()
                        elif line.startswith('Home-page:'):
                            metadata['homepage'] = line.split(':', 1)[1].strip()
                        elif line.startswith('Author:'):
                            metadata['author'] = line.split(':', 1)[1].strip()
        except Exception:
            pass  # Metadata not available
        
        return metadata
    
    def _get_installed_version(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get version info for a specific installed package."""
        normalized_name = normalize_package_name(package_name)
        
        try:
            package = pkg_resources.get_distribution(normalized_name)
            return {
                'name': package.project_name,
                'version': package.version,
                'location': package.location,
                'editable': self._is_editable_install(package)
            }
        except pkg_resources.DistributionNotFound:
            return None
    
    def _fallback_pip_list(self) -> List[Dict[str, Any]]:
        """Fallback method using pip list command."""
        packages = []
        
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'list', '--format=json'
            ], capture_output=True, text=True, check=True)
            
            import json
            pip_packages = json.loads(result.stdout)
            
            for pkg in pip_packages:
                if self._should_skip_pip_package(pkg['name']):
                    continue
                    
                package_info = {
                    'name': normalize_package_name(pkg['name']),
                    'version': pkg['version'],
                    'location': '',
                    'editable': False,
                    'metadata': {}
                }
                packages.append(package_info)
                
        except Exception as e:
            logger.error(f"Fallback pip list failed: {e}")
        
        return packages
    
    def _should_skip_pip_package(self, package_name: str) -> bool:
        """Check if pip package should be skipped."""
        return package_name.lower() in {'pip', 'setuptools', 'wheel'} and \
               not self.config.include_system_packages

    def get_package_files(self, package_name: str) -> List[str]:
        """Get list of files for a package (for advanced analysis)."""
        try:
            package = pkg_resources.get_distribution(normalize_package_name(package_name))
            if hasattr(package, 'get_metadata_lines'):
                record = package.get_metadata_lines('RECORD')
                return [line.split(',')[0] for line in record if line.strip()]
        except Exception:
            pass
        return []
    
    def get_package_dependencies(self, package_name: str) -> List[str]:
        """Get dependencies for a specific package."""
        try:
            package = pkg_resources.get_distribution(normalize_package_name(package_name))
            return [str(req) for req in package.requires()]
        except Exception:
            return []
