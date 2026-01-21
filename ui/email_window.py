# ui/email_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QWidget, QLineEdit, QMessageBox, QListWidget
)
from PyQt6.QtWidgets import QInputDialog, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from ui.auto_text_window import AutoTextWindow 
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
import os
import sys
import base64
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import imaplib
import email
from email.header import decode_header
import pandas as pd
from utils.common_functions import show_error_dialog, show_warning_dialog, show_info_dialog, confirm_action, close_application
from utils.company_utils import get_company_data
from utils.dialog_utils import load_company_options
from utils.excel_utils import load_dataframe
from utils.gui_utils import create_button, create_navbar
from utils.file_utils import select_files
from utils.mail_utills import clear_mail_message, load_inbox, load_drafts, get_mail_connection
from config import EMAIL_ADDRESS, APP_PASSWORD, SMTP_SERVER, SMTP_PORT, IMAP_SERVER

SCOPES = ['https://www.googleapis.com/auth/gmail.compose', 'https://www.googleapis.com/auth/gmail.readonly']

# Configuración de Gmail IMAP
IMAP_SERVER = "imap.gmail.com"

class EmailWindow(QMainWindow):    
    def __init__(self, main_window, has_internet=True):
        super().__init__()
        self.main_window = main_window
        self.has_internet = has_internet  # Estado de conexión
        self.attached_files = []
        self.sendfactura = False
        
        self.setWindowTitle("Gmail")
        self.setWindowIcon(QIcon(os.path.join("data", "icon", "gmail.png")))
        self.setGeometry(100, 100, 800, 800)
        
        # Inicializar mail_connection como None
        self.mail = None
        
        # Verificar conexión y mostrar mensaje si es necesario
        if not self.has_internet:
            from utils.common_functions import show_warning_dialog
            show_warning_dialog(self, "Conexión Limitada", "No hay conexión a Internet. Algunas funciones estarán limitadas.")
        
        # Widgets
        self.received_messages_area = QTextEdit()
        self.received_messages_area.setStyleSheet("background-color: #333333;")
        self.subject_input = QLineEdit()
        self.subject_input.setStyleSheet("background-color: #333333;")
        self.destination_input = QLineEdit()
        self.destination_input.setStyleSheet("background-color: #333333;")
        self.compose_area = QTextEdit()
        self.compose_area.setStyleSheet("background-color: #333333;")

        # Widget para mostrar archivos adjuntos
        self.attach_list = QListWidget() 
        self.attach_list.setStyleSheet("""
        QListWidget {background-color: #333; color: white; border: 1px solid #555;}
        QListWidget::item {padding: 5px;}""")
        self.attach_list.setFixedHeight(100) # Altura fija para la lista de adjuntos

        # Configuración de widgets
        self.received_messages_area.setReadOnly(True)
        self.received_messages_area.setPlaceholderText("Aquí aparecerán los mensajes recibidos...")
        self.subject_input.setPlaceholderText("Asunto")
        self.destination_input.setPlaceholderText("Destinatario")
        self.compose_area.setPlaceholderText("Escribe tu mensaje aquí...")

        # Estilos
        self.setStyleSheet("background-color: #212121;")
        button_style = """
            QPushButton {
                background-color: rgb(45, 45, 45); 
                color: white; 
                border: 2px solid #111111;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgb(220, 220, 220); 
                color: black;
            }
        """

        # Layout principal (vertical)
        main_layout = QVBoxLayout()

        # --- SECCIÓN DE MENSAJES RECIBIDOS ---
        received_layout = QVBoxLayout()
        received_label = QLabel("Emails recibidos", alignment=Qt.AlignmentFlag.AlignCenter)
        received_label.setStyleSheet("font-size: 20px; color: #ffffff;")
        received_layout.addWidget(received_label)
        received_layout.addWidget(self.received_messages_area)
        main_layout.addLayout(received_layout)

        # --- SECCIÓN DE ESCRITURA DE EMAIL ---
        compose_container = QWidget()
        compose_layout = QHBoxLayout()

        # Layout izquierdo (campos de texto)
        left_layout = QVBoxLayout()  
        email_label = QLabel("Escribir email", alignment=Qt.AlignmentFlag.AlignCenter)
        email_label.setStyleSheet("font-size: 20px; color: #ffffff;")
        left_layout.addWidget(email_label)
        left_layout.addWidget(self.subject_input)
        left_layout.addWidget(self.destination_input)
        left_layout.addWidget(self.compose_area)

        # Agregar la etiqueta de adjuntos y la lista
        left_layout.addWidget(QLabel("Archivos adjuntos:"))
        left_layout.addWidget(self.attach_list)

        # Layout derecho (botones de acción)
        action_buttons_layout = QVBoxLayout()
        action_buttons_layout.setSpacing(5)

        # __ BOTONES DE ACCIÓN __
        action_buttons_layout.addWidget(create_button(
            " Enviar",
            "send_message.png",
            self.send_email # <- Corrección aquí
        ))
        action_buttons_layout.addWidget(create_button(
            " Adjuntar",
            "adjuntar.png",
            lambda: select_files(self, ["*"], self.attach_list)  # cargar todos los tipos de archivo
        ))
        action_buttons_layout.addWidget(create_button(
            " Borrar",
            "papelera.png",
            lambda: self.clear_current_message() # Método para limpiar todo
        ))
        # action_buttons_layout.addWidget(create_button(
        #     " Guardar",
        #     "draft.png",
        #     self.save_email
        # ))

        compose_layout.addLayout(left_layout)
        compose_layout.addLayout(action_buttons_layout)
        compose_container.setLayout(compose_layout)
        main_layout.addWidget(compose_container)

        # --- SECCIÓN DE BOTONES ADICIONALES ---
        additional_buttons_layout = QHBoxLayout()
        additional_buttons_layout.addWidget(create_button(
            " Borradores",
            "drafts_view.png",
            self.load_drafts
        ))
        additional_buttons_layout.addWidget(create_button(
            " Recibidos",
            "email_receive.png",
            self.load_received_messages
        ))
        additional_buttons_layout.addWidget(create_button(
            " Autotext",
            "autotext.png",
            self.open_autotext_window
        ))
        main_layout.addLayout(additional_buttons_layout)

        # Navbar (sin 'email', pero con 'apagar' incluido)
        navbar = create_navbar("email", self.main_window)
        main_layout.addWidget(navbar)

        # Widget central
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Cargar datos iniciales solo si hay conexión
        if self.has_internet:
            try:
                self.mail = get_mail_connection()
                self.load_received_messages()
            except Exception as e:
                print(f"[WARNING] No se pudo conectar a Gmail: {e}")
                # No mostrar error aquí, solo cuando el usuario intente usar la función
        else:
            print("[INFO] Modo offline - no se intenta conexión a Gmail")

    def load_received_messages(self):
        """Cargar mensajes recibidos con manejo de conexión"""
        if not self.has_internet:
            self.received_messages_area.setPlainText("Modo offline: No hay mensajes disponibles.")
            return
            
        if not self.mail:
            try:
                self.mail = get_mail_connection()
            except Exception as e:
                self.received_messages_area.setPlainText(f"Error de conexión: {e}")
                return
        
        try:
            inbox_messages = load_inbox(self.mail, LIMIT=5)
            self.received_messages_area.setPlainText("\n".join(inbox_messages))
        except Exception as e:
            self.received_messages_area.setPlainText(f"Error al cargar mensajes: {e}")

    def load_drafts(self):
        """Cargar borradores con manejo de conexión"""
        if not self.has_internet:
            self.received_messages_area.setPlainText("Modo offline: No hay borradores disponibles.")
            return
            
        if not self.mail:
            try:
                self.mail = get_mail_connection()
            except Exception as e:
                self.received_messages_area.setPlainText(f"Error de conexión: {e}")
                return
        
        try:
            draft_messages = load_drafts(self.mail, LIMIT=10)
            self.received_messages_area.setPlainText("\n".join(draft_messages))
        except Exception as e:
            self.received_messages_area.setPlainText(f"Error al cargar borradores: {e}")

    def send_email(self):
        """
        Envía el correo electrónico con archivos adjuntos.
        """
        # 1. Obtener datos del formulario
        asunto = self.subject_input.text()
        destination = self.destination_input.text()
        message_text = self.compose_area.toPlainText()
        
        # 2. Validar campos obligatorios
        if not asunto or not destination or not message_text:
            show_warning_dialog(self, "Advertencia", "Todos los campos deben estar llenos.")
            return False, "Campos incompletos"
        
        # 3. Validar factura solo si está en modo "Enviar Factura"
        if getattr(self, 'sendfactura', False):
            success, message = self.validate_invoice_before_send()
            if not success:
                return False, message
        
        # 4. Continuar con el envío normal (resto del código existente)
        message = MIMEMultipart()
        message['Subject'] = asunto
        message['From'] = EMAIL_ADDRESS
        message['To'] = destination
        message.attach(MIMEText(message_text, "plain"))
        
        # Adjuntar archivos
        for file_path in self.attached_files:
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "rb") as file:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(file.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(file_path)
                    part.add_header("Content-Disposition", f"attachment; filename= {filename}")
                    message.attach(part)
                    print(f"[INFO] Archivo adjuntado: {file_path}")
                except Exception as e:
                    error_msg = f"Falló al adjuntar {file_path}: {e}"
                    print(f"[ERROR] {error_msg}")
                    show_error_dialog(self, "Error", error_msg)
                    continue
        
        # Enviar correo
        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(EMAIL_ADDRESS, APP_PASSWORD)
                server.sendmail(EMAIL_ADDRESS, destination, message.as_string())
            print("[INFO] Correo enviado exitosamente.")
            show_info_dialog(self, "Éxito", "Correo enviado exitosamente.")
            self.clear_current_message()
            return True, "Correo enviado exitosamente"
        except Exception as e:
            error_msg = f"Error al enviar correo: {e}"
            print(f"[ERROR] {error_msg}")
            show_error_dialog(self, "Error", error_msg)
            return False, error_msg

    def save_email(self):
        """
        Guardar el correo como borrador con validación condicional.
        """
        # Validar factura solo si está en modo "Enviar Factura"
        if getattr(self, 'sendfactura', False):
            success, message = self.validate_invoice_before_send()
            if not success:
                return False, message
        """
        Guardar el correo electrónico en borradores de Gmail.
        """
        # 1. Obtener datos del formulario
        asunto = self.subject_input.text()
        destination = self.destination_input.text()
        message_text = self.compose_area.toPlainText()

        # 2. Validar campos obligatorios
        if not asunto or not destination or not message_text:
            show_warning_dialog(self, "Advertencia", "Todos los campos (Asunto, Destinatario y Mensaje) deben estar llenos.")
            return False, "Campos incompletos"

        # 3. Crear el mensaje MIME base
        message = MIMEMultipart()
        message['Subject'] = asunto
        message['From'] = EMAIL_ADDRESS
        message['To'] = destination
        message.attach(MIMEText(message_text, "plain"))

        # --- 4. Adjuntar archivos 
        for file_path in self.attached_files:
            if os.path.isfile(file_path): # Verificar que el archivo exista
                try:
                    with open(file_path, "rb") as file:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(file.read())

                    # Codificar el archivo en base64
                    encoders.encode_base64(part)

                    # Definir el nombre del archivo y adjuntarlo
                    filename = os.path.basename(file_path)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {filename}" # Espacio después de ':'
                    )
                    message.attach(part)
                    print(f"[INFO] Archivo adjuntado al borrador: {file_path}")
                except Exception as e:
                    error_msg = f"Falló al adjuntar {file_path} al borrador: {e}"
                    print(f"[ERROR] {error_msg}")
                    show_error_dialog(self, "Error", error_msg)
            else:
                warning_msg = f"El archivo no existe o no es un archivo válido para adjuntar al borrador: {file_path}"
                print(f"[WARNING] {warning_msg}")
                # Opcional: advertir al usuario
                
        # -------------------------------------------------------------

        # --- 5. Convertir el mensaje MIME a formato raw para la API de Gmail ---
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # --- 6. Autenticación y Autorización con la API de Gmail ---
        creds = None
        token_path = os.path.join(os.path.dirname(__file__), 'token.json')
        # Asumiendo que credentials.json está en calendar_api_setting/ en la raíz del proyecto
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        credentials_path = os.path.join(project_root, 'calendar_api_setting', 'credentials.json')

        # Verificar existencia de credentials.json
        if not os.path.exists(credentials_path):
            error_msg = f"El archivo credentials.json no se encuentra en la ruta: {credentials_path}"
            print(f"[ERROR] {error_msg}")
            show_error_dialog(self, "Error", error_msg)
            return False, error_msg

        # Cargar token si existe
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # Si no hay credenciales válidas, iniciar flujo OAuth
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    error_msg = f"Error al refrescar el token: {e}"
                    print(f"[ERROR] {error_msg}")
                    show_error_dialog(self, "Error", error_msg)
                    return False, error_msg # Detener si no se puede refrescar
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    # Guardar las credenciales para la próxima ejecución
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                    print("[INFO] Nuevas credenciales guardadas.")
                except Exception as e:
                    error_msg = f"Error en el flujo de autenticación OAuth: {e}"
                    print(f"[ERROR] {error_msg}")
                    show_error_dialog(self, "Error", error_msg)
                    return False, error_msg # Detener si falla OAuth

        # ---------------------------------------------------------------
    
        # --- 7. Interactuar con la API de Gmail para crear el borrador ---
        try:
            # Construir el servicio de Gmail
            service = build('gmail', 'v1', credentials=creds)

            # Crear el cuerpo de la solicitud para el borrador
            create_draft_request_body = {
                'message': {
                    'raw': raw_message
                }
            }
            print(f"[DEBUG] Creando borrador con asunto: '{asunto}' para '{destination}'...")

            # Ejecutar la solicitud para crear el borrador
            draft = service.users().drafts().create(userId='me', body=create_draft_request_body).execute()

            success_msg = f"Borrador guardado con ID: {draft['id']}"
            show_info_dialog(self, "Éxito", "Correo guardado en borradores correctamente.")
            # Limpiar campos después de guardar
            self.clear_current_message()
            return True, success_msg # Devolver éxito

        except HttpError as error:
            # Manejar errores específicos de la API de Google
            error_msg = f"Error al guardar el borrador (HttpError): {error}"
            print(f"[ERROR] {error_msg}")
            show_error_dialog(self, "Error", f"Error al guardar el borrador: {error}")
            return False, error_msg # Devolver fallo
        except Exception as e:
            # Manejar cualquier otro error inesperado
            error_msg = f"Error inesperado al guardar el borrador: {e}"
            print(f"[ERROR] {error_msg}")
            show_error_dialog(self, "Error", f"Error inesperado: {e}")
            return False, error_msg # Devolver fallo
        # --------------------------------------------------------------------

    def clear_current_message(self):
        """Limpia todos los campos del formulario de correo, incluyendo adjuntos."""
        self.subject_input.clear()
        self.destination_input.clear()
        self.compose_area.clear()
        self.attach_list.clear()
        # Limpiar también la lista interna de rutas de archivos
        self.attached_files.clear()
        self.sendfactura=False   

    def return_mail(self, mail_ids):
        messages = []
        for num in mail_ids:
            # Obtener el contenido del correo
            status, msg_data = self.mail.fetch(num, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # Decodificar el mensaje
                    msg = email.message_from_bytes(response_part[1])

                    # Obtener el asunto
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")

                    # Obtener el remitente
                    from_email = msg.get("From")
                    messages.append(f"De: {from_email}\nAsunto: {subject}\n")
        return messages

    def load_received_messages(self):
        inbox_messages = load_inbox(self.mail, LIMIT=5)
        self.received_messages_area.setPlainText("\n\n".join(inbox_messages))

    def load_drafts(self):
        draft_messages = load_drafts(self.mail, LIMIT=10)
        self.received_messages_area.setPlainText("\n\n".join(draft_messages))

    # __AutoText Window__ 
    def open_autotext_window(self):
        """
        Abrir la ventana de textos predefinidos.
        """
        self.auto_text_window = AutoTextWindow(parent=self)
        self.auto_text_window.show()
        
    def set_auto_text(self, subject, text, to_email=None):
        """Actualizar campos con los valores recibidos"""
        self.subject_input.setText(subject)
        self.compose_area.setPlainText(text)
        if to_email:
            self.destination_input.setText(to_email)
        else:
            self.destination_input.setText(EMAIL_ADDRESS)
         
    def validate_invoice_before_send(self):
        """
        Validar factura adjunta antes de enviar (solo para 'Enviar Factura').
        """
        from utils.common_functions import show_warning_dialog, show_info_dialog
        
        # Verificar si hay archivos adjuntos
        if not self.attached_files:
            show_warning_dialog(self, "Advertencia", "Debe adjuntar una factura antes de enviar.")
            return False, "No hay factura adjunta"
        
        # Verificar si hay un PDF adjunto
        pdf_found = False
        pdf_path = None
        for file_path in self.attached_files:
            if file_path.lower().endswith('.pdf'):
                pdf_found = True
                pdf_path = file_path
                break
        
        if not pdf_found:
            show_warning_dialog(self, "Advertencia", "Debe adjuntar una factura PDF antes de enviar.")
            return False, "No hay factura PDF adjunta"
        
        # Verificar que el PDF exista
        if not os.path.exists(pdf_path):
            show_warning_dialog(self, "Error", f"El archivo PDF no existe: {pdf_path}")
            return False, f"Archivo PDF no existe: {pdf_path}"
        
        # Extraer texto del PDF
        from ia_processor.utils.ocr_utils import extract_text_from_file
        invoice_text = extract_text_from_file(pdf_path)
        if not invoice_text:
            show_warning_dialog(self, "Error", "No se pudo extraer texto de la factura PDF.")
            return False, "No se pudo leer la factura PDF"
        
        # Extraer importe de la factura
        importe_factura = self._extract_amount_from_invoice_text(invoice_text)
        if importe_factura is None:
            show_warning_dialog(self, "Advertencia", "No se encontró importe total en la factura PDF.")
            return False, "No se encontró importe en la factura"
        
        # Extraer importe del mensaje
        importe_mensaje = self._extract_amount_from_message_text(self.compose_area.toPlainText())
        if importe_mensaje is None:
            show_warning_dialog(self, "Advertencia", "No se encontró importe en el mensaje del correo.")
            return False, "No se encontró importe en el mensaje"
        
        # Comparar importes
        difference = abs(importe_factura - importe_mensaje)
        if difference > 0.01:  # Más de 1 céntimo de diferencia
            warning_msg = f"""
    Se encontró discrepancia en los importes:
    - Importe en factura PDF: {importe_factura:.2f}€
    - Importe en mensaje: {importe_mensaje:.2f}€
    - Diferencia: {difference:.2f}€

    ¿Desea continuar con el envío a pesar de la discrepancia?
            """.strip()
            if confirm_action(self, "Discrepancia encontrada", warning_msg):
                show_info_dialog(self, "Continuando", "Factura enviada a pesar de discrepancia de importe.")
                return True, "Validación pasada con discrepancia aceptada"
            else:
                return False, "Discrepancia de importe rechazada por el usuario"
        else:
            # Importes coinciden
            show_info_dialog(self, "Éxito", "La factura adjunta coincide con el mensaje.")
            return True, "Validación completada exitosamente"
        
    def _extract_amount_from_invoice_text(self, invoice_text):
        """
        Extrae el importe total de un texto de factura.
        Busca patrones como 'TOTAL: 1234.56€' o '(Total: 1234,56€)'
        """
        import re
        
        # Patrones comunes para importe total en facturas
        patterns = [
            r'(?:TOTAL|Total|Importe Total)[^\w\n]*([0-9.,]+)\s*€',
            r'\(Total:\s*([0-9.,]+)\s*€\)',
            r'(?:TOTAL|Total):\s*€?\s*([0-9.,]+)',
            r'(?:IMPORTE|Importe):\s*([0-9.,]+)\s*€'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, invoice_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        # Convertir a número (manejar comas como decimales)
                        amount_str = match.replace('.', '').replace(',', '.')  # 1.234,56 -> 1234.56
                        return float(amount_str)
                    except ValueError:
                        continue
        
        return None

    def _extract_amount_from_message_text(self, message_text):
        """
        Extrae el importe del mensaje del correo.
        Busca patrones como 'importe total de 1234.56€'
        """
        import re
        
        # Patrones comunes para importe en mensajes
        patterns = [
            r'(?:importe total|total|importe)\s*de?\s*([0-9.,]+)\s*€',
            r'([0-9.,]+)\s*€\s*(?:\+?\s*IVA)?',
            r'(?:factura|monto)\s*de\s*([0-9.,]+)\s*€'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        # Convertir a número (manejar comas como decimales)
                        amount_str = match.replace('.', '').replace(',', '.')  # 1.234,56 -> 1234.56
                        return float(amount_str)
                    except ValueError:
                        continue
        
        return None

    # Método para enviar correo validado
    def send_email_with_validation(self):
        """
        Enviar correo con validación previa.
        """
        # Validar factura antes de enviar
        if not self.validate_invoice_before_send():
            return
        
        pass  
            
    # Botones navegación
    def show_main_screen(self):
        self.main_window.show_main_screen()

    def show_calendar(self):
        self.main_window.show_calendar()

    def show_gestion(self):
        self.main_window.show_gestion()

    def show_stats(self):
        """Abrir ventana de estadísticas como ventana independiente."""
        from ui.calendar_window import CalendarWindow
        from utils.stats_utils import show_company_stats
       
        show_company_stats(self.main_window)
    
    def close_application(self):
        from utils.common_functions import close_application
        close_application(self)