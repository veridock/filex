"""
HTTP Server for xsl - Web interface for remote file editing.
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict
from urllib.parse import parse_qs, urlparse

from . import __version__
from .editor import FileEditor


class FileEditorServer(BaseHTTPRequestHandler):
    """HTTP request handler for xsl server."""

    # Class variable to store loaded editors
    editors: Dict[str, FileEditor] = {}

    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        if path == '/':
            self._serve_interface()
        elif path == '/api/health':
            self._send_json_response({'status': 'ok', 'version': __version__})
        elif path == '/api/extract':
            # Direct extraction endpoint with URL + XPath
            self._extract_from_url(query)
        else:
            self._send_error(404, "Not Found")

    def do_POST(self):
        """Handle POST requests."""
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
        elif path == '/api/add':
            self._add_element(data)
        elif path == '/api/remove':
            self._remove_element(data)
        elif path == '/api/info':
            self._get_file_info(data)
        else:
            self._send_error(404, "Not Found")

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
    def _send_response(self, status_code, content, content_type='text/plain'):
        """Send HTTP response."""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def _send_json_response(self, data):
        """Send JSON response."""
        self._send_response(200, json.dumps(data, indent=2), 'application/json')

    def _send_error(self, status_code, message):
        """Send error response."""
        self._send_response(status_code, json.dumps({'error': message}), 'application/json')

    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"{self.address_string()} - {format % args}")


def start_server(host='localhost', port=8080):
    """Start the xsl HTTP server."""
    try:
        server = HTTPServer((host, port), FileEditorServer)
        print(f"🌐 xsl Server v{__version__} starting on {host}:{port}")
        print(f"📖 Open http://{host}:{port} in your browser")
        print("🔗 API endpoints:")
        print(f"   GET  http://{host}:{port}/api/extract?url=<URL>&xpath=<XPATH>")
        print(f"   POST http://{host}:{port}/api/load")
        print(f"   POST http://{host}:{port}/api/query")
        print(f"   POST http://{host}:{port}/api/update")
        print(f"   POST http://{host}:{port}/api/save")
        print("\n⏹️  Press Ctrl+C to stop the server")
        print("-" * 60)

        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


def main():
    """Entry point for xsl-server command."""
    parser = argparse.ArgumentParser(
        description='xsl HTTP Server - Web interface for file editing',
        epilog='Visit https://github.com/veridock/xsl for documentation'
    )
    parser.add_argument('--version', action='version', version=f'xsl Server {__version__}')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    start_server(args.host, args.port)


if __name__ == "__main__":
    main()

    def _extract_from_url(self, query):
        """Extract Data URI from URL using XPath (GET endpoint)."""
        try:
            url = query.get('url', [''])[0]
            xpath = query.get('xpath', [''])[0]

            if not url or not xpath:
                self._send_json_response({'error': 'Missing url or xpath parameter'})
                return

            # Load file from URL
            editor = FileEditor(url)

            # Extract Data URI
            result = editor.extract_data_uri(xpath)

            self._send_json_response(result)

        except Exception as e:
            self._send_json_response({'error': str(e)})

    def _serve_interface(self):
        """Serve the web interface."""
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>xsl Server v{__version__}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f5f7fa; line-height: 1.6;
        }}
        .container {{ 
            max-width: 1200px; margin: 0 auto; background: white; 
            border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); 
            overflow: hidden;
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; text-align: center;
        }}
        .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .tabs {{ 
            display: flex; border-bottom: 2px solid #e1e8ed;
            background: #fafbfc;
        }}
        .tab {{ 
            flex: 1; padding: 15px 20px; cursor: pointer; 
            border-bottom: 3px solid transparent; transition: all 0.3s;
            text-align: center; font-weight: 500;
        }}
        .tab:hover {{ background: #f0f3f6; }}
        .tab.active {{ 
            background: white; border-bottom-color: #667eea;
            color: #667eea;
        }}
        .tab-content {{ display: none; padding: 30px; }}
        .tab-content.active {{ display: block; }}
        .section {{ 
            margin: 25px 0; padding: 25px; 
            border: 1px solid #e1e8ed; border-radius: 8px; 
            background: #fafbfc;
        }}
        .section h3 {{ 
            margin: 0 0 20px 0; color: #2c3e50; 
            font-size: 1.3em; font-weight: 600;
        }}
        .form-group {{ margin: 15px 0; }}
        .form-group label {{ 
            display: block; margin-bottom: 5px; 
            font-weight: 500; color: #34495e;
        }}
        input, textarea, select {{ 
            width: 100%; padding: 12px; border: 2px solid #e1e8ed; 
            border-radius: 6px; font-size: 14px; transition: border-color 0.3s;
        }}
        input:focus, textarea:focus, select:focus {{ 
            outline: none; border-color: #667eea; 
        }}
        .input-group {{ display: flex; gap: 10px; }}
        .input-group > * {{ flex: 1; }}
        button {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; padding: 12px 24px; 
            border-radius: 6px; cursor: pointer; font-size: 14px;
            font-weight: 500; transition: transform 0.2s;
        }}
        button:hover {{ transform: translateY(-1px); }}
        button:active {{ transform: translateY(0); }}
        .result {{ 
            background: #f8f9fa; padding: 20px; margin: 20px 0; 
            border-radius: 6px; font-family: 'Monaco', 'Consolas', monospace; 
            white-space: pre-wrap; max-height: 400px; overflow-y: auto;
            border-left: 4px solid #6c757d;
        }}
        .result.success {{ 
            background: #d4edda; border-left-color: #28a745; 
            color: #155724;
        }}
        .result.error {{ 
            background: #f8d7da; border-left-color: #dc3545; 
            color: #721c24;
        }}
        .url-extractor {{ 
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            border: 2px solid #2196f3;
        }}
        .examples {{ 
            background: #fff3cd; border: 1px solid #ffc107; 
            border-radius: 6px; padding: 15px; margin: 20px 0;
        }}
        .examples h4 {{ margin: 0 0 10px 0; color: #856404; }}
        .examples code {{ 
            background: #fff; padding: 2px 6px; border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace; font-size: 12px;
        }}
        .feature-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px; margin: 30px 0;
        }}
        .feature-card {{ 
            background: white; padding: 20px; border-radius: 8px;
            border: 1px solid #e1e8ed; transition: transform 0.2s;
        }}
        .feature-card:hover {{ transform: translateY(-2px); }}
        .status-indicator {{ 
            display: inline-block; width: 10px; height: 10px; 
            border-radius: 50%; margin-right: 8px;
        }}
        .status-ok {{ background: #28a745; }}
        .status-error {{ background: #dc3545; }}
        @media (max-width: 768px) {{
            .container {{ margin: 10px; border-radius: 8px; }}
            .header {{ padding: 20px; }}
            .header h1 {{ font-size: 2em; }}
            .tab-content {{ padding: 20px; }}
            .input-group {{ flex-direction: column; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛠️ xsl Server</h1>
            <p>Universal File Editor for XML/SVG/HTML • Version {__version__}</p>
            <p><span class="status-indicator status-ok"></span>Server running and ready</p>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('local')">📁 Local Files</div>
            <div class="tab" onclick="showTab('remote')">🌐 URL Extraction</div>
            <div class="tab" onclick="showTab('api')">⚡ API Reference</div>
        </div>
        
        <div id="local" class="tab-content active">
            <div class="section">
                <h3>📂 Load File</h3>
                <div class="form-group">
                    <label for="filePath">File Path</label>
                    <input type="text" id="filePath" placeholder="Path to file (e.g., ./example.svg)" value="./example.svg">
                </div>
                <button onclick="loadFile()">Load File</button>
                <div id="loadResult" class="result"></div>
            </div>
            
            <div class="section">
                <h3>🔍 Query Elements</h3>
                <div class="input-group">
                    <div class="form-group">
                        <label for="query">XPath or CSS Selector</label>
                        <input type="text" id="query" placeholder="e.g., //svg:text[@id='title'] or .my-class">
                    </div>
                    <div class="form-group">
                        <label for="queryType">Query Type</label>
                        <select id="queryType">
                            <option value="xpath">XPath</option>
                            <option value="css">CSS Selector</option>
                        </select>
                    </div>
                </div>
                <button onclick="queryElements()">Execute Query</button>
                <div id="queryResult" class="result"></div>
            </div>
            
            <div class="section">
                <h3>✏️ Edit Elements</h3>
                <div class="input-group">
                    <div class="form-group">
                        <label for="updateXPath">XPath to Element</label>
                        <input type="text" id="updateXPath" placeholder="XPath to element to modify">
                    </div>
                    <div class="form-group">
                        <label for="updateType">Update Type</label>
                        <select id="updateType">
                            <option value="text">Text Content</option>
                            <option value="attribute">Attribute</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label for="attributeName">Attribute Name (if attribute type)</label>
                    <input type="text" id="attributeName" placeholder="e.g., fill, href, id">
                </div>
                <div class="form-group">
                    <label for="newValue">New Value</label>
                    <textarea id="newValue" rows="3" placeholder="Enter new value here"></textarea>
                </div>
                <button onclick="updateElement()">Update Element</button>
                <div id="updateResult" class="result"></div>
            </div>
            
            <div class="section">
                <h3>💾 Save Changes</h3>
                <div class="form-group">
                    <label for="savePath">Output Path (leave empty to overwrite)</label>
                    <input type="text" id="savePath" placeholder="e.g., ./modified.svg">
                </div>
                <button onclick="saveFile()">Save File</button>
                <div id="saveResult" class="result"></div>
            </div>
        </div>
        
        <div id="remote" class="tab-content">
            <div class="section url-extractor">
                <h3>🌐 Extract Data URI from URL</h3>
                <p>Fetch remote SVG/XML files and extract embedded Data URIs using XPath</p>
                <div class="form-group">
                    <label for="remoteUrl">File URL</label>
                    <input type="text" id="remoteUrl" placeholder="https://example.com/diagram.svg">
                </div>
                <div class="form-group">
                    <label for="remoteXPath">XPath Expression</label>
                    <input type="text" id="remoteXPath" placeholder="//svg:image/@xlink:href">
                </div>
                <button onclick="extractFromUrl()">Extract Data URI</button>
                <div id="extractResult" class="result"></div>
            </div>
            
            <div class="examples">
                <h4>📋 Common XPath Examples</h4>
                <p><strong>SVG Data URIs:</strong></p>
                <ul>
                    <li><code>//svg:image/@xlink:href</code> - Image href attribute</li>
                    <li><code>//*[contains(@href,'data:')]/@href</code> - Any href with data:</li>
                    <li><code>//svg:object/@data</code> - Object data attribute</li>
                </ul>
                <p><strong>XML Data:</strong></p>
                <ul>
                    <li><code>//file[@name='document.pdf']/@data</code> - PDF data by filename</li>
                    <li><code>//record[@type='user']/avatar/@src</code> - User avatar data</li>
                </ul>
            </div>
        </div>
        
        <div id="api" class="tab-content">
            <div class="feature-grid">
                <div class="feature-card">
                    <h4>🔗 API Endpoints</h4>
                    <p><strong>GET</strong> <code>/api/health</code><br>Server status</p>
                    <p><strong>GET</strong> <code>/api/extract?url=&xpath=</code><br>Direct Data URI extraction</p>
                    <p><strong>POST</strong> <code>/api/load</code><br>Load file for editing</p>
                    <p><strong>POST</strong> <code>/api/query</code><br>Query elements</p>
                    <p><strong>POST</strong> <code>/api/update</code><br>Update elements</p>
                    <p><strong>POST</strong> <code>/api/save</code><br>Save changes</p>
                </div>
                
                <div class="feature-card">
                    <h4>📝 Example cURL Commands</h4>
                    <p><strong>Extract Data URI:</strong></p>
                    <code>curl "http://localhost:8080/api/extract?url=example.svg&xpath=//svg:image/@href"</code>
                    
                    <p><strong>Load File:</strong></p>
                    <code>curl -X POST -H "Content-Type: application/json" -d '{{"file_path":"example.svg"}}' http://localhost:8080/api/load</code>
                </div>
                
                <div class="feature-card">
                    <h4>🐍 Python Client Example</h4>
                    <pre><code>import requests

# Extract Data URI
r = requests.get('http://localhost:8080/api/extract', 
    params={{'url': 'file.svg', 'xpath': '//svg:image/@href'}})
print(r.json())

# Load and query
requests.post('http://localhost:8080/api/load', 
    json={{'file_path': 'example.svg'}})
    
r = requests.post('http://localhost:8080/api/query',
    json={{'query': '//svg:text', 'type': 'xpath'}})
print(r.json())</code></pre>
                </div>
                
                <div class="feature-card">
                    <h4>🚀 CLI Integration</h4>
                    <p>Use xsl CLI alongside the server:</p>
                    <pre><code># Start server
xsl server --port 8080

# Use CLI separately
xsl load example.svg
xsl extract "//svg:image/@href" --output doc.pdf
xsl save --output modified.svg</code></pre>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {{
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}
        
        async function apiCall(endpoint, data) {{
            try {{
                const response = await fetch(endpoint, {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                return await response.json();
            }} catch (error) {{
                return {{success: false, error: error.message}};
            }}
        }}
        
        async function extractFromUrl() {{
            const url = document.getElementById('remoteUrl').value;
            const xpath = document.getElementById('remoteXPath').value;
            
            if (!url || !xpath) {{
                document.getElementById('extractResult').textContent = 'Please provide both URL and XPath';
                document.getElementById('extractResult').className = 'result error';
                return;
            }}
            
            try {{
                const response = await fetch(`/api/extract?url=${{encodeURIComponent(url)}}&xpath=${{encodeURIComponent(xpath)}}`);
                const result = await response.json();
                
                document.getElementById('extractResult').textContent = JSON.stringify(result, null, 2);
                document.getElementById('extractResult').className = 'result ' + (result.error ? 'error' : 'success');
            }} catch (error) {{
                document.getElementById('extractResult').textContent = 'Error: ' + error.message;
                document.getElementById('extractResult').className = 'result error';
            }}
        }}
        
        async function loadFile() {{
            const filePath = document.getElementById('filePath').value;
            const result = await apiCall('/api/load', {{file_path: filePath}});
            document.getElementById('loadResult').textContent = JSON.stringify(result, null, 2);
            document.getElementById('loadResult').className = 'result ' + (result.success ? 'success' : 'error');
        }}
        
        async function queryElements() {{
            const query = document.getElementById('query').value;
            const queryType = document.getElementById('queryType').value;
            const result = await apiCall('/api/query', {{query, type: queryType}});
            document.getElementById('queryResult').textContent = JSON.stringify(result, null, 2);
            document.getElementById('queryResult').className = 'result ' + (result.success ? 'success' : 'error');
        }}
        
        async function updateElement() {{
            const xpath = document.getElementById('updateXPath').value;
            const updateType = document.getElementById('updateType').value;
            const attributeName = document.getElementById('attributeName').value;
            const newValue = document.getElementById('newValue').value;
            
            const data = {{xpath, type: updateType, value: newValue}};
            if (updateType === 'attribute') {{
                data.attribute = attributeName;
            }}
            
            const result = await apiCall('/api/update', data);
            document.getElementById('updateResult').textContent = JSON.stringify(result, null, 2);
            document.getElementById('updateResult').className = 'result ' + (result.success ? 'success' : 'error');
        }}
        
        async function saveFile() {{
            const savePath = document.getElementById('savePath').value;
            const result = await apiCall('/api/save', {{output_path: savePath || null}});
            document.getElementById('saveResult').textContent = JSON.stringify(result, null, 2);
            document.getElementById('saveResult').className = 'result ' + (result.success ? 'success' : 'error');
        }}
        
        // Auto-clear results after 10 seconds
        function autoClearResult(elementId) {{
            setTimeout(() => {{
                const elem = document.getElementById(elementId);
                if (elem && elem.textContent) {{
                    elem.style.opacity = '0.5';
                }}
            }}, 10000);
        }}
        
        // Add auto-clear to all API calls
        document.addEventListener('DOMContentLoaded', function() {{
            const observer = new MutationObserver(function(mutations) {{
                mutations.forEach(function(mutation) {{
                    if (mutation.target.className.includes('result')) {{
                        autoClearResult(mutation.target.id);
                    }}
                }});
            }});
            
            document.querySelectorAll('.result').forEach(elem => {{
                observer.observe(elem, {{attributes: true, attributeFilter: ['class']}});
            }});
        }});
    </script>
</body>
</html>'''
        self._send_response(200, html, 'text/html')

    def _load_file(self, data):
        """Load file for editing."""
        try:
            file_path = data['file_path']
            editor = FileEditor(file_path)
            self.editors[file_path] = editor

            info = editor.get_info()
            response = {
                'success': True,
                'message': f'File loaded: {file_path}',
                'file_info': info
            }
        except Exception as e:
            response = {'success': False, 'error': str(e)}

        self._send_json_response(response)

    def _query_elements(self, data):
        """Execute XPath/CSS query."""
        try:
            query = data['query']
            query_type = data.get('type', 'xpath')

            if not self.editors:
                raise ValueError("No files loaded")

            editor = list(self.editors.values())[0]

            if query_type == 'xpath':
                elements = editor.list_elements(query)
            else:
                elements = editor.find_by_css(query)
                # Convert CSS results to XPath-like format
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
        """Update element content or attributes."""
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
        """Save file changes."""
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
        """Extract Data URI from loaded file."""
        try:
            xpath = data['xpath']

            if not self.editors:
                raise ValueError("No files loaded")

            editor = list(self.editors.values())[0]
            result = editor.extract_data_uri(xpath)

            self._send_json_response(result)
        except Exception as e:
            self._send_json_response({'error': str(e)})

    def _add_element(self, data):
        """Add new element."""
        try:
            parent_xpath = data['parent_xpath']
            tag_name = data['tag']
            text = data.get('text', '')
            attributes = data.get('attributes', {})

            if not self.editors:
                raise ValueError("No files loaded")

            editor = list(self.editors.values())[0]
            success = editor.add_element(parent_xpath, tag_name, text, attributes)

            response = {
                'success': success,
                'message': f'Element added successfully' if success else 'Parent element not found'
            }
        except Exception as e:
            response = {'success': False, 'error': str(e)}

        self._send_json_response(response)

    def _remove_element(self, data):
        """Remove element."""
        try:
            xpath = data['xpath']

            if not self.editors:
                raise ValueError("No files loaded")

            editor = list(self.editors.values())[0]
            success = editor.remove_element(xpath)

            response = {
                'success': success,
                'message': f'Element removed successfully' if success else 'Element not found'
            }
        except Exception as e:
            response = {'success': False, 'error': str(e)}

        self._send_json_response(response)

    def _get_file_info(self, data):
        """Get information about loaded file."""
        try:
            if not self.editors:
                raise ValueError("No files loaded")

            editor = list(self.editors.values())[0]
            info = editor.get_info()

            response = {
                'success': True,
                'info': info
            }
        except Exception as e:
            response = {'success': False, 'error': str(e)}

        self._send_json_response(response)

    def _send_response(self, status_code, content, content_type='text/plain'):
        """Send HTTP response."""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access