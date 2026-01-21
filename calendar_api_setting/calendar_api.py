# calendar_api_settings\calendar_api.py
import os
from datetime import datetime, timedelta
from utils.company_utils import get_company_name, get_company_data
from utils.excel_utils import load_dataframe
from config import EXCEL_FILE_PATH
# Importaciones con manejo de errores
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("[ERROR] Bibliotecas de Google no instaladas. Ejecuta: pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    raise

from config import SERVICE_ACCOUNT_FILE, CALENDAR_ID
from utils.common_functions import show_error_dialog
from PyQt6.QtGui import QColor, QTextCharFormat
from PyQt6.QtCore import QDate

# Verificar si el archivo existe antes de continuar
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    raise Exception(f"El archivo de service account no se encuentra en: {SERVICE_ACCOUNT_FILE}")

# Alcances requeridos para la API de Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Obtener credenciales desde la cuenta de servicio
def get_credentials():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return creds
    except Exception as e:
        print(f"Error al cargar las credenciales: {str(e)}")
        raise

# Crear un evento en el calendario usando la cuenta de servicio
def create_event_api(params, calendar_window=None):
    try:
        credentials = get_credentials()
        service = build('calendar', 'v3', credentials=credentials)

        evento = {
            "summary": params["summary"],
            "location": params.get("location", "Madrid"),
            "description": params.get("description", ""),
            "start": {
                "dateTime": params["start"]["dateTime"],
                "timeZone": params.get("timezone", "Europe/Madrid"),
            },
            "end": {
                "dateTime": params["end"]["dateTime"],
                "timeZone": params.get("timezone", "Europe/Madrid"),
            },
            "transparency": params.get("transparency", "opaque"),
            "extendedProperties": {
                "private": {
                    "company": params.get("company", "VISUALMAX S.L."),
                    "task": params.get("task", "Técnico de video"),
                    "color": params.get("color", "#ba3a3a")
                }
            }
        }

        event = service.events().insert(calendarId=CALENDAR_ID, body=evento).execute()
        
    except Exception as e:
        error_msg = f"Error al crear el evento: {str(e)}"
        print(f"[ERROR] {error_msg}")
        if calendar_window:
            show_error_dialog(calendar_window, "Error de Calendario", error_msg)
        raise
    finally:
        if calendar_window:
            from utils.calendar_utils import refresh_calendar
            refresh_calendar(calendar_window)

def get_events():
    credentials = get_credentials()
    # Construir el servicio de Google Calendar
    service = build('calendar', 'v3', credentials=credentials)
    try:
        # Obtener eventos desde el 1 de enero de 2024 hasta el 31 de diciembre de 2030
        eventos = service.events().list(
            calendarId=CALENDAR_ID,
            singleEvents=True,
            orderBy='startTime',
            timeMin='2024-01-01T00:00:00Z',  # Desde el 1 de enero de 2024
            timeMax='2030-12-31T23:59:59Z',  # Hasta el 31 de diciembre de 2030
            fields='nextPageToken,items(id,summary,start,end,location,description,extendedProperties)'
        ).execute()
        eventos_lista = eventos.get('items', [])
        return eventos_lista
    except Exception as e:
        print(f"Error al obtener los eventos: {str(e)}")
        return []
    
def get_events_by_month(month_str):
    """
    Obtener eventos de un mes específico en formato 'YYYY-MM'.
    Args:
        month_str (str): Mes en formato 'YYYY-MM'.
    Returns:
        list: Lista de eventos.
    """
    credentials = get_credentials()
    service = build('calendar', 'v3', credentials=credentials)

    # Parsear el mes ingresado (ej: '2025-04')
    year, month = map(int, month_str.split('-'))

    # Calcular primer y último día del mes en UTC
    first_day = datetime.datetime(year, month, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    last_day = datetime.datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59, tzinfo=datetime.timezone.utc)

    # Convertir a formato ISO con 'Z'
    time_min = first_day.isoformat().replace('+00:00', 'Z')
    time_max = last_day.isoformat().replace('+00:00', 'Z')

    try:
        eventos = service.events().list(
            calendarId=CALENDAR_ID,
            singleEvents=True,
            orderBy='startTime',
            timeMin=time_min,  # Fecha de inicio en UTC
            timeMax=time_max,  # Fecha de fin en UTC
            fields='nextPageToken,items(id,summary,start,end,location,description,extendedProperties)'
        ).execute()
        eventos_lista = eventos.get('items', [])
        return eventos_lista
    except Exception as e:
        print(f"[ERROR] al obtener los eventos del mes {month_str}: {e}")
        return []

def get_events_by_year(year_str):
    """
    Obtener eventos de un año específico.
    Args:
        year_str (str): Año en formato 'YYYY'.
    Returns:
        list: Lista de eventos.
    """
    credentials = get_credentials()
    service = build('calendar', 'v3', credentials=credentials)

    # Parsear el año ingresado
    year = int(year_str)

    # Calcular primer y último día del año en UTC
    first_day = datetime.datetime(year, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    last_day = datetime.datetime(year, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)

    # Convertir a formato ISO con 'Z'
    time_min = first_day.isoformat().replace('+00:00', 'Z')
    time_max = last_day.isoformat().replace('+00:00', 'Z')

    try:
        eventos = service.events().list(
            calendarId=CALENDAR_ID,
            singleEvents=True,
            orderBy='startTime',
            timeMin=time_min,  # Fecha de inicio en UTC
            timeMax=time_max,  # Fecha de fin en UTC
            fields='nextPageToken,items(id,summary,start,end,location,description,extendedProperties)'
        ).execute()
        eventos_lista = eventos.get('items', [])
        return eventos_lista
    except Exception as e:
        print(f"[ERROR] al obtener los eventos del año {year_str}: {e}")
        return []

# Borrar un evento desde el calendario usando la cuenta de servicio
def delete_event_api(event_id, calendar_window=None):
    """Borrar evento y refrescar calendario."""
    credentials = get_credentials()
    # Construir el servicio de Google Calendar
    service = build('calendar', 'v3', credentials=credentials)
    try:
        # Eliminar el evento utilizando su ID y el ID del calendario proporcionado
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
    except Exception as e:
        print(f"Error al eliminar el evento: {e}")
        if calendar_window:
            show_error_dialog(calendar_window, "Error", f"Error al eliminar el evento: {str(e)}")
    finally:
        if calendar_window:
            refresh_calendar(calendar_window)

# Modificar un evento en el calendario usando la cuenta de servicio
def edit_event_api(event_id, nuevos_datos, calendar_window=None):
    """Editar evento y refrescar calendario."""
    creds = get_credentials()
    # Construir el servicio de Google Calendar
    service = build('calendar', 'v3', credentials=creds)
    try:
        # Obtener el evento original
        evento = service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
        # Actualizar los campos del evento con los nuevos datos
        evento['summary'] = nuevos_datos.get('summary', evento['summary'])
        evento['location'] = nuevos_datos.get('location', evento.get('location'))
        evento['description'] = nuevos_datos.get('description', evento.get('description'))
        evento['start'] = {'dateTime': nuevos_datos.get('start')['dateTime'], 'timeZone': 'Europe/Madrid'}
        evento['end'] = {'dateTime': nuevos_datos.get('end')['dateTime'], 'timeZone': 'Europe/Madrid'}
        evento['transparency'] = nuevos_datos.get('transparency', 'opaque')  # 'opaque' o 'transparent'
        evento['extendedProperties'] = {
            "private": {
                "company": nuevos_datos["company"],
                "task": nuevos_datos.get("task", "Sin tarea"),  # Asegúrate de incluir "task"
                "color": nuevos_datos["color"]
            }
        }
        # Actualizar el evento
        evento_actualizado = service.events().update(
            calendarId=CALENDAR_ID,
            eventId=event_id,
            body=evento
        ).execute()

    except HttpError as error:
        print(f"Error al modificar el evento: {error}")
        if calendar_window:
            show_error_dialog(calendar_window, "Error", f"Error al modificar el evento: {str(error)}")
    finally:
        if calendar_window:
            refresh_calendar(calendar_window)

def refresh_calendar(calendar_window):
    """Refrescar el calendario."""
    try:
        events = get_events()
        for event in events:
            company = get_company_name(event)
            df_comp = load_dataframe(EXCEL_FILE_PATH, 'datos_empresa')
            company_info = get_company_data(company, df_comp)
            try:
                # Verificar si existe 'dateTime' o 'date'
                if 'dateTime' in event.get('start', {}):
                    start_date_str = event['start']['dateTime'][:10]
                elif 'date' in event.get('start', {}):
                    start_date_str = event['start']['date']
                else:
                    continue  # Saltar evento sin fecha válida
                
                start_date = QDate.fromString(start_date_str, "yyyy-MM-dd")
                if not start_date.isValid():
                    continue  # Saltar fechas inválidas
            except Exception as e:
                print(f"Error procesando evento {event.get('id', 'desconocido')}: {str(e)}")
                continue  # Continuar con el siguiente evento
            
            color = company_info.get('Color', '#000000')

            format = QTextCharFormat()
            format.setBackground(QColor(color))
            calendar_window.calendar.setDateTextFormat(start_date, format)
    except Exception as e:
        show_error_dialog(calendar_window, "Error", f"Error al refrescar: {str(e)}")
