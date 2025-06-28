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
            
        Raises:
            ValueError: If the file cannot be loaded or parsed
        """
        self.file_path = file_path
        self.tree = None
        self.original_content = None
        # Default namespaces for common XML formats
        self.ns = {
            'svg': 'http://www.w3.org/2000/svg',
            'xlink': 'http://www.w3.org/1999/xlink',
            'html': 'http://www.w3.org/1999/xhtml',
            'xhtml': 'http://www.w3.org/1999/xhtml'
        }
        self._load_file()
    
    @property
    def is_remote(self) -> bool:
        """Check if the file is a remote URL.
        
        Returns:
            bool: True if file_path is a URL, False otherwise
        """
        return (isinstance(self.file_path, str) and 
                (self.file_path.startswith('http://') or 
                 self.file_path.startswith('https://') or
                 self.file_path.startswith('ftp://')))

    def _load_file(self):
        """Load file content from path or URL."""
        if not self.file_path:
            raise ValueError("No file path provided")
            
        if self.is_remote:
            import requests
            try:
                response = requests.get(self.file_path)
                response.raise_for_status()
                content = response.content
            except Exception as e:
                raise IOError(f"Failed to fetch remote file: {str(e)}")
        else:
            with open(self.file_path, 'rb') as f:
                content = f.read()
        
        self.original_content = content.decode('utf-8')
        self._parse_content(content)

    def _parse_content(self, content: bytes):
        """Parse file content with appropriate parser.
        
        Args:
            content: The raw bytes content to parse
            
        Raises:
            ValueError: If the content cannot be parsed
        """
        if LXML_AVAILABLE:
            try:
                self.tree = etree.fromstring(content)
                # Update namespaces from the document
                if hasattr(self.tree, 'nsmap'):
                    for prefix, uri in self.tree.nsmap.items():
                        if prefix is not None:  # Skip default namespace
                            self.ns[prefix] = uri
                return
            except etree.XMLSyntaxError as e:
                logging.warning(f"Failed to parse with lxml: {e}")
                # Continue to standard library fallback
        
        # Fallback to standard library
        try:
            self.tree = ET.fromstring(content)
        except ET.ParseError as e:
            raise ValueError(f"Cannot parse file: {str(e)}")

    def query(self, xpath: str) -> List[Any]:
        """Query elements using XPath.
        
        Args:
            xpath: XPath expression (can include namespaces)
            
        Returns:
            List of matching elements
            
        Raises:
            ValueError: If no file is loaded or XPath is invalid
        """
        if self.tree is None:
            raise ValueError("No file loaded")
            
        try:
            if LXML_AVAILABLE:
                # Register namespaces with lxml
                return self.tree.xpath(xpath, namespaces=self.ns)
            else:
                # Basic XPath support with standard library
                # Replace namespace prefixes in XPath for standard library
                if ':' in xpath:
                    # Simple namespace handling for standard library
                    for prefix, uri in self.ns.items():
                        xpath = xpath.replace(f"{prefix}:", f"{{'{uri}'}}")
                return self.tree.findall(xpath)
        except Exception as e:
            raise ValueError(f"Invalid XPath expression '{xpath}': {str(e)}")

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
            dict: Parsed data URI components with 'mime_type' and other metadata,
                  or {'error': str} if not found
        """
        try:
            elements = self.query(xpath)
            if not elements:
                return {'error': 'No elements found matching XPATH'}
                
            # Handle attribute XPath (e.g., @xlink:href)
            attr = None
            if xpath.endswith('/@xlink:href'):
                element_xpath = xpath.rsplit('/', 1)[0]
                attr = 'xlink:href'
                elements = self.query(element_xpath)
            elif xpath.endswith('/@href'):
                element_xpath = xpath.rsplit('/', 1)[0]
                attr = 'href'
                elements = self.query(element_xpath)
            
            if not elements:
                return {'error': 'No elements found matching XPath'}
                
            # Try to find a data URI in the elements
            for elem in elements:
                # If we have a specific attribute, check that first
                if attr:
                    uri = self._get_attribute(elem, attr)
                    if uri and is_data_uri(uri):
                        result = parse_data_uri(uri)
                        result['xpath'] = xpath
                        return result
                
                # Otherwise check common attributes
                for attr_name in ['xlink:href', 'href', 'data', 'src']:
                    uri = self._get_attribute(elem, attr_name)
                    if uri and is_data_uri(uri):
                        result = parse_data_uri(uri)
                        result['xpath'] = xpath
                        return result
            
            return {
                'error': 'No data URI found in element attributes',
                'mime_type': 'text/plain',
                'data': ''
            }
            
        except Exception as e:
            return {
                'error': f'Error extracting data URI: {str(e)}',
                'mime_type': 'text/plain',
                'data': ''
            }
    
    def _get_attribute(self, element, name: str) -> str:
        """Get an attribute from an element, handling namespaces.
        
        Args:
            element: The XML element
            name: Attribute name (can include namespace prefix)
            
        Returns:
            The attribute value or None if not found
        """
        if not hasattr(element, 'get'):
            return None
            
        # Try direct attribute first
        value = element.get(name)
        if value is not None:
            return value
            
        # Try with xlink: prefix
        if name.startswith('xlink:'):
            return element.get(f"{{{self.ns.get('xlink', '')}}}{name[6:]}")
            
        # Try with full namespace
        if ':' in name:
            prefix = name.split(':', 1)[0]
            if prefix in self.ns:
                return element.get(f"{{{self.ns[prefix]}}}{name.split(':', 1)[1]}")
                
        return None
    
    @property
    def file_type(self) -> str:
        """Get the type of the loaded file.
        
        Returns:
            str: File type ('svg', 'html', 'xml', or 'unknown')
        """
        return self.detect_file_type()
    
    def get_element_attribute(self, xpath: str, attr_name: str, default: str = None) -> str:
        """Get an attribute value from an element.
        
        Args:
            xpath: XPath to the element
            attr_name: Name of the attribute to get
            default: Default value if attribute not found
            
        Returns:
            The attribute value or default if not found
        """
        elements = self.query(xpath)
        if not elements:
            return default
            
        return self._get_attribute(elements[0], attr_name) or default
    
    def set_element_text(self, xpath: str, text: str) -> bool:
        """Set the text content of an element.
        
        Args:
            xpath: XPath to the element
            text: New text content
            
        Returns:
            bool: True if successful, False otherwise
        """
        elements = self.query(xpath)
        if not elements:
            return False
            
        for elem in elements:
            if hasattr(elem, 'text'):
                elem.text = text
        return True
        
    def set_element_attribute(self, xpath: str, attr_name: str, attr_value: str) -> bool:
        """Set an attribute on elements matching XPath.
        
        Args:
            xpath: XPath to the element(s)
            attr_name: Name of the attribute to set
            attr_value: Value to set
            
        Returns:
            bool: True if any elements were modified, False otherwise
        """
        elements = self.query(xpath)
        if not elements:
            return False
            
        modified = False
        for elem in elements:
            if hasattr(elem, 'set'):
                # Handle namespaced attributes (e.g., xlink:href)
                if ':' in attr_name:
                    prefix = attr_name.split(':', 1)[0]
                    if prefix in self.ns:
                        ns_attr = f"{{{self.ns[prefix]}}}{attr_name.split(':', 1)[1]}"
                        elem.set(ns_attr, attr_value)
                        modified = True
                else:
                    elem.set(attr_name, attr_value)
                    modified = True
                    
        return modified
    
    def list_elements(self, xpath: str) -> List[Dict[str, Any]]:
        """List elements matching XPath with their attributes.
        
        Args:
            xpath: XPath expression to find elements
            
        Returns:
            List of dictionaries with element information
        """
        elements = self.query(xpath)
        result = []
        
        for elem in elements:
            if hasattr(elem, 'attrib'):
                result.append({
                    'tag': elem.tag,
                    'text': getattr(elem, 'text', ''),
                    'attributes': dict(elem.attrib)
                })
        
        return result
    
    def backup(self) -> str:
        """Create a backup of the current file.
        
        Returns:
            str: Path to the backup file
            
        Raises:
            IOError: If backup creation fails
        """
        if not self.file_path:
            raise IOError("No file loaded to back up")
            
        backup_path = f"{self.file_path}.bak"
        try:
            import shutil
            shutil.copy2(self.file_path, backup_path)
            return backup_path
        except Exception as e:
            raise IOError(f"Failed to create backup: {str(e)}")
