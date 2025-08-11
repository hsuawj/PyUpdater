"""
Version Comparator module for handling semantic version comparison.
Implements SemVer compatibility checking and version analysis.
"""

import re
import colorlog
from typing import Dict, List, Optional, Tuple, Any
from packaging import version
from packaging.specifiers import SpecifierSet
from packaging.requirements import Requirement

logger = colorlog.getLogger(__name__)

class VersionComparator:
    """
    Handles version comparison and SemVer compatibility analysis.
    
    Provides functionality for:
    - Comparing package versions using SemVer rules
    - Determining update types (major, minor, patch)
    - Handling pre-release and development versions
    - Compatibility checking with version constraints
    """
    
    def __init__(self, include_prerelease: bool = False):
        """
        Initialize the version comparator.
        
        Args:
            include_prerelease: Whether to consider pre-release versions
        """
        self.include_prerelease = include_prerelease
        
        # Pre-release identifiers
        self.prerelease_patterns = [
            r'.*[ab]\d+$',      # alpha/beta: 1.0.0a1, 1.0.0b2
            r'.*rc\d+$',        # release candidate: 1.0.0rc1
            r'.*dev\d*$',       # development: 1.0.0dev, 1.0.0dev1
            r'.*pre\d*$',       # pre-release: 1.0.0pre
            r'.*post\d+$',      # post-release: 1.0.0post1
        ]
    
    def compare_versions(self, installed_version: str, 
                        latest_version: str) -> Dict[str, Any]:
        """
        Compare two versions and determine update information.
        
        Args:
            installed_version: Currently installed version
            latest_version: Latest available version
            
        Returns:
            Dict containing comparison results
        """
        try:
            # Parse versions using packaging.version
            current_ver = version.parse(installed_version)
            latest_ver = version.parse(latest_version)
            
            # Check if update is needed
            needs_update = latest_ver > current_ver
            
            if not needs_update:
                return {
                    'needs_update': False,
                    'update_type': None,
                    'compatible': True,
                    'version_diff': None,
                    'is_prerelease': self._is_prerelease(latest_version),
                    'is_yanked': False,
                    'breaking_change': False
                }
            
            # Determine update type and compatibility
            update_type = self._determine_update_type(current_ver, latest_ver)
            compatible = self._is_semver_compatible(current_ver, latest_ver, update_type)
            breaking_change = update_type == 'major'
            
            # Calculate version difference
            version_diff = self._calculate_version_diff(current_ver, latest_ver)
            
            # Check if latest version is pre-release
            is_prerelease = self._is_prerelease(latest_version)
            
            return {
                'needs_update': True,
                'update_type': update_type,
                'compatible': compatible,
                'version_diff': version_diff,
                'is_prerelease': is_prerelease,
                'is_yanked': False,  # This would need to be checked via PyPI API
                'breaking_change': breaking_change,
                'semver_jump': self._calculate_semver_jump(current_ver, latest_ver)
            }
            
        except Exception as e:
            logger.error(f"Error comparing versions {installed_version} -> {latest_version}: {e}")
            return {
                'needs_update': False,
                'update_type': 'unknown',
                'compatible': False,
                'version_diff': None,
                'is_prerelease': False,
                'is_yanked': False,
                'breaking_change': False,
                'error': str(e)
            }
    
    def _determine_update_type(self, current_ver: version.Version, 
                              latest_ver: version.Version) -> str:
        """
        Determine the type of update (major, minor, patch).
        
        Args:
            current_ver: Current version object
            latest_ver: Latest version object
            
        Returns:
            str: Update type ('major', 'minor', 'patch', or 'other')
        """
        try:
            # Get version components
            current_parts = self._extract_version_parts(current_ver)
            latest_parts = self._extract_version_parts(latest_ver)
            
            # Compare major version
            if latest_parts['major'] > current_parts['major']:
                return 'major'
            
            # Compare minor version
            if latest_parts['minor'] > current_parts['minor']:
                return 'minor'
            
            # Compare patch version
            if latest_parts['micro'] > current_parts['micro']:
                return 'patch'
            
            # If we get here, it might be a pre-release or other change
            return 'other'
            
        except Exception as e:
            logger.debug(f"Could not determine update type: {e}")
            return 'unknown'
    
    def _extract_version_parts(self, ver: version.Version) -> Dict[str, int]:
        """
        Extract major, minor, and micro version parts.
        
        Args:
            ver: Version object
            
        Returns:
            Dict with major, minor, micro parts
        """
        # Get the release tuple (major, minor, micro, ...)
        release = ver.release
        
        return {
            'major': release[0] if len(release) > 0 else 0,
            'minor': release[1] if len(release) > 1 else 0,
            'micro': release[2] if len(release) > 2 else 0
        }
    
    def _is_semver_compatible(self, current_ver: version.Version, 
                             latest_ver: version.Version, update_type: str) -> bool:
        """
        Check if the update is SemVer compatible.
        
        Args:
            current_ver: Current version
            latest_ver: Latest version
            update_type: Type of update
            
        Returns:
            bool: True if compatible according to SemVer rules
        """
        try:
            current_parts = self._extract_version_parts(current_ver)
            latest_parts = self._extract_version_parts(latest_ver)
            
            # Major version changes are breaking (not compatible)
            if update_type == 'major':
                return False
            
            # Minor and patch updates should be compatible
            if update_type in ['minor', 'patch']:
                return True
            
            # For other types, check if major version is the same
            return current_parts['major'] == latest_parts['major']
            
        except Exception:
            return False
    
    def _is_prerelease(self, version_string: str) -> bool:
        """
        Check if a version string represents a pre-release.
        
        Args:
            version_string: Version string to check
            
        Returns:
            bool: True if version is a pre-release
        """
        if not self.include_prerelease:
            return False
            
        # Use packaging.version to check
        try:
            ver = version.parse(version_string)
            return ver.is_prerelease
        except Exception:
            # Fallback to regex patterns
            for pattern in self.prerelease_patterns:
                if re.match(pattern, version_string.lower()):
                    return True
            return False
    
    def _calculate_version_diff(self, current_ver: version.Version, 
                               latest_ver: version.Version) -> Dict[str, int]:
        """
        Calculate the difference between versions.
        
        Args:
            current_ver: Current version
            latest_ver: Latest version
            
        Returns:
            Dict with version differences
        """
        try:
            current_parts = self._extract_version_parts(current_ver)
            latest_parts = self._extract_version_parts(latest_ver)
            
            return {
                'major': latest_parts['major'] - current_parts['major'],
                'minor': latest_parts['minor'] - current_parts['minor'],
                'micro': latest_parts['micro'] - current_parts['micro']
            }
        except Exception:
            return {'major': 0, 'minor': 0, 'micro': 0}
    
    def _calculate_semver_jump(self, current_ver: version.Version, 
                              latest_ver: version.Version) -> str:
        """
        Calculate the semantic versioning jump description.
        
        Args:
            current_ver: Current version
            latest_ver: Latest version
            
        Returns:
            str: Description of the version jump
        """
        try:
            diff = self._calculate_version_diff(current_ver, latest_ver)
            
            if diff['major'] > 0:
                return f"+{diff['major']} major"
            elif diff['minor'] > 0:
                return f"+{diff['minor']} minor"
            elif diff['micro'] > 0:
                return f"+{diff['micro']} patch"
            else:
                return "other"
                
        except Exception:
            return "unknown"
    
    def check_version_constraint(self, version_string: str, 
                               constraint: str) -> bool:
        """
        Check if a version satisfies a constraint.
        
        Args:
            version_string: Version to check
            constraint: Version constraint (e.g., '>=1.0.0,<2.0.0')
            
        Returns:
            bool: True if version satisfies constraint
        """
        try:
            ver = version.parse(version_string)
            spec = SpecifierSet(constraint)
            return ver in spec
        except Exception as e:
            logger.debug(f"Error checking version constraint: {e}")
            return False
    
    def parse_requirement_specifier(self, requirement_string: str) -> Optional[Dict[str, Any]]:
        """
        Parse a requirement string and extract version constraints.
        
        Args:
            requirement_string: Requirement string (e.g., 'requests>=2.0.0')
            
        Returns:
            Optional[Dict]: Parsed requirement information
        """
        try:
            req = Requirement(requirement_string)
            
            return {
                'name': req.name,
                'specifier': str(req.specifier) if req.specifier else '',
                'extras': list(req.extras) if req.extras else [],
                'marker': str(req.marker) if req.marker else '',
                'url': req.url
            }
        except Exception as e:
            logger.debug(f"Error parsing requirement '{requirement_string}': {e}")
            return None
    
    def find_compatible_versions(self, available_versions: List[str], 
                                constraint: str) -> List[str]:
        """
        Find versions that satisfy a constraint from a list.
        
        Args:
            available_versions: List of available version strings
            constraint: Version constraint
            
        Returns:
            List[str]: Compatible versions sorted by version
        """
        compatible = []
        
        try:
            spec = SpecifierSet(constraint)
            
            for ver_string in available_versions:
                try:
                    ver = version.parse(ver_string)
                    
                    # Skip pre-releases unless explicitly included
                    if ver.is_prerelease and not self.include_prerelease:
                        continue
                        
                    if ver in spec:
                        compatible.append(ver_string)
                except Exception:
                    continue
                    
            # Sort by version
            compatible.sort(key=lambda x: version.parse(x), reverse=True)
            
        except Exception as e:
            logger.debug(f"Error finding compatible versions: {e}")
            
        return compatible
    
    def get_latest_stable_version(self, versions: List[str]) -> Optional[str]:
        """
        Get the latest stable (non-prerelease) version from a list.
        
        Args:
            versions: List of version strings
            
        Returns:
            Optional[str]: Latest stable version or None
        """
        stable_versions = []
        
        for ver_string in versions:
            try:
                ver = version.parse(ver_string)
                if not ver.is_prerelease:
                    stable_versions.append(ver_string)
            except Exception:
                continue
                
        if not stable_versions:
            return None
            
        # Sort and return the latest
        stable_versions.sort(key=lambda x: version.parse(x), reverse=True)
        return stable_versions[0]
