# ui/calendar_window.py
import datetime
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCalendarWidget, QMainWindow, QApplication, QMessageBox, QTextEdit, QDialog
from PyQt6.QtGui import QIcon, QColor, QFont, QTextCharFormat
from PyQt6.QtCore import Qt, QDate, QTime
from calendar_api_setting.calendar_api import get_events, get_events_by_month
from utils.business_manager import BusinessManager
from utils.calendar_utils import display_event_info, refresh_calendar,select_date
from utils.event_utils import create_event, edit_event, delete_event
from utils.custom_calendar_utils import CustomCalendar
from utils.gui_utils import create_navbar
from config import EXCEL_FILE_PATH, TASK_OPTIONS, ICON_DIR

class CalendarWindow(QMainWindow):
    def __init__(self, main_window, has_internet=True):
        super().__init__()     
        self.main_window = main_window
        self.has_internet = has_internet  # Estado de conexión
        
        self.setWindowIcon(QIcon(os.path.join("data", "icon", "calendar.png")))
        self.setStyleSheet("background-color: #1b376d;") 
        self.setWindowTitle("Calendario")
        self.setGeometry(100, 100, 800, 600)
        
        # Verificar conexión
        if not self.has_internet:
            from utils.common_functions import show_warning_dialog
            show_warning_dialog(self, "Modo Offline", "Calendario en modo offline. Algunas funciones pueden estar limitadas.")
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --- WIDGET PARA MOSTRAR ESTADÍSTICAS (Añadido) ---
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        self.stats_display.setVisible(False) # Oculto por defecto
        self.stats_display.setStyleSheet("background-color: #333333; color: white;")
        self.stats_display.setMaximumHeight(200) # Altura máxima, ajustable
        
        self.calendar = CustomCalendar()
        self.calendar.setStyleSheet(
            """
            QCalendarWidget {
                background-color: #1b376d;  /* Fondo principal */
            }
            QCalendarWidget QHeaderView {
                background-color: #444444;  /* gris claro para días de la semana */
                color: white;
                font-weight: bold;
            }
            QCalendarWidget QToolButton {
                background-color: #444444;
                color: white;
            }
            QCalendarWidget QAbstractItemView {
                background-color: #333333;  /* Fondo gris oscuro por defecto */
                selection-background-color: transparent;  /* Eliminar color de selección fijo */
            }
            QCalendarWidget QTableView::item {
                border: none;  /* Eliminar bordes */
            }
            """
        )
            
        # Configuración básica 2024-2030
        self.calendar.setMinimumDate(QDate(2024, 12, 31))
        self.calendar.setMaximumDate(QDate(2030, 12, 31))
        # Primer día lunes
        self.calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.calendar.setNavigationBarVisible(True)
        self.calendar.setGridVisible(True)  
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)  
        
        # Título y botón Refresh
        title_layout = QHBoxLayout()
        title_label = QLabel("Calendario", alignment=Qt.AlignmentFlag.AlignLeft)
        title_label.setStyleSheet("font-size: 20px; color: #ffffff;")
        title_layout.addWidget(title_label)
        
        self.btn_refresh = QPushButton(" Refresh")
        icono_refresh = QIcon(os.path.join(ICON_DIR, "refresh.png"))
        self.btn_refresh.setIcon(icono_refresh)
        self.btn_refresh.setStyleSheet("background-color: #333333; color: white;")
        self.btn_refresh.setFixedSize(80, 40)
        self.btn_refresh.clicked.connect(lambda: self.refresh_calendar_safe())
        title_layout.addWidget(self.btn_refresh, alignment=Qt.AlignmentFlag.AlignRight)
        
        main_layout.addLayout(title_layout)
        
        # Añadir el calendario al layout principal
        main_layout.addWidget(self.calendar)

        main_layout.addWidget(self.stats_display)
        
        # Resaltar el día actual con el formato especificado
        today = QDate.currentDate()
        today_format = QTextCharFormat()
        today_format.setBackground(QColor("#465068"))  # Fondo azul claro
        today_format.setForeground(QColor("black"))    # Texto negro
        self.calendar.setDateTextFormat(today, today_format)
        
        # Mes visible
        self.current_month = QDate.currentDate().toString("yyyy-MM") 
        self.calendar.currentPageChanged.connect(self.update_current_month)
        self.calendar.clicked.connect(lambda date: select_date(self, date))
        self.calendar.activated.connect(lambda date: display_event_info(self, date))
        
        # Conexiones de señales
        self.calendar.clicked.connect(lambda date: select_date(self, date))  
        self.calendar.activated.connect(lambda date: display_event_info(self, date))  
        self.calendar.setMinimumDate(QDate(2024, 12, 31))
        self.calendar.setMaximumDate(QDate(2030, 12, 31))
        
        # Botones de acción (Crear/Editar/Borrar/Estadísticas)
        button_layout = QHBoxLayout()
        self.btn_create = QPushButton(" Crear Evento")
        icono_create = QIcon(os.path.join(ICON_DIR, "create.png"))
        self.btn_create.setIcon(icono_create)
        self.btn_create.setStyleSheet("background-color: #333333; color: white;")
        self.btn_create.setFixedSize(120, 40)
        self.btn_create.clicked.connect(lambda: create_event(self))
        button_layout.addWidget(self.btn_create)
        
        self.btn_edit = QPushButton(" Editar Evento")
        icono_edit = QIcon(os.path.join(ICON_DIR, "edit.png"))
        self.btn_edit.setIcon(icono_edit)
        self.btn_edit.setStyleSheet("background-color: #333333; color: white;")
        self.btn_edit.setFixedSize(120, 40)
        self.btn_edit.clicked.connect(lambda: edit_event(self))
        button_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton(" Borrar Evento")
        icono_delete = QIcon(os.path.join(ICON_DIR, "papelera.png"))
        self.btn_delete.setIcon(icono_delete)
        self.btn_delete.setStyleSheet("background-color: #333333; color: white;")
        self.btn_delete.setFixedSize(120, 40)
        self.btn_delete.clicked.connect(lambda: delete_event(self))
        button_layout.addWidget(self.btn_delete)        
        main_layout.addLayout(button_layout)
        
        # Botones de navegación (WhatsApp/Gmail/Salir)
        navbar = create_navbar("calendar", self.main_window)
        main_layout.addWidget(navbar)
        
        # Cargar eventos solo si hay conexión
        if self.has_internet:
            self.refresh_calendar_safe()
        else:
            print("[INFO] Modo offline - no se intenta conexión a calendario")

    def refresh_calendar_safe(self):
        """Refrescar calendario con manejo de conexión"""
        if not self.has_internet:
            from utils.common_functions import show_warning_dialog
            show_warning_dialog(self, "Modo Offline", "No hay conexión a Internet. Cargando eventos locales.")
            # Aquí puedes cargar eventos locales si existen
            return
        
        try:
            refresh_calendar(self)
        except Exception as e:
            from utils.common_functions import show_error_dialog
            show_error_dialog(self, "Error", f"Error al refrescar calendario: {e}")

    def update_current_month(self, year, month):
        """Actualizar el mes visible cuando el usuario navega."""
        self.current_month = f"{year}-{month:02d}"  # <<<< GUARDAR COMO 'YYYY-MM'

    def show_company_stats(self):
        """
        Mostrar estadísticas del mes actual al hacer clic en el botón.
        Llama a la función utilitaria.
        """
        from utils.stats_utils import show_company_stats
        show_company_stats(parent_window=self)

    def show_company_stats_month(self, month_str):
        """
        Mostrar estadísticas para un mes específico.
        Llama a la función utilitaria.
        Args:
            month_str (str): Cadena del mes en formato 'YYYY-MM'.
        """
        from utils.stats_utils import show_company_stats_month
        show_company_stats_month(parent_window=self.main_window, month_str=month_str)
    
    def show_success_dialog(parent, title, message):
        """Mostrar un mensaje de éxito con icono de tick."""
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setStyleSheet("background-color: #333333; color: white;")

        layout = QVBoxLayout()

        # Icono de éxito
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(os.path.join("data", "icon", "tick.png")).pixmap(32, 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(icon_label)

        # Mensaje
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(message_label)

        # Botón OK
        btn_ok = QPushButton("OK")
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                color: white;
                border: 1px solid #555;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignRight)

        dialog.setLayout(layout)
        dialog.exec()

    def show_error_dialog_custom(parent, title, message):
        """Mostrar un mensaje de error con icono de x."""
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setStyleSheet("background-color: #333333; color: white;")

        layout = QVBoxLayout()

        # Icono de error
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(os.path.join("data", "icon", "x.png")).pixmap(32, 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(icon_label)

        # Mensaje
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(message_label)

        # Botón OK
        btn_ok = QPushButton("OK")
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                color: white;
                border: 1px solid #555;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignRight)

        dialog.setLayout(layout)
        dialog.exec()     
        
    # __Links navegación__
    def show_main_screen(self):
        self.main_window.show_main_screen()

    def show_email(self):
        self.main_window.show_email()

    def show_gestion(self):
        self.main_window.show_gestion()

    def show_calendar(self):
        pass  

    def show_stats(self):
        """Abrir ventana de estadísticas como ventana independiente."""
        from utils.stats_utils import show_company_stats
        self.show()  # Mostrar temporalmente si es necesario
        show_company_stats(self.main_window)

    def close_application(self):
        from utils.common_functions import close_application
        close_application(self)