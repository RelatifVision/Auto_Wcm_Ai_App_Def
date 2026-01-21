# utils/common_functions.py

import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox, QApplication, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog, QMainWindow
from config import ICON_DIR
def show_error_dialog(parent, title, message):
    """Mostrar un mensaje de error con estilo oscuro."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setStyleSheet("background-color: #333333; color: white;")

    layout = QVBoxLayout()

    # Icono de error
    icon_label = QLabel()
    icon_label.setPixmap(QIcon.fromTheme("dialog-error").pixmap(32, 32))
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

def show_info_dialog(parent, title, message):
    """Mostrar un mensaje informativo con estilo oscuro."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setStyleSheet("background-color: #333333; color: white;")

    layout = QVBoxLayout()

    # Icono de información
    icon_label = QLabel()
    icon_label.setPixmap(QIcon.fromTheme("dialog-information").pixmap(32, 32))
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

def confirm_action(parent, title, message):
    """Mostrar un cuadro de diálogo de confirmación con icono de apagado rojo."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setStyleSheet("background-color: #333333; color: white;")

    # --- Establecer el icono 'off.png' para la ventana del diálogo ---
    off_icon_path = os.path.join(ICON_DIR, "off.png")
    if os.path.exists(off_icon_path):
        dialog.setWindowIcon(QIcon(off_icon_path))
    else:
        # Si no se encuentra, puedes usar un icono por defecto o mostrar un mensaje
        print(f"[WARNING] Icono no encontrado: {off_icon_path}")

    layout = QVBoxLayout()

    # Icono de apagado rojo
    icon_label = QLabel()
    icon_label.setPixmap(QIcon(os.path.join("data", "icon", "off.png")).pixmap(32, 32)) 
    icon_label.setStyleSheet("QLabel { color: red; }")  # Color rojo
    icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    layout.addWidget(icon_label)

    # Mensaje
    message_label = QLabel(message)
    message_label.setWordWrap(True)
    message_label.setStyleSheet("font-size: 14px;")
    layout.addWidget(message_label)

    # Botones
    button_layout = QHBoxLayout()
    # --- Botón OK ---
    btn_ok = QPushButton("OK")
    # if os.path.exists(off_icon_path):
    #     btn_ok.setIcon(QIcon(off_icon_path))
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
    btn_ok.clicked.connect(lambda: dialog.done(QDialog.DialogCode.Accepted))

    # --- Botón Cancelar ---
    btn_cancel = QPushButton("Cancelar")
    # Opcional: añadir icono a este botón
    # cancel_icon_path = os.path.join(ICON_DIR, "x.png")
    # if os.path.exists(cancel_icon_path):
    #     btn_cancel.setIcon(QIcon(cancel_icon_path))
    btn_cancel.setStyleSheet("""
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
    btn_cancel.clicked.connect(lambda: dialog.done(QDialog.DialogCode.Rejected))
    
    button_layout.addWidget(btn_ok)
    button_layout.addWidget(btn_cancel)
    layout.addLayout(button_layout)

    dialog.setLayout(layout)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted
    

def show_warning_dialog(parent, title, message):
    QMessageBox.warning(parent, title, message)

def show_success_dialog(parent, title, message):
    """
    Mostrar un diálogo de éxito con icono de tick y tamaño ajustado.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setStyleSheet("background-color: #333333; color: white;")
    
    # Icono de tick en la ventana del diálogo
    tick_icon_path = os.path.join(ICON_DIR, "tick.png")
    if os.path.exists(tick_icon_path):
        dialog.setWindowIcon(QIcon(tick_icon_path))

    # Establecer tamaño mínimo (más ancho)
    dialog.setMinimumWidth(400)  # Ajusta este valor según necesites

    layout = QVBoxLayout()

    # Icono de tick (opcional: puedes mostrarlo también dentro del diálogo)
    icon_label = QLabel()
    if os.path.exists(tick_icon_path):
        icon_label.setPixmap(QIcon(tick_icon_path).pixmap(48, 48))  # Tamaño del icono grande
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

# __Cerrar aplicación__

def close_application(window_instance):
    """
    Muestra un diálogo de confirmación y, si el usuario acepta, cierra la aplicación.
    También puede encargarse de guardar datos.
    """
    reply = confirm_action(
        window_instance,  # <-- Pasamos la ventana que llama como parent
        "Confirmar salida",
        "¿Está seguro que desea apagar la aplicación?"
    )
    if reply:  # Si el usuario hizo clic en OK/Aceptar
        if hasattr(window_instance, 'save_data'):
            try:
                window_instance.save_data()
            except Exception as e:
                print(f"[ERROR] Error al guardar datos: {e}")

        # Cerrar la aplicación
        QApplication.instance().quit()
