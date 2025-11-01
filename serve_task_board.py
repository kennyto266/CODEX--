#!/usr/bin/env python3
"""
Simple HTTP Server for Task Board
Serves the task board demo at http://localhost:8001
"""

import sys
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import threading
import time

class TaskBoardHandler(SimpleHTTPRequestHandler):
    """Custom handler for task board"""

    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=str(Path(__file__).parent / "src" / "dashboard" / "static"), **kwargs)

    def end_headers(self):
        # Add CORS headers to allow local file access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def log_message(self, format, *args):
        # Custom log format
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")


def open_browser(url, delay=2):
    """Open browser after a delay"""
    time.sleep(delay)
    print(f"\nOpening browser to {url}...")
    webbrowser.open(url)


def main():
    """Main function"""
    port = 8001
    host = 'localhost'

    print("\n" + "="*60)
    print("Task Board HTTP Server")
    print("="*60)

    # Check if task board demo exists
    demo_file = Path(__file__).parent / "src" / "dashboard" / "static" / "task-board-demo.html"
    if not demo_file.exists():
        print(f"\nERROR: Task board demo not found at {demo_file}")
        print("Please ensure the file exists.")
        return 1

    print(f"\nStarting server...")
    print(f"  - Port: {port}")
    print(f"  - Host: {host}")
    print(f"  - Directory: {demo_file.parent}")
    print(f"\nServer will be available at:")
    print(f"  http://{host}:{port}/task-board-demo.html")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    try:
        # Create server
        server = HTTPServer((host, port), TaskBoardHandler)

        # Start browser in a separate thread
        browser_thread = threading.Thread(
            target=open_browser,
            args=(f"http://{host}:{port}/task-board-demo.html",)
        )
        browser_thread.daemon = True
        browser_thread.start()

        # Start serving
        print(f"Server started successfully on http://{host}:{port}")
        print("Serving task board demo...\n")
        server.serve_forever()

    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.shutdown()
        print("Server stopped.")
        return 0
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"\nERROR: Port {port} is already in use.")
            print(f"Please either:")
            print(f"  1. Stop the process using port {port}")
            print(f"  2. Use a different port: python serve_task_board.py --port 8002")
            print(f"  3. Open the file directly in browser:")
            print(f"     file://{demo_file}")
        else:
            print(f"\nERROR: {e}")
        return 1


if __name__ == '__main__':
    # Check for custom port
    if '--port' in sys.argv:
        try:
            port_idx = sys.argv.index('--port')
            port = int(sys.argv[port_idx + 1])
        except (IndexError, ValueError):
            print("ERROR: Invalid port number")
            sys.exit(1)

    sys.exit(main())
