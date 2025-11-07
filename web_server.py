"""Simple HTTP server for hosting generated images"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import logging
import threading

logger = logging.getLogger(__name__)


class ImageHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP request handler that serves files from the output directory"""

    def __init__(self, *args, directory=None, **kwargs):
        """
        Initialize the request handler

        Args:
            directory: Directory to serve files from
        """
        self.directory = directory
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr"""
        logger.info(f"{self.address_string()} - {format % args}")


class WebServer:
    """HTTP server for hosting generated images"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080, directory: str = "output"):
        """
        Initialize the web server

        Args:
            host: Host address to bind to
            port: Port to listen on
            directory: Directory to serve files from
        """
        self.host = host
        self.port = port
        self.directory = os.path.abspath(directory)
        self.server = None
        self.thread = None

        # Create directory if it doesn't exist
        os.makedirs(self.directory, exist_ok=True)

    def start(self):
        """Start the web server in a background thread"""
        if self.thread and self.thread.is_alive():
            logger.warning("Server is already running")
            return

        def run_server():
            """Run the server"""
            handler = lambda *args, **kwargs: ImageHTTPRequestHandler(
                *args, directory=self.directory, **kwargs
            )
            self.server = HTTPServer((self.host, self.port), handler)
            logger.info(f"Server started at http://{self.host}:{self.port}")
            logger.info(f"Serving files from: {self.directory}")
            self.server.serve_forever()

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        logger.info("Server thread started")

    def stop(self):
        """Stop the web server"""
        if self.server:
            logger.info("Stopping server...")
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            logger.info("Server stopped")

    def is_running(self) -> bool:
        """
        Check if the server is running

        Returns:
            True if server is running, False otherwise
        """
        return self.thread is not None and self.thread.is_alive()
