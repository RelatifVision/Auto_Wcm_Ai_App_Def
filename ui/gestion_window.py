# ui/gestion_window.py
import os
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QTableWidget, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from utils.gestion_utils import load_gestion_data, create_entry, edit_entry, delete_entry, display_table, save_inline_entry
from utils.common_functions import confirm_action
from utils.gui_utils import create_navbar

class GestionWindow(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Gestión de Clientes y Cooperativas")
        self.setWindowIcon(QIcon(os.path.join("data", "icon", "gestion.png")))
        self.setGeometry(100, 100, 1920, 1080)
        self.showMaximized()  
        
        layout = QVBoxLayout()
        
        # --- SECCIÓN EMPRESAS ---
        empresa_layout = QHBoxLayout()
        
        # Tabla de empresas (ocupará el espacio principal)
        self.table_empresa = QTableWidget()
        empresa_layout.addWidget(self.table_empresa, stretch=1)
        
        # Botones de empresa (derecha)
        button_container_empresa = QWidget()
        button_layout_empresa = QVBoxLayout()
        button_layout_empresa.setSpacing(10)
        
        self.btn_create = QPushButton("Crear")
        self.btn_edit = QPushButton("Editar")
        self.btn_delete = QPushButton("Borrar")
        self.btn_save_empresa = QPushButton("Guardar")
        
        # Estilos comunes para botones
        button_style = """
            QPushButton {
                background-color: rgb(45, 45, 45); 
                color: #ffffff;
                border: 2px solid #000000;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgb(220, 220, 220); 
                color: #000000;
            }
        """
        for btn in [self.btn_create, self.btn_edit, self.btn_delete, self.btn_save_empresa]:
            btn.setFixedSize(120, 40)
            btn.setStyleSheet(button_style)
        
        # Conectar botones de empresa
        self.btn_create.clicked.connect(lambda: create_entry(self, 'empresa'))
        self.btn_edit.clicked.connect(lambda: edit_entry(self, 'empresa'))
        self.btn_delete.clicked.connect(lambda: delete_entry(self, 'empresa'))
        self.btn_save_empresa.clicked.connect(lambda: save_inline_entry(self, 'empresa'))  # CORREGIDO: conexión aquí
        
        button_layout_empresa.addWidget(self.btn_create)
        button_layout_empresa.addWidget(self.btn_edit)
        button_layout_empresa.addWidget(self.btn_delete)
        button_layout_empresa.addWidget(self.btn_save_empresa)
        button_layout_empresa.addStretch()
        
        button_container_empresa.setLayout(button_layout_empresa)
        empresa_layout.addWidget(button_container_empresa, stretch=0)
        
        # Etiqueta y sección completa de empresas
        empresa_section = QVBoxLayout()
        label_empresa = QLabel("Empresas", alignment=Qt.AlignmentFlag.AlignCenter)
        label_empresa.setStyleSheet("font-weight: bold; font-size: 18px; color: #ffffff; background-color: #2a2a2a; padding: 8px; border-radius: 5px;")
        empresa_section.addWidget(label_empresa)
        empresa_section.addLayout(empresa_layout)
        layout.addLayout(empresa_section)
        
        # --- SECCIÓN COOPERATIVAS ---
        coop_layout = QHBoxLayout()
        
        # Tabla de cooperativas (ocupará el espacio principal)
        self.table_coop = QTableWidget()
        coop_layout.addWidget(self.table_coop, stretch=1)
        
        # Botones de cooperativas (derecha)
        button_container_coop = QWidget()
        button_layout_coop = QVBoxLayout()
        button_layout_coop.setSpacing(10)
        
        self.btn_create_coop = QPushButton("Crear")
        self.btn_edit_coop = QPushButton("Editar")
        self.btn_delete_coop = QPushButton("Borrar")
        self.btn_save_coop = QPushButton("Guardar")
        
        for btn in [self.btn_create_coop, self.btn_edit_coop, self.btn_delete_coop, self.btn_save_coop]:
            btn.setFixedSize(120, 40)
            btn.setStyleSheet(button_style)
        
        # Conectar botones de cooperativas
        self.btn_create_coop.clicked.connect(lambda: create_entry(self, 'cooperativa'))
        self.btn_edit_coop.clicked.connect(lambda: edit_entry(self, 'cooperativa'))
        self.btn_delete_coop.clicked.connect(lambda: delete_entry(self, 'cooperativa'))
        self.btn_save_coop.clicked.connect(lambda: save_inline_entry(self, 'cooperativa'))  # CORREGIDO: conexión aquí
        
        button_layout_coop.addWidget(self.btn_create_coop)
        button_layout_coop.addWidget(self.btn_edit_coop)
        button_layout_coop.addWidget(self.btn_delete_coop)
        button_layout_coop.addWidget(self.btn_save_coop)
        button_layout_coop.addStretch()
        
        button_container_coop.setLayout(button_layout_coop)
        coop_layout.addWidget(button_container_coop, stretch=0)
        
        # Etiqueta y sección completa de cooperativas
        coop_section = QVBoxLayout()
        label_coop = QLabel("Cooperativas", alignment=Qt.AlignmentFlag.AlignCenter)
        label_coop.setStyleSheet("font-weight: bold; font-size: 18px; color: #ffffff; background-color: #2a2a2a; padding: 8px; border-radius: 5px;")
        coop_section.addWidget(label_coop)
        coop_section.addLayout(coop_layout)
        layout.addLayout(coop_section)
        
        # --- NAVBAR ---
        navbar = create_navbar("gestion", self.main_window)
        layout.addWidget(navbar)
        
        # Widget central
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Cargar datos al iniciar
        load_gestion_data(self)

    def display_data(self):
        """
        Mostrar los datos en las tablas.
        """
        display_table(self.table_empresa, self.df_empresa)
        display_table(self.table_coop, self.df_cooperativa)
    
    # __Funciones de navegación__    
    def show_main_screen(self):
        self.main_window.show_main_screen()

    def show_email(self):
        self.main_window.show_email()
        
    def show_calendar(self):
        self.main_window.show_calendar()
 
    def show_stats(self):
        """Abrir ventana de estadísticas como ventana independiente."""
        from utils.stats_utils import show_company_stats
        show_company_stats(self.main_window)
    
    def close_application(self):
        from utils.common_functions import close_application
        close_application(self)