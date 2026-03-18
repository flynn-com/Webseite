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
    QStackedWidget, QLabel, QLineEdit, QTextEdit, QPushButton, 
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QInputDialog,
    QScrollArea, QSpacerItem, QSizePolicy, QDialog, QCheckBox, QGroupBox, QGridLayout
)

class ProjectDialog(QDialog):
    def __init__(self, parent=None, project_data=None, website_dir=None):
        super().__init__(parent)
        self.setWindowTitle("Projekt bearbeiten")
        self.resize(900, 750)
        self.website_dir = website_dir
        self.project_data = project_data or {}
        
        # Apply standard style to Dialog
        self.setStyleSheet("""
            QDialog {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #18181A, stop: 1 #080809);
                color: white;
                font-family: 'Inter', sans-serif;
            }
            QLabel { color: white; font-weight: 500; font-size: 15px; }
            QLineEdit, QTextEdit, QListWidget {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                color: black;
                border-radius: 18px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #ffffff; }
            QGroupBox {
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #bbbbbb;
            }
            QCheckBox { color: white; font-size: 14px;}
        """)

        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; } QWidget#scrollContent { background-color: transparent; }")
        
        content = QWidget()
        content.setObjectName("scrollContent")
        c_layout = QVBoxLayout(content)
        
        # Basic Info
        grp_basic = QGroupBox("Grunddaten")
        l_basic = QGridLayout(grp_basic)
        
        l_basic.addWidget(QLabel("Titel:"), 0, 0)
        self.inp_title = QLineEdit(self.project_data.get("title", ""))
        l_basic.addWidget(self.inp_title, 0, 1)
        
        l_basic.addWidget(QLabel("Kategorie / Kopfzeile:"), 1, 0)
        self.inp_category = QLineEdit(self.project_data.get("category", ""))
        l_basic.addWidget(self.inp_category, 1, 1)

        l_basic.addWidget(QLabel("Youtube Link (optional):"), 2, 0)
        self.inp_video = QLineEdit(self.project_data.get("video", ""))
        l_basic.addWidget(self.inp_video, 2, 1)
        
        c_layout.addWidget(grp_basic)
        
        # Icons
        grp_icons = QGroupBox("Icons auf Projektkarte")
        l_icons = QHBoxLayout(grp_icons)
        self.chk_photo = QCheckBox("Photo Icon")
        self.chk_video = QCheckBox("Video Icon")
        self.chk_design = QCheckBox("Design Icon")
        
        # Parse existing icons
        icons_list = self.project_data.get("icons", [])
        if "ph:camera-thin" in icons_list: self.chk_photo.setChecked(True)
        if "ph:video-camera-thin" in icons_list: self.chk_video.setChecked(True)
        if "ph:paint-brush-thin" in icons_list: self.chk_design.setChecked(True)
        
        l_icons.addWidget(self.chk_photo)
        l_icons.addWidget(self.chk_video)
        l_icons.addWidget(self.chk_design)
        c_layout.addWidget(grp_icons)
        
        # Descriptions
        grp_desc = QGroupBox("Texte")
        l_desc = QVBoxLayout(grp_desc)
        
        l_desc.addWidget(QLabel("Kurzbeschreibung (Übersicht):"))
        self.inp_short = QTextEdit(self.project_data.get("shortDescription", ""))
        self.inp_short.setMaximumHeight(80)
        l_desc.addWidget(self.inp_short)
        
        l_desc.addWidget(QLabel("Ausführliche Beschreibung (Detailseite):"))
        self.inp_desc = QTextEdit(self.project_data.get("description", ""))
        self.inp_desc.setMaximumHeight(150)
        l_desc.addWidget(self.inp_desc)
        c_layout.addWidget(grp_desc)
        
        # Images
        grp_img = QGroupBox("Bilder")
        l_img = QVBoxLayout(grp_img)
        
        # Main Image Preview
        self.lbl_preview = QLabel("Kein Bild ausgewählt")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setMinimumHeight(150)
        self.lbl_preview.setStyleSheet("border: 1px dashed rgba(255,255,255,0.2); border-radius: 8px; background-color: rgba(0,0,0,0.3);")
        l_img.addWidget(self.lbl_preview)

        # Main Image (Startbild)
        l_main = QHBoxLayout()
        l_main.addWidget(QLabel("Startbild (groß links):"))
        
        # Look for existing image in either "image" or "companyLogo"
        existing_main = self.project_data.get("image", "")
        if not existing_main:
            existing_main = self.project_data.get("companyLogo", "")
            
        self.inp_main_img = QLineEdit(existing_main)
        self.inp_main_img.setReadOnly(True)
        l_main.addWidget(self.inp_main_img)
        btn_main = QPushButton("Wählen...")
        btn_main.clicked.connect(self.select_main_image)
        l_main.addWidget(btn_main)
        l_img.addLayout(l_main)
        
        self.update_image_preview(existing_main)
        
        l_img.addWidget(QLabel("Galeriebilder:"))
        self.list_gallery = QListWidget()
        self.list_gallery.setMaximumHeight(120)
        self.gallery_items = []
        for g_img in self.project_data.get("gallery", []):
            self.add_gallery_item(g_img)
        l_img.addWidget(self.list_gallery)
        
        l_gal_btns = QHBoxLayout()
        btn_add_gal = QPushButton("+ Bild hinzufügen")
        btn_add_gal.clicked.connect(self.add_gallery_image)
        btn_rm_gal = QPushButton("- Bild entfernen")
        btn_rm_gal.clicked.connect(self.remove_gallery_image)
        btn_up_gal = QPushButton("▲ Hoch")
        btn_up_gal.clicked.connect(self.move_gallery_up)
        btn_dn_gal = QPushButton("▼ Runter")
        btn_dn_gal.clicked.connect(self.move_gallery_down)
        
        l_gal_btns.addWidget(btn_add_gal)
        l_gal_btns.addWidget(btn_rm_gal)
        l_gal_btns.addWidget(btn_up_gal)
        l_gal_btns.addWidget(btn_dn_gal)
        l_img.addLayout(l_gal_btns)
        
        c_layout.addWidget(grp_img)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Speichern")
        btn_save.clicked.connect(self.accept)
        btn_layout.addStretch(1)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def add_gallery_item(self, path):
        self.gallery_items.append(path)
        self.list_gallery.addItem(os.path.basename(path))

    def select_main_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Bild auswählen", "", "Bilder (*.png *.jpg *.jpeg *.webp)")
        if fname:
            rel_path = self.copy_image_to_assets(fname)
            self.inp_main_img.setText(rel_path)
            self.update_image_preview(rel_path)

    def update_image_preview(self, rel_path):
        if rel_path and rel_path.strip():
            abs_path = os.path.join(self.website_dir, rel_path)
            if os.path.exists(abs_path):
                pixmap = QPixmap(abs_path)
                # Scale to fit while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(300, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.lbl_preview.setPixmap(scaled_pixmap)
                self.lbl_preview.setText("")
            else:
                self.lbl_preview.setText("Bilddatei nicht gefunden")
        else:
            self.lbl_preview.setText("Kein Bild ausgewählt")

    def add_gallery_image(self):
        fnames, _ = QFileDialog.getOpenFileNames(self, "Bilder auswählen", "", "Bilder (*.png *.jpg *.jpeg *.webp)")
        for fname in fnames:
            rel_path = self.copy_image_to_assets(fname)
            self.add_gallery_item(rel_path)

    def remove_gallery_image(self):
        row = self.list_gallery.currentRow()
        if row >= 0:
            self.list_gallery.takeItem(row)
            del self.gallery_items[row]

    def move_gallery_up(self):
        row = self.list_gallery.currentRow()
        if row > 0:
            item = self.list_gallery.takeItem(row)
            self.list_gallery.insertItem(row - 1, item)
            self.gallery_items.insert(row - 1, self.gallery_items.pop(row))
            self.list_gallery.setCurrentRow(row - 1)

    def move_gallery_down(self):
        row = self.list_gallery.currentRow()
        if row >= 0 and row < self.list_gallery.count() - 1:
            item = self.list_gallery.takeItem(row)
            self.list_gallery.insertItem(row + 1, item)
            self.gallery_items.insert(row + 1, self.gallery_items.pop(row))
            self.list_gallery.setCurrentRow(row + 1)

    def copy_image_to_assets(self, filepath):
        ext = os.path.splitext(filepath)[1]
        new_filename = f"img_{uuid.uuid4().hex[:8]}{ext}"
        dest_dir = os.path.join(self.website_dir, "assets", "projects")
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, new_filename)
        shutil.copy2(filepath, dest_path)
        return f"assets/projects/{new_filename}"

    def get_data(self):
        icons = []
        if self.chk_photo.isChecked(): icons.append("ph:camera-thin")
        if self.chk_video.isChecked(): icons.append("ph:video-camera-thin")
        if self.chk_design.isChecked(): icons.append("ph:paint-brush-thin")

        self.project_data["title"] = self.inp_title.text()
        self.project_data["category"] = self.inp_category.text()
        self.project_data["video"] = self.inp_video.text()
        self.project_data["shortDescription"] = self.inp_short.toPlainText()
        self.project_data["description"] = self.inp_desc.toPlainText()
        self.project_data["icons"] = icons
        
        main_img = self.inp_main_img.text()
        self.project_data["image"] = main_img
        # Also assign to companyLogo so single_project.html definitely shows it 
        self.project_data["companyLogo"] = main_img
        
        self.project_data["gallery"] = self.gallery_items
        return self.project_data


class AdminApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(".FLYNN | Admin Center")
        self.resize(1200, 850)
        
        # Apply Global Stylesheet matching glassmorphism/dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #18181A, stop: 1 #080809);
            }
            QWidget {
                background-color: transparent;
                color: #ffffff;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 15px;
            }
            QLabel {
                font-weight: 500;
                margin-top: 5px;
            }
            QLineEdit, QTextEdit, QListWidget {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                padding: 12px;
                color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QListWidget:focus {
                border: 1px solid rgba(255, 255, 255, 0.4);
                background-color: rgba(255, 255, 255, 0.07);
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 8px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.95);
                color: #080809;
                border: none;
                border-radius: 24px; /* Pill shape */
                padding: 14px 28px;
                font-weight: 700;
                font-size: 14px;
                letter-spacing: 1px;
                text-transform: uppercase;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #e6e6e6;
            }
            QMessageBox {
                background-color: #1a1a1a;
            }
            QInputDialog {
                background-color: #1a1a1a;
            }
        """)
        
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
            self.website_dir = os.path.join(self.base_dir, "Website")
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            self.website_dir = os.path.join(self.base_dir, "..", "Website")
            
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        self.setup_main_menu()
        self.setup_projects_page()
        self.setup_about_page()
        self.setup_settings_page()
        self.setup_legal_page()

    def add_back_button(self, layout, title):
        top_bar = QHBoxLayout()
        btn_back = QPushButton("< Zurück")
        btn_back.setFixedWidth(120)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                margin-top: 0px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.1);
            }
        """)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        top_bar.addWidget(btn_back)
        
        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        lbl_title.setStyleSheet("margin-left: 20px; margin-top: 0px;")
        top_bar.addWidget(lbl_title)
        top_bar.addStretch(1)
        
        layout.addLayout(top_bar)
        layout.addSpacing(10)

    # ================= MAIN MENU =================
    def setup_main_menu(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        layout.addStretch(1)
        
        # Logo / Title - EVEN LARGER
        logo_label = QLabel(".FLYNN")
        logo_font = QFont("Inter", 160, QFont.Weight.Bold)
        logo_label.setFont(logo_font)
        logo_label.setStyleSheet("color: white; letter-spacing: 4px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        layout.addSpacing(40)
        
        # Buttons Container
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setSpacing(20)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        main_btn_style = """
            QPushButton {
                padding: 16px; 
                font-size: 15px;
                border-radius: 25px;
                margin-top: 0px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """
        
        btn_projects = QPushButton("Projekte")
        btn_projects.setFixedWidth(350)
        btn_projects.setStyleSheet(main_btn_style)
        btn_projects.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_layout.addWidget(btn_projects)
        
        btn_about = QPushButton("About me")
        btn_about.setFixedWidth(350)
        btn_about.setStyleSheet(main_btn_style)
        btn_about.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        btn_layout.addWidget(btn_about)
        
        btn_settings = QPushButton("Webseiten Einstellungen")
        btn_settings.setFixedWidth(350)
        btn_settings.setStyleSheet(main_btn_style)
        btn_settings.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        btn_layout.addWidget(btn_settings)
        
        btn_legal = QPushButton("Rechtliches")
        btn_legal.setFixedWidth(350)
        btn_legal.setStyleSheet(main_btn_style)
        btn_legal.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        btn_layout.addWidget(btn_legal)

        layout.addWidget(btn_container)
        layout.addStretch(1)

        # Speichern und Beenden Button at the very bottom
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch(1)
        btn_exit = QPushButton("Speichern und Beenden")
        btn_exit.setFixedWidth(250)
        btn_exit.setStyleSheet("""
            QPushButton {
                background-color: #cc0000;
                color: white;
                padding: 12px;
                font-size: 14px;
                border-radius: 20px;
                margin-bottom: 10px;
            }
            QPushButton:hover { background-color: #ff3333; }
        """)
        btn_exit.clicked.connect(self.close)
        bottom_layout.addWidget(btn_exit)
        bottom_layout.addStretch(1)
        
        layout.addLayout(bottom_layout)
        
        self.stack.addWidget(page)

    # ================= PROJECTS PAGE (NEW) =================
    def setup_projects_page(self):
        page = QWidget()
        main_vbox = QVBoxLayout(page)
        self.add_back_button(main_vbox, "Projekte Übersicht")
        
        layout = QHBoxLayout()
        main_vbox.addLayout(layout)
        
        # Center List
        center_layout = QVBoxLayout()
        self.overview_project_list = QListWidget()
        self.overview_project_list.setStyleSheet("font-size: 18px; padding: 15px;")
        center_layout.addWidget(QLabel("Alle Projekte in Reihenfolge (Drag & Drop möglich):"))
        center_layout.addWidget(self.overview_project_list)
        layout.addLayout(center_layout, stretch=2)
        
        # Right Buttons
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        right_layout.addSpacing(35)
        
        btn_up = QPushButton("▲ Nach oben verschieben")
        btn_up.clicked.connect(self.move_project_up)
        btn_dn = QPushButton("▼ Nach unten verschieben")
        btn_dn.clicked.connect(self.move_project_down)
        
        right_layout.addWidget(btn_up)
        right_layout.addWidget(btn_dn)
        right_layout.addSpacing(30)
        
        btn_add = QPushButton("+ Neues Projekt erstellen")
        btn_add.clicked.connect(self.add_new_project)
        btn_edit = QPushButton("✎ Ausgewähltes Bearbeiten")
        btn_edit.clicked.connect(self.edit_selected_project)
        btn_del = QPushButton("✖ Projekt löschen")
        btn_del.setStyleSheet("QPushButton { background-color: #cc0000; color: white; } QPushButton:hover { background-color: #ff3333; }")
        btn_del.clicked.connect(self.del_selected_project)
        
        right_layout.addWidget(btn_add)
        right_layout.addWidget(btn_edit)
        right_layout.addWidget(btn_del)
        right_layout.addStretch(1)
        
        layout.addLayout(right_layout, stretch=1)
        
        self.stack.addWidget(page)
        self.projects = []
        self.load_projects()

    def load_projects(self):
        self.overview_project_list.clear()
        try:
            data_path = os.path.join(self.website_dir, "data.js")
            if not os.path.exists(data_path):
                return
            with open(data_path, "r", encoding="utf-8") as f:
                js = f.read()
            match = re.search(r'const\s+initialProjects\s*=\s*(\[.*?\]);', js, re.DOTALL)
            if match:
                self.projects = json.loads(match.group(1))
                self.refresh_project_list_ui()
        except Exception as e:
            print("Konnte data.js nicht laden:", e)
            self.projects = []

    def refresh_project_list_ui(self):
        self.overview_project_list.clear()
        for idx, p in enumerate(self.projects):
            # Recalculate numbers
            p["number"] = f"{(idx+1):02d}"
            p["bigNumber"] = f"{(idx+1):02d}"
            self.overview_project_list.addItem(f"{p['number']} - {p.get('title', 'Unbenannt')}")

    def move_project_up(self):
        row = self.overview_project_list.currentRow()
        if row > 0:
            self.projects.insert(row - 1, self.projects.pop(row))
            self.refresh_project_list_ui()
            self.overview_project_list.setCurrentRow(row - 1)
            self.write_projects_to_disk()

    def move_project_down(self):
        row = self.overview_project_list.currentRow()
        if row >= 0 and row < len(self.projects) - 1:
            self.projects.insert(row + 1, self.projects.pop(row))
            self.refresh_project_list_ui()
            self.overview_project_list.setCurrentRow(row + 1)
            self.write_projects_to_disk()

    def add_new_project(self):
        new_p = {
            "id": len(self.projects) + 1,
            "number": f"{(len(self.projects) + 1):02d}",
            "bigNumber": f"{(len(self.projects) + 1):02d}",
            "title": "Neues Projekt",
            "category": "",
            "shortDescription": "",
            "description": "",
            "image": "",
            "gallery": [],
            "video": "",
            "icons": []
        }
        dlg = ProjectDialog(self, new_p, self.website_dir)
        if dlg.exec():
            self.projects.append(dlg.get_data())
            self.refresh_project_list_ui()
            self.overview_project_list.setCurrentRow(len(self.projects)-1)
            self.write_projects_to_disk()

    def edit_selected_project(self):
        row = self.overview_project_list.currentRow()
        if row >= 0:
            dlg = ProjectDialog(self, self.projects[row], self.website_dir)
            if dlg.exec():
                self.projects[row] = dlg.get_data()
                self.refresh_project_list_ui()
                self.overview_project_list.setCurrentRow(row)
                self.write_projects_to_disk()

    def del_selected_project(self):
        row = self.overview_project_list.currentRow()
        if row >= 0:
            reply = QMessageBox.question(self, 'Löschen', 'Projekt wirklich löschen?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                del self.projects[row]
                self.refresh_project_list_ui()
                self.write_projects_to_disk()

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

    # ================= SETTINGS PAGE (OLD PROJECTS) =================
    def setup_settings_page(self):
        page = QWidget()
        main_vbox = QVBoxLayout(page)
        self.add_back_button(main_vbox, "Webseiten Einstellungen")
        
        info = QLabel("Hierhin wurde das alte einfache Projekt-Formular temporär verschoben. Zukünftig können hier SEO / Favicons konfiguriert werden.")
        info.setWordWrap(True)
        info.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-style: italic;")
        main_vbox.addWidget(info)
        
        layout = QHBoxLayout()
        main_vbox.addLayout(layout)
        
        left_layout = QVBoxLayout()
        self.old_project_list = QListWidget()
        left_layout.addWidget(QLabel("Alt: Deine Projekte"))
        left_layout.addWidget(self.old_project_list)
        layout.addLayout(left_layout, stretch=1)
        
        right_layout = QVBoxLayout()
        self.old_proj_title = QLineEdit()
        self.old_proj_category = QLineEdit()
        self.old_proj_desc = QTextEdit()
        
        right_layout.addWidget(QLabel("Titel:"))
        right_layout.addWidget(self.old_proj_title)
        right_layout.addWidget(QLabel("Kategorie:"))
        right_layout.addWidget(self.old_proj_category)
        right_layout.addWidget(QLabel("Beschreibung:"))
        right_layout.addWidget(self.old_proj_desc)
        right_layout.addStretch(1)
        layout.addLayout(right_layout, stretch=2)
        
        self.stack.addWidget(page)

    # ================= ABOUT PAGE =================
    def setup_about_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.add_back_button(layout, "About Me")
        
        layout.addWidget(QLabel("Name:"))
        self.about_name = QLineEdit()
        layout.addWidget(self.about_name)
        
        layout.addWidget(QLabel("Rolle/Beruf:"))
        self.about_role = QLineEdit()
        layout.addWidget(self.about_role)
        
        layout.addWidget(QLabel("Über mich Text:"))
        self.about_bio = QTextEdit()
        layout.addWidget(self.about_bio)
        
        layout.addWidget(QLabel("Skills (z.B. Design, Foto, Web):"))
        self.about_skills = QLineEdit()
        layout.addWidget(self.about_skills)
        
        btn_save = QPushButton("About-Seite Speichern")
        btn_save.clicked.connect(self.save_about)
        layout.addWidget(btn_save)
        
        self.stack.addWidget(page)
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
            pass

    def save_about(self):
        try:
            html_path = os.path.join(self.website_dir, "about.html")
            with open(html_path, "r", encoding="utf-8") as f: html = f.read()
            mapping = {
                'ABOUT_NAME': self.about_name.text(),
                'ABOUT_ROLE': self.about_role.text(),
                'ABOUT_BIO':  self.about_bio.toPlainText(),
            }
            for key, value in mapping.items():
                html = re.sub(
                    r'<!-- TXT:' + key + r' -->.*?<!-- /TXT:' + key + r' -->',
                    f'<!-- TXT:{key} -->{value}<!-- /TXT:{key} -->', html, flags=re.DOTALL)
            with open(html_path, "w", encoding="utf-8") as f: f.write(html)
            js_path = os.path.join(self.website_dir, "about_data.js")
            with open(js_path, "r", encoding="utf-8") as f: js = f.read()
            js = re.sub(r"var ABOUT_SKILLS\s*=.*?;", f"var ABOUT_SKILLS = '{self.about_skills.text()}';", js)
            with open(js_path, "w", encoding="utf-8") as f: f.write(js)
            QMessageBox.information(self, "Erfolg", "About-Seite gespeichert!")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

    # ================= LEGAL PAGE =================
    def setup_legal_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.add_back_button(layout, "Impressum & Kontakt")
        
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
        
        self.stack.addWidget(page)
        self.load_legal()

    def load_legal(self):
        try:
            idx_path = os.path.join(self.website_dir, "index.html")
            with open(idx_path, "r", encoding="utf-8") as f: html = f.read()
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
        except: pass

    def save_legal(self):
        try:
            for fname in ["index.html", "single_project.html", "about.html", "contact.html"]:
                fpath = os.path.join(self.website_dir, fname)
                if not os.path.exists(fpath): continue
                with open(fpath, "r", encoding="utf-8") as f: html = f.read()
                html = re.sub(r'<!-- LGL:NAME -->.*?<!-- /LGL:NAME -->', f'<!-- LGL:NAME -->{self.leg_name.text()}<!-- /LGL:NAME -->', html, flags=re.DOTALL)
                html = re.sub(r'<!-- LGL:ADDRESS -->.*?<!-- /LGL:ADDRESS -->', f'<!-- LGL:ADDRESS -->{self.leg_addr.text()}<!-- /LGL:ADDRESS -->', html, flags=re.DOTALL)
                html = re.sub(r'<!-- LGL:CITY -->.*?<!-- /LGL:CITY -->', f'<!-- LGL:CITY -->{self.leg_city.text()}<!-- /LGL:CITY -->', html, flags=re.DOTALL)
                html = re.sub(r'<!-- LGL:EMAIL -->.*?<!-- /LGL:EMAIL -->', f'<!-- LGL:EMAIL -->{self.leg_email.text()}<!-- /LGL:EMAIL -->', html, flags=re.DOTALL)
                html = re.sub(r'<!-- LGL:PHONE -->.*?<!-- /LGL:PHONE -->', f'<!-- LGL:PHONE -->{self.leg_phone.text()}<!-- /LGL:PHONE -->', html, flags=re.DOTALL)
                with open(fpath, "w", encoding="utf-8") as f: f.write(html)
            QMessageBox.information(self, "Erfolg", "Rechtliche Daten gespeichert!")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AdminApp()
    window.show()
    sys.exit(app.exec())
