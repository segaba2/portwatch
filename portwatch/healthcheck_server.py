"""Tiny HTTP server that exposes the /health endpoint."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from portwatch.healthcheck import get_health


class _HealthHandler(BaseHTTPRequestHandler):
    """Minimal request handler — only GET /health is supported."""

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            body = get_health().as_json().encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: D401
        """Suppress default access log output."""


_server: Optional[HTTPServer] = None
_thread: Optional[threading.Thread] = None


def start_healthcheck_server(host: str = "127.0.0.1", port: int = 9090) -> HTTPServer:
    """Start the health-check HTTP server in a daemon thread.

    Returns the HTTPServer instance so callers can shut it down cleanly.
    """
    global _server, _thread
    _server = HTTPServer((host, port), _HealthHandler)
    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    return _server


def stop_healthcheck_server() -> None:
    """Shut down the health-check server if it is running."""
    global _server, _thread
    if _server is not None:
        _server.shutdown()
        _server = None
    if _thread is not None:
        _thread.join(timeout=5)
        _thread = None
