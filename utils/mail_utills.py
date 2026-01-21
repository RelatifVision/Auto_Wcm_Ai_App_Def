# utils/mail_utills.py
import base64
import email
import imaplib
import os
import smtplib

from email import message_from_bytes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header  

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from config import EMAIL_ADDRESS, APP_PASSWORD, SMTP_SERVER, SMTP_PORT, IMAP_SERVER

SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose', 
    'https://www.googleapis.com/auth/gmail.readonly' 
]

def send_email(subject, recipient, body):
    """
    Envía un correo electrónico usando SMTP.
    Args:
        subject (str): Asunto del correo.
        recipient (str): Dirección del destinatario.
        body (str): Cuerpo del mensaje.
    Returns:
        tuple: (bool, str) Indicando éxito/mensaje.
    """
    # 1. Crear el mensaje MIME base
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = EMAIL_ADDRESS
    message['To'] = recipient
    message.attach(MIMEText(body, "plain"))

    # 2. Enviar el correo usando SMTP
    try:
        # Asegurarse de usar las variables importadas
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, APP_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient, message.as_string())
        print("[INFO] Correo enviado exitosamente.")
        return True, "Correo enviado exitosamente"
    except smtplib.SMTPException as e:
        error_msg = f"Error SMTP: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Error inesperado al enviar correo: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg

def save_draft(subject, recipient, body):
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = EMAIL_ADDRESS
    message['To'] = recipient
    message.attach(MIMEText(body, "plain"))
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    try:
        creds = _get_google_credentials()
        service = build('gmail', 'v1', credentials=creds)
        draft = service.users().drafts().create(userId='me', body={'message': {'raw': raw_message}}).execute()
        return True, f"Borrador guardado con ID: {draft['id']}"
    except Exception as e:
        return False, f"Error al guardar borrador: {str(e)}"

def load_inbox(mail_connection, LIMIT=5):
    try:
        mail_connection.select("inbox")
        status, messages = mail_connection.search(None, "ALL")
        if status != "OK":
            return []
        
        mail_ids = messages[0].split()
        if not mail_ids:
            return []
        
        if len(mail_ids) > LIMIT:
            mail_ids = mail_ids[-LIMIT:]  
            return process_messages(mail_connection, mail_ids)
    except Exception as e:
        print(f"Error al cargar mensajes recibidos: {e}")
        return []

def process_messages(mail_connection, mail_ids):
    messages = []
    for num in mail_ids:
        _, msg_data = mail_connection.fetch(num, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")
                from_email = msg.get("From")
                messages.append(f"De: {from_email}\nAsunto: {subject}")
    return messages

def get_mail_connection():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ADDRESS, APP_PASSWORD)
    return mail

def load_drafts(mail_connection, LIMIT=10):
    try:
        mail_connection.select('[Gmail]/Borradores')
        status, messages = mail_connection.search(None, "ALL")
        if status != "OK":
            return []
        
        mail_ids = messages[0].split()  
        if not mail_ids:
            return []
        
        if len(mail_ids) > LIMIT:
            mail_ids = mail_ids[-LIMIT:]  
        return process_emails(mail_connection, mail_ids)
    except Exception as e:
        print(f"Error al cargar borradores: {str(e)}")
        return []

def process_emails(mail_connection, mail_ids):
    messages = []
    for num in mail_ids:
        _, msg_data = mail_connection.fetch(num, "(RFC822)")
        for part in msg_data:
            if isinstance(part, tuple):
                msg = message_from_bytes(part[1])
                subject, _ = decode_header(msg["Subject"])[0]
                subject = subject.decode() if isinstance(subject, bytes) else subject
                from_email = msg.get("From")
                messages.append(f"De: {from_email}\nAsunto: {subject}")
    return messages

def clear_mail_message(subject_input, destination_input, compose_area, attach_list):
    subject_input.clear()
    destination_input.clear()
    compose_area.clear()
    attach_list.clear()


def _get_google_credentials():
    """
    Obtiene credenciales válidas de Google para la API de Gmail.
    Usa run_console() para evitar errores con run_local_server().
    """
    import os
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    # Rutas correctas
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    token_path = os.path.join(project_root, 'calendar_api_setting', 'token.json')
    credentials_path = os.path.join(project_root, 'calendar_api_setting', 'credentials.json')
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.compose', 'https://www.googleapis.com/auth/gmail.readonly']
    
    creds = None
    
    # Cargar token si existe
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"[WARNING] Error al cargar credenciales desde token: {e}")
            # Si hay un error al cargar el token, lo eliminamos para forzar una nueva autenticación
            os.remove(token_path)
            creds = None

    # Si no hay credenciales válidas, iniciar flujo OAuth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("[DEBUG] Token refrescado exitosamente.")
            except Exception as e:
                print(f"[WARNING] No se pudo refrescar el token: {e}. Iniciando nuevo login.")
                # Eliminar token si no se puede refrescar
                if os.path.exists(token_path):
                    os.remove(token_path)
                creds = None
        
        # Si aún no hay credenciales, iniciar flujo de autenticación por consola
        if not creds:
            if os.path.exists(credentials_path):
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    
                    # <-- USAR run_console() EN LUGAR DE run_local_server() -->
                    print("[INFO] Iniciando flujo de autenticación por consola...")
                    creds = flow.run_console()
                    # <-- FIN DEL CAMBIO -->

                    # Guardar las credenciales en la ubicación correcta
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                    print(f"[INFO] Nuevas credenciales guardadas en: {token_path}")
                    
                except Exception as e:
                    print(f"[ERROR] Error en el flujo OAuth: {e}")
                    return None
            else:
                print(f"[ERROR] Archivo credentials.json no encontrado en: {credentials_path}")
                return None

    return creds
