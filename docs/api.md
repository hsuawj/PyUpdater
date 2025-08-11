# API Reference

This document provides a comprehensive reference for all classes, methods, and functions in the Python Dependency Reader.

## Core Modules

### CLI Module (`src/cli.py`)

The main command-line interface for PDR.

#### Commands

##### `check`
Check for outdated packages and display results.

```bash
python main.py check [OPTIONS]
```

**Options:**
- `--requirements, -r PATH`: Path to requirements.txt file
- `--output, -o [table|json|csv]`: Output format (default: table)
- `--export, -e PATH`: Export results to file
- `--filter-type, -f [all|major|minor|patch]`: Filter updates by type
- `--include-prerelease`: Include pre-release versions
- `--batch-size INTEGER`: Batch size for PyPI API calls (default: 10)
- `--timeout INTEGER`: Timeout for PyPI API calls in seconds (default: 30)

**Examples:**
```bash
# Basic check
python main.py check

# Check with requirements file
python main.py check --requirements requirements.txt

# Export to JSON
python main.py check --output json --export results.json

# Only show major updates
python main.py check --filter-type major
```

##### `info`
Get detailed information about a specific package.

```bash
python main.py info PACKAGE_NAME [OPTIONS]
```

**Arguments:**
- `PACKAGE_NAME`: Name of the package to get information about

**Options:**
- `--version`: Specific version to check

**Example:**
```bash
python main.py info requests
python main.py info django --version 4.2.0
```

##### `config-show`
Display current configuration settings.

```bash
python main.py config-show
```

### Package Manager (`src/package_manager.py`)

#### Class: `PackageManager`

Manages Python package operations including discovery of installed packages and parsing requirements files.

**Methods:**

##### `get_installed_packages() -> List[Package]`
Get list of all installed Python packages.

**Returns:** List of Package objects with name, version, and metadata

##### `read_requirements_file(requirements_path: str) -> List[Package]`
Parse a requirements.txt file and extract package information.

**Arguments:**
- `requirements_path`: Path to requirements.txt file

**Returns:** List of Package objects from requirements file

##### `get_package_dependencies(package_name: str) -> List[str]`
Get dependencies for a specific package.

**Arguments:**
- `package_name`: Name of the package

**Returns:** List of dependency names

#### Class: `Package`
NamedTuple representing a Python package.

**Attributes:**
- `name: str`: Package name
- `version: str`: Package version
- `location: Optional[str]`: Installation location
- `editable: bool`: Whether package is editable install

### PyPI Client (`src/pypi_client.py`)

#### Class: `PyPIClient`

Client for interacting with PyPI (Python Package Index) API.

**Constructor:**
```python
PyPIClient(timeout=30, batch_size=10, max_retries=3, rate_limit_delay=0.1)
```

**Methods:**

##### `get_package_info(package_name: str, version: str = None) -> Optional[Dict[str, Any]]`
Get package information from PyPI.

**Arguments:**
- `package_name`: Name of the package
- `version`: Specific version (if None, gets latest)

**Returns:** Package information dictionary or None if not found

##### `get_package_versions(package_name: str) -> List[str]`
Get all available versions for a package.

**Arguments:**
- `package_name`: Name of the package

**Returns:** List of available version strings

##### `batch_get_package_info(package_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]`
Get package information for multiple packages concurrently.

**Arguments:**
- `package_names`: List of package names

**Returns:** Dictionary mapping package names to their information

### Version Comparator (`src/version_comparator.py`)

#### Class: `VersionComparator`

Handles version comparison and SemVer compatibility analysis.

**Constructor:**
```python
VersionComparator(include_prerelease=False)
```

**Methods:**

##### `compare_versions(installed_version: str, latest_version: str) -> Dict[str, Any]`
Compare two versions and determine update information.

**Arguments:**
- `installed_version`: Currently installed version
- `latest_version`: Latest available version

**Returns:** Dictionary containing comparison results:
```python
{
    'needs_update': bool,
    'update_type': str,  # 'major', 'minor', 'patch', 'other'
    'compatible': bool,
    'version_diff': Dict[str, int],
    'is_prerelease': bool,
    'breaking_change': bool
}
```

##### `check_version_constraint(version_string: str, constraint: str) -> bool`
Check if a version satisfies a constraint.

**Arguments:**
- `version_string`: Version to check
- `constraint`: Version constraint (e.g., '>=1.0.0,<2.0.0')

**Returns:** True if version satisfies constraint

##### `find_compatible_versions(available_versions: List[str], constraint: str) -> List[str]`
Find versions that satisfy a constraint from a list.

**Arguments:**
- `available_versions`: List of available version strings
- `constraint`: Version constraint

**Returns:** Compatible versions sorted by version

### Output Formatter (`src/output_formatter.py`)

#### Class: `OutputFormatter`

Handles formatting and display of package update results.

**Methods:**

##### `format_results(results: List[Dict[str, Any]], format_type: str = 'table') -> str`
Format results in the specified format.

**Arguments:**
- `results`: List of package update results
- `format_type`: Output format ('table', 'json', 'csv')

**Returns:** Formatted output string

##### `export_results(results: List[Dict[str, Any]], filepath: str, format_type: str)`
Export results to a file.

**Arguments:**
- `results`: Package update results
- `filepath`: Output file path
- `format_type`: Export format

##### `format_package_info(package_info: Dict[str, Any]) -> str`
Format detailed package information for display.

**Arguments:**
- `package_info`: Package information dictionary

**Returns:** Formatted package information string

### Configuration (`src/config.py`)

#### Class: `Config`

Configuration manager for the application.

**Constructor:**
```python
Config(config_path=None)
```

**Methods:**

##### `get(section: str, key: str, default: Any = None) -> Any`
Get a configuration value.

**Arguments:**
- `section`: Configuration section
- `key`: Configuration key
- `default`: Default value if not found

**Returns:** Configuration value or default

##### `get_section(section: str) -> Dict[str, Any]`
Get an entire configuration section.

**Arguments:**
- `section`: Section name

**Returns:** Section configuration dictionary

##### `save(filepath: Optional[str] = None)`
Save current configuration to file.

**Arguments:**
- `filepath`: Optional file path (uses config_path if not provided)

##### `create_sample_config(filepath: str)`
Create a sample configuration file.

**Arguments:**
- `filepath`: Path for the sample configuration

### Utilities (`src/utils.py`)

Collection of utility functions for common operations.

#### Functions

##### `setup_logging(verbose: bool = False, log_level: Optional[str] = None)`
Setup colorful logging for the application.

##### `validate_file_path(filepath: str, must_exist: bool = True) -> bool`
Validate a file path.

##### `safe_read_file(filepath: str, encoding: str = 'utf-8') -> Optional[str]`
Safely read a file with error handling.

##### `parse_version_string(version_str: str) -> Dict[str, Any]`
Parse a version string into components.

##### `retry_with_backoff(func, max_retries: int = 3, backoff_factor: float = 2.0)`
Retry a function with exponential backoff.

#### Class: `SimpleCache`

Simple in-memory cache with TTL support.

**Constructor:**
```python
SimpleCache(default_ttl=3600)
```

**Methods:**
- `get(key: str) -> Any`: Get item from cache
- `set(key: str, value: Any, ttl: Optional[int] = None)`: Set item in cache
- `clear()`: Clear all cache entries
- `size() -> int`: Get cache size

## Usage Examples

### Basic Package Checking
```python
from src.package_manager import PackageManager
from src.pypi_client import PyPIClient
from src.version_comparator import VersionComparator

# Initialize components
package_manager = PackageManager()
pypi_client = PyPIClient()
version_comparator = VersionComparator()

# Get installed packages
packages = package_manager.get_installed_packages()

# Check for updates
for package in packages[:5]:  # Check first 5 packages
    latest_info = pypi_client.get_package_info(package.name)
    if latest_info:
        comparison = version_comparator.compare_versions(
            package.version, 
            latest_info['version']
        )
        if comparison['needs_update']:
            print(f"{package.name}: {package.version} -> {latest_info['version']} ({comparison['update_type']})")
```

### Custom Output Formatting
```python
from src.output_formatter import OutputFormatter

formatter = OutputFormatter()
results = [
    {
        'package': 'requests',
        'installed': '2.28.0',
        'latest': '2.31.0',
        'update_type': 'minor',
        'compatible': True
    }
]

# Format as table
table_output = formatter.format_results(results, 'table')
print(table_output)

# Export as JSON
formatter.export_results(results, 'updates.json', 'json')
```

### Configuration Management
```python
from src.config import Config

# Load configuration
config = Config()

# Get PyPI settings
timeout = config.get('pypi', 'timeout', 30)
batch_size = config.get('pypi', 'batch_size', 10)

# Update and save configuration
config.set('pypi', 'timeout', 60)
config.save()
```

## Error Handling

All modules implement comprehensive error handling:

- **Network errors**: Automatic retries with exponential backoff
- **API errors**: Graceful handling of PyPI API failures
- **Version parsing errors**: Fallback to string comparison
- **File system errors**: Clear error messages with suggestions
- **Configuration errors**: Validation with default fallbacks

## Performance Considerations

- **Caching**: PyPI responses are cached for 1 hour by default
- **Batch processing**: Concurrent API calls with configurable limits
- **Rate limiting**: Respects PyPI API constraints
- **Memory efficiency**: Streaming processing for large package lists
- **Network optimization**: Connection pooling and compression
