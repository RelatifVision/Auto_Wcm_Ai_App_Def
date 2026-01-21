# utils/calendar_utils.py
import json
import pandas as pd
from datetime import datetime
import re
import dateparser

from PyQt6.QtCore import QDate, QTime, QDateTime, Qt
from PyQt6.QtWidgets import QPushButton, QDialog, QFormLayout, QComboBox, QLineEdit, QTimeEdit, QMessageBox, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon, QColor, QTextCharFormat
from calendar_api_setting.calendar_api import create_event_api, get_events, delete_event_api, edit_event_api
from utils.company_utils import get_company_name, get_company_color, get_task, get_company_data
from utils.common_functions import show_info_dialog, show_error_dialog, confirm_action
from utils.dialog_utils import load_company_options
from utils.excel_utils import load_dataframe
from utils.event_utils import create_event, edit_event, delete_event
from config import EXCEL_FILE_PATH, TASK_OPTIONS

def refresh_calendar(calendar_window):
    try:
        events = get_events()
        events_by_date = {} 
        
        for event in events:
            try:
                # Verificar si existe 'dateTime' o 'date'
                if 'dateTime' in event.get('start', {}):
                    start_date_str = event['start']['dateTime'][:10]
                    # Extraer también la hora para manejar correctamente los eventos
                    start_datetime_str = event['start']['dateTime']
                elif 'date' in event.get('start', {}):
                    start_date_str = event['start']['date']
                    start_datetime_str = event['start']['date'] + "T00:00:00Z"  # Asignar hora por defecto
                else:
                    continue  # Saltar evento sin fecha válida
                
                start_date = QDate.fromString(start_date_str, "yyyy-MM-dd")
                if not start_date.isValid():
                    continue  # Saltar fechas inválidas
                
                company = get_company_name(event)
                # Incluir también la información de hora para comparaciones precisas
                event_data = {
                    "company": company,
                    "start": event["start"],
                    "end": event["end"],
                    "start_datetime_str": start_datetime_str  # Añadir para comparaciones
                }
                if start_date not in events_by_date:
                    events_by_date[start_date] = []
                events_by_date[start_date].append(event_data)
                
            except Exception as e:
                print(f"Error procesando evento {event.get('id', 'desconocido')}: {str(e)}")
                continue  # Continuar con el siguiente evento
        
        # Actualizar CustomCalendar
        if hasattr(calendar_window, 'calendar'):
            calendar_window.calendar.set_events_by_date(events_by_date)
            calendar_window.calendar.update()  # Forzar repintado
        else:
            print("[WARNING] calendar_window no tiene atributo 'calendar'")
        
    except Exception as e:
        show_error_dialog(calendar_window, "Error", f"Error al refrescar: {str(e)}")

def display_event_info(calendar_window, date):
    """Muestra detalles del evento con formato HTML y colores."""
    selected_date = date.toString("yyyy-MM-dd")
    events = load_calendar_data(calendar_window, selected_date)
    if not events:
        show_info_dialog(calendar_window, "Detalles", "No hay eventos para esta fecha.")
        return

    # Crear una ventana personalizada
    dialog = QDialog(calendar_window)
    dialog.setWindowTitle(f"Detalles de eventos para {selected_date}")
    dialog.setStyleSheet("background-color: #333333; color: white;")  # ← Fondo oscuro consistente
    layout = QVBoxLayout(dialog)

    # Título
    title_label = QLabel(f"<h3>Detalles de eventos para {selected_date}</h3>", alignment=Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet("color: white; font-size: 16px;")
    layout.addWidget(title_label)

    # Contenido de los eventos
    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_widget.setStyleSheet("background-color: #212121; padding: 10px; border-radius: 5px;")

    for event in events:
        company = get_company_name(event)
        task = get_task(event)
        start_time = event['start']['dateTime'][11:16]
        end_time = event['end']['dateTime'][11:16]
        event_color = get_company_color(company)
        formatted = (
            f"<div style='margin: 5px; padding: 5px; background-color: {event_color}; color: white; border-radius: 3px;'>"
            f"<strong>Empresa:</strong> {company}<br>"
            f"<strong>Tarea:</strong> {task}<br>"
            f"<strong>Evento:</strong> {event['summary']}<br>"
            f"<strong>Horario:</strong> {start_time} - {end_time}<br>"
            f"<strong>Ubicación:</strong> {event.get('location', 'N/A')}<br>"
            f"</div>"
        )
        content_layout.addWidget(QLabel(formatted, textFormat=Qt.TextFormat.RichText))

    layout.addWidget(content_widget)

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

def load_calendar_data(calendar_window, selected_date):
    """Cargar eventos para una fecha seleccionada desde Google Calendar."""
    try:
        events = get_events()
        events_on_date = [event for event in events if 'start' in event and 'dateTime' in event['start'] and event['start']['dateTime'].startswith(selected_date)]
        return events_on_date
    except Exception as e:
        show_error_dialog(calendar_window, "Error", f"Error al cargar los eventos: {e}")
        return []

def select_date(calendar_window, date):
    """Almacena la fecha seleccionada con un clic simple y actualiza la interfaz."""
    calendar_window.selected_date = date 
    events = load_calendar_data(calendar_window, date.toString("yyyy-MM-dd"))
    calendar_window.btn_edit.setEnabled(bool(events))
    calendar_window.btn_delete.setEnabled(bool(events))
