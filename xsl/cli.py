#!/usr/bin/env python3
"""
Universal File Editor CLI Tool
Edytor plików SVG/HTML/XML z obsługą XPath i CSS selectors
Obsługuje tryb CLI oraz serwer HTTP dla zdalnej edycji
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Union
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.parse
import logging
import base64

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
    """Główna klasa do edycji plików XML/HTML/SVG"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path) if not file_path.startswith('http') else file_path
        self.tree = None
        self.root = None
        self.file_type = None
        self.original_content = None
        self.is_remote = file_path.startswith('http')
        self._load_file()

    def _load_file(self):
        """Ładuje plik i określa jego typ"""
        if self.is_remote:
            if not REQUESTS_AVAILABLE:
                raise ImportError("requests library required for remote files")
            try:
                response = requests.get(self.file_path)
                response.raise_for_status()
                self.original_content = response.text
            except Exception as e:
                raise ConnectionError(f"Cannot fetch remote file: {e}")
        else:
            if not self.file_path.exists():
                raise FileNotFoundError(f"File not found: {self.file_path}")
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.original_content = f.read()

        # Określ typ pliku
        if self.is_remote:
            extension = Path(urlparse(str(self.file_path)).path).suffix.lower()
        else:
            extension = self.file_path.suffix.lower()

        content_lower = self.original_content.lower()

        if extension == '.svg' or '<svg' in content_lower:
            self.file_type = 'svg'
        elif extension in ['.html', '.htm'] or '<!doctype html' in content_lower or '<html' in content_lower:
            self.file_type = 'html'
        elif extension == '.xml' or '<?xml' in content_lower:
            self.file_type = 'xml'
        else:
            self.file_type = 'xml'  # domyślnie XML

        # Parsuj plik
        if LXML_AVAILABLE:
            try:
                if self.file_type == 'html':
                    self.tree = html.fromstring(self.original_content)
                else:
                    self.tree = etree.fromstring(self.original_content.encode('utf-8'))
                self.root = self.tree
            except Exception as e:
                print(f"lxml parsing failed: {e}, trying ElementTree...")
                self._fallback_parse()
        else:
            self._fallback_parse()

    def _fallback_parse(self):
        """Fallback parsing using ElementTree"""
        try:
            self.tree = ET.fromstring(self.original_content)
            self.root = self.tree
        except ET.ParseError as e:
            raise ValueError(f"Cannot parse file: {e}")

    def find_by_xpath(self, xpath: str) -> List:
        """Znajdź elementy używając XPath"""
        if not LXML_AVAILABLE:
            raise NotImplementedError("XPath requires lxml library")

        try:
            if isinstance(self.tree, etree._Element):
                # Zarejestruj standardowe przestrzenie nazw
                namespaces = {
                    'svg': 'http://www.w3.org/2000/svg',
                    'xlink': 'http://www.w3.org/1999/xlink',
                    'html': 'http://www.w3.org/1999/xhtml'
                }
                return self.tree.xpath(xpath, namespaces=namespaces)
            else:
                return []
        except Exception as e:
            raise ValueError(f"Invalid XPath expression: {e}")

    def find_by_css(self, css_selector: str) -> List:
        """Znajdź elementy używając CSS selectors (tylko HTML)"""
        if not BS4_AVAILABLE:
            raise NotImplementedError("CSS selectors require beautifulsoup4 library")

        if self.file_type != 'html':
            raise ValueError("CSS selectors work only with HTML files")

        soup = BeautifulSoup(self.original_content, 'html.parser')
        return soup.select(css_selector)

    def extract_data_uri(self, xpath: str) -> Dict[str, str]:
        """Wyciągnij Data URI z SVG i zdekoduj zawartość"""
        elements = self.find_by_xpath(xpath)
        if not elements:
            return {"error": "No elements found with given XPath"}

        element = elements[0]
        data_uri = None

        # Sprawdź różne atrybuty, które mogą zawierać Data URI
        for attr in ['href', 'xlink:href', 'src', 'data']:
            if hasattr(element, 'get'):
                uri = element.get(attr)
            elif hasattr(element, 'attrib'):
                uri = element.attrib.get(attr)
            else:
                continue

            if uri and uri.startswith('data:'):
                data_uri = uri
                break

        if not data_uri:
            return {"error": "No Data URI found in element"}

        try:
            # Rozdziel nagłówek i dane
            header, base64_data = data_uri.split(',', 1)
            mime_type = header.split(':')[1].split(';')[0]

            # Dekoduj base64
            decoded_data = base64.b64decode(base64_data)

            return {
                "mime_type": mime_type,
                "size": len(decoded_data),
                "base64_data": base64_data,
                "decoded_size": len(decoded_data)
            }
        except Exception as e:
            return {"error": f"Failed to decode Data URI: {e}"}

    def save_data_uri_to_file(self, xpath: str, output_path: str) -> bool:
        """Zapisz zawartość Data URI do pliku"""
        result = self.extract_data_uri(xpath)
        if "error" in result:
            print(f"Error: {result['error']}")
            return False

        try:
            decoded_data = base64.b64decode(result['base64_data'])
            with open(output_path, 'wb') as f:
                f.write(decoded_data)
            print(f"Data URI saved to {output_path} ({result['size']} bytes, {result['mime_type']})")
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def get_element_text(self, xpath: str) -> str:
        """Pobierz tekst elementu"""
        elements = self.find_by_xpath(xpath)
        if elements:
            element = elements[0]
            if hasattr(element, 'text'):
                return element.text or ""
            return str(element)
        return ""

    def get_element_attribute(self, xpath: str, attr_name: str) -> str:
        """Pobierz atrybut elementu"""
        elements = self.find_by_xpath(xpath)
        if elements:
            element = elements[0]
            if hasattr(element, 'get'):
                return element.get(attr_name, "")
            elif hasattr(element, 'attrib'):
                return element.attrib.get(attr_name, "")
        return ""

    def set_element_text(self, xpath: str, new_text: str) -> bool:
        """Ustaw tekst elementu"""
        elements = self.find_by_xpath(xpath)
        if elements:
            element = elements[0]
            if hasattr(element, 'text'):
                element.text = new_text
            return True
        return False

    def set_element_attribute(self, xpath: str, attr_name: str, attr_value: str) -> bool:
        """Ustaw atrybut elementu"""
        elements = self.find_by_xpath(xpath)
        if elements:
            element = elements[0]
            if hasattr(element, 'set'):
                element.set(attr_name, attr_value)
            elif hasattr(element, 'attrib'):
                element.attrib[attr_name] = attr_value
            return True
        return False

    def add_element(self, parent_xpath: str, tag_name: str, text: str = "", attributes: Dict[str, str] = None) -> bool:
        """Dodaj nowy element"""
        parents = self.find_by_xpath(parent_xpath)
        if parents:
            parent = parents[0]
            if LXML_AVAILABLE:
                new_element = etree.SubElement(parent, tag_name)
                if text:
                    new_element.text = text
                if attributes:
                    for key, value in attributes.items():
                        new_element.set(key, value)
            return True
        return False

    def remove_element(self, xpath: str) -> bool:
        """Usuń element"""
        elements = self.find_by_xpath(xpath)
        if elements:
            element = elements[0]
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
                return True
        return False

    def list_elements(self, xpath: str = "//*") -> List[Dict]:
        """Wylistuj elementy z ich ścieżkami"""
        elements = self.find_by_xpath(xpath)
        result = []

        for i, element in enumerate(elements):
            if LXML_AVAILABLE:
                element_path = self.tree.getpath(element) if hasattr(self.tree, 'getpath') else f"element[{i}]"
                element_info = {
                    'path': element_path,
                    'tag': element.tag,
                    'text': (element.text or "").strip(),
                    'attributes': dict(element.attrib) if hasattr(element, 'attrib') else {}
                }
                result.append(element_info)

        return result

    def save(self, output_path: str = None) -> bool:
        """Zapisz zmiany do pliku"""
        if self.is_remote and not output_path:
            raise ValueError("Cannot save remote file without specifying output path")

        save_path = output_path or str(self.file_path)

        try:
            if LXML_AVAILABLE:
                if self.file_type == 'html':
                    content = etree.tostring(self.tree, encoding='unicode', method='html', pretty_print=True)
                else:
                    content = etree.tostring(self.tree, encoding='unicode', pretty_print=True)
                    if not content.startswith('<?xml'):
                        content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
            else:
                content = ET.tostring(self.tree, encoding='unicode')

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def backup(self) -> str:
        """Utwórz kopię zapasową"""
        if self.is_remote:
            raise ValueError("Cannot create backup of remote file")
        backup_path = f"{self.file_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(self.original_content)
        return backup_path


class FileEditorServer(BaseHTTPRequestHandler):
    """HTTP Server dla zdalnej edycji plików"""

    editors: Dict[str, FileEditor] = {}

    def do_GET(self):
        """Obsługa żądań GET"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        if path == '/':
            self._serve_interface()
        elif path == '/api/files':
            self._list_files()
        elif path.startswith('/api/file/'):
            file_path = path[10:]  # usuń /api/file/
            self._serve_file_info(file_path)
        elif path == '/api/extract':
            # Endpoint do ekstrakcji Data URI z URL + XPath
            self._extract_from_url(query)
        else:
            self._send_error(404, "Not Found")

    def do_POST(self):
        """Obsługa żądań POST"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(post_data)
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == '/api/load':
            self._load_file(data)
        elif path == '/api/query':
            self._query_elements(data)
        elif path == '/api/update':
            self._update_element(data)
        elif path == '/api/save':
            self._save_file(data)
        elif path == '/api/extract_data_uri':
            self._extract_data_uri(data)
        else:
            self._send_error(404, "Not Found")

    def _extract_from_url(self, query):
        """Ekstrakcja Data URI z URL + XPath (GET endpoint)"""
        try:
            url = query.get('url', [''])[0]
            xpath = query.get('xpath', [''])[0]

            if not url or not xpath:
                self._send_json_response({'error': 'Missing url or xpath parameter'})
                return

            # Załaduj plik z URL
            editor = FileEditor(url)

            # Wyciągnij Data URI
            result = editor.extract_data_uri(xpath)

            self._send_json_response(result)

        except Exception as e:
            self._send_json_response({'error': str(e)})

    def _serve_interface(self):
        """Serwuj interfejs webowy"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>File Editor Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background: #fafafa; }
                input, textarea, select { padding: 8px; margin: 5px; width: 300px; border: 1px solid #ccc; border-radius: 4px; }
                button { padding: 10px 15px; background: #007cba; color: white; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #005a87; }
                .result { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
                .error { background: #ffe6e6; color: #d00; }
                .success { background: #e6ffe6; color: #0a0; }
                .url-extractor { background: #e6f3ff; border-left: 4px solid #007cba; }
                .tabs { display: flex; border-bottom: 1px solid #ddd; }
                .tab { padding: 10px 20px; cursor: pointer; border-bottom: 2px solid transparent; }
                .tab.active { border-bottom-color: #007cba; background: #f0f8ff; }
                .tab-content { display: none; }
                .tab-content.active { display: block; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛠️ Universal File Editor Server</h1>
                <p>Edytuj pliki SVG/HTML/XML za pomocą XPath i CSS selectors</p>

                <div class="tabs">
                    <div class="tab active" onclick="showTab('local')">Pliki lokalne</div>
                    <div class="tab" onclick="showTab('remote')">Ekstrakcja z URL</div>
                </div>

                <div id="local" class="tab-content active">
                    <div class="section">
                        <h3>1. Załaduj plik lokalny</h3>
                        <input type="text" id="filePath" placeholder="Ścieżka do pliku (np. ./data.svg)" value="./example.svg">
                        <button onclick="loadFile()">Załaduj</button>
                        <div id="loadResult" class="result"></div>
                    </div>

                    <div class="section">
                        <h3>2. Zapytania XPath/CSS</h3>
                        <input type="text" id="query" placeholder="XPath (np. //text[@id='title']) lub CSS (np. .my-class)">
                        <select id="queryType">
                            <option value="xpath">XPath</option>
                            <option value="css">CSS Selector</option>
                        </select>
                        <button onclick="queryElements()">Wykonaj</button>
                        <div id="queryResult" class="result"></div>
                    </div>

                    <div class="section">
                        <h3>3. Edycja elementów</h3>
                        <input type="text" id="updateXPath" placeholder="XPath elementu do edycji">
                        <select id="updateType">
                            <option value="text">Tekst</option>
                            <option value="attribute">Atrybut</option>
                        </select>
                        <input type="text" id="attributeName" placeholder="Nazwa atrybutu (jeśli atrybut)">
                        <textarea id="newValue" placeholder="Nowa wartość"></textarea>
                        <button onclick="updateElement()">Aktualizuj</button>
                        <div id="updateResult" class="result"></div>
                    </div>

                    <div class="section">
                        <h3>4. Zapisz zmiany</h3>
                        <input type="text" id="savePath" placeholder="Ścieżka zapisu (puste = nadpisz)">
                        <button onclick="saveFile()">Zapisz</button>
                        <div id="saveResult" class="result"></div>
                    </div>
                </div>

                <div id="remote" class="tab-content">
                    <div class="section url-extractor">
                        <h3>🌐 Ekstrakcja Data URI z URL</h3>
                        <p>Pobierz i wyciągnij Data URI z pliku SVG/XML za pomocą XPath</p>
                        <input type="text" id="remoteUrl" placeholder="URL pliku (np. http://localhost/file.svg)" style="width: 400px;">
                        <input type="text" id="remoteXPath" placeholder="XPath (np. //svg:image/@xlink:href)" style="width: 300px;">
                        <button onclick="extractFromUrl()">Wyciągnij</button>
                        <div id="extractResult" class="result"></div>
                    </div>

                    <div class="section">
                        <h3>Przykłady XPath dla Data URI</h3>
                        <ul>
                            <li><code>//svg:image/@xlink:href</code> - atrybut href w elemencie image</li>
                            <li><code>//*[contains(@href,'data:')]/@href</code> - dowolny element z data: w href</li>
                            <li><code>//svg:object/@data</code> - atrybut data w object</li>
                            <li><code>//svg:foreignObject//text()</code> - tekst w foreignObject</li>
                        </ul>
                    </div>
                </div>
            </div>

            <script>
                function showTab(tabName) {
                    // Ukryj wszystkie zakładki
                    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
                    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));

                    // Pokaż wybraną zakładkę
                    document.getElementById(tabName).classList.add('active');
                    event.target.classList.add('active');
                }

                async function apiCall(endpoint, data) {
                    try {
                        const response = await fetch(endpoint, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(data)
                        });
                        return await response.json();
                    } catch (error) {
                        return {success: false, error: error.message};
                    }
                }

                async function extractFromUrl() {
                    const url = document.getElementById('remoteUrl').value;
                    const xpath = document.getElementById('remoteXPath').value;

                    if (!url || !xpath) {
                        document.getElementById('extractResult').textContent = 'Podaj URL i XPath';
                        return;
                    }

                    try {
                        const response = await fetch(`/api/extract?url=${encodeURIComponent(url)}&xpath=${encodeURIComponent(xpath)}`);
                        const result = await response.json();

                        document.getElementById('extractResult').textContent = JSON.stringify(result, null, 2);
                        document.getElementById('extractResult').className = 'result ' + (result.error ? 'error' : 'success');
                    } catch (error) {
                        document.getElementById('extractResult').textContent = 'Błąd: ' + error.message;
                        document.getElementById('extractResult').className = 'result error';
                    }
                }

                async function loadFile() {
                    const filePath = document.getElementById('filePath').value;
                    const result = await apiCall('/api/load', {file_path: filePath});
                    document.getElementById('loadResult').textContent = JSON.stringify(result, null, 2);
                    document.getElementById('loadResult').className = 'result ' + (result.success ? 'success' : 'error');
                }

                async function queryElements() {
                    const query = document.getElementById('query').value;
                    const queryType = document.getElementById('queryType').value;
                    const result = await apiCall('/api/query', {query, type: queryType});
                    document.getElementById('queryResult').textContent = JSON.stringify(result, null, 2);
                    document.getElementById('queryResult').className = 'result ' + (result.success ? 'success' : 'error');
                }

                async function updateElement() {
                    const xpath = document.getElementById('updateXPath').value;
                    const updateType = document.getElementById('updateType').value;
                    const attributeName = document.getElementById('attributeName').value;
                    const newValue = document.getElementById('newValue').value;

                    const data = {xpath, type: updateType, value: newValue};
                    if (updateType === 'attribute') {
                        data.attribute = attributeName;
                    }

                    const result = await apiCall('/api/update', data);
                    document.getElementById('updateResult').textContent = JSON.stringify(result, null, 2);
                    document.getElementById('updateResult').className = 'result ' + (result.success ? 'success' : 'error');
                }

                async function saveFile() {
                    const savePath = document.getElementById('savePath').value;
                    const result = await apiCall('/api/save', {output_path: savePath || null});
                    document.getElementById('saveResult').textContent = JSON.stringify(result, null, 2);
                    document.getElementById('saveResult').className = 'result ' + (result.success ? 'success' : 'error');
                }
            </script>
        </body>
        </html>
        """
        self._send_response(200, html, 'text/html')

    def _load_file(self, data):
        """Załaduj plik do edycji"""
        try:
            file_path = data['file_path']
            editor = FileEditor(file_path)
            self.editors[file_path] = editor

            response = {
                'success': True,
                'message': f'File loaded: {file_path}',
                'file_type': editor.file_type,
                'is_remote': editor.is_remote,
                'elements_count': len(editor.find_by_xpath("//*")) if LXML_AVAILABLE else 0
            }
        except Exception as e:
            response = {'success': False, 'error': str(e)}

        self._send_json_response(response)

    def _query_elements(self, data):
        """Wykonaj zapytanie XPath/CSS"""
        try:
            query = data['query']
            query_type = data.get('type', 'xpath')

            # Znajdź pierwszy załadowany plik
            if not self.editors:
                raise ValueError("No files loaded")

            editor = list(self.editors.values())[0]

            if query_type == 'xpath':
                elements = editor.list_elements(query)
            else:
                elements = editor.find_by_css(query)
                # Konwertuj wyniki CSS na format podobny do XPath
                elements = [{'tag': str(elem.name), 'text': elem.get_text(), 'attributes': elem.attrs}
                            for elem in elements]

            response = {
                'success': True,
                'elements': elements,
                'count': len(elements)
            }
        except Exception as e:
            response = {'success': False, 'error': str(e)}

        self._send_json_response(response)

    def _update_element(self, data):
        """Aktualizuj element"""
        try:
            xpath = data['xpath']
            update_type = data['type']
            value = data['value']

            if not self.editors:
                raise ValueError("No files loaded")

            editor = list(self.editors.values())[0]

            if update_type == 'text':
                success = editor.set_element_text(xpath, value)
            elif update_type == 'attribute':
                attribute = data['attribute']
                success = editor.set_element_attribute(xpath, attribute, value)
            else:
                raise ValueError(f"Unknown update type: {update_type}")

            response = {
                'success': success,
                'message': f'Element updated successfully' if success else 'Element not found'
            }
        except Exception as e:
            response = {'success': False, 'error': str(e)}

        self._send_json_response(response)

    def _save_file(self, data):
        """Zapisz plik"""
        try:
            output_path = data.get('output_path')

            if not self.editors:
                raise ValueError("No files loaded")

            editor = list(self.editors.values())[0]
            success = editor.save(output_path)

            response = {
                'success': success,
                'message': f'File saved successfully to {output_path or editor.file_path}'
            }
        except Exception as e:
            response = {'success': False, 'error': str(e)}

        self._send_json_response(response)

    def _extract_data_uri(self, data):
        """Wyciągnij Data URI z załadowanego pliku"""
        try:
            xpath = data['xpath']

            if not self.editors:
                raise ValueError("No files loaded")

            editor = list(self.editors.values())[0]
            result = editor.extract_data_uri(xpath)

            self._send_json_response(result)
        except Exception as e:
            self._send_json_response({'error': str(e)})

    def _send_response(self, status_code, content, content_type='text/plain'):
        """Wyślij odpowiedź HTTP"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def _send_json_response(self, data):
        """Wyślij odpowiedź JSON"""
        self._send_response(200, json.dumps(data, indent=2), 'application/json')

    def _send_error(self, status_code, message):
        """Wyślij błąd"""
        self._send_response(status_code, json.dumps({'error': message}), 'application/json')


class CLI:
    """Interfejs CLI"""

    def __init__(self):
        self.editor = None

    def run(self):
        """Uruchom CLI"""
        parser = argparse.ArgumentParser(description='Universal File Editor CLI')
        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Load command
        load_parser = subparsers.add_parser('load', help='Load file (local or remote)')
        load_parser.add_argument('file', help='File path or URL')

        # Query command
        query_parser = subparsers.add_parser('query', help='Query elements')
        query_parser.add_argument('xpath', help='XPath expression')
        query_parser.add_argument('--type', choices=['text', 'attribute'], default='text')
        query_parser.add_argument('--attr', help='Attribute name')

        # Set command
        set_parser = subparsers.add_parser('set', help='Set element value')
        set_parser.add_argument('xpath', help='XPath expression')
        set_parser.add_argument('value', help='New value')
        set_parser.add_argument('--type', choices=['text', 'attribute'], default='text')
        set_parser.add_argument('--attr', help='Attribute name')

        # Extract Data URI command
        extract_parser = subparsers.add_parser('extract', help='Extract Data URI from element')
        extract_parser.add_argument('xpath', help='XPath to element with Data URI')
        extract_parser.add_argument('--output', help='Save extracted data to file')
        extract_parser.add_argument('--info', action='store_true', help='Show Data URI info only')

        # List command
        list_parser = subparsers.add_parser('list', help='List elements')
        list_parser.add_argument('--xpath', default='//*', help='XPath filter')
        list_parser.add_argument('--limit', type=int, default=20, help='Limit results')

        # Save command
        save_parser = subparsers.add_parser('save', help='Save file')
        save_parser.add_argument('--output', help='Output file path')

        # Server command
        server_parser = subparsers.add_parser('server', help='Start HTTP server')
        server_parser.add_argument('--port', type=int, default=8080, help='Server port')
        server_parser.add_argument('--host', default='localhost', help='Server host')

        # Shell command
        shell_parser = subparsers.add_parser('shell', help='Interactive shell')

        # Create examples command
        examples_parser = subparsers.add_parser('examples', help='Create example files')
        examples_parser.add_argument('--dir', default='.', help='Directory to create examples')

        args = parser.parse_args()

        if args.command == 'server':
            self.start_server(args.host, args.port)
        elif args.command == 'shell':
            self.start_shell()
        elif args.command == 'examples':
            self.create_examples(args.dir)
        else:
            self.execute_command(args)

    def execute_command(self, args):
        """Wykonaj komendę CLI"""
        try:
            if args.command == 'load':
                self.editor = FileEditor(args.file)
                file_type = "remote" if args.file.startswith('http') else "local"
                print(f"✅ Loaded {file_type} file: {args.file} ({self.editor.file_type})")
                if LXML_AVAILABLE:
                    elements_count = len(self.editor.find_by_xpath("//*"))
                    print(f"   Found {elements_count} elements")

            elif args.command == 'query':
                if not self.editor:
                    print("❌ No file loaded. Use 'load' command first.")
                    return

                if args.type == 'text':
                    result = self.editor.get_element_text(args.xpath)
                    print(f"Text: {result}")
                elif args.type == 'attribute':
                    if not args.attr:
                        print("❌ --attr required for attribute queries")
                        return
                    result = self.editor.get_element_attribute(args.xpath, args.attr)
                    print(f"Attribute {args.attr}: {result}")

            elif args.command == 'extract':
                if not self.editor:
                    print("❌ No file loaded. Use 'load' command first.")
                    return

                if args.info:
                    # Tylko informacje o Data URI
                    result = self.editor.extract_data_uri(args.xpath)
                    if "error" in result:
                        print(f"❌ {result['error']}")
                    else:
                        print(f"✅ Data URI found:")
                        print(f"   MIME type: {result['mime_type']}")
                        print(f"   Size: {result['size']} bytes")
                        print(f"   Base64 length: {len(result['base64_data'])} chars")
                elif args.output:
                    # Zapisz do pliku
                    success = self.editor.save_data_uri_to_file(args.xpath, args.output)
                    if not success:
                        print("❌ Failed to extract and save Data URI")
                else:
                    # Wyświetl surowe dane
                    result = self.editor.extract_data_uri(args.xpath)
                    if "error" in result:
                        print(f"❌ {result['error']}")
                    else:
                        print(f"MIME: {result['mime_type']}")
                        print(f"Size: {result['size']} bytes")
                        print(f"Base64 data: {result['base64_data'][:100]}...")

            elif args.command == 'set':
                if not self.editor:
                    print("❌ No file loaded. Use 'load' command first.")
                    return

                if args.type == 'text':
                    success = self.editor.set_element_text(args.xpath, args.value)
                elif args.type == 'attribute':
                    if not args.attr:
                        print("❌ --attr required for attribute updates")
                        return
                    success = self.editor.set_element_attribute(args.xpath, args.attr, args.value)

                if success:
                    print("✅ Element updated")
                else:
                    print("❌ Element not found")

            elif args.command == 'list':
                if not self.editor:
                    print("❌ No file loaded. Use 'load' command first.")
                    return

                elements = self.editor.list_elements(args.xpath)
                if not elements:
                    print("No elements found")
                    return

                print(f"Found {len(elements)} elements:")
                for i, elem in enumerate(elements[:args.limit]):
                    print(f"\n{i + 1}. Path: {elem['path']}")
                    print(f"   Tag: {elem['tag']}")
                    if elem['text']:
                        text_preview = elem['text'][:100] + "..." if len(elem['text']) > 100 else elem['text']
                        print(f"   Text: {repr(text_preview)}")
                    if elem['attributes']:
                        print(f"   Attributes: {elem['attributes']}")

                if len(elements) > args.limit:
                    print(f"\n... and {len(elements) - args.limit} more (use --limit to see more)")

            elif args.command == 'save':
                if not self.editor:
                    print("❌ No file loaded. Use 'load' command first.")
                    return

                if self.editor.is_remote and not args.output:
                    print("❌ Remote file requires --output parameter")
                    return

                success = self.editor.save(args.output)
                if success:
                    save_path = args.output or self.editor.file_path
                    print(f"✅ File saved to {save_path}")
                else:
                    print("❌ Save failed")

        except Exception as e:
            print(f"❌ Error: {e}")

    def start_shell(self):
        """Uruchom interaktywny shell"""
        print("🚀 Interactive File Editor Shell")
        print("Commands:")
        print("  load <file>          - Load file (local path or URL)")
        print("  query <xpath>        - Query element text")
        print("  attr <xpath> <name>  - Get element attribute")
        print("  set <xpath> <value>  - Set element text")
        print("  setattr <xpath> <name> <value> - Set element attribute")
        print("  extract <xpath>      - Show Data URI info")
        print("  save [path]          - Save file")
        print("  list [xpath]         - List elements")
        print("  help                 - Show this help")
        print("  exit                 - Exit shell")
        print()

        while True:
            try:
                command_line = input("📝 > ").strip()
                if not command_line:
                    continue

                if command_line == 'exit':
                    break
                elif command_line == 'help':
                    print("Available commands: load, query, attr, set, setattr, extract, save, list, help, exit")
                    continue

                parts = command_line.split()
                command = parts[0]

                if command == 'load' and len(parts) == 2:
                    self.editor = FileEditor(parts[1])
                    file_type = "remote" if parts[1].startswith('http') else "local"
                    print(f"✅ Loaded {file_type} file ({self.editor.file_type})")

                elif command == 'query' and len(parts) >= 2:
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = ' '.join(parts[1:])
                    result = self.editor.get_element_text(xpath)
                    print(f"Result: {result}")

                elif command == 'attr' and len(parts) >= 3:
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = parts[1]
                    attr_name = parts[2]
                    result = self.editor.get_element_attribute(xpath, attr_name)
                    print(f"Attribute {attr_name}: {result}")

                elif command == 'set' and len(parts) >= 3:
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = parts[1]
                    value = ' '.join(parts[2:])
                    success = self.editor.set_element_text(xpath, value)
                    print("✅ Updated" if success else "❌ Not found")

                elif command == 'setattr' and len(parts) >= 4:
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = parts[1]
                    attr_name = parts[2]
                    attr_value = ' '.join(parts[3:])
                    success = self.editor.set_element_attribute(xpath, attr_name, attr_value)
                    print("✅ Updated" if success else "❌ Not found")

                elif command == 'extract' and len(parts) >= 2:
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = ' '.join(parts[1:])
                    result = self.editor.extract_data_uri(xpath)
                    if "error" in result:
                        print(f"❌ {result['error']}")
                    else:
                        print(f"✅ MIME: {result['mime_type']}, Size: {result['size']} bytes")

                elif command == 'list':
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = parts[1] if len(parts) > 1 else "//*"
                    elements = self.editor.list_elements(xpath)[:10]  # limit to 10
                    for elem in elements:
                        text_preview = elem['text'][:50] + "..." if len(elem['text']) > 50 else elem['text']
                        print(f"{elem['tag']}: {repr(text_preview)}")

                elif command == 'save':
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    output = parts[1] if len(parts) > 1 else None
                    if self.editor.is_remote and not output:
                        print("❌ Remote file requires output path")
                        continue
                    success = self.editor.save(output)
                    print("✅ Saved" if success else "❌ Save failed")

                else:
                    print("❌ Unknown command or wrong arguments. Type 'help' for available commands.")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def start_server(self, host, port):
        """Uruchom serwer HTTP"""
        print(f"🌐 Starting File Editor Server on {host}:{port}")
        print(f"Open http://{host}:{port} in your browser")
        print("API endpoints:")
        print(f"  GET  http://{host}:{port}/api/extract?url=<URL>&xpath=<XPATH>")
        print(f"  POST http://{host}:{port}/api/load")
        print(f"  POST http://{host}:{port}/api/query")
        print(f"  POST http://{host}:{port}/api/update")
        print(f"  POST http://{host}:{port}/api/save")
        print()

        server = HTTPServer((host, port), FileEditorServer)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

    def create_examples(self, directory):
        """Utwórz przykładowe pliki do testowania"""
        base_path = Path(directory)
        base_path.mkdir(exist_ok=True)

        # Przykładowy SVG z Data URI
        svg_with_data_uri = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="400" height="300">
    <metadata>
        {
            "title": "Example SVG with Data URI",
            "description": "Test file for editor",
            "author": "File Editor Tool"
        }
    </metadata>
    <rect x="10" y="10" width="50" height="50" fill="red" id="square1"/>
    <circle cx="100" cy="100" r="30" fill="blue" id="circle1"/>
    <text x="50" y="150" id="text1" font-size="16">Hello World</text>

    <!-- Embedded PDF as Data URI -->
    <image x="200" y="50" width="150" height="100" 
           xlink:href="data:application/pdf;base64,JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovUGFnZXMgMiAwIFIKPj4KZW5kb2JqCjIgMCBvYmoKPDwKL1R5cGUgL1BhZ2VzCi9LaWRzIFszIDAgUl0KL0NvdW50IDEKPD4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovTWVkaWFCb3ggWzAgMCA2MTIgNzkyXQovUmVzb3VyY2VzIDw8Ci9Gb250IDw8Ci9GMSA0IDAgUgo+Pgo+PgovQ29udGVudHMgNSAwIFIKPj4KZW5kb2JqCjQgMCBvYmoKPDwKL1R5cGUgL0ZvbnQKL1N1YnR5cGUgL1R5cGUxCi9CYXNlRm9udCAvSGVsdmV0aWNhCj4+CmVuZG9iago1IDAgb2JqCjw8Ci9MZW5ndGggNDQKPj4Kc3RyZWFtCkJUCi9GMSAxMiBUZgoxMDAgNzAwIFRkCihIZWxsbyBXb3JsZCEpIFRqCkVUCmVuZHN0cmVhbQplbmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMDExNSAwMDAwMCBuIAowMDAwMDAwMjQ1IDAwMDAwIG4gCjAwMDAwMDAzMTYgMDAwMDAgbiAKdHJhaWxlcgo8PAovU2l6ZSA2Ci9Sb290IDEgMCBSCj4+CnN0YXJ0eHJlZgo0MTAKJSVFT0Y=" />

    <!-- JSON data in foreignObject -->
    <foreignObject x="0" y="250" width="400" height="50">
        <script type="application/json">
        {
            "data": [10, 20, 30, 40],
            "labels": ["A", "B", "C", "D"],
            "config": {"type": "chart", "animated": true}
        }
        </script>
    </foreignObject>
</svg>'''

        # Przykładowy XML z danymi
        xml_with_data = '''<?xml version="1.0" encoding="UTF-8"?>
<data xmlns:xlink="http://www.w3.org/1999/xlink">
    <metadata>
        <title>Example Data XML</title>
        <version>1.0</version>
        <created>2025-01-01</created>
    </metadata>
    <records>
        <record id="1" type="user">
            <name>John Doe</name>
            <age>30</age>
            <email>john@example.com</email>
            <avatar xlink:href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" />
        </record>
        <record id="2" type="admin">
            <name>Jane Smith</name>
            <age>25</age>
            <email>jane@example.com</email>
            <settings>{"theme": "dark", "notifications": true}</settings>
        </record>
    </records>
    <files>
        <file name="document.pdf" 
              data="data:application/pdf;base64,JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovUGFnZXMgMiAwIFIKPj4KZW5kb2JqCjIgMCBvYmoKPDwKL1R5cGUgL1BhZ2VzCi9LaWRzIFszIDAgUl0KL0NvdW50IDEKPD4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovTWVkaWFCb3ggWzAgMCA2MTIgNzkyXQovUmVzb3VyY2VzIDw8Ci9Gb250IDw8Ci9GMSA0IDAgUgo+Pgo+PgovQ29udGVudHMgNSAwIFIKPj4KZW5kb2JqCjQgMCBvYmoKPDwKL1R5cGUgL0ZvbnQKL1N1YnR5cGUgL1R5cGUxCi9CYXNlRm9udCAvSGVsdmV0aWNhCj4+CmVuZG9iago1IDAgb2JqCjw8Ci9MZW5ndGggNDQKPj4Kc3RyZWFtCkJUCi9GMSAxMiBUZgoxMDAgNzAwIFRkCihIZWxsbyBXb3JsZCEpIFRqCkVUCmVuZHN0cmVhbQplbmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMDExNSAwMDAwMCBuIAowMDAwMDAwMjQ1IDAwMDAwIG4gCjAwMDAwMDAzMTYgMDAwMDAgbiAKdHJhaWxlcgo8PAovU2l6ZSA2Ci9Sb290IDEgMCBSCj4+CnN0YXJ0eHJlZgo0MTAKJSVFT0Y=" />
    </files>
</data>'''

        # Przykładowy HTML z osadzonym SVG
        html_with_svg = '''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Example HTML with embedded SVG</title>
    <meta name="description" content="Test HTML file with SVG and data">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .data-container { background: #f0f0f0; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1 id="main-title">Example HTML Document</h1>

    <div class="content">
        <p id="intro">This HTML contains embedded SVG with Data URI.</p>

        <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" 
             width="300" height="200" id="embedded-svg">
            <rect x="10" y="10" width="100" height="50" fill="green" />
            <text x="20" y="35" fill="white">Embedded SVG</text>
            <image x="150" y="20" width="100" height="60"
                   xlink:href="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjYwIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iNjAiIGZpbGw9InJlZCIvPjx0ZXh0IHg9IjEwIiB5PSIzNSIgZmlsbD0id2hpdGUiPkRhdGEgVVJJPC90ZXh0Pjwvc3ZnPg==" />
        </svg>

        <div class="data-container">
            <h3>JSON Data</h3>
            <script type="application/json" id="page-data">
            {
                "page": "example",
                "data": {
                    "users": [
                        {"id": 1, "name": "Alice"},
                        {"id": 2, "name": "Bob"}
                    ],
                    "settings": {
                        "theme": "light",
                        "language": "en"
                    }
                }
            }
            </script>
        </div>

        <ul>
            <li class="item" data-value="1">Item 1</li>
            <li class="item" data-value="2">Item 2</li>
            <li class="item" data-value="3">Item 3</li>
        </ul>
    </div>
</body>
</html>'''

        # Zapisz pliki
        files = [
            ('example.svg', svg_with_data_uri),
            ('example.xml', xml_with_data),
            ('example.html', html_with_svg)
        ]

        for filename, content in files:
            file_path = base_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Created: {file_path}")

        # Utwórz plik z przykładami użycia
        examples_usage = '''# File Editor Tool - Examples

## Example XPath queries for created files:

### example.svg:
- Get text content: `//svg:text[@id='text1']`
- Get image Data URI: `//svg:image/@xlink:href`
- Get JSON metadata: `//svg:metadata`
- Get all elements with fill attribute: `//*[@fill]`

### example.xml:
- Get user names: `//record[@type='user']/name`
- Get file Data URI: `//file[@name='document.pdf']/@data`
- Get user by ID: `//record[@id='1']`
- Get JSON settings: `//record[@id='2']/settings`

### example.html:
- Get page title: `//html:h1[@id='main-title']`
- Get embedded SVG Data URI: `//svg:image/@xlink:href`
- Get JSON data: `//script[@type='application/json']`
- Get list items: `//html:li[@class='item']`

## CLI Usage Examples:

```bash
# Load and explore SVG file
python file_editor.py load example.svg
python file_editor.py list --xpath "//svg:*"
python file_editor.py query "//svg:text[@id='text1']"

# Extract Data URI from SVG
python file_editor.py extract "//svg:image/@xlink:href" --info
python file_editor.py extract "//svg:image/@xlink:href" --output extracted.pdf

# Edit elements
python file_editor.py set "//svg:text[@id='text1']" "Modified Text"
python file_editor.py save --output modified.svg

# Work with remote files
python file_editor.py load "http://example.com/file.svg"
python file_editor.py extract "//svg:image/@xlink:href" --info

# Start server
python file_editor.py server --port 8080
# Then open http://localhost:8080 in browser
```

## Server API Examples:

```bash
# Extract Data URI from remote file
curl "http://localhost:8080/api/extract?url=http://example.com/file.svg&xpath=//svg:image/@xlink:href"

# Load file via POST
curl -X POST http://localhost:8080/api/load \\
  -H "Content-Type: application/json" \\
  -d '{"file_path": "example.svg"}'

# Query elements
curl -X POST http://localhost:8080/api/query \\
  -H "Content-Type: application/json" \\
  -d '{"query": "//svg:text", "type": "xpath"}'
```
'''

        usage_path = base_path / 'EXAMPLES.md'
        with open(usage_path, 'w', encoding='utf-8') as f:
            f.write(examples_usage)
        print(f"✅ Created: {usage_path}")

        print(f"\n🎉 Example files created in {base_path}")
        print("Use 'python file_editor.py examples --help' to see usage examples")


def main():
    """Główna funkcja"""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()