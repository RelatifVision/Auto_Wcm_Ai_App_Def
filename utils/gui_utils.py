# utils/gui_utils.py

import os
from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout, QDialog, QVBoxLayout, QLabel
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from utils.styles import BUTTON_STYLE, ICON_DIR 
from utils.common_functions import confirm_action

def create_button(text, icon_name, callback, fixed_size=(120, 40)):
    btn = QPushButton(text)
    btn.setIcon(QIcon(os.path.join(ICON_DIR, icon_name)))
    btn.setStyleSheet(BUTTON_STYLE)
    btn.setFixedSize(*fixed_size)
    btn.clicked.connect(callback)
    return btn


def get_close_function(current_window_name, main_window):
    def close_func():
        windows = {
            "calendar": main_window.calendar_window,
            "email": main_window.email_window,
            "stats": main_window.stats_window,
            "gestion": main_window.gestion_window,
        }
        if current_window_name in windows and windows[current_window_name] is not None:
            windows[current_window_name].close_application()
        else:
            main_window.close_application()
    return close_func

# Y luego en el botón:

def create_navbar(current_window_name, main_window):
    """
    Crea un navbar con botones comunes, excluyendo el de la ventana actual.
    current_window_name: "whatsapp", "calendar", "email", "gestion", "stats"
    main_window: instancia de MainWindow para conectar las funciones.
    El botón "Apagar" siempre aparece al final.
    """
    navbar = QWidget()
    layout = QHBoxLayout()
    navbar.setLayout(layout)

    # Estilo común para los botones (más pequeño)
    button_style = """
        QPushButton {
            background-color: #333333;
            color: white;
            border: 1px solid #555;
            padding: 6px 10px;  /* Reducir padding */
            font-size: 12px;    /* Reducir tamaño de fuente */
            min-width: 100px;   /* Ancho mínimo más pequeño */
            min-height: 30px;   /* Alto mínimo más pequeño */
        }
        QPushButton:hover {
            background-color: #444444;
        }
        QPushButton:pressed {
            background-color: #555555;
        }
    """

    # Definir botones y sus rutas de icono
    # "Apagar" se manejará por separado
    buttons = {
        "whatsapp": ("WhatsApp", "whatsapp.png", main_window.show_main_screen),
        "calendar": ("Calendar", "calendar.png", main_window.show_calendar),
        "email": ("Mail", "gmail.png", main_window.show_email),
        "gestion": ("Gestión", "gestion.png", main_window.show_gestion),
        "stats": ("Estadísticas", "stats.png", main_window.show_stats),
    }

    # Determinar qué botones mostrar (excluir el actual)
    exclude_key = current_window_name

    for key, (text, icon_file, callback) in buttons.items():
        if key != exclude_key:
            # Obtener el método desde main_window
            btn = QPushButton(text)
            icon_path = os.path.join(ICON_DIR, icon_file)
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                # Opcional: Aumentar el tamaño del icono si es necesario
                # btn.setIconSize(QSize(24, 24))  # Descomenta si quieres controlar el tamaño del icono
                btn.setIcon(icon)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
            # Añadir espaciado entre botones
            layout.setSpacing(30)  # Ajusta este valor según necesites (más pequeño)

    # Botón "Apagar" siempre al final
    btn_apagar = QPushButton("Apagar")
    icono_apagar = QIcon(os.path.join(ICON_DIR, "off.png"))
    btn_apagar.setIcon(icono_apagar)
    # Opcional: Aumentar el tamaño del icono del botón "Apagar"
    # btn_apagar.setIconSize(QSize(24, 24))
    btn_apagar.setStyleSheet(button_style)
    btn_apagar.clicked.connect(get_close_function(current_window_name, main_window))

        
    layout.addWidget(btn_apagar)

    # Alinear botones al centro
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    return navbar

def show_shutdown_confirmation(parent_window, title: str, message: str) -> bool:
    """
    Muestra un diálogo de confirmación de apagado simple y aislado.
    
    Args:
        parent_window: La ventana que solicita el cierre (será el parent del diálogo).
        title: Título del diálogo.
        message: Mensaje de confirmación.
        
    Returns:
        bool: True si el usuario confirma, False en caso contrario.
    """
    from PyQt6.QtWidgets import QMessageBox
    # Crear un QMessageBox estándar, asegurando que el parent sea la ventana correcta
    # Esto lo aisla completamente de MainWindow en términos de jerarquía de widgets.
    reply = QMessageBox.question(
        parent_window,  # Crucial: parent es la ventana que llama
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    return reply == QMessageBox.StandardButton.Yes
