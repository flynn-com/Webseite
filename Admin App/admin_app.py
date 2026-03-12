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

# Fix paths for new structure
ORIGINAL_DIR = os.path.dirname(os.path.abspath(__file__))
WEBSITE_DIR = os.path.join(ORIGINAL_DIR, '..', 'Website')
os.chdir(WEBSITE_DIR)

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

    def do_GET(self):
        if self.path == '/admin.html':
            admin_path = os.path.join(ORIGINAL_DIR, 'admin.html')
            with open(admin_path, 'rb') as f:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f.read())
            return
        elif self.path == '/api/get_legal':
            self.handle_get_legal()
        elif self.path == '/api/get_texts':
            self.handle_get_texts()
        elif self.path == '/api/get_about':
            self.handle_get_about()
        elif self.path == '/api/get_background':
            self.handle_get_background()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/save_all':
            self.handle_save()
        elif self.path == '/api/deploy':
            self.handle_deploy()
        elif self.path == '/api/save_legal':
            self.handle_save_legal()
        elif self.path == '/api/save_texts':
            self.handle_save_texts()
        elif self.path == '/api/save_about_photo':
            self.handle_save_about_photo()
        elif self.path == '/api/save_about_texts':
            self.handle_save_about_texts()
        elif self.path == '/api/save_background':
            self.handle_save_background()
        elif self.path == '/api/delete_background':
            self.handle_delete_background()
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

    def handle_get_about(self):
        """Read current about page data from about.html and about_data.js"""
        import re
        try:
            # Read text markers from about.html
            with open('about.html', 'r', encoding='utf-8') as f:
                html = f.read()
            def get_txt(key):
                m = re.search(r'<!-- TXT:' + key + r' -->(.*?)<!-- /TXT:' + key + r' -->', html, re.DOTALL)
                return m.group(1).strip() if m else ''

            # Read skills from about_data.js
            skills = ''
            try:
                with open('about_data.js', 'r', encoding='utf-8') as f:
                    js = f.read()
                sm = re.search(r"var ABOUT_SKILLS\s*=\s*'([^']*?)'", js)
                if sm: skills = sm.group(1)
            except: pass

            # Read photo path from about_data.js
            photo = ''
            try:
                with open('about_data.js', 'r', encoding='utf-8') as f:
                    js = f.read()
                pm = re.search(r"var ABOUT_PHOTO\s*=\s*'([^']*?)'", js)
                if pm: photo = pm.group(1)
            except: pass

            self.send_json_response({
                'name':   get_txt('ABOUT_NAME'),
                'role':   get_txt('ABOUT_ROLE'),
                'bio':    get_txt('ABOUT_BIO'),
                'skills': skills,
                'photo':  photo,
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def handle_save_about_photo(self):
        """Save base64 profile photo to assets/profile/profile.jpg and update about_data.js"""
        import base64, os, re
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))
            b64  = data.get('photo', '')
            if not b64 or ',' not in b64:
                raise ValueError('Invalid image data')
            header, encoded = b64.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            os.makedirs('assets/profile', exist_ok=True)
            img_path = 'assets/profile/profile.jpg'
            with open(img_path, 'wb') as f:
                f.write(img_bytes)
            # Update about_data.js
            js_path = 'assets/profile/profile.jpg'
            with open('about_data.js', 'r', encoding='utf-8') as f:
                js = f.read()
            js = re.sub(r"var ABOUT_PHOTO\s*=.*?;", f"var ABOUT_PHOTO  = '{js_path}';", js)
            with open('about_data.js', 'w', encoding='utf-8') as f:
                f.write(js)
            self.send_json_response({'status': 'success', 'path': js_path})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def handle_save_about_texts(self):
        """Write TXT markers for about page into about.html"""
        import re
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))
            with open('about.html', 'r', encoding='utf-8') as f:
                html = f.read()
            mapping = {
                'ABOUT_NAME': data.get('name', ''),
                'ABOUT_ROLE': data.get('role', ''),
                'ABOUT_BIO':  data.get('bio',  ''),
            }
            for key, value in mapping.items():
                if value:
                    html = re.sub(
                        r'<!-- TXT:' + key + r' -->.*?<!-- /TXT:' + key + r' -->',
                        f'<!-- TXT:{key} -->{value}<!-- /TXT:{key} -->',
                        html, flags=re.DOTALL)
            with open('about.html', 'w', encoding='utf-8') as f:
                f.write(html)
            # Update skills in about_data.js
            if 'skills' in data:
                with open('about_data.js', 'r', encoding='utf-8') as f:
                    js = f.read()
                js = re.sub(r"var ABOUT_SKILLS\s*=.*?;", f"var ABOUT_SKILLS = '{data['skills'].strip()}';", js)
                with open('about_data.js', 'w', encoding='utf-8') as f:
                    f.write(js)
            self.send_json_response({'status': 'success'})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)


    def handle_get_background(self):
        """Return whether the background image exists and its path"""
        bg_path = os.path.join('Bilder', 'background.png')
        exists = os.path.isfile(bg_path)
        self.send_json_response({'exists': exists, 'path': bg_path.replace('\\', '/') if exists else ''})

    def handle_save_background(self):
        """Save uploaded background image as Bilder/background.png"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))
            b64 = data.get('image', '')
            if not b64 or ',' not in b64:
                raise ValueError('Ungueltige Bilddaten')
            header, encoded = b64.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            os.makedirs('Bilder', exist_ok=True)
            with open(os.path.join('Bilder', 'background.png'), 'wb') as f:
                f.write(img_bytes)
            self.send_json_response({'status': 'success'})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def handle_delete_background(self):
        """Delete the background image"""
        try:
            bg_path = os.path.join('Bilder', 'background.png')
            if os.path.isfile(bg_path):
                os.remove(bg_path)
            self.send_json_response({'status': 'success'})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def handle_get_texts(self):
        """Read all TXT: marker values from index.html"""
        import re
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read()

            txt_keys = [
                'CORNER_TL', 'CORNER_TR', 'CORNER_BL', 'CORNER_BR',
                'FOOTER_BRAND', 'FOOTER_TAGLINE', 'FOOTER_COPY'
            ]
            data = {}
            for key in txt_keys:
                m = re.search(
                    r'<!-- TXT:' + key + r' -->(.*?)<!-- /TXT:' + key + r' -->',
                    content, re.DOTALL)
                data[key] = m.group(1).strip() if m else ''
            self.send_json_response(data)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def handle_save_texts(self):
        """Write TXT: marker values into index.html and single_project.html"""
        import re
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))

            # Keys only in index.html (landing page)
            index_only_keys = ['CORNER_TL', 'CORNER_TR', 'CORNER_BL', 'CORNER_BR']
            # Keys in both files (footer)
            both_keys = ['FOOTER_BRAND', 'FOOTER_TAGLINE', 'FOOTER_COPY']

            def patch_file(filename, keys):
                with open(filename, 'r', encoding='utf-8') as f:
                    html = f.read()
                for key in keys:
                    if key in data:
                        value = data[key].strip()
                        html = re.sub(
                            r'<!-- TXT:' + key + r' -->.*?<!-- /TXT:' + key + r' -->',
                            f'<!-- TXT:{key} -->{value}<!-- /TXT:{key} -->',
                            html, flags=re.DOTALL)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html)

            patch_file('index.html', index_only_keys + both_keys)
            patch_file('single_project.html', both_keys)
            patch_file('about.html', both_keys)
            patch_file('contact.html', both_keys)
            self.send_json_response({'status': 'success'})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)


    def handle_get_legal(self):
        """Read current legal placeholder values from index.html"""
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read()

            import re
            # Extract current values (defaults if still placeholders)
            name_match  = re.search(r'<!-- LGL:NAME -->(.*?)<!-- /LGL:NAME -->', content)
            addr_match  = re.search(r'<!-- LGL:ADDRESS -->(.*?)<!-- /LGL:ADDRESS -->', content)
            city_match  = re.search(r'<!-- LGL:CITY -->(.*?)<!-- /LGL:CITY -->', content)
            email_match = re.search(r'<!-- LGL:EMAIL -->(.*?)<!-- /LGL:EMAIL -->', content)
            phone_match = re.search(r'<!-- LGL:PHONE -->(.*?)<!-- /LGL:PHONE -->', content)

            data = {
                'name':  name_match.group(1)  if name_match  else '',
                'addr':  addr_match.group(1)  if addr_match  else '',
                'city':  city_match.group(1)  if city_match  else '',
                'email': email_match.group(1) if email_match else '',
                'phone': phone_match.group(1) if phone_match else '',
            }
            self.send_json_response(data)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def handle_save_legal(self):
        """Write legal data into index.html and single_project.html"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            import re
            data = json.loads(post_data.decode('utf-8'))
            name  = data.get('name',  '').strip()
            addr  = data.get('addr',  '').strip()
            city  = data.get('city',  '').strip()
            email = data.get('email', '').strip()
            phone = data.get('phone', '').strip()

            def patch_file(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    html = f.read()

                html = re.sub(
                    r'<!-- LGL:NAME -->.*?<!-- /LGL:NAME -->',
                    f'<!-- LGL:NAME -->{name}<!-- /LGL:NAME -->',
                    html, flags=re.DOTALL)
                html = re.sub(
                    r'<!-- LGL:ADDRESS -->.*?<!-- /LGL:ADDRESS -->',
                    f'<!-- LGL:ADDRESS -->{addr}<!-- /LGL:ADDRESS -->',
                    html, flags=re.DOTALL)
                html = re.sub(
                    r'<!-- LGL:CITY -->.*?<!-- /LGL:CITY -->',
                    f'<!-- LGL:CITY -->{city}<!-- /LGL:CITY -->',
                    html, flags=re.DOTALL)
                html = re.sub(
                    r'<!-- LGL:EMAIL -->.*?<!-- /LGL:EMAIL -->',
                    f'<!-- LGL:EMAIL -->{email}<!-- /LGL:EMAIL -->',
                    html, flags=re.DOTALL)
                html = re.sub(
                    r'<!-- LGL:PHONE -->.*?<!-- /LGL:PHONE -->',
                    f'<!-- LGL:PHONE -->{phone}<!-- /LGL:PHONE -->',
                    html, flags=re.DOTALL)

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html)

            patch_file('index.html')
            patch_file('single_project.html')
            patch_file('about.html')
            patch_file('contact.html')
            self.send_json_response({'status': 'success'})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
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
        # Forcefully terminate the entire process to prevent the server thread from hanging
        event.accept()
        os._exit(0)

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
