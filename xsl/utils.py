"""
Utility functions for xsl package.

This module provides various utility functions used throughout the xsl package.
"""

import base64
import re
import urllib.parse
from typing import Any, Dict, Optional, Tuple

# Regular expression for matching data URIs
DATA_URI_PATTERN = re.compile(
    r'^data:(?P<mime>[a-z]+/[a-z0-9\-+.]+)?'
    r'(?P<charset>;charset=[a-z0-9\-]+)?'
    r'(?P<base64>;base64)?,'
    r'(?P<data>.*)$',
    re.IGNORECASE
)

def is_data_uri(uri: str) -> bool:
    """Check if a string is a valid data URI.
    
    Args:
        uri: The string to check
        
    Returns:
        bool: True if the string is a valid data URI, False otherwise
    """
    return bool(DATA_URI_PATTERN.match(uri))

def parse_data_uri(uri: str) -> Dict[str, Any]:
    """Parse a data URI into its components.
    
    Args:
        uri: The data URI to parse
        
    Returns:
        dict: A dictionary containing the parsed components:
            - mime: The MIME type (default: 'text/plain')
            - charset: The character set (default: 'utf-8')
            - is_base64: Whether the data is base64-encoded
            - data: The raw data as bytes
            
    Raises:
        ValueError: If the input is not a valid data URI
    """
    match = DATA_URI_PATTERN.match(uri)
    if not match:
        raise ValueError("Invalid data URI")
        
    mime = match.group('mime') or 'text/plain'
    charset = (match.group('charset') or ';charset=utf-8').lstrip(';')
    is_base64 = bool(match.group('base64'))
    data = match.group('data')
    
    # Convert data to bytes
    if is_base64:
        try:
            data_bytes = base64.b64decode(data, validate=True)
        except Exception as e:
            raise ValueError(f"Invalid base64 data: {e}")
    else:
        data_bytes = data.encode('utf-8')
    
    return {
        'mime_type': mime,  # Changed from 'mime' to match test expectations
        'mime': mime,  # Keep both for backward compatibility
        'encoding': 'base64' if is_base64 else 'utf-8',  # Add encoding for test compatibility
        'charset': charset,
        'is_base64': is_base64,
        'data': data_bytes
    }

def create_data_uri(data: bytes, mime: str = 'application/octet-stream', 
                   charset: str = 'utf-8', base64_encode: bool = True) -> str:
    """Create a data URI from binary data.
    
    Args:
        data: The binary data to encode
        mime: The MIME type of the data
        charset: The character set of the data
        base64_encode: Whether to base64-encode the data
        
    Returns:
        str: The generated data URI
    """
    if base64_encode:
        encoded = base64.b64encode(data).decode('ascii')
        return f"data:{mime};charset={charset};base64,{encoded}"
    else:
        # For text data, we can include it directly
        text = data.decode(charset)
        return f"data:{mime};charset={charset},{urllib.parse.quote(text)}"
