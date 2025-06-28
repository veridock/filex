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

        if path == "/":
            self._serve_interface()
        elif path == "/api/health":
            self._send_json_response({"status": "ok", "version": __version__})
        elif path == "/api/extract":
            # Direct extraction endpoint with URL + XPath
            self._extract_from_url(query)
        else:
            self._send_error(404, "Not Found")

    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(post_data)
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/api/load":
            self._load_file(data)
        elif path == "/api/query":
            self._query_elements(data)
        elif path == "/api/update":
            self._update_element(data)
        elif path == "/api/save":
            self._save_file(data)
        elif path == "/api/extract_data_uri":
            self._extract_data_uri(data)
        elif path == "/api/add":
            self._add_element(data)
        elif path == "/api/remove":
            self._remove_element(data)
        elif path == "/api/info":
            self._get_file_info(data)
        else:
            self._send_error(404, "Not Found")

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_response(self, status_code, content, content_type="text/plain"):
        """Send HTTP response."""
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(
            content.encode("utf-8") if isinstance(content, str) else content
        )

    def _send_json_response(self, data):
        """Send JSON response."""
        self._send_response(200, json.dumps(data, indent=2), "application/json")

    def _send_error(self, status_code, message):
        """Send error response."""
        self._send_response(
            status_code, json.dumps({"error": message}), "application/json"
        )

    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"{self.address_string()} - {format % args}")


def start_server(host="localhost", port=8080):
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


def main(args: list = None) -> int:
    """Entry point for xsl-server command.
    
    Args:
        args: Command line arguments (default: None, uses sys.argv[1:])
        
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(description="Start xsl HTTP server")
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind to (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8082,
        help="Port to listen on (default: 8082)",
    )
    args = parser.parse_args(args)

    print(f"Starting xsl server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")

    try:
        start_server(host=args.host, port=args.port)
        return 0
    except KeyboardInterrupt:
        print("\nServer stopped")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    main()
