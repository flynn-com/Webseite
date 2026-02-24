import http.server
import socketserver
import json
import base64
import os
import re
import uuid
import webbrowser
import threading
import time

PORT = 8080
DIRECTORY = "."

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Force the browser to never cache files from this local server
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_POST(self):
        if self.path == '/api/save_all':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                projects = json.loads(post_data.decode('utf-8'))
                
                # Make sure assets directory exists
                os.makedirs(os.path.join('assets', 'projects'), exist_ok=True)
                
                # Process images
                for p in projects:
                    p = self.process_project_images(p)
                
                # Save to data.js
                with open('data.js', 'w', encoding='utf-8') as f:
                    js_content = "// Initial Project Data\n"
                    js_content += "const initialProjects = " + json.dumps(projects, indent=4) + ";\n\n"
                    js_content += "// Export initial data for seeding\n"
                    js_content += "window.initialProjects = initialProjects;\n"
                    f.write(js_content)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def process_project_images(self, p):
        # Handle companyLogo
        if p.get('companyLogo') and p['companyLogo'].startswith('data:image'):
            p['companyLogo'] = self.save_base64_image(p['companyLogo'])
            
        # Handle gallery
        if p.get('gallery'):
            new_gallery = []
            for img in p['gallery']:
                if img.startswith('data:image'):
                    new_gallery.append(self.save_base64_image(img))
                else:
                    new_gallery.append(img)
            p['gallery'] = new_gallery
            
        return p

    def save_base64_image(self, data_uri):
        # Format: data:image/jpeg;base64,/9j/4AA...
        match = re.match(r'data:image/(?P<ext>[a-zA-Z0-9]+);base64,(?P<data>.+)', data_uri)
        if not match:
            return data_uri
        
        ext = match.group('ext')
        if ext == 'jpeg':
            ext = 'jpg'
        
        b64_data = match.group('data')
        image_data = base64.b64decode(b64_data)
        
        filename = f"img_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join('assets', 'projects', filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
            
        return filepath.replace('\\', '/') # Ensure browser-friendly forward slashes

def open_browser():
    time.sleep(1) # Wait a second for the server to start
    webbrowser.open(f'http://localhost:{PORT}/admin.html')

if __name__ == "__main__":
    Handler.protocol_version = "HTTP/1.0"
    
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
        
    with ReusableTCPServer(("", PORT), Handler) as httpd:
        print(f"Local Admin Server started at http://localhost:{PORT}")
        print("Opening browser...")
        
        # Start a thread to open the browser
        threading.Thread(target=open_browser, daemon=True).start()
        
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        print("\nServer stopped.")
