# ui/main_window.py
import os
from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from PyQt6.QtGui import QIcon
from utils.whatsapp_utils import create_main_screen_widget, show_test_dialog_logic, save_test_message_logic
class MainWindow(QMainWindow):
    def __init__(self, has_internet=True):
        super().__init__()
        self.chats = []
        self.email_window = None
        self.calendar_window = None
        self.gestion_window = None
        self.stats_window = None
        self.has_internet = has_internet  # Estado de conexión

        self.setWindowTitle("WhatsApp")
        self.setWindowIcon(QIcon(os.path.join("data", "icon", "whatsapp.png")))
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #212121;")

        # Widget central
        self.stacked_widget = QStackedWidget()
        # Llamar a la función que crea el widget principal
        self.main_screen = create_main_screen_widget(self)
        self.stacked_widget.addWidget(self.main_screen)
        self.setCentralWidget(self.stacked_widget)

        # Cargar datos iniciales
        from utils.whatsapp_utils import load_and_display_data
        load_and_display_data(self)

    def handle_chat_action(self, url):
        """
        Wrapper para llamar a la función de handle_chat_action en utils.
        """
        from utils.whatsapp_utils import handle_chat_action_logic
        handle_chat_action_logic(self, url)

    def show_test_dialog(self):
        """
        Wrapper para llamar a la función de show_test_dialog en utils.
        """
        from utils.whatsapp_utils import show_test_dialog_logic
        show_test_dialog_logic(self) 

    # Métodos NavBar
    def show_calendar(self):
        """Abrir ventana de calendario como ventana independiente."""
        if not hasattr(self, 'calendar_window') or self.calendar_window is None:
            from ui.calendar_window import CalendarWindow
            self.calendar_window = CalendarWindow(main_window=self)
        self.calendar_window.show()
        self.calendar_window.raise_()  # Traer al frente si ya estaba abierta
        self.calendar_window.activateWindow()

    def show_email(self):
        """Abrir ventana de email como ventana independiente."""
        if not hasattr(self, 'email_window') or self.email_window is None:
            from ui.email_window import EmailWindow
            self.email_window = EmailWindow(main_window=self)
        self.email_window.show()
        self.email_window.raise_()
        self.email_window.activateWindow()

    def show_gestion(self):
        """Abrir ventana de gestión como ventana independiente."""
        if not hasattr(self, 'gestion_window') or self.gestion_window is None:
            from ui.gestion_window import GestionWindow
            self.gestion_window = GestionWindow(main_window=self)
        self.gestion_window.show()
        self.gestion_window.raise_()
        self.gestion_window.activateWindow()

    def show_stats(self):
        """
        Abrir ventana de estadísticas desde el navbar.
        """
        # Llamar a la función utilitaria, pasándose a sí mismo (self)
        from utils.stats_utils import show_company_stats
        show_company_stats(self)

    def show_main_screen(self):
        """Traer la ventana principal (WhatsApp) al frente."""
        self.show()
        self.raise_()
        self.activateWindow()

    def close_application(self):
        from utils.common_functions import close_application
        close_application(self)