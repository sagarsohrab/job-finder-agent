import os
import json
import http.server
import socketserver
import threading
from urllib.parse import urlparse
from job_finder import main as run_job_finder_main

PORT = 8080
is_scraping = False

def background_scrape():
    global is_scraping
    is_scraping = True
    print("\n⚡ Live Market Scraper started on CPU thread...")
    try:
        run_job_finder_main()
        print("✅ Live Market Scrape completed and jobs_data.json updated!")
    except Exception as e:
        print(f"Error during live background scrape: {e}")
    finally:
        is_scraping = False

class CopilotRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/scrape":
            global is_scraping
            if not is_scraping:
                t = threading.Thread(target=background_scrape)
                t.daemon = True
                t.start()
                msg = "Live market scrape initiated on CPU!"
            else:
                msg = "Scraper is already running in background..."

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            response = {"status": "started", "message": msg}
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            super().do_GET()

def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CopilotRequestHandler) as httpd:
        print(f"Job Copilot Pro Server running at http://localhost:{PORT}")
        print("Listening for live scraper requests on /api/scrape...")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
