# Usage Examples

This document provides practical examples of using Python Dependency Reader in various scenarios.

## Basic Usage

### Check All Installed Packages

```bash
# Check all installed packages for updates
pdr check

# Include pre-release versions
pdr check --include-prerelease

# Show only major updates
pdr check --filter-type major
