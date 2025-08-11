#!/usr/bin/env python3
"""
PyUpdater v1.0.0
Main entry point for the CLI application.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cli import main

if __name__ == '__main__':
    main()
