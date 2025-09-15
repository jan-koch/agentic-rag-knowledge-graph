#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend applications for testing.
Run this script to test the frontend implementations locally.
"""

import http.server
import socketserver
import os
import sys
import webbrowser
from pathlib import Path

def main():
    # Change to frontend directory
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    PORT = 3000
    
    # Try to find an available port
    for port in range(3000, 3010):
        try:
            with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
                PORT = port
                break
        except OSError:
            continue
    else:
        print("Could not find an available port in range 3000-3009")
        sys.exit(1)
    
    print(f"Starting HTTP server on port {PORT}")
    print(f"Frontend directory: {frontend_dir.absolute()}")
    print()
    print("Available applications:")
    print(f"  📱 Standalone Chat App: http://localhost:{PORT}/app/")
    print(f"  🔗 Embeddable Widget Demo: http://localhost:{PORT}/widget/example.html")
    print()
    print("Make sure your Agentic RAG API is running on http://localhost:8058")
    print("Press Ctrl+C to stop the server")
    print()
    
    # Start server
    try:
        with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
            # Open browser to main page
            webbrowser.open(f"http://localhost:{PORT}/app/")
            
            print(f"Server running at http://localhost:{PORT}/")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()