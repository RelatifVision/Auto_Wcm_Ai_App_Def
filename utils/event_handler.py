# utils/event_handler.py (corregido)
import datetime
from datetime import datetime, timedelta, timezone
from PyQt6.QtCore import Qt
from calendar_api_setting.calendar_api import create_event_api, get_events
from utils.calendar_utils import refresh_calendar
from utils.company_utils import get_company_color
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from utils.common_functions import show_error_dialog, show_info_dialog

def confirm_event(calendar_window, date, time):
    """
    Confirma un evento en el calendario con duración de 8 horas (jornada laboral).
    Ahora detecta conflicto si hay cualquier evento en la misma fecha.
    """
    from PyQt6.QtCore import QDate  # Importar QDate para la conversión
    
    # 1. Verificar si calendar_window es None (solo para refrescar después)
    if calendar_window is None:
        print("[WARNING] calendar_window es None en confirm_event. No se podrá refrescar el calendario después de crear el evento.")

    # 2. Verificar si ya hay algún evento en esa fecha
    events = get_events() # Siempre se obtienen los eventos de la API
    
    if isinstance(date, QDate):
        requested_date = date.toPyDate() # Convertir QDate a date
    else:
        requested_date = date # Si ya es date, usar directamente
    
    for event in events:
        event_start_str = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')

        if event_start_str:
            try:
                if 'T' in event_start_str: 
                    event_date_str = event_start_str[:10] 
                else: 
                    event_date_str = event_start_str
                
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
                
                # Comparar solo la fecha (día/mes/año)
                if requested_date == event_date:
                    show_conflict_dialog(event, requested_date, time)
                    return False  

            except ValueError as e:
                print(f"[WARNING] Error al parsear fecha del evento existente: {e}")
                continue

    # 3. Si no hay conflicto (ningún evento en la misma fecha), crear el evento
    start_datetime = datetime.combine(requested_date, time) 
    end_datetime = start_datetime + timedelta(hours=8)
    
    try:
        start_naive = start_datetime.replace(tzinfo=None)
        end_naive = end_datetime.replace(tzinfo=None)

        event_data = {
            "summary": f"Evento confirmado - {requested_date.strftime('%d/%m/%Y')} {time.strftime('%H:%M')}", # Usar requested_date
            "start": {
                "dateTime": start_naive.isoformat(),
                "timeZone": "Europe/Madrid"
            },
            "end": {
                "dateTime": end_naive.isoformat(),
                "timeZone": "Europe/Madrid"
            }
        }

        create_event_api(event_data)

        # 4. Refrescar calendario solo si calendar_window no es None
        if calendar_window is not None:
            refresh_calendar(calendar_window)
        else:
            print("[WARNING] No se pudo refrescar el calendario: calendar_window es None.")

        show_info_dialog(calendar_window, "Confirmación", "Evento confirmado exitosamente.")
        return True
    except Exception as e:
        show_error_dialog(calendar_window, "Error", f"Error al confirmar evento: {str(e)}")
        return False
   
def reject_event(calendar_window, date, time):
    """
    Rechaza un evento en el calendario.
    """
    if calendar_window is None:
        print("[ERROR] calendar_window es None en reject_event")
        return False

    # Aquí puedes implementar la lógica para rechazar un evento
    show_info_dialog(calendar_window, "Rechazo", "Evento rechazado.")
    return True

def show_conflict_dialog(conflicting_event, requested_start, requested_end):
    """
    Muestra una ventana emergente roja con información sobre el conflicto.
    """
    dialog = QDialog()
    dialog.setWindowTitle("Conflicto de horarios")
    from PyQt6.QtGui import QIcon
    dialog.setWindowIcon(QIcon("data/icon/alert.png"))
    dialog.setStyleSheet("""
        QDialog {
            background-color: #333333;
            color: white;
        }
        QLabel {
            color: white;
        }
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

    layout = QVBoxLayout()

    # Mensaje de error en rojo
    error_label = QLabel("¡Horario ocupado! Coincidencia detectada con otro evento:")
    error_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
    layout.addWidget(error_label)

    # Información del evento en conflicto
    summary = conflicting_event.get('summary', 'Evento desconocido')
    start_time_str = conflicting_event.get('start', {}).get('dateTime', 'Fecha/Hora desconocida')
    end_time_str = conflicting_event.get('end', {}).get('dateTime', 'Fecha/Hora desconocida')

    conflict_info = QLabel(f"Evento existente:\n  - Título: {summary}\n  - Inicio: {start_time_str}\n  - Fin: {end_time_str}")
    conflict_info.setStyleSheet("color: white;")
    layout.addWidget(conflict_info)

    combined_start = datetime.combine(requested_start, requested_end)
    combined_end = combined_start + timedelta(hours=8)
    requested_info = QLabel(f"\nSolicitado:\n  - Inicio: {combined_start.replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')}\n  - Fin: {combined_end.replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')}")
    requested_info.setStyleSheet("color: yellow;")  
    layout.addWidget(requested_info)

    # Botones de Aceptar/Rechazar
    buttons_layout = QHBoxLayout()

    accept_button = QPushButton("Aceptar")
    accept_button.setStyleSheet("""
        QPushButton {
            background-color: #4CAF50;  /* Verde */
            color: white;
            border: 1px solid #45a049;
            padding: 5px 10px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #45a045;
        }
    """)
    accept_button.clicked.connect(dialog.accept)
    buttons_layout.addWidget(accept_button)

    reject_button = QPushButton("Rechazar")
    reject_button.setStyleSheet("""
        QPushButton {
            background-color: #f44336;  /* Rojo */
            color: white;
            border: 1px solid #d32f2f;
            padding: 5px 10px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #d32f2f;
        }
    """)
    reject_button.clicked.connect(dialog.reject)
    buttons_layout.addWidget(reject_button)

    layout.addLayout(buttons_layout)

    dialog.setLayout(layout)
    dialog.exec()
