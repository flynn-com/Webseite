import sys
import os
import json
import base64
import re
import uuid
import shutil
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon, QImage, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QLineEdit, QTextEdit, QPushButton, 
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QInputDialog,
    QScrollArea
)

class AdminApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(".FLYNN | Admin Center")
        self.resize(1000, 750)
        
        # Apply Global Stylesheet matching glassmorphism/dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d0d0d;
            }
            QWidget {
                background-color: transparent;
                color: #ffffff;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QLabel {
                font-weight: 500;
                margin-top: 5px;
            }
            QLineEdit, QTextEdit, QListWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 10px;
                color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QListWidget:focus {
                border: 1px solid rgba(255, 255, 255, 0.6);
                background-color: rgba(255, 255, 255, 0.08);
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
            QPushButton {
                background-color: white;
                color: #0d0d0d;
                border: none;
                border-radius: 20px; /* Pill shape */
                padding: 12px 24px;
                font-weight: 700;
                font-size: 13px;
                letter-spacing: 1px;
                text-transform: uppercase;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #cccccc;
            }
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                background-color: rgba(255, 255, 255, 0.02);
            }
            QTabBar::tab {
                background-color: transparent;
                color: rgba(255, 255, 255, 0.5);
                padding: 12px 25px;
                font-weight: 600;
                font-size: 15px;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                color: #ffffff;
                border-bottom: 2px solid #ffffff;
            }
            QTabBar::tab:hover {
                color: #dddddd;
            }
            QMessageBox {
                background-color: #1a1a1a;
            }
            QInputDialog {
                background-color: #1a1a1a;
            }
        """)
        
        # Bestimme Original-Ordner für Dateien
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.website_dir = os.path.join(self.base_dir, "..", "Website")
        
        # Main Layout Construct
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        # Prominent Header
        header_label = QLabel(".FLYNN ADMIN")
        header_font = QFont("Inter", 24, QFont.Weight.Bold)
        header_label.setFont(header_font)
        header_label.setStyleSheet("color: white; letter-spacing: 2px;")
        main_layout.addWidget(header_label)

        # UI Aufbau
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.setup_about_tab()
        self.setup_projects_tab()
        self.setup_legal_tab()

    # ================= ABOUT TAB =================
    def setup_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Name
        layout.addWidget(QLabel("Name:"))
        self.about_name = QLineEdit()
        layout.addWidget(self.about_name)
        
        # Rolle
        layout.addWidget(QLabel("Rolle/Beruf:"))
        self.about_role = QLineEdit()
        layout.addWidget(self.about_role)
        
        # Bio
        layout.addWidget(QLabel("Über mich Text:"))
        self.about_bio = QTextEdit()
        layout.addWidget(self.about_bio)
        
        # Skills
        layout.addWidget(QLabel("Skills (z.B. Design, Foto, Web):"))
        self.about_skills = QLineEdit()
        layout.addWidget(self.about_skills)
        
        btn_save = QPushButton("About-Seite Speichern")
        btn_save.clicked.connect(self.save_about)
        layout.addWidget(btn_save)
        
        self.tabs.addTab(tab, "About Me")
        self.load_about()

    def load_about(self):
        try:
            html_path = os.path.join(self.website_dir, "about.html")
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            
            name = re.search(r'<!-- TXT:ABOUT_NAME -->(.*?)<!-- /TXT:ABOUT_NAME -->', html, re.DOTALL)
            role = re.search(r'<!-- TXT:ABOUT_ROLE -->(.*?)<!-- /TXT:ABOUT_ROLE -->', html, re.DOTALL)
            bio = re.search(r'<!-- TXT:ABOUT_BIO -->(.*?)<!-- /TXT:ABOUT_BIO -->', html, re.DOTALL)
            
            if name: self.about_name.setText(name.group(1).strip())
            if role: self.about_role.setText(role.group(1).strip())
            if bio: self.about_bio.setText(bio.group(1).strip())
                
            js_path = os.path.join(self.website_dir, "about_data.js")
            with open(js_path, "r", encoding="utf-8") as f:
                js = f.read()
            skills = re.search(r"var ABOUT_SKILLS\s*=\s*'([^']*?)'", js)
            if skills: self.about_skills.setText(skills.group(1).strip())
        except Exception as e:
            print("Fehler beim Laden von About:", e)

    def save_about(self):
        try:
            html_path = os.path.join(self.website_dir, "about.html")
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
                
            mapping = {
                'ABOUT_NAME': self.about_name.text(),
                'ABOUT_ROLE': self.about_role.text(),
                'ABOUT_BIO':  self.about_bio.toPlainText(),
            }
            
            for key, value in mapping.items():
                html = re.sub(
                    r'<!-- TXT:' + key + r' -->.*?<!-- /TXT:' + key + r' -->',
                    f'<!-- TXT:{key} -->{value}<!-- /TXT:{key} -->',
                    html, flags=re.DOTALL)
                    
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
                
            js_path = os.path.join(self.website_dir, "about_data.js")
            with open(js_path, "r", encoding="utf-8") as f:
                js = f.read()
            js = re.sub(r"var ABOUT_SKILLS\s*=.*?;", f"var ABOUT_SKILLS = '{self.about_skills.text()}';", js)
            with open(js_path, "w", encoding="utf-8") as f:
                f.write(js)
                
            QMessageBox.information(self, "Erfolg", "About-Seite erfolgreich gespeichert!")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    # ================= LEGAL TAB =================
    def setup_legal_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("Name:"))
        self.leg_name = QLineEdit()
        layout.addWidget(self.leg_name)
        
        layout.addWidget(QLabel("Adresse:"))
        self.leg_addr = QLineEdit()
        layout.addWidget(self.leg_addr)
        
        layout.addWidget(QLabel("Stadt / PLZ:"))
        self.leg_city = QLineEdit()
        layout.addWidget(self.leg_city)
        
        layout.addWidget(QLabel("E-Mail:"))
        self.leg_email = QLineEdit()
        layout.addWidget(self.leg_email)
        
        layout.addWidget(QLabel("Telefon:"))
        self.leg_phone = QLineEdit()
        layout.addWidget(self.leg_phone)
        
        btn_save = QPushButton("Impressum / Footer Speichern")
        btn_save.clicked.connect(self.save_legal)
        layout.addWidget(btn_save)
        
        self.tabs.addTab(tab, "Impressum & Kontakt")
        self.load_legal()

    def load_legal(self):
        try:
            idx_path = os.path.join(self.website_dir, "index.html")
            with open(idx_path, "r", encoding="utf-8") as f:
                html = f.read()
            name = re.search(r'<!-- LGL:NAME -->(.*?)<!-- /LGL:NAME -->', html)
            addr = re.search(r'<!-- LGL:ADDRESS -->(.*?)<!-- /LGL:ADDRESS -->', html)
            city = re.search(r'<!-- LGL:CITY -->(.*?)<!-- /LGL:CITY -->', html)
            email = re.search(r'<!-- LGL:EMAIL -->(.*?)<!-- /LGL:EMAIL -->', html)
            phone = re.search(r'<!-- LGL:PHONE -->(.*?)<!-- /LGL:PHONE -->', html)
            
            if name: self.leg_name.setText(name.group(1).strip())
            if addr: self.leg_addr.setText(addr.group(1).strip())
            if city: self.leg_city.setText(city.group(1).strip())
            if email: self.leg_email.setText(email.group(1).strip())
            if phone: self.leg_phone.setText(phone.group(1).strip())
        except Exception as e:
            print("Fehler beim Laden von Legal:", e)

    def save_legal(self):
        try:
            files_to_patch = ["index.html", "single_project.html", "about.html", "contact.html"]
            for fname in files_to_patch:
                fpath = os.path.join(self.website_dir, fname)
                if not os.path.exists(fpath): continue
                with open(fpath, "r", encoding="utf-8") as f:
                    html = f.read()
                    
                html = re.sub(r'<!-- LGL:NAME -->.*?<!-- /LGL:NAME -->', f'<!-- LGL:NAME -->{self.leg_name.text()}<!-- /LGL:NAME -->', html, flags=re.DOTALL)
                html = re.sub(r'<!-- LGL:ADDRESS -->.*?<!-- /LGL:ADDRESS -->', f'<!-- LGL:ADDRESS -->{self.leg_addr.text()}<!-- /LGL:ADDRESS -->', html, flags=re.DOTALL)
                html = re.sub(r'<!-- LGL:CITY -->.*?<!-- /LGL:CITY -->', f'<!-- LGL:CITY -->{self.leg_city.text()}<!-- /LGL:CITY -->', html, flags=re.DOTALL)
                html = re.sub(r'<!-- LGL:EMAIL -->.*?<!-- /LGL:EMAIL -->', f'<!-- LGL:EMAIL -->{self.leg_email.text()}<!-- /LGL:EMAIL -->', html, flags=re.DOTALL)
                html = re.sub(r'<!-- LGL:PHONE -->.*?<!-- /LGL:PHONE -->', f'<!-- LGL:PHONE -->{self.leg_phone.text()}<!-- /LGL:PHONE -->', html, flags=re.DOTALL)
                
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(html)
            QMessageBox.information(self, "Erfolg", "Rechtliche Daten gespeichert!")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    # ================= PROJECTS TAB =================
    def setup_projects_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Linke Liste
        left_layout = QVBoxLayout()
        self.project_list = QListWidget()
        self.project_list.itemClicked.connect(self.select_project)
        left_layout.addWidget(QLabel("Deine Projekte:"))
        left_layout.addWidget(self.project_list)
        
        btn_add = QPushButton("Neues Projekt")
        btn_add.clicked.connect(self.add_project)
        btn_del = QPushButton("Projekt Löschen")
        btn_del.clicked.connect(self.del_project)
        left_layout.addWidget(btn_add)
        left_layout.addWidget(btn_del)
        
        layout.addLayout(left_layout, stretch=1)
        
        # Rechte Bearbeitung
        right_layout = QVBoxLayout()
        self.proj_title = QLineEdit()
        self.proj_category = QLineEdit()
        self.proj_desc = QTextEdit()
        
        right_layout.addWidget(QLabel("Titel:"))
        right_layout.addWidget(self.proj_title)
        right_layout.addWidget(QLabel("Kategorie:"))
        right_layout.addWidget(self.proj_category)
        right_layout.addWidget(QLabel("Beschreibung:"))
        right_layout.addWidget(self.proj_desc)
        
        # Bild Upload (Main Image)
        img_layout = QHBoxLayout()
        self.proj_img_path = QLineEdit()
        self.proj_img_path.setReadOnly(True)
        btn_img = QPushButton("Hintergrundbild wählen")
        btn_img.clicked.connect(self.choose_image)
        img_layout.addWidget(self.proj_img_path)
        img_layout.addWidget(btn_img)
        right_layout.addLayout(img_layout)
        
        btn_save = QPushButton("Projekt Speichern")
        btn_save.clicked.connect(self.save_current_project)
        right_layout.addWidget(btn_save)
        
        layout.addLayout(right_layout, stretch=2)
        self.tabs.addTab(tab, "Projekte verwalten")
        
        self.projects = []
        self.current_project_index = -1
        self.load_projects()

    def load_projects(self):
        self.project_list.clear()
        try:
            data_path = os.path.join(self.website_dir, "data.js")
            with open(data_path, "r", encoding="utf-8") as f:
                js = f.read()
            match = re.search(r'const\s+initialProjects\s*=\s*(\[.*?\]);', js, re.DOTALL)
            if match:
                self.projects = json.loads(match.group(1))
                for idx, p in enumerate(self.projects):
                    self.project_list.addItem(f"{idx+1}. {p.get('title', 'Unbenannt')}")
        except Exception as e:
            print("Konnte data.js nicht laden:", e)
            self.projects = []

    def select_project(self, item):
        self.current_project_index = self.project_list.currentRow()
        p = self.projects[self.current_project_index]
        self.proj_title.setText(p.get("title", ""))
        self.proj_category.setText(p.get("category", ""))
        self.proj_desc.setText(p.get("description", ""))
        self.proj_img_path.setText(p.get("image", ""))

    def add_project(self):
        title, ok = QInputDialog.getText(self, "Neues Projekt", "Projekttitel:")
        if ok and title:
            new_p = {
                "id": len(self.projects) + 1,
                "title": title,
                "category": "",
                "description": "",
                "image": "",
                "gallery": [],
                "video": "",
                "companyLogo": ""
            }
            self.projects.append(new_p)
            self.project_list.addItem(f"{len(self.projects)}. {title}")
            self.project_list.setCurrentRow(len(self.projects) - 1)
            self.select_project(None)

    def del_project(self):
        if self.current_project_index >= 0:
            del self.projects[self.current_project_index]
            self.current_project_index = -1
            self.proj_title.clear()
            self.proj_category.clear()
            self.proj_desc.clear()
            self.proj_img_path.clear()
            self.write_projects_to_disk()
            self.load_projects()

    def choose_image(self):
        if self.current_project_index < 0: return
        fname, _ = QFileDialog.getOpenFileName(self, "Bild auswählen", "", "Bilder (*.png *.jpg *.jpeg *.webp)")
        if fname:
            # Kopiere Bild nach assets/projects
            ext = os.path.splitext(fname)[1]
            new_filename = f"img_{uuid.uuid4().hex[:8]}{ext}"
            dest_dir = os.path.join(self.website_dir, "assets", "projects")
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, new_filename)
            shutil.copy2(fname, dest_path)
            
            rel_path = f"assets/projects/{new_filename}"
            self.proj_img_path.setText(rel_path)

    def save_current_project(self):
        if self.current_project_index >= 0:
            p = self.projects[self.current_project_index]
            p["title"] = self.proj_title.text()
            p["category"] = self.proj_category.text()
            p["description"] = self.proj_desc.toPlainText()
            p["image"] = self.proj_img_path.text()
            self.write_projects_to_disk()
            self.load_projects()
            self.project_list.setCurrentRow(self.current_project_index)
            QMessageBox.information(self, "Erfolg", "Projekt gespeichert!")

    def write_projects_to_disk(self):
        try:
            data_path = os.path.join(self.website_dir, "data.js")
            js_content = "// Initial Project Data\n"
            js_content += "const initialProjects = " + json.dumps(self.projects, indent=4) + ";\n\n"
            js_content += "window.initialProjects = initialProjects;\n"
            with open(data_path, "w", encoding="utf-8") as f:
                f.write(js_content)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Konnte Projekte nicht speichern: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AdminApp()
    window.show()
    sys.exit(app.exec())
