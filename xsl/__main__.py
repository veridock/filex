#!/usr/bin/env python3
"""
Main entry point for the xsl package.

This module allows the package to be run as a script using `python -m xsl`.
"""

def main():
    """Run the xsl CLI."""
    from .cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()
