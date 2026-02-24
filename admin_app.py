import sys
import os
import threading
import http.server
import socketserver
import json
import base64
import re
import uuid
import subprocess
from PyQt6.QtCore import QUrl, QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView

PORT = 8080
DIRECTORY = "."

# ----------------------------------------------------
# 1. LOCAL PYTHON BACKEND SERVER
# ----------------------------------------------------
class AdminHandler(http.server.SimpleHTTPRequestHandler):
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
            self.handle_save()
        elif self.path == '/api/deploy':
            self.handle_deploy()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_save(self):
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
            
            self.send_json_response({"status": "success"})
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)

    def handle_deploy(self):
        """Executes git add, commit, push"""
        try:
            # Check if git exists
            subprocess.run(["git", "--version"], check=True, capture_output=True, text=True)
            
            # Git add
            subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
            
            # Git commit
            # We ignore the error if there's nothing to commit
            subprocess.run(["git", "commit", "-m", "Auto-Deploy from Admin App"], capture_output=True, text=True)
            
            # Git push
            result = subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True, text=True)
            
            self.send_json_response({"status": "success", "message": "Erfolgreich hochgeladen!\nIn 1-2 Minuten ist deine Website online."})
        except subprocess.CalledProcessError as e:
            error_msg = f"Git Error (Exit Code {e.returncode}):\n{e.stderr or e.stdout}"
            self.send_json_response({"error": error_msg}, 500)
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

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
            
        return filepath.replace('\\', '/')

class ServerThread(QThread):
    def run(self):
        AdminHandler.protocol_version = "HTTP/1.0"
        
        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True
            
        with ReusableTCPServer(("", PORT), AdminHandler) as httpd:
            print(f"Backend listening on port {PORT}")
            self.httpd = httpd
            httpd.serve_forever()
            
    def stop(self):
        if hasattr(self, 'httpd'):
            self.httpd.shutdown()

# ----------------------------------------------------
# 2. DESKTOP GUI
# ----------------------------------------------------
class AdminApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle(".FLYNN | Admin Center")
        self.resize(1200, 800)
        
        # Determine center of screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

        # Main Widget & Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Chromium Webkit Engine
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(f"http://localhost:{PORT}/admin.html"))
        
        layout.addWidget(self.browser)
        
        # Start Server
        self.server_thread = ServerThread()
        self.server_thread.start()

    def closeEvent(self, event):
        # Stop Server when window closes
        self.server_thread.stop()
        self.server_thread.wait()
        event.accept()

if __name__ == '__main__':
    # Add Git context to PATH if it's the standard Windows installation
    # because subprocess.run might not find it otherwise
    git_path = r"C:\Program Files\Git\cmd"
    if os.path.exists(git_path) and git_path not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + git_path

    app = QApplication(sys.argv)
    window = AdminApp()
    window.show()
    sys.exit(app.exec())
