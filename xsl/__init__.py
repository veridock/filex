"""
XSL - Universal File Editor for XML/SVG/HTML

A powerful tool for editing XML-based files with XPath and CSS selectors.
"""

__version__ = '0.1.0'

# Core functionality
from .editor import FileEditor
from .cli import CLI, main as cli_main
from .server import FileEditorServer

__all__ = [
    'FileEditor',
    'CLI',
    'FileEditorServer',
    'cli_main',
]
