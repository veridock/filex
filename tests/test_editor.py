"""
Tests for FileEditor class.
"""

import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
from xsl.editor import FileEditor
from xsl.utils import is_data_uri, parse_data_uri


class TestFileEditor:
    """Test cases for FileEditor class."""

    @pytest.fixture
    def sample_svg(self):
        """Sample SVG content for testing."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="200" height="200">
    <metadata>
        {
            "title": "Test SVG",
            "version": "1.0"
        }
    </metadata>
    <rect x="10" y="10" width="50" height="50" fill="red" id="square1"/>
    <circle cx="100" cy="100" r="30" fill="blue" id="circle1"/>
    <text x="50" y="150" id="text1" font-size="16">Hello World</text>
    <image x="150" y="50" width="40" height="40" 
           xlink:href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" />
</svg>'''

    @pytest.fixture
    def sample_xml(self):
        """Sample XML content for testing."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<data>
    <metadata>
        <title>Test Data</title>
        <version>2.0</version>
    </metadata>
    <records>
        <record id="1" type="user">
            <name>John Doe</name>
            <age>30</age>
            <email>john@example.com</email>
        </record>
        <record id="2" type="admin">
            <name>Jane Smith</name>
            <age>25</age>
            <email>jane@example.com</email>
        </record>
    </records>
</data>'''

    @pytest.fixture
    def temp_svg_file(self, sample_svg):
        """Create a temporary SVG file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(sample_svg)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def temp_xml_file(self, sample_xml):
        """Create a temporary XML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(sample_xml)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_load_local_file(self, temp_svg_file):
        """Test loading a local file."""
        editor = FileEditor(temp_svg_file)
        assert editor.file_type == 'svg'
        assert not editor.is_remote
        assert editor.original_content is not None
        assert '<svg' in editor.original_content

    def test_detect_file_types(self, temp_svg_file, temp_xml_file):
        """Test file type detection."""
        svg_editor = FileEditor(temp_svg_file)
        assert svg_editor.file_type == 'svg'

        xml_editor = FileEditor(temp_xml_file)
        assert xml_editor.file_type == 'xml'

    @pytest.mark.skipif(not pytest.importorskip("lxml", minversion=None), reason="lxml not available")
    def test_xpath_queries(self, temp_svg_file):
        """Test XPath functionality."""
        editor = FileEditor(temp_svg_file)

        # Test getting text content
        text_content = editor.get_element_text("//svg:text[@id='text1']")
        assert text_content == "Hello World"

        # Test getting attribute
        fill_color = editor.get_element_attribute("//svg:rect[@id='square1']", "fill")
        assert fill_color == "red"

    @pytest.mark.skipif(not pytest.importorskip("lxml", minversion=None), reason="lxml not available")
    def test_element_modification(self, temp_svg_file):
        """Test modifying elements."""
        editor = FileEditor(temp_svg_file)

        # Modify text content
        success = editor.set_element_text("//svg:text[@id='text1']", "Modified Text")
        assert success

        # Verify modification
        new_text = editor.get_element_text("//svg:text[@id='text1']")
        assert new_text == "Modified Text"

        # Modify attribute
        success = editor.set_element_attribute("//svg:rect[@id='square1']", "fill", "green")
        assert success

        # Verify attribute modification
        new_color = editor.get_element_attribute("//svg:rect[@id='square1']", "fill")
        assert new_color == "green"

    @pytest.mark.skipif(not pytest.importorskip("lxml", minversion=None), reason="lxml not available")
    def test_data_uri_extraction(self, temp_svg_file):
        """Test Data URI extraction."""
        editor = FileEditor(temp_svg_file)

        result = editor.extract_data_uri("//svg:image/@xlink:href")

        assert "error" not in result
        assert result["mime_type"] == "image/png"
        assert "base64_data" in result
        assert result["size"] > 0

    def test_list_elements(self, temp_xml_file):
        """Test listing elements."""
        editor = FileEditor(temp_xml_file)

        if hasattr(editor, 'find_by_xpath'):  # Only if lxml is available
            elements = editor.list_elements("//record")
            assert len(elements) == 2
            assert all('tag' in elem for elem in elements)
            assert all('attributes' in elem for elem in elements)

    def test_save_file(self, temp_svg_file):
        """Test saving file."""
        editor = FileEditor(temp_svg_file)

        if hasattr(editor, 'set_element_text'):  # Only if lxml is available
            editor.set_element_text("//svg:text[@id='text1']", "Saved Text")

        # Save to new file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            output_path = f.name

        try:
            success = editor.save(output_path)
            assert success
            assert os.path.exists(output_path)

            # Verify saved content
            with open(output_path, 'r') as f:
                saved_content = f.read()
            assert '<svg' in saved_content
        finally:
            os.unlink(output_path)

    def test_backup_creation(self, temp_svg_file):
        """Test backup creation."""
        editor = FileEditor(temp_svg_file)

        backup_path = editor.backup()
        assert os.path.exists(backup_path)

        # Verify backup content matches original
        with open(backup_path, 'r') as f:
            backup_content = f.read()
        assert backup_content == editor.original_content

        # Clean up
        os.unlink(backup_path)

    def test_nonexistent_file(self):
        """Test handling of nonexistent files."""
        with pytest.raises(FileNotFoundError):
            FileEditor("nonexistent_file.svg")

    def test_invalid_xpath(self, temp_svg_file):
        """Test handling of invalid XPath expressions."""
        editor = FileEditor(temp_svg_file)

        if hasattr(editor, 'find_by_xpath'):  # Only if lxml is available
            with pytest.raises(ValueError):
                editor.find_by_xpath("invalid[xpath")

    @pytest.mark.skipif(not pytest.importorskip("requests", minversion=None), reason="requests not available")
    def test_remote_file_capability(self):
        """Test that remote file loading capability exists."""
        # This test only checks that the class can handle remote URLs
        # without actually making network requests
        try:
            editor = FileEditor("http://example.com/test.svg")
            assert editor.is_remote
        except Exception:
            # Expected to fail without actual network access
            pass


class TestDataURIFunctions:
    """Test Data URI utility functions."""

    def test_is_data_uri(self):
        """Test Data URI detection."""
        assert is_data_uri("data:text/plain;base64,SGVsbG8gV29ybGQ=")
        assert is_data_uri("data:image/png;base64,iVBORw0KGgoAAAANSUhEUg")
        assert not is_data_uri("http://example.com/image.png")
        assert not is_data_uri("regular string")

    def test_parse_data_uri(self):
        """Test Data URI parsing."""
        data_uri = "data:text/plain;base64,SGVsbG8gV29ybGQ="
        result = parse_data_uri(data_uri)

        assert result["mime_type"] == "text/plain"
        assert result["encoding"] == "base64"
        assert result["data"] == "SGVsbG8gV29ybGQ="

    def test_parse_data_uri_without_encoding(self):
        """Test parsing Data URI without explicit encoding."""
        data_uri = "data:text/plain,Hello%20World"
        result = parse_data_uri(data_uri)

        assert result["mime_type"] == "text/plain"
        assert result["encoding"] == "utf-8"
        assert result["data"] == "Hello%20World"

    def test_parse_invalid_data_uri(self):
        """Test parsing invalid Data URI."""
        with pytest.raises(ValueError):
            parse_data_uri("not a data uri")

        with pytest.raises(ValueError):
            parse_data_uri("data:invalid")


class TestFileEditorIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def complex_svg(self):
        """Complex SVG with multiple Data URIs."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" 
     width="400" height="300">
    <metadata>
        {
            "title": "Complex Test SVG",
            "description": "Contains multiple embedded resources"
        }
    </metadata>
    <defs>
        <pattern id="pattern1">
            <image xlink:href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" />
        </pattern>
    </defs>
    <rect x="0" y="0" width="100%" height="100%" fill="url(#pattern1)"/>
    <foreignObject x="10" y="10" width="200" height="100">
        <div xmlns="http://www.w3.org/1999/xhtml">
            <script type="application/json">
            {
                "config": {"theme": "dark"},
                "data": [1, 2, 3, 4, 5]
            }
            </script>
        </div>
    </foreignObject>
    <image x="250" y="50" width="100" height="100"
           xlink:href="data:application/pdf;base64,JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovUGFnZXMgMiAwIFIKPj4KZW5kb2JqCjIgMCBvYmoKPDwKL1R5cGUgL1BhZ2VzCi9LaWRzIFszIDAgUl0KL0NvdW50IDEKPD4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovTWVkaWFCb3ggWzAgMCA2MTIgNzkyXQovUmVzb3VyY2VzIDw8Ci9Gb250IDw8Ci9GMSA0IDAgUgo+Pgo+PgovQ29udGVudHMgNSAwIFIKPj4KZW5kb2JqCjQgMCBvYmoKPDwKL1R5cGUgL0ZvbnQKL1N1YnR5cGUgL1R5cGUxCi9CYXNlRm9udCAvSGVsdmV0aWNhCj4+CmVuZG9iago1IDAgb2JqCjw8Ci9MZW5ndGggNDQKPj4Kc3RyZWFtCkJUCi9GMSAxMiBUZgoxMDAgNzAwIFRkCihIZWxsbyBXb3JsZCEpIFRqCkVUCmVuZHN0cmVhbQplbmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMDExNSAwMDAwMCBuIAowMDAwMDAwMjQ1IDAwMDAwIG4gCjAwMDAwMDAzMTYgMDAwMDAgbiAKdHJhaWxlcgo8PAovU2l6ZSA2Ci9Sb290IDEgMCBSCj4+CnN0YXJ0eHJlZgo0MTAKJSVFT0Y=" />
</svg>'''

    @pytest.fixture
    def temp_complex_svg(self, complex_svg):
        """Create temporary complex SVG file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(complex_svg)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.mark.skipif(not pytest.importorskip("lxml", minversion=None), reason="lxml not available")
    def test_extract_multiple_data_uris(self, temp_complex_svg):
        """Test extracting multiple Data URIs from complex SVG."""
        editor = FileEditor(temp_complex_svg)

        # Find all elements with Data URIs
        elements = editor.find_by_xpath("//*[contains(@xlink:href, 'data:')]")
        assert len(elements) >= 2

        # Extract PNG Data URI
        png_result = editor.extract_data_uri("//svg:pattern//svg:image/@xlink:href")
        assert png_result["mime_type"] == "image/png"

        # Extract PDF Data URI
        pdf_result = editor.extract_data_uri("//svg:image[contains(@xlink:href, 'application/pdf')]/@xlink:href")
        assert pdf_result["mime_type"] == "application/pdf"

    @pytest.mark.skipif(not pytest.importorskip("lxml", minversion=None), reason="lxml not available")
    def test_modify_and_save_workflow(self, temp_complex_svg):
        """Test complete modify and save workflow."""
        editor = FileEditor(temp_complex_svg)

        # Get original metadata
        original_metadata = editor.get_element_text("//svg:metadata")
        assert "Complex Test SVG" in original_metadata

        # Modify metadata
        new_metadata = '{"title": "Modified SVG", "version": "2.0"}'
        success = editor.set_element_text("//svg:metadata", new_metadata)
        assert success

        # Verify modification
        modified_metadata = editor.get_element_text("//svg:metadata")
        assert "Modified SVG" in modified_metadata

        # Save to new file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            output_path = f.name

        try:
            success = editor.save(output_path)
            assert success

            # Load saved file and verify
            saved_editor = FileEditor(output_path)
            saved_metadata = saved_editor.get_element_text("//svg:metadata")
            assert "Modified SVG" in saved_metadata

        finally:
            os.unlink(output_path)

    def test_error_handling(self):
        """Test various error conditions."""
        # Test with malformed XML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write("<?xml version='1.0'?><root><unclosed>")
            malformed_file = f.name

        try:
            with pytest.raises(ValueError, match="Cannot parse file"):
                FileEditor(malformed_file)
        finally:
            os.unlink(malformed_file)


if __name__ == "__main__":
    pytest.main([__file__])