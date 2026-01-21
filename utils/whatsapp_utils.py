# utils/whatsapp_utils.py

import os
import datetime
from datetime import datetime as dttime, date as dt, time as dt_time, timedelta
from PyQt6.QtWidgets import QListWidget, QTextEdit
from PyQt6.QtCore import Qt
from utils.calendar_utils import create_event_api, get_company_color, refresh_calendar
from models.chat_parser import (
    load_chats, highlight_keywords, infer_date,
    handle_chat_message, check_availability, nlp, extract_location, extract_time
)
from utils.common_functions import show_info_dialog, show_error_dialog
from utils.event_handler import confirm_event, reject_event
from utils.file_utils import select_files, clear_whatsapp_message

def load_and_display_data(main_window):
    """
    Cargar y mostrar los datos de los chats.
    """
    try:
        main_window.chats = load_chats()
        main_window.chat_list.clear()
        main_window.chat_list_send.clear()
        for chat in main_window.chats:
            chat_name = chat.get("nombre", "Sin título")
            main_window.chat_list.addItem(chat_name)
            main_window.chat_list_send.addItem(chat_name)
    except Exception as e:
        show_error_dialog(main_window, "Error", f"Error al cargar los chats: {str(e)}")

def process_chat(messages, calendar_window):
    html_output = ''
    previous_date = None

    for msg in messages:
        date_str = msg.get("date", "")
        time_str = msg.get("time", "")
        sender = msg.get("sender", "")
        styled_message = msg.get("message", "")

        if not date_str:
            continue

        try:
            current_date = dttime.strptime(date_str, "%d/%m/%y")
            if date_str != previous_date:
                html_output += f'''
                    <div class="date-header">
                        <strong>{current_date.strftime("%d de %B de %Y")}</strong>
                    </div>
                '''
                previous_date = date_str
        except ValueError:
            continue

        # 1. Resaltar keywords generales (montos, fechas sueltas, etc.)
        styled_message = highlight_keywords(styled_message)

        # 2. Extraer información contextual específica del mensaje
        # Asumimos que extract_location y extract_time devuelven strings o None
        location = None
        extracted_time_str = None
        try:
            # Intentar importar desde models/chat_parser
            from models.chat_parser import extract_location, extract_time
            location = extract_location(styled_message)
            extracted_time_str = extract_time(styled_message)
        except ImportError:
            # Si no están definidas allí, puedes definirlas aquí localmente o manejar el error
            print("[WARNING] Funciones extract_location/extract_time no encontradas en models/chat_parser.py")

        # 3. Mostrar detalles extraídos con estilos
        # Solo mostrar si se encontró algo
        if location:
            styled_message += f'<div class="location-info" style="color: #00ff32; font-style: italic; margin: 5px 0;">Ubicación: {location}</div>'
        if extracted_time_str:
            styled_message += f'<div class="time-info" style="color: #00d4ff; font-style: italic; margin: 5px 0;">Horario Indicado: {extracted_time_str}</div>'
            
       # 4. Procesamiento con spaCy para fechas (ya se hizo highlight_keywords, pero este es para acciones)
        doc = nlp(styled_message)
        for ent in doc.ents:
            if ent.label_ == 'DATE':
                styled_message = styled_message.replace(
                    ent.text,
                    f'<span class="highlight">{ent.text}</span>' # Mantener estilo highlight
                )

        # 5. Generar botones de disponibilidad si se detectan palabras clave
        if "disponible" in styled_message.lower() or "libre" in styled_message.lower():
            # Llamar a infer_date que debe devolver (date, time)
            inferred_result = infer_date(styled_message)

            # Manejar el resultado de infer_date que puede ser date sola o (date, time)
            inferred_date = None
            inferred_time = None
            if isinstance(inferred_result, tuple):
                 inferred_date, inferred_time = inferred_result
                 # Asegurarse de que inferred_time sea un objeto time
                 if not isinstance(inferred_time, dt_time):
                     # Si infer_date devuelve (date, datetime), convertir
                     if hasattr(inferred_time, 'time'):
                         inferred_time = inferred_time.time()
                     else:
                         # Fallback si no es un time válido
                         inferred_time = dt_time(9, 0)
            else:
                 # Si es solo un date
                 inferred_date = inferred_result
                 inferred_time = dt_time(9, 0) # Hora por defecto

            # Asegurarse de que inferred_date sea un objeto date
            if inferred_date and isinstance(inferred_date, dt):
                response = handle_chat_message(styled_message, calendar_window)
                # Usar la hora extraída o la hora inferida por infer_date, o por defecto
                final_time_obj = None
                if extracted_time_str:
                    # Intentar parsear la hora extraída del texto
                    try:
                        final_time_obj = dttime.strptime(extracted_time_str, "%H:%M").time()
                    except ValueError:
                        # Si falla, usar la hora de infer_date
                        final_time_obj = inferred_time
                else:
                    # Usar la hora de infer_date
                    final_time_obj = inferred_time
                
                # Formato para la URL: DD-MM-YYYY HH:MM
                formatted_date_for_url = inferred_date.strftime("%d-%m-%Y")
                formatted_time_for_url = final_time_obj.strftime("%H.%M")
                datetime_str_for_url = f"{formatted_date_for_url}T{formatted_time_for_url}"
                styled_message += f"""
                    <div class="disponibilidad normal">
                        {response}
                        <a href='confirm://{datetime_str_for_url}'>Confirmar</a> |
                        <a href='reject://{datetime_str_for_url}'>Rechazar</a>
                    </div>
                """

        # Bloque de mensaje con estilo original
        html_output += f'''
            <div class="message-block">
                <div class="timestamp" title="{date_str}">
                    {time_str} - {sender}:
                </div>
                <div class="message-content">
                    {styled_message}
                </div>
                <hr class="message-divider">
            </div>
        '''

    return f'''
        <html>
        <head>
            <style>
                /* Estilos originales */
                body {{
                    background-color: #333;
                    color: white;
                    font-family: Arial, sans-serif;
                    padding: 10px;
                }}
                .date-header {{
                    text-align: center;
                    margin: 20px 0;
                    padding: 8px 12px;
                    background-color: #424242;
                    border-radius: 5px;
                    font-size: 1.1em;
                    color: #EEEEEE;
                }}
                .message-block {{
                    margin: 15px 0;
                    padding: 10px;
                    background-color: #212121;
                    border-radius: 5px;
                    position: relative;
                }}
                .timestamp {{
                    background-color: #000000;
                    color: white;
                    font-size: 0.9em;
                    padding: 5px 10px;
                    border-radius: 3px;
                    display: inline-block;
                    margin-bottom: 8px;
                }}
                .message-content {{
                    margin: 10px 0;
                    padding: 5px;
                    line-height: 1.4em;
                }}
                .highlight {{
                    background-color: #00d4ff;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-weight: bold;
                }}
                .disponibilidad {{
                    display: block;
                    margin: 10px 0;
                    padding: 8px;
                    border-radius: 5px;
                    font-weight: bold;
                    color: white;
                }}
                .disponibilidad.normal {{
                    background-color: #4CAF50;
                }}
                .disponibilidad.error {{
                    background-color: #FF5722;
                }}
                 .disponibilidad a {{
                     color: white;
                     text-decoration: none;
                     margin: 0 5px;
                     padding: 3px 7px;
                     border-radius: 3px;
                 }}
                 .disponibilidad a:hover {{
                     background-color: #616161;
                 }}
                .message-divider {{
                    border: none;
                    border-top: 1px solid #424242;
                    margin: 12px 0;
                }}
                /* Estilos para información extraída */
                .location-info {{
                    margin: 5px 0;
                    padding: 2px 4px;
                    border-radius: 3px;
                    background-color: #001a00; /* Fondo muy oscuro para verde */
                }}
                .time-info {{
                    margin: 5px 0;
                    padding: 2px 4px;
                    border-radius: 3px;
                    background-color: #000d1a; /* Fondo muy oscuro para azul */
                }}
            </style>
        </head>
        <body>
            <div class="chat-container">
                {html_output}
            </div>
        </body>
        </html>
    '''

# WhatsApp specific functions
def update_chat_content(main_window_instance, current_item, list_widget):
    try:
        if current_item:
            selected_chat_name = current_item.text()
            for chat in main_window_instance.chats: # Usar main_window_instance
                if chat["nombre"] == selected_chat_name:
                    # Validar que los mensajes tengan los campos necesarios
                    valid_messages = [
                        msg for msg in chat.get("messages", [])
                        if isinstance(msg, dict) and "date" in msg and "message" in msg
                    ]
                    # Asegurarse de que process_chat reciba parámetros correctos
                    formatted_chat = process_chat(valid_messages, main_window_instance) # Pasar main_window_instance
                    main_window_instance.chat_content.setHtml(formatted_chat) # Usar main_window_instance
                    break
    except Exception as e:
        print(f"[ERROR] Error en update_chat_content: {e}")
        
def create_event_from_message(message, calendar_window):
    inferred = infer_date(message)
    if not inferred:
        return False, "No se pudo inferir la fecha."

    start = inferred
    end = start + timedelta(days=1)

    task = "Tarea no especificada"
    location = "Ubicación no especificada"
    for keyword in ["instalar", "operar", "mantenimiento"]:
        if keyword in message.lower():
            task = keyword.title()

    if check_availability(start, end, calendar_window):
        create_event_api({
            "summary": f"{task} - {start.strftime('%d/%m/%Y')}",
            "location": location,
            "description": message,
            "start": {
                "dateTime": f"{start.isoformat()}T09:00:00Z",
                "timeZone": "Europe/Madrid"
            },
            "end": {
                "dateTime": f"{end.isoformat()}T17:00:00Z",
                "timeZone": "Europe/Madrid"
            },
            "extendedProperties": {
                "private": {
                    "company": "Empresa por defecto",
                    "task": task,
                    "color": get_company_color("Empresa por defecto")
                }
            }
        })
        if calendar_window is not None:
            from utils.calendar_utils import refresh_calendar 
            refresh_calendar(calendar_window)
        else:
            print("[DEBUG] calendar_window es None, no se puede refrescar el calendario.")
        return True, "Evento creado exitosamente"
    else:
        return False, "No hay disponibilidad en ese horario"

def send_wpp(main_window):
    # 1. Obtener el texto del mensaje
    message = main_window.message_input.toPlainText()
    selected_chat = main_window.chat_list_send.currentItem()
    destinatario = selected_chat.text() if selected_chat else "Sin destinatario"
    
    # Acceder directamente al QListWidget de adjuntos 
    attached_files_list_widget= getattr(main_window, 'attached_files', [])       
  
    message_text = f"El mensaje:\n\n{message}"
  
    if attached_files_list_widget:
        files_str = "\n- " + "\n- ".join([os.path.basename(f) for f in attached_files_list_widget])
        message_text += f"\n\nArchivos adjuntos:{files_str}"
    
    message_text += f"\n\nSerá enviado a '{destinatario}' por WhatsApp.\nAPIs de Meta no están disponibles."
    
    show_info_dialog(main_window, "Mensaje preparado", message_text)

def confirm_wpp(main_window):
    main_window.message_input.setText(
        "Confirmo la disponibilidad para las fechas indicadas. Evento creado en el calendario."
    )

def reject_wpp(main_window):
    main_window.message_input.setText(
        "Lamentablemente no hay disponibilidad para esas fechas. ¿Desea programar para otra fecha?"
    )

def clear_whatsapp_message(chat_list, compose_area, attach_list):
    chat_list.setCurrentRow(-1) # Deseleccionar item en la lista de chats
    compose_area.clear()
    attach_list.clear()

# Create_main_screen_widget UI
def create_main_screen_widget(main_window_instance):
    """
    Crea el widget principal de la pantalla de WhatsApp.
    """
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor, QIcon
    from utils.gui_utils import create_button, create_navbar # Asumiendo que create_button y create_navbar están aquí

    # Widget principal
    screen = QWidget()
    screen.setStyleSheet("background-color: #112211;")

    # Layout principal
    main_layout = QVBoxLayout(screen) # Crear y asignar directamente

    # Título Historial
    title_label = QLabel("Historial What'sApp", alignment=Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet("font-size: 20px; color: #ffffff;")
    main_layout.addWidget(title_label)

    # Crear widgets necesarios (esto reemplaza las variables de instancia de MainWindow)
    chat_content = create_chat_content_widget(main_window_instance) # Función nueva
    chat_list = create_chat_list_widget(main_window_instance, chat_content) # Función nueva

    # Layout de chats superior (historial)
    chat_layout = QHBoxLayout()
    chat_layout.addWidget(chat_list)
    chat_layout.addWidget(chat_content)
    main_layout.addLayout(chat_layout)

    # Sección de envío
    send_container = create_send_section_widget(main_window_instance) # Función nueva
    main_layout.addWidget(send_container)

    # Botones de acción (Confirmar, Test, Rechazar)
    button_layout = create_action_buttons_layout(main_window_instance) # Función nueva
    main_layout.addLayout(button_layout)

    # Navbar
    navbar = create_navbar("whatsapp", main_window_instance) # Asumiendo create_navbar está en utils
    main_layout.addWidget(navbar)

    # Asignar widgets como atributos a main_window_instance para que puedan ser usados por otras funciones
    main_window_instance.chat_content = chat_content
    main_window_instance.chat_list = chat_list
    main_window_instance.destination_input = None # Si es necesario, crearlo aquí
    main_window_instance.btn_confirm = None # Se crea en create_action_buttons_layout
    main_window_instance.btn_reject = None # Se crea en create_action_buttons_layout
    main_window_instance.btn_test = None # Se crea en create_action_buttons_layout
    main_window_instance.attach_list = None # Se crea en create_send_section_widget

    return screen

def create_chat_content_widget(main_window_instance):
    """
    Crea el widget de contenido del chat.
    """
    from PyQt6.QtWidgets import QTextBrowser
    chat_content = QTextBrowser()
    chat_content.setReadOnly(True)
    chat_content.setAcceptRichText(True)
    chat_content.setOpenExternalLinks(False)
    # Conectar la señal al wrapper en MainWindow
    chat_content.anchorClicked.connect(main_window_instance.handle_chat_action) # Conectar al wrapper
    chat_content.setStyleSheet("""
        QTextBrowser {
            background-color: #333333;
            color: white;
            font-family: Arial;
        }
    """)
    return chat_content

def create_chat_list_widget(main_window_instance, chat_content_widget):
    """
    Crea el widget de lista de chats.
    """
    from PyQt6.QtWidgets import QListWidget
    from utils.whatsapp_utils import update_chat_content # Importar localmente para evitar ciclos
    chat_list = QListWidget()
    chat_list.setFixedWidth(200)
    chat_list.setStyleSheet("QListWidget { background-color: #333333; color: white; }")
    # Conectar señal para actualizar contenido
    chat_list.currentItemChanged.connect(
        lambda current, prev: update_chat_content(main_window_instance, current, chat_list)
    )
    return chat_list

def create_send_section_widget(main_window_instance):
    """
    Crea el contenedor y layout para la sección de envío de mensajes.
    """
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTextEdit, QListWidget
    from utils.gui_utils import create_button 
    from utils.file_utils import select_files, clear_whatsapp_message 

    container = QWidget()
    layout = QVBoxLayout()

    # Título
    title_label = QLabel("Enviar What'sApp", alignment=Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet("font-size: 20px; color: #ffffff;")
    layout.addWidget(title_label)

    # Layout principal para la sección de envío
    message_layout = QHBoxLayout()

   
    # Lista de chats (izquierda) - Opcional, si se quiere una lista separada para enviar
    chat_list_send = create_chat_list_widget(main_window_instance, None) 
    # Asignar como atributo a main_window_instance
    main_window_instance.chat_list_send = chat_list_send
    message_layout.addWidget(chat_list_send, stretch=1)  

    # Área de mensaje (centro)
    message_input = QTextEdit()
    message_input.setStyleSheet("QTextEdit { background-color: #333333; color: white; }")
    message_layout.addWidget(message_input, stretch=2)  # Factor de expansión 2
    main_window_instance.message_input = message_input

    # Contenedor para botones (derecha)
    buttons_container = QWidget()
    buttons_layout = QVBoxLayout()
    buttons_layout.setSpacing(10)
    buttons_container.setLayout(buttons_layout)
    message_layout.addWidget(buttons_container, stretch=0)

    # Botón Enviar
    btn_send = create_button(
        " Enviar",
        "send_message.png",
        lambda: send_wpp(main_window_instance), 
        fixed_size=(120, 40)
    )
    buttons_layout.addWidget(btn_send)

    # Botón Adjuntar
    if not hasattr(main_window_instance, "attach_list"):
        attach_list = QListWidget() 
        attach_list.setStyleSheet("""
            QListWidget {background-color: #333; color: white; border: 1px solid #555;}
            QListWidget::item {padding: 5px;}""")
        attach_list.setMinimumHeight(10)
        attach_list.setFixedHeight(40)
        main_window_instance.attach_list = attach_list 
    attach_list = main_window_instance.attach_list
    btn_attach = create_button(
        " Adjuntar",
        "adjuntar.png",
        lambda: select_files(main_window_instance, ["*"], attach_list), # Pasar main_window_instance y attach_list
        fixed_size=(120, 40)
    )
    buttons_layout.addWidget(btn_attach)

    # Botón Borrar
    btn_delete = create_button(" Borrar", "papelera.png", lambda: clear_whatsapp_message(
            message_input,
            attach_list  
        ),
        fixed_size=(120, 40)
    )
    buttons_layout.addWidget(btn_delete)

    #message_layout.addLayout(buttons_layout)
    # Añadir el layout principal al contenedor
    layout.addLayout(message_layout)

    # Lista de adjuntos debajo del área de mensaje
    layout.addWidget(attach_list)

    container.setLayout(layout)
    return container

def create_action_buttons_layout(main_window_instance):
    """
    Crea el layout para los botones de acción (Confirmar, Test, Rechazar).
    """
    from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout
    from utils.gui_utils import create_button # Asumiendo create_button está en utils

    button_layout = QVBoxLayout()
    confirm_reject_layout = QHBoxLayout()

    # Crear botones y asignarlos como atributos de main_window_instance
    main_window_instance.btn_confirm = create_button(
        " Confirmar",
        "tick.png",
        lambda: confirm_wpp(main_window_instance) # Pasar main_window_instance
    )
    main_window_instance.btn_reject = create_button(
        " Rechazar",
        "x.png",
        lambda: reject_wpp(main_window_instance) # Pasar main_window_instance
    )
    main_window_instance.btn_test = create_button(
        " Test",
        "test.png",
        main_window_instance.show_test_dialog, # Pasar la función como callback - ESTO DEBE FUNCIONAR AHORA
        fixed_size=(120, 40)
    )
    main_window_instance.btn_test.setStyleSheet("background-color: #333333; color: white;")

    confirm_reject_layout.addWidget(main_window_instance.btn_confirm)
    confirm_reject_layout.addWidget(main_window_instance.btn_test)
    confirm_reject_layout.addWidget(main_window_instance.btn_reject)
    button_layout.addLayout(confirm_reject_layout)
    return button_layout

def handle_chat_action_logic(main_window_instance, url): 
    """
    Procesa las acciones de los enlaces 'Confirmar'/'Rechazar' en el chat.
    """
    try: # <-- Inicio del try
        # 1. Obtener la URL como string
        url_str = url.toString().strip()

        # 2. Validaciones básicas de la URL
        if not url_str:
            raise ValueError("URL vacía recibida.")
        if '://' not in url_str:
            raise ValueError(f"URL malformada (falta '://'): '{url_str}'")

        # 3. División SEGURA de la URL
        parts = url_str.split('://', 1)
        if len(parts) != 2:
            raise ValueError(f"Formato de URL inválido: '{url_str}'")

        action, date_str = parts

        # 4. Validar que 'action' sea conocida
        if action not in ['confirm', 'reject']:
            raise ValueError(f"Acción desconocida: '{action}'")

        # 5. Validar que 'date_str' no esté vacío
        if not date_str:
            raise ValueError("La URL no contiene datos de fecha.")

        # 6. Parsear la fecha (formato esperado: DD-MM-YYYYTHH.MM)
        try:
            # Formato: DD-MM-YYYYTHH.MM
            date_part, time_part = date_str.split('t', 1)
            inferred_date = dttime.strptime(date_part, "%d-%m-%Y").date()
            inferred_time = dttime.strptime(time_part, "%H.%M").time()
        except ValueError as ve:
            raise ValueError(f"Error al parsear la fecha '{date_str}': {ve}")


        # 7. Llamar a las funciones correspondientes
        if action == 'confirm':
            confirm_event(main_window_instance.calendar_window, inferred_date, inferred_time) # Usar main_window_instance
        elif action == 'reject':
            reject_event(main_window_instance.calendar_window, inferred_date, inferred_time) # Usar main_window_instance
            
        # 8. Actualizar contenido del chat
        current_item = main_window_instance.chat_list.currentItem() # Usar main_window_instance
        if current_item:
            update_chat_content(main_window_instance, current_item, main_window_instance.chat_list) # Usar main_window_instance

    except Exception as e: # <-- Añadir el 'except'
        error_msg = f"Error al procesar acción '{url_str if 'url_str' in locals() else 'URL desconocida'}': {str(e)}"
        print(f"[ERROR] {error_msg}")
        show_error_dialog(main_window_instance, "Error", error_msg) # Usar main_window_instance

    # Código que se ejecuta *siempre*, después del try/except
    if main_window_instance.calendar_window is not None:
        from utils.calendar_utils import refresh_calendar # Importar aquí para evitar ciclos potenciales si no está ya importado
        refresh_calendar(main_window_instance.calendar_window)
    else:
        print("[DEBUG] calendar_window es None, no se puede refrescar el calendario.")

def show_test_dialog_logic(main_window_instance):
    """Mostrar diálogo para mensajes de prueba."""
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton # Importar aquí para evitar ciclos
    dialog = QDialog(main_window_instance) # Pasar main_window_instance como parent
    dialog.setWindowTitle("Mensaje de Prueba")
    
    input_text = QTextEdit()
    btn_send = QPushButton("Enviar")
    btn_send.clicked.connect(
        lambda: save_test_message_logic(main_window_instance, input_text.toPlainText(), dialog) # Pasar main_window_instance
    )
    
    layout = QVBoxLayout()
    layout.addWidget(input_text)
    layout.addWidget(btn_send)
    dialog.setLayout(layout)
    dialog.exec()

def save_test_message_logic(main_window_instance, message_text, dialog): 
    from datetime import datetime # Importar aquí
    now = datetime.now()
    formatted_date = now.strftime("%d/%m/%y")
    formatted_time = now.strftime("%H:%M")
    
    test_message = {
        "date": formatted_date,
        "time": formatted_time,
        "sender": "Test User",
        "message": message_text
    }
    
    test_chat_name = "Test Chat"
    found = False
    for chat in main_window_instance.chats: # Usar main_window_instance
        if chat["nombre"] == test_chat_name:
            chat["messages"].append(test_message)
            found = True
            break
    if not found:
        main_window_instance.chats.append({ # Usar main_window_instance
            "nombre": test_chat_name,
            "messages": [test_message]
        })
    
    main_window_instance.chat_list.addItem(test_chat_name) # Usar main_window_instance
    main_window_instance.chat_list_send.addItem(test_chat_name) # Usar main_window_instance
    dialog.accept()
