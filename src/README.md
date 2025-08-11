# Source Code Directory

This directory contains the core Python modules for the Python Dependency Reader (PDR) application.

## Module Overview

### Core Modules

- **`cli.py`** - Command-line interface implementation using Click framework
- **`package_manager.py`** - Package discovery and requirements parsing
- **`pypi_client.py`** - PyPI API client with batch processing and caching
- **`version_comparator.py`** - SemVer version comparison and compatibility checking
- **`output_formatter.py`** - Result formatting for table, JSON, and CSV outputs
- **`config.py`** - Configuration management and settings
- **`utils.py`** - Common utility functions and helpers

## Architecture Overview

The application follows a modular design with clear separation of concerns:

```
CLI Layer (cli.py)
    ↓
Business Logic Layer
    ├── Package Manager
    ├── PyPI Client  
    ├── Version Comparator
    └── Output Formatter
    ↓
Infrastructure Layer
    ├── Configuration
    └── Utilities
```

## Module Details

### Command-Line Interface (`cli.py`)
Main entry point providing core commands:
- `check` - Scans packages and identifies updates
- `info` - Gets detailed package information  
- `config-show` - Displays current configuration

Features rich help system, progress bars, and error handling.

### Package Manager (`package_manager.py`)
Handles package discovery from multiple sources:
- System-installed packages via `pkg_resources`
- Requirements.txt file parsing
- Development/editable installs detection

### PyPI Client (`pypi_client.py`)
Manages all PyPI API interactions:
- Concurrent batch processing with ThreadPoolExecutor
- Intelligent caching with TTL support
- Rate limiting and retry logic
- Request/response error handling

### Version Comparator (`version_comparator.py`)
Implements semantic versioning analysis:
- PEP 440 compliant version parsing
- SemVer compatibility checking
- Pre-release version handling
- Breaking change detection

### Output Formatter (`output_formatter.py`)
Provides multiple output formats:
- **Table**: Colored terminal output with alignment
- **JSON**: Structured data with metadata
- **CSV**: Spreadsheet-compatible format

### Configuration Management (`config.py`)
Centralized configuration system:
- TOML file format support
- Environment variable overrides
- Runtime configuration validation

### Utilities (`utils.py`)
Common functionality and helpers:
- Colored logging setup
- File system operations with error handling
- Version string parsing utilities
- Simple caching implementation

## Dependencies

The modules use these key libraries:

- **Click 8.0+** - Command-line interface framework
- **colorlog 6.0+** - Colored logging output
- **requests 2.25+** - HTTP client for PyPI API
- **packaging 21.0+** - Version parsing and comparison
- **toml 0.10+** - Configuration file parsing
- **psutil 7.0+** - System utilities

## Architecture Flow

1. **CLI Layer** parses command-line arguments and options
2. **Package Manager** discovers installed packages or reads requirements.txt
3. **PyPI Client** fetches latest version information from PyPI API
4. **Version Comparator** analyzes version differences and SemVer compatibility
5. **Output Formatter** presents results in requested format

## Design Patterns

- **Dependency Injection**: Components are injected into CLI commands
- **Factory Pattern**: Used for creating formatters and clients
- **Strategy Pattern**: Multiple output formats and version comparison strategies

## Error Handling Strategy

All modules implement comprehensive error handling:

- **Network errors**: Automatic retries with exponential backoff
- **API errors**: Graceful handling of PyPI API failures  
- **Version parsing errors**: Fallback to string comparison
- **File system errors**: Clear error messages with suggestions
- **Configuration errors**: Validation with default fallbacks

## Performance Optimizations

- **Caching**: PyPI responses cached for 1 hour by default
- **Batch processing**: Concurrent API calls with configurable limits
- **Rate limiting**: Respects PyPI API constraints
- **Memory efficiency**: Streaming processing for large package lists

## Testing Considerations

Each module is designed for easy testing:
- Dependency injection allows mocking
- Pure functions for business logic
- Error conditions are testable
- Configuration is isolated

## Development Guidelines

- Follow PEP 8 with 4-space indentation
- Use type hints for all public methods
- Document all classes and functions
- Keep line length under 100 characters
- Be specific about error messages
- Cache expensive operations
- Use concurrent processing appropriately
