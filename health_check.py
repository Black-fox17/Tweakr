import http.server
import socketserver
import os
import threading
import time
import subprocess
import signal
import sys

# Global variable to store the Streamlit process
streamlit_process = None

def run_health_check_server():
    """Run a simple HTTP server on port 5000 to respond to health checks"""
    class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")
    
    with socketserver.TCPServer(("0.0.0.0", 5000), HealthCheckHandler) as httpd:
        print("Health check server started on port 5000")
        httpd.serve_forever()

def run_streamlit():
    """Run the Streamlit app"""
    global streamlit_process
    streamlit_process = subprocess.Popen(
        ["streamlit", "run", "app/main.py", "--server.port=5000", "--server.address=0.0.0.0"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Print Streamlit output
    for line in streamlit_process.stdout:
        print(line.decode().strip())
    
    # Wait for the process to complete
    streamlit_process.wait()

def signal_handler(sig, frame):
    """Handle termination signals"""
    print("Shutting down...")
    if streamlit_process:
        streamlit_process.terminate()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the health check server in a separate thread
    health_check_thread = threading.Thread(target=run_health_check_server)
    health_check_thread.daemon = True
    health_check_thread.start()
    
    # Give the health check server time to start
    time.sleep(1)
    
    # Start Streamlit
    run_streamlit() 