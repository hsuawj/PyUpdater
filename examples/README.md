# Examples Directory

This directory contains example files and usage scenarios for Python Dependency Reader (PDR).

## Files

### `sample-requirements.txt`
A sample requirements.txt file that demonstrates various dependency patterns for testing PDR functionality.

## Usage Examples

### Basic Package Checking
```bash
# Check all installed packages
python main.py check

# Check with verbose output
python main.py --verbose check

# Check only major updates
python main.py check --filter-type major
```

### Requirements File Testing
```bash
# Check packages from requirements file
python main.py check --requirements examples/sample-requirements.txt

# Export results to JSON
python main.py check --requirements examples/sample-requirements.txt --output json --export results.json
```

### Advanced Options
```bash
# Include pre-release versions
python main.py check --include-prerelease

# Batch processing with custom settings
python main.py check --batch-size 5 --timeout 20

# Multiple output formats
python main.py check --output csv --export outdated-packages.csv
python main.py check --output json --export package-updates.json
```

### Package Information
```bash
# Get detailed info about a specific package
python main.py info requests
python main.py info django --version 4.2.0
```

### Configuration
```bash
# Show current configuration
python main.py config-show

# Use custom configuration file
python main.py --config ~/.pdr-config.toml check
```

## Sample Output

When you run `python main.py check`, you'll see output like:

```
Checking packages  [####################################]  100%          
Outdated Packages:
---------------------------------------------------------------
Package            | Installed    | Latest | Type  | Compatible
---------------------------------------------------------------
pip                | 25.0.1       | 25.2   | minor | ✓
setuptools         | 80.7.1       | 80.9.0 | minor | ✓
flask              | 2.0.1        | 3.0.3  | major | ✗
django             | 3.2.0        | 5.1.5  | major | ✗
---------------------------------------------------------------

Summary:
Total packages with updates: 4
Major updates: 2
Minor updates: 2
Patch updates: 0
```

## Integration Examples

### CI/CD Pipeline
```yaml
# .github/workflows/dependency-check.yml
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
        run: pip install -r requirements.txt
      - name: Check for outdated packages
        run: python main.py check --output json --export dependency-report.json
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: dependency-report
          path: dependency-report.json
```

### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
python main.py check --filter-type major --timeout 10
if [ $? -ne 0 ]; then
    echo "Major package updates available. Please review."
    exit 1
fi
```