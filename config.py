import os
COMPANY_EMAIL_ADDRESS = None
COOP_EMAIL_ADDRESS = None
EMAIL_ADDRESS = "CORREO_ELECTRONICO" 
APP_PASSWORD = "PASSWORD_APP" 
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465
SMTP_PORT = 587
IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
EXCEL_FILE_PATH = r'data\db.xlsx'
SERVICE_ACCOUNT_FILE = './calendar_api_setting/service-account-file.json'
CALENDAR_ID = 'ID_CALENDAR' 
ICON_DIR = os.path.join(os.path.dirname(__file__), 'data', 'icon')

CREDENTIALS_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), 
        './calendar_api_setting/credentials.json'
    )
)
TOKEN_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), 
        'token.json'
    )
)


# Opciones de tareas
TASK_OPTIONS = [
    "Técnico de Video",
    "Técnico de Iluminación",
    "Técnico pantalla Led",
    "Técnico de Streaming",
    "VideoMapping",
    "LedMapping",
    "Técnico Iluminación y Video",
    "Técnico Iluminación, Video y Sónido"
]