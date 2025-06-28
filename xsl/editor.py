"""
Core FileEditor class for xsl package.
Provides functionality for editing XML/HTML/SVG files with XPath and CSS selectors.
"""

import os
import re
import base64
import logging
import shutil
from typing import Any, Dict, Optional, Union, List
from pathlib import Path
import xml.etree.ElementTree as ET

from .utils import is_data_uri, parse_data_uri

try:
    from lxml import etree, html
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    print("Warning: lxml not available. Installing: pip install lxml")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("Warning: BeautifulSoup4 not available. Installing: pip install beautifulsoup4")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available. Installing: pip install requests")


class FileEditor:
    """Main class for XML/HTML/SVG file editing with XPath and CSS selector support."""

    def __init__(self, file_path: str):
        """Initialize FileEditor with a file path or URL.
        
        Args:
            file_path: Path to file or URL
        """
        self.file_path = file_path
        self.tree = None
        self.ns = {}
        self._load_file()

    def _load_file(self):
        """Load file from path or URL."""
        if self.file_path.startswith(('http://', 'https://')):
            if not REQUESTS_AVAILABLE:
                raise ImportError("requests library is required for loading remote files")
            response = requests.get(self.file_path)
            response.raise_for_status()
            content = response.content
            self._parse_content(content)
        else:
            with open(self.file_path, 'rb') as f:
                self._parse_content(f.read())

    def _parse_content(self, content: bytes):
        """Parse file content with appropriate parser."""
        if LXML_AVAILABLE:
            try:
                self.tree = etree.fromstring(content)
                # Register namespaces
                for k, v in self.tree.nsmap.items():
                    if k:
                        self.ns[k] = v
                return
            except Exception as e:
                logging.warning(f"Failed to parse with lxml: {e}")
        
        # Fallback to standard library
        try:
            self.tree = ET.fromstring(content)
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse XML content: {e}")

    def query(self, xpath: str) -> List[Any]:
        """Query elements using XPath.
        
        Args:
            xpath: XPath expression
            
        Returns:
            List of matching elements
        """
        if not self.tree:
            raise ValueError("No file loaded")
            
        if LXML_AVAILABLE:
            return self.tree.xpath(xpath, namespaces=self.ns)
        else:
            # Basic XPath support with standard library
            return self.tree.findall(xpath)

    def set_value(self, xpath: str, value: str) -> bool:
        """Set value of elements matching XPath.
        
        Args:
            xpath: XPath expression
            value: New value
            
        Returns:
            True if successful
        """
        elements = self.query(xpath)
        if not elements:
            return False
            
        for elem in elements:
            if hasattr(elem, 'text'):
                elem.text = value
        return True

    def save(self, output_path: str = None, create_backup: bool = False) -> str:
        """Save changes to file.
        
        Args:
            output_path: Output file path (default: overwrite original)
            create_backup: If True, create a backup before saving
            
        Returns:
            Path to saved file
            
        Raises:
            IOError: If file cannot be written
        """
        output_path = output_path or self.file_path
        
        if create_backup and os.path.exists(output_path):
            backup_path = f"{output_path}.bak"
            import shutil
            shutil.copy2(output_path, backup_path)
        
        try:
            if LXML_AVAILABLE:
                etree.ElementTree(self.tree).write(
                    output_path,
                    encoding='utf-8',
                    xml_declaration=True,
                    pretty_print=True
                )
            else:
                ET.ElementTree(self.tree).write(
                    output_path,
                    encoding='utf-8',
                    xml_declaration=True
                )
            return output_path
        except Exception as e:
            raise IOError(f"Failed to save file {output_path}: {str(e)}")
    
    def find_by_xpath(self, xpath: str) -> list:
        """Find elements by XPath.
        
        Args:
            xpath: XPath expression
            
        Returns:
            List of matching elements
        """
        return self.query(xpath)
    
    def get_element_text(self, xpath: str, default: str = "") -> str:
        """Get text content of first element matching XPath.
        
        Args:
            xpath: XPath expression
            default: Default value if element not found
            
        Returns:
            Text content of the element or default value
        """
        elements = self.query(xpath)
        if elements and hasattr(elements[0], 'text'):
            return elements[0].text or default
        return default
    
    def detect_file_type(self) -> str:
        """Detect the type of the loaded file.
        
        Returns:
            str: File type ('svg', 'html', 'xml', or 'unknown')
        """
        if not self.tree:
            return "unknown"
            
        # Check for SVG
        if hasattr(self.tree, 'tag') and 'svg' in self.tree.tag:
            return 'svg'
            
        # Check for HTML
        if hasattr(self.tree, 'find'):
            if self.tree.find('.//html') is not None:
                return 'html'
                
        # Default to XML
        return 'xml'
    
    def extract_data_uri(self, xpath: str) -> dict:
        """Extract data URI from element's attribute.
        
        Args:
            xpath: XPath to the element containing data URI
            
        Returns:
            dict: Parsed data URI components or None if not found
        """
        elements = self.query(xpath)
        if not elements:
            return None
            
        # Try common attribute names for data URIs
        for attr in ['href', 'xlink:href', 'data', 'src']:
            if hasattr(elements[0], 'get'):
                uri = elements[0].get(attr)
                if uri and is_data_uri(uri):
                    return parse_data_uri(uri)
        return None
    
    def _get_attribute(self, element, name: str) -> str:
        """Get an attribute from an element, handling namespaces."""
        if hasattr(element, 'get'):
            # Try direct attribute first
            value = element.get(name)
            if value is not None:
                return value
                
            # Try with xlink: prefix
            if 'xlink:' in name:
                return element.get(name.split(':')[-1])
            return element.get(f"{{{self.ns.get('xlink', '')}}}{name}")
        return None
