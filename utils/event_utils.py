# utils/event_utils.py

import json
import pandas as pd
from datetime import datetime
import re
import dateparser
from PyQt6.QtCore import QDate, QTime, QDateTime
from PyQt6.QtWidgets import QPushButton, QDialog, QFormLayout, QComboBox, QLineEdit, QTimeEdit, QMessageBox
from PyQt6.QtGui import QIcon, QColor, QTextCharFormat, QDoubleValidator
from calendar_api_setting.calendar_api import create_event_api, delete_event_api, edit_event_api, get_events
from utils.common_functions import show_info_dialog, show_error_dialog, confirm_action, show_success_dialog, show_error_dialog_custom
from utils.company_utils import get_company_name, get_company_color, get_task, get_company_data
from utils.dialog_utils import load_company_options
from utils.excel_utils import load_dataframe
from utils.common_functions import confirm_action
from config import EXCEL_FILE_PATH, TASK_OPTIONS

def create_event(calendar_window):
    selected_date = calendar_window.calendar.selectedDate().toString("yyyy-MM-dd")
    dialog = QDialog(calendar_window)
    form_layout = QFormLayout(dialog)
    empresas = load_company_options(EXCEL_FILE_PATH, 'datos_empresa')
    if not empresas:
        show_error_dialog(calendar_window, "Error", "No se encontraron empresas en el archivo Excel.")
        return
    calendar_window.company_input = QComboBox(dialog)
    calendar_window.company_input.addItems(empresas)
    calendar_window.task_input = QComboBox(dialog)
    calendar_window.task_input.addItems(TASK_OPTIONS)
    calendar_window.event_name_input = QLineEdit(dialog)
    calendar_window.location_input = QLineEdit(dialog)
    calendar_window.start_hour_input = QTimeEdit(dialog)
    calendar_window.end_hour_input = QTimeEdit(dialog)
    calendar_window.rate_input = QLineEdit(dialog)
    calendar_window.rate_input.setValidator(QDoubleValidator(0.0, 999999.99, 2, calendar_window.rate_input))
    form_layout.addRow("Empresa:", calendar_window.company_input)
    form_layout.addRow("Tarea:", calendar_window.task_input)
    form_layout.addRow("Nombre del evento:", calendar_window.event_name_input)
    form_layout.addRow("Ubicación:", calendar_window.location_input)
    form_layout.addRow("Tarifa:", calendar_window.rate_input)
    form_layout.addRow("Hora de inicio:", calendar_window.start_hour_input)
    form_layout.addRow("Hora de fin:", calendar_window.end_hour_input)
    btn_save = QPushButton("Guardar")
    btn_save.clicked.connect(lambda: save_event(calendar_window, dialog, selected_date))
    form_layout.addWidget(btn_save)
    dialog.setLayout(form_layout)
    dialog.setWindowTitle("Crear Evento")
    dialog.resize(300, 300)
    result = dialog.exec()
    if result == QDialog.DialogCode.Accepted:
        refresh_calendar(calendar_window)
        show_success_dialog(calendar_window, "Éxito", "Evento creado exitosamente.") 
        
def edit_event(calendar_window):
    selected_date = calendar_window.calendar.selectedDate().toString("yyyy-MM-dd")
    events = load_calendar_data(calendar_window, selected_date)
    if not events:
        show_info_dialog(calendar_window, "Información", "No hay eventos para editar en esta fecha.")
        return
    event = events[0]
    event_id = event['id']
    dialog = QDialog(calendar_window)
    form_layout = QFormLayout(dialog)
    empresas = load_company_options(EXCEL_FILE_PATH, 'datos_empresa')
    if not empresas:
        show_error_dialog(calendar_window, "Error", "No se encontraron empresas en el archivo Excel.")
        return
    calendar_window.company_input = QComboBox(dialog)
    calendar_window.company_input.addItems(empresas)
    calendar_window.company_input.setCurrentText(get_company_name(event))
    calendar_window.task_input = QComboBox(dialog)
    calendar_window.task_input.addItems(TASK_OPTIONS)
    calendar_window.task_input.setCurrentText(get_task(event))
    calendar_window.event_name_input = QLineEdit(dialog)
    calendar_window.event_name_input.setText(event['summary'])
    calendar_window.location_input = QLineEdit(dialog)
    calendar_window.location_input.setText(event.get('location', ''))
    start_time_str = event['start']['dateTime'][11:16]
    end_time_str = event['end']['dateTime'][11:16]
    start_time = QTime.fromString(start_time_str, "HH:mm")
    end_time = QTime.fromString(end_time_str, "HH:mm")
    calendar_window.start_hour_input = QTimeEdit(dialog)
    calendar_window.start_hour_input.setTime(start_time)
    calendar_window.end_hour_input = QTimeEdit(dialog)
    calendar_window.end_hour_input.setTime(end_time)
    calendar_window.rate_input = QLineEdit(dialog)
    calendar_window.rate_input.setText(event.get('description', ''))
    form_layout.addRow("Empresa:", calendar_window.company_input)
    form_layout.addRow("Tarea:", calendar_window.task_input)
    form_layout.addRow("Nombre del evento:", calendar_window.event_name_input)
    form_layout.addRow("Ubicación:", calendar_window.location_input)
    form_layout.addRow("Hora de inicio:", calendar_window.start_hour_input)
    form_layout.addRow("Hora de fin:", calendar_window.end_hour_input)
    form_layout.addRow("Tarifa:", calendar_window.rate_input)
    btn_save = QPushButton("Guardar")
    btn_save.clicked.connect(lambda: save_edited_event(calendar_window, dialog, event_id, selected_date))
    form_layout.addWidget(btn_save)
    dialog.setLayout(form_layout)
    dialog.setWindowTitle("Editar Evento")
    dialog.resize(300, 300)
    result = dialog.exec()
    if result == QDialog.DialogCode.Accepted:
        refresh_calendar(calendar_window)
        show_success_dialog(calendar_window, "Éxito", "Evento editado exitosamente.") 
           
def save_event(calendar_window, dialog, selected_date):
    from utils.company_utils import build_event_description
    """Guardar el evento personalizado en Google Calendar."""
    company = calendar_window.company_input.currentText()
    company_info = get_company_data(company, load_dataframe(EXCEL_FILE_PATH, sheet_name='datos_empresa'))
    jornada_precio = company_info.get('Jornada_Precio', 0)
    description = build_event_description(str(jornada_precio), company)
    task = calendar_window.task_input.currentText()
    event_name = calendar_window.event_name_input.text()
    location = calendar_window.location_input.text()
    start_time = calendar_window.start_hour_input.time().toString("HH:mm")
    end_time = calendar_window.end_hour_input.time().toString("HH:mm")
    start_datetime = f"{selected_date}T{start_time}:00"
    end_datetime = adjust_end_datetime(selected_date, start_time, end_time)
    params = {
        "summary": event_name,
        "location": location,
        "description": description,
        "start": {"dateTime": start_datetime},
        "end": {"dateTime": end_datetime},
        "transparency": "opaque",
        "company": company,
        "task": task,
        "color": get_company_color(company)  # Obtener el color desde la empresa
    }
    try:
        create_event_api(params, calendar_window)
        dialog.accept()
        refresh_calendar(calendar_window)
    except Exception as e:
        show_error_dialog_custom(calendar_window, "Error", f"Error al crear el evento: {e}") 

def save_edited_event(calendar_window, dialog, event_id, selected_date):
    """Guardar los cambios del evento editado en Google Calendar."""
    from utils.company_utils import build_event_description # Importar aquí si no está arriba
    try:
        # Obtener datos del formulario del diálogo
        company = calendar_window.company_input.currentText()
        task = calendar_window.task_input.currentText()
        event_name = calendar_window.event_name_input.text()
        location = calendar_window.location_input.text()
        start_time = calendar_window.start_hour_input.time().toString("HH:mm")
        end_time = calendar_window.end_hour_input.time().toString("HH:mm")
        rate = calendar_window.rate_input.text().strip()

        # Obtener información de la empresa
        company_info = get_company_data(company, load_dataframe(EXCEL_FILE_PATH, sheet_name='datos_empresa'))
        if not company_info:
             show_error_dialog_custom(calendar_window, "Error", f"No se encontraron datos para la empresa: {company}")
             return # Salir si no se encuentra la empresa

        jornada_precio = company_info.get('Jornada_Precio', 0)
        # Si no se ingresó una tarifa, usar la de la empresa
        if not rate:
            rate = str(jornada_precio)
        # Construir la descripción correctamente
        description = build_event_description(rate, company)

        # Ajustar fechas/horas
        start_datetime = f"{selected_date}T{start_time}:00"
        end_datetime = adjust_end_datetime(selected_date, start_time, end_time)

        # Preparar datos para la API
        nuevos_datos = {
            "summary": event_name,
            "location": location,
            "description": description,
            "start": {"dateTime": start_datetime},
            "end": {"dateTime": end_datetime},
            "transparency": "opaque",
            "company": company,
            "task": task,
            "color": get_company_color(company) # Obtener el color desde la empresa
        }

        # Llamar a la API para editar
        edit_event_api(event_id, nuevos_datos, calendar_window)
        dialog.accept() # Cerrar el diálogo de edición
        refresh_calendar(calendar_window) # Refrescar el calendario
        # Mostrar mensaje de éxito (opcional, lo haces en edit_event después de dialog.exec())
        # show_success_dialog(calendar_window, "Éxito", "Evento editado exitosamente.")

    except Exception as e:
        error_msg = f"Error al editar el evento: {str(e)}"
        print(f"[ERROR] {error_msg}") # Loggear el error
        show_error_dialog_custom(calendar_window, "Error", error_msg)

def delete_event(calendar_window):
    """Borrar evento seleccionado en el calendario."""
    selected_date = calendar_window.calendar.selectedDate().toString("yyyy-MM-dd")
    events = load_calendar_data(calendar_window, selected_date)
    if not events:
        show_info_dialog(calendar_window, "Información", "No hay eventos para borrar en esta fecha.")
        return

    event = events[0] 
    event_id = event['id']

    # Crear diálogo de confirmación con icono de papelera
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout
    from PyQt6.QtGui import QIcon
    from PyQt6.QtCore import Qt
    from config import ICON_DIR  # Aseguramos que ICON_DIR esté disponible
    import os

    dialog = QDialog(calendar_window)
    dialog.setWindowTitle("Confirmar Eliminación")
    dialog.setWindowIcon(QIcon(os.path.join("data", "icon", "papelera.png")))  # Icono de papelera
    dialog.setStyleSheet("background-color: #333333; color: white;")

    layout = QVBoxLayout()

    # Icono de papelera en el contenido del diálogo
    icon_label = QLabel()
    icon_label.setPixmap(QIcon(os.path.join("data", "icon", "papelera.png")).pixmap(32, 32))
    icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    layout.addWidget(icon_label)

    # Mensaje
    message_label = QLabel("¿Está seguro de que desea eliminar esta entrada?")
    message_label.setWordWrap(True)
    message_label.setStyleSheet("font-size: 14px;")
    layout.addWidget(message_label)

    # Botones
    button_layout = QHBoxLayout()
    
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
    btn_ok.clicked.connect(lambda: dialog.done(QDialog.DialogCode.Accepted))

    btn_cancel = QPushButton("Cancelar")
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

    if result == QDialog.DialogCode.Accepted:
        try:
            delete_event_api(event_id, calendar_window)
            refresh_calendar(calendar_window)
            # Mostrar mensaje de éxito
            show_success_dialog(calendar_window, "Éxito", "Evento eliminado exitosamente.")

        except Exception as e:
            error_msg = f"Error al borrar el evento: {str(e)}"
            print(f"[ERROR] {error_msg}") 
            show_error_dialog_custom(calendar_window, "Error", error_msg) 

def adjust_end_datetime(selected_date, start_time, end_time):
    """Ajustar la fecha de fin si es posterior a 00:00."""
    start_datetime = f"{selected_date}T{start_time}:00"
    end_datetime = f"{selected_date}T{end_time}:00"
    
    start_datetime_obj = QDateTime.fromString(start_datetime, "yyyy-MM-ddTHH:mm:ss")
    end_datetime_obj = QDateTime.fromString(end_datetime, "yyyy-MM-ddTHH:mm:ss")
    
    if end_datetime_obj < start_datetime_obj:
        end_datetime_obj = end_datetime_obj.addDays(1)
    
    return end_datetime_obj.toString("yyyy-MM-ddTHH:mm:ss")

def refresh_calendar(calendar_window):
    try:
        events = get_events()
        events_by_date = {}
        for event in events:
            try:
                if 'dateTime' in event.get('start', {}):
                    start_date_str = event['start']['dateTime'][:10]
                elif 'date' in event.get('start', {}):
                    start_date_str = event['start']['date']
                else:
                    continue
                start_date = QDate.fromString(start_date_str, "yyyy-MM-dd")
                if not start_date.isValid():
                    continue
                company = get_company_name(event)
                event_data = {"company": company, "start": event["start"], "end": event["end"]}
                if start_date not in events_by_date:
                    events_by_date[start_date] = []
                events_by_date[start_date].append(event_data)
            except Exception as e:
                print(f"Error procesando evento: {e}")
                continue
        calendar_window.calendar.set_events_by_date(events_by_date)
        calendar_window.calendar.update()
    except Exception as e:
        show_error_dialog(calendar_window, "Error", f"Error al refrescar: {str(e)}")

def load_calendar_data(calendar_window, selected_date):
    try:
        events = get_events()
        events_on_date = [event for event in events if 'start' in event and 'dateTime' in event['start'] and event['start']['dateTime'].startswith(selected_date)]
        return events_on_date
    except Exception as e:
        show_error_dialog(calendar_window, "Error", f"Error al cargar los eventos: {e}")
        return []
