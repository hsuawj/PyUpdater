"""
Output Formatter module for displaying results in various formats.
Handles table formatting, JSON/CSV export, and colored output.
"""

import json
import csv
import io
import colorlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import click

logger = colorlog.getLogger(__name__)

class OutputFormatter:
    """
    Handles formatting and display of package update results.
    
    Supports multiple output formats:
    - Rich table format with colors
    - JSON format for programmatic use
    - CSV format for spreadsheet import
    - Summary statistics
    """
    
    def __init__(self):
        """Initialize the output formatter."""
        self.color_map = {
            'major': 'red',
            'minor': 'yellow', 
            'patch': 'green',
            'unknown': 'white'
        }
    
    def format_results(self, results: List[Dict[str, Any]], 
                      format_type: str = 'table') -> str:
        """
        Format results in the specified format.
        
        Args:
            results: List of package update results
            format_type: Output format ('table', 'json', 'csv')
            
        Returns:
            str: Formatted output string
        """
        if not results:
            return self._format_empty_results(format_type)
        
        if format_type == 'table':
            return self._format_table(results)
        elif format_type == 'json':
            return self._format_json(results)
        elif format_type == 'csv':
            return self._format_csv(results)
        else:
            logger.error(f"Unknown format type: {format_type}")
            return self._format_table(results)
    
    def _format_table(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results as a rich table with colors and alignment.
        
        Args:
            results: Package update results
            
        Returns:
            str: Formatted table string
        """
        if not results:
            return "No packages need updates."
        
        # Calculate column widths
        max_package_len = max(len(r['package']) for r in results)
        max_installed_len = max(len(r['installed']) for r in results)
        max_latest_len = max(len(r['latest']) for r in results)
        max_type_len = max(len(r['update_type']) for r in results)
        
        # Ensure minimum widths
        package_width = max(max_package_len, 10)
        installed_width = max(max_installed_len, 9)
        latest_width = max(max_latest_len, 6)
        type_width = max(max_type_len, 4)
        
        # Build header
        header = f"{'Package':<{package_width}} | {'Installed':<{installed_width}} | {'Latest':<{latest_width}} | {'Type':<{type_width}} | Compatible"
        separator = "-" * len(header)
        
        lines = [
            click.style("Outdated Packages:", fg='cyan', bold=True),
            click.style(separator, fg='blue'),
            click.style(header, fg='blue', bold=True),
            click.style(separator, fg='blue')
        ]
        
        # Add package rows
        for result in results:
            package = result['package']
            installed = result['installed']
            latest = result['latest']
            update_type = result['update_type']
            compatible = '✓' if result.get('compatible', True) else '✗'
            
            # Color code the update type
            type_color = self.color_map.get(update_type, 'white')
            
            # Format row
            row = (f"{package:<{package_width}} | "
                  f"{installed:<{installed_width}} | "
                  f"{click.style(latest, fg='green'):<{latest_width + 9}} | "  # +9 for ANSI codes
                  f"{click.style(update_type, fg=type_color):<{type_width + 9}} | "
                  f"{click.style(compatible, fg='green' if compatible == '✓' else 'red')}")
            
            lines.append(row)
        
        lines.append(click.style(separator, fg='blue'))
        
        return '\n'.join(lines)
    
    def _format_json(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results as JSON.
        
        Args:
            results: Package update results
            
        Returns:
            str: JSON formatted string
        """
        output = {
            'timestamp': datetime.now().isoformat(),
            'total_packages': len(results),
            'packages': results,
            'summary': self._generate_summary(results)
        }
        
        return json.dumps(output, indent=2, default=str)
    
    def _format_csv(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results as CSV.
        
        Args:
            results: Package update results
            
        Returns:
            str: CSV formatted string
        """
        if not results:
            return "package,installed,latest,update_type,compatible,description\n"
        
        output = io.StringIO()
        fieldnames = ['package', 'installed', 'latest', 'update_type', 
                     'compatible', 'description', 'upload_time']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = {
                'package': result.get('package', ''),
                'installed': result.get('installed', ''),
                'latest': result.get('latest', ''),
                'update_type': result.get('update_type', ''),
                'compatible': 'Yes' if result.get('compatible', True) else 'No',
                'description': result.get('description', '').replace('\n', ' ').replace('\r', ''),
                'upload_time': result.get('upload_time', '')
            }
            writer.writerow(row)
        
        return output.getvalue()
    
    def _format_empty_results(self, format_type: str) -> str:
        """
        Format empty results based on format type.
        
        Args:
            format_type: Output format
            
        Returns:
            str: Empty results message
        """
        if format_type == 'json':
            return json.dumps({
                'timestamp': datetime.now().isoformat(),
                'total_packages': 0,
                'packages': [],
                'message': 'All packages are up to date'
            }, indent=2)
        elif format_type == 'csv':
            return "package,installed,latest,update_type,compatible,description\n"
        else:
            return click.style("All packages are up to date! 🎉", fg='green')
    
    def export_results(self, results: List[Dict[str, Any]], 
                      filepath: str, format_type: str):
        """
        Export results to a file.
        
        Args:
            results: Package update results
            filepath: Output file path
            format_type: Export format
        """
        try:
            formatted_output = self.format_results(results, format_type)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
                
            logger.info(f"Results exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting results to {filepath}: {e}")
            raise
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from results.
        
        Args:
            results: Package update results
            
        Returns:
            Dict: Summary statistics
        """
        if not results:
            return {
                'total_updates': 0,
                'by_type': {},
                'compatible_updates': 0,
                'breaking_updates': 0
            }
        
        # Count by update type
        type_counts = {}
        compatible_count = 0
        breaking_count = 0
        
        for result in results:
            update_type = result.get('update_type', 'unknown')
            type_counts[update_type] = type_counts.get(update_type, 0) + 1
            
            if result.get('compatible', True):
                compatible_count += 1
            else:
                breaking_count += 1
        
        return {
            'total_updates': len(results),
            'by_type': type_counts,
            'compatible_updates': compatible_count,
            'breaking_updates': breaking_count,
            'percentage_compatible': round((compatible_count / len(results)) * 100, 1)
        }
    
    def format_package_info(self, package_info: Dict[str, Any]) -> str:
        """
        Format detailed package information for display.
        
        Args:
            package_info: Package information dictionary
            
        Returns:
            str: Formatted package information
        """
        lines = []
        
        # Basic information
        lines.append(click.style("Package Information:", fg='cyan', bold=True))
        lines.append(f"Name: {package_info.get('name', 'N/A')}")
        lines.append(f"Version: {click.style(package_info.get('version', 'N/A'), fg='green')}")
        lines.append(f"Summary: {package_info.get('summary', 'N/A')}")
        
        # Author information
        author = package_info.get('author', '')
        author_email = package_info.get('author_email', '')
        if author or author_email:
            author_info = f"{author} <{author_email}>" if author and author_email else (author or author_email)
            lines.append(f"Author: {author_info}")
        
        # URLs
        home_page = package_info.get('home_page', '')
        if home_page:
            lines.append(f"Home Page: {home_page}")
        
        # Project URLs
        project_urls = package_info.get('project_urls', {})
        if project_urls:
            lines.append("\nProject URLs:")
            for name, url in project_urls.items():
                lines.append(f"  {name}: {url}")
        
        # Requirements
        requires_python = package_info.get('requires_python', '')
        if requires_python:
            lines.append(f"\nRequires Python: {requires_python}")
        
        requires_dist = package_info.get('requires_dist', [])
        if requires_dist:
            lines.append(f"Dependencies: {len(requires_dist)} packages")
        
        # Upload information
        upload_time = package_info.get('upload_time', '')
        if upload_time:
            lines.append(f"Upload Time: {upload_time}")
        
        # Status indicators
        if package_info.get('yanked', False):
            reason = package_info.get('yanked_reason', 'No reason provided')
            lines.append(f"\n{click.style('⚠️  YANKED', fg='red', bold=True)}: {reason}")
        
        return '\n'.join(lines)
    
    def format_progress_message(self, current: int, total: int, 
                               package_name: str) -> str:
        """
        Format progress message for package checking.
        
        Args:
            current: Current package number
            total: Total packages
            package_name: Name of current package
            
        Returns:
            str: Formatted progress message
        """
        percentage = (current / total) * 100 if total > 0 else 0
        return f"[{current}/{total}] ({percentage:.1f}%) Checking {package_name}..."
    
    def format_error_message(self, error: str, package_name: Optional[str] = None) -> str:
        """
        Format error message with consistent styling.
        
        Args:
            error: Error message
            package_name: Optional package name
            
        Returns:
            str: Formatted error message
        """
        if package_name:
            return click.style(f"Error checking {package_name}: {error}", fg='red')
        else:
            return click.style(f"Error: {error}", fg='red')
