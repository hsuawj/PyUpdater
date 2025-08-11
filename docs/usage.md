# Usage Guide

Comprehensive guide for using Python Dependency Reader effectively.

## Quick Start

### Basic Package Checking
```bash
# Check all installed packages for updates
python main.py check

# Enable detailed logging
python main.py --verbose check

# Show help for any command
python main.py --help
python main.py check --help
```

### First Run Example
```bash
$ python main.py check
Checking packages  [####################################]  100%          
Outdated Packages:
---------------------------------------------------------------
Package            | Installed    | Latest | Type  | Compatible
---------------------------------------------------------------
pip                | 25.0.1       | 25.2   | minor | ✓
setuptools         | 80.7.1       | 80.9.0 | minor | ✓
requests           | 2.28.0       | 2.31.0 | minor | ✓
django             | 3.2.0        | 5.1.5  | major | ✗
---------------------------------------------------------------

Summary:
Total packages with updates: 4
Major updates: 1
Minor updates: 3
Patch updates: 0
```

## Command Reference

### Global Options

Available for all commands:
- `--version`: Show version and exit
- `--verbose, -v`: Enable detailed logging
- `--config PATH, -c PATH`: Use custom configuration file

### Core Commands

#### `check` - Package Update Analysis
Check for outdated packages and display results.

```bash
python main.py check [OPTIONS]
```

**Options:**
- `--requirements PATH, -r PATH`: Check packages from requirements.txt
- `--output FORMAT, -o FORMAT`: Output format (table, json, csv)
- `--export PATH, -e PATH`: Export results to file
- `--filter-type TYPE, -f TYPE`: Filter by update type (all, major, minor, patch)
- `--include-prerelease`: Include pre-release versions
- `--batch-size INTEGER`: API batch size (default: 10)
- `--timeout INTEGER`: API timeout in seconds (default: 30)

**Examples:**
```bash
# Basic check with table output
python main.py check

# Check requirements file and export to JSON
python main.py check --requirements requirements.txt --output json --export updates.json

# Only show major updates with verbose logging
python main.py --verbose check --filter-type major

# Include pre-release versions
python main.py check --include-prerelease
```

#### `info` - Package Information
Get detailed information about a specific package.

```bash
python main.py info PACKAGE_NAME [OPTIONS]
```

**Options:**
- `--version VERSION`: Specific version to check

**Examples:**
```bash
# Get latest info about requests
python main.py info requests

# Get info about specific version
python main.py info django --version 4.2.0
```

#### `config-show` - Configuration Display
Display current configuration settings.

```bash
python main.py config-show
```

## Output Formats

### Table Format (Default)
Clean, colored terminal output with alignment and compatibility indicators.

**Features:**
- Color-coded compatibility (✓ green, ✗ red)
- Aligned columns for easy reading
- Progress bar during checking
- Summary statistics

### JSON Format
Structured data perfect for automation and integration.

```bash
python main.py check --output json
python main.py check --output json --export results.json
```

**Sample JSON Output:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "scan_duration": 12.5,
  "total_packages_checked": 28,
  "packages": [
    {
      "package": "requests",
      "installed_version": "2.28.0",
      "latest_version": "2.31.0",
      "update_type": "minor",
      "compatible": true,
      "pypi_url": "https://pypi.org/project/requests/"
    }
  ],
  "summary": {
    "total_updates_available": 14,
    "major_updates": 2,
    "minor_updates": 11,
    "patch_updates": 1
  }
}
```

### CSV Format
Spreadsheet-compatible format for data analysis.

```bash
python main.py check --output csv --export outdated.csv
```

## Advanced Usage

### Requirements File Analysis

Check packages from a requirements.txt file:

```bash
python main.py check --requirements requirements.txt
python main.py check --requirements dev-requirements.txt
```

**Supported formats:**
```txt
# Basic requirements.txt
requests>=2.25.0
django==3.2.0
numpy~=1.20.0
pandas[extras]>=1.3.0,<2.0.0

# With comments and URLs
click>=8.0.0  # CLI framework
-e git+https://github.com/user/repo.git#egg=mypackage
```

### Filtering Results

Focus on specific types of updates:

```bash
# Only major updates (breaking changes)
python main.py check --filter-type major

# Only minor updates (new features)
python main.py check --filter-type minor

# Only patch updates (bug fixes)
python main.py check --filter-type patch
```

### Pre-release Versions

Include alpha, beta, and release candidates:

```bash
# Include pre-releases
python main.py check --include-prerelease

# Combine with filtering
python main.py check --include-prerelease --filter-type major
```

### Performance Tuning

Optimize for your environment:

```bash
# Increase batch size for faster processing
python main.py check --batch-size 20

# Reduce timeout for faster failure detection
python main.py check --timeout 10

# Combine for maximum performance
python main.py check --batch-size 15 --timeout 20
```

## Configuration

### Configuration Files

PDR supports TOML configuration files for persistent settings.

**Sample configuration:**
```toml
[pypi]
timeout = 30
batch_size = 10
rate_limit_delay = 0.1

[output]
default_format = "table"
colors_enabled = true

[version_checking]
include_prerelease = false
strict_semver = true
```

### Environment Variables

Override configuration with environment variables:

```bash
export PDR_PYPI_TIMEOUT=60
export PDR_PYPI_BATCH_SIZE=5
export PDR_INCLUDE_PRERELEASE=true
export PDR_LOG_LEVEL=DEBUG

python main.py check
```

## Integration Examples

### CI/CD Pipeline Integration

**GitHub Actions:**
```yaml
name: Dependency Check
on: [push, pull_request]
jobs:
  check-dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install PDR
        run: pip install click colorlog packaging requests toml psutil
      - name: Check for major updates
        run: python main.py check --filter-type major --output json --export major-updates.json
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: dependency-report
          path: major-updates.json
```

### Pre-commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit
python main.py check --filter-type major --timeout 10
if [ $? -ne 0 ]; then
    echo "Major package updates available. Please review before committing."
    exit 1
fi
```

### Makefile Integration

```makefile
.PHONY: deps-check deps-update deps-report

deps-check:
	python main.py check

deps-update:
	python main.py check --filter-type minor --output csv --export minor-updates.csv

deps-report:
	python main.py check --output json --export dependency-report.json
```

## Troubleshooting

### Common Issues

**Network Timeouts:**
```bash
# Increase timeout for slow connections
python main.py check --timeout 60

# Reduce batch size for unstable connections
python main.py check --batch-size 5
```

**PyPI API Rate Limits:**
```bash
# Use smaller batch sizes
python main.py check --batch-size 3

# Enable verbose logging to see rate limit issues
python main.py --verbose check
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Verbose mode shows API calls and timing
python main.py --verbose check

# Focus debugging on specific packages
python main.py --verbose info requests
```

### Log Output Example

With verbose mode enabled:
```
DEBUG | utils | Verbose logging enabled
INFO | cli | Python Dependency Reader v1.0.0 initialized
INFO | package_manager | Found 28 installed packages
DEBUG | pypi_client | API call took 0.245s
DEBUG | version_comparator | Comparing versions: 2.28.0 vs 2.31.0
```

## Best Practices

### Performance Optimization

1. **Use appropriate batch sizes:**
   - Small projects: `--batch-size 5-10`
   - Large projects: `--batch-size 15-20`
   - Slow networks: `--batch-size 3-5`

2. **Tune timeouts:**
   - Fast networks: `--timeout 15`
   - Normal networks: `--timeout 30`
   - Slow networks: `--timeout 60`

3. **Filter results:**
   - Development: `--filter-type major` (focus on breaking changes)
   - Production: `--filter-type minor` (safe updates)

### Workflow Integration

1. **Daily monitoring:**
   - Automated checks with JSON export
   - Focus on major updates for alerts

2. **Development workflow:**
   - Pre-commit hooks for major updates
   - Regular checks during development

3. **Release preparation:**
   - Complete dependency audit
   - Update compatible packages
   - Document breaking changes

## Tips and Tricks

### Quick Commands

```bash
# Quick check for breaking changes only
python main.py check --filter-type major

# Export to timestamped file
python main.py check --output json --export "deps-$(date +%Y%m%d).json"

# Check specific project
cd /path/to/project && python /path/to/pdr/main.py check --requirements requirements.txt
```

### Shell Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias pdr-check='python /path/to/pdr/main.py check'
alias pdr-major='python /path/to/pdr/main.py check --filter-type major'
alias pdr-export='python /path/to/pdr/main.py check --output json --export'
```

This usage guide covers all major features and use cases for Python Dependency Reader. For detailed API information, see the [API Reference](api.md).