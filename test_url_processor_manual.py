import asyncio
from src.processors.url_processor import URLProcessor
import os
import http.server
import socketserver
import threading
import time
import webbrowser

def start_http_server():
    # Set up a simple HTTP server
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", 8000), Handler)
    print("Serving at port 8000...")
    httpd.serve_forever()

async def main():
    # Start HTTP server in a separate thread
    server_thread = threading.Thread(target=start_http_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait a moment for the server to start
    time.sleep(1)
    
    # Create an instance of URLProcessor
    processor = URLProcessor()
    
    try:
        # Use localhost URL instead of file://
        url = "http://localhost:8000/test.html"
        print(f"Processing URL: {url}")
        charts = await processor.extract_charts(url)
        
        # Print results
        print(f"\nFound {len(charts)} charts:")
        for i, chart in enumerate(charts, 1):
            print(f"\nChart {i}:")
            print(f"URL: {chart['url']}")
            print(f"Caption: {chart.get('caption', 'No caption')}")
            print(f"Alt text: {chart.get('alt_text', 'No alt text')}")
            print(f"Image data size: {len(chart['image_data'])} bytes")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # The server will be automatically stopped when the script ends
        # because it's running in a daemon thread
        pass

if __name__ == "__main__":
    asyncio.run(main()) 