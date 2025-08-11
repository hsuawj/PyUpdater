"""
Command-line interface for Python Dependency Reader.
Handles all CLI commands, options, and user interactions.
"""

import click
import colorlog
import sys
import os
from typing import Optional, List
import json

from package_manager import PackageManager
from pypi_client import PyPIClient
from version_comparator import VersionComparator
from output_formatter import OutputFormatter
from config import Config
from utils import setup_logging, validate_file_path

# Setup colorful logging
logger = colorlog.getLogger(__name__)

@click.group()
@click.version_option(version="1.0.0", prog_name="PyUpdater")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
@click.pass_context
def main(ctx, verbose, config):
    """
    PyUpdater v1.0.0
    
    A command-line utility for identifying outdated Python packages by 
    comparing installed versions with PyPI using SemVer compatibility.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config_path'] = config
    
    # Setup logging
    setup_logging(verbose)
    
    # Load configuration
    ctx.obj['config'] = Config(config_path=config)
    
    logger.info("PyUpdater v1.0.0 initialized")

@main.command()
@click.option('--requirements', '-r', type=click.Path(exists=True), 
              help='Path to requirements.txt file')
@click.option('--output', '-o', type=click.Choice(['table', 'json', 'csv']), 
              default='table', help='Output format')
@click.option('--export', '-e', type=click.Path(), 
              help='Export results to file')
@click.option('--filter-type', '-f', type=click.Choice(['all', 'major', 'minor', 'patch']), 
              default='all', help='Filter updates by type')
@click.option('--include-prerelease', is_flag=True, 
              help='Include pre-release versions')
@click.option('--batch-size', type=int, default=10, 
              help='Batch size for PyPI API calls')
@click.option('--timeout', type=int, default=30, 
              help='Timeout for PyPI API calls in seconds')
@click.pass_context
def check(ctx, requirements, output, export, filter_type, include_prerelease, batch_size, timeout):
    """
    Check for outdated packages and display results.
    
    This command will:
    1. Scan installed packages or read from requirements.txt
    2. Query PyPI API for latest versions
    3. Compare versions using SemVer compatibility
    4. Display results in specified format
    """
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    try:
        # Initialize components
        package_manager = PackageManager()
        pypi_client = PyPIClient(timeout=timeout, batch_size=batch_size)
        version_comparator = VersionComparator(include_prerelease=include_prerelease)
        output_formatter = OutputFormatter()
        
        # Get packages to check
        if requirements:
            logger.info(f"Reading packages from {requirements}")
            packages = package_manager.read_requirements_file(requirements)
        else:
            logger.info("Scanning installed packages")
            packages = package_manager.get_installed_packages()
        
        if not packages:
            click.echo(click.style("No packages found to check.", fg='yellow'))
            return
        
        # Show progress
        with click.progressbar(packages, label='Checking packages') as bar:
            results = []
            for package in bar:
                try:
                    # Get latest version from PyPI
                    latest_info = pypi_client.get_package_info(package.name)
                    if latest_info:
                        # Compare versions
                        comparison = version_comparator.compare_versions(
                            package.version, 
                            latest_info['version']
                        )
                        
                        if comparison['needs_update']:
                            # Apply filter
                            if filter_type == 'all' or comparison['update_type'] == filter_type:
                                results.append({
                                    'package': package.name,
                                    'installed': package.version,
                                    'latest': latest_info['version'],
                                    'update_type': comparison['update_type'],
                                    'compatible': comparison['compatible'],
                                    'description': latest_info.get('summary', ''),
                                    'upload_time': latest_info.get('upload_time', '')
                                })
                except Exception as e:
                    if verbose:
                        logger.error(f"Error checking {package.name}: {e}")
                    continue
        
        # Format and display results
        if results:
            formatted_output = output_formatter.format_results(results, output)
            click.echo(formatted_output)
            
            # Export if requested
            if export:
                output_formatter.export_results(results, export, output)
                click.echo(click.style(f"Results exported to {export}", fg='green'))
            
            # Summary
            total_updates = len(results)
            major_updates = len([r for r in results if r['update_type'] == 'major'])
            minor_updates = len([r for r in results if r['update_type'] == 'minor'])
            patch_updates = len([r for r in results if r['update_type'] == 'patch'])
            
            click.echo(f"\n{click.style('Summary:', fg='cyan', bold=True)}")
            click.echo(f"Total packages with updates: {total_updates}")
            click.echo(f"Major updates: {click.style(str(major_updates), fg='red')}")
            click.echo(f"Minor updates: {click.style(str(minor_updates), fg='yellow')}")
            click.echo(f"Patch updates: {click.style(str(patch_updates), fg='green')}")
        else:
            click.echo(click.style("All packages are up to date! 🎉", fg='green'))
            
    except KeyboardInterrupt:
        click.echo(click.style("\nOperation cancelled by user.", fg='yellow'))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        click.echo(click.style(f"Error: {e}", fg='red'))
        sys.exit(1)

@main.command()
@click.argument('package_name')
@click.option('--version', help='Specific version to check')
@click.pass_context
def info(ctx, package_name, version):
    """
    Get detailed information about a specific package.
    """
    try:
        pypi_client = PyPIClient()
        package_manager = PackageManager()
        
        # Get package info from PyPI
        package_info = pypi_client.get_package_info(package_name)
        if not package_info:
            click.echo(click.style(f"Package '{package_name}' not found on PyPI.", fg='red'))
            return
        
        # Get installed version if available
        installed_packages = package_manager.get_installed_packages()
        installed_version = None
        for pkg in installed_packages:
            if pkg.name.lower() == package_name.lower():
                installed_version = pkg.version
                break
        
        # Display information
        click.echo(f"\n{click.style('Package Information:', fg='cyan', bold=True)}")
        click.echo(f"Name: {package_info['name']}")
        click.echo(f"Latest Version: {package_info['version']}")
        click.echo(f"Installed Version: {installed_version or 'Not installed'}")
        click.echo(f"Summary: {package_info.get('summary', 'N/A')}")
        click.echo(f"Author: {package_info.get('author', 'N/A')}")
        click.echo(f"Home Page: {package_info.get('home_page', 'N/A')}")
        click.echo(f"Upload Time: {package_info.get('upload_time', 'N/A')}")
        
        if installed_version and installed_version != package_info['version']:
            version_comparator = VersionComparator()
            comparison = version_comparator.compare_versions(
                installed_version, 
                package_info['version']
            )
            
            click.echo(f"\n{click.style('Update Information:', fg='yellow', bold=True)}")
            click.echo(f"Update Available: {click.style('Yes', fg='green')}")
            click.echo(f"Update Type: {click.style(comparison['update_type'], fg='yellow')}")
            click.echo(f"SemVer Compatible: {click.style(str(comparison['compatible']), fg='green' if comparison['compatible'] else 'red')}")
            
    except Exception as e:
        logger.error(f"Error getting package info: {e}")
        click.echo(click.style(f"Error: {e}", fg='red'))

@main.command()
@click.pass_context
def config_show(ctx):
    """
    Display current configuration settings.
    """
    config = ctx.obj['config']
    click.echo(f"\n{click.style('Configuration:', fg='cyan', bold=True)}")
    click.echo(json.dumps(config.get_all(), indent=2))

if __name__ == '__main__':
    main()
