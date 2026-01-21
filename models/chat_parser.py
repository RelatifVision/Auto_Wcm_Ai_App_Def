# models/chat_parser.py
import os
import re
import pandas as pd
import spacy
import random
import datetime
from datetime import datetime as dttime, date, time, timedelta, timezone # Renombramos para evitar conflictos

import dateparser
from calendar_api_setting.calendar_api import get_events
from utils.common_functions import show_error_dialog
from utils.event_handler import confirm_event, reject_event

# Load the spaCy model
nlp = spacy.load("es_core_news_lg")

def is_relevant_message(message):
    """
    Determina si un mensaje es relevante basado en su contenido.
    :param message: El contenido del mensaje.
    :return: True si el mensaje es relevante, False en caso contrario.
    """
    # Expresiones regulares para detectar información relevante
    patterns = [
        r'\b(horario|hora|mañana|tarde|noche|cita|disponibilidad|nocturnidad|pasado|mes siguiente|próximo)\b',  # Horarios
        r'\b(ubicación|dirección|lugar|envío|localización|sede|oficina|local|calle|avenida|paseo|nave|hotel|plaza)\b'  # Ubicaciones,
        r'\b(precio|tarifa|coste|valor|factura|pedido|importe|presupuesto|cotización)\b',  # Presupuestos
        r'\b(urgente|importante|revisar|última|último|urgencia|inmediato|necesito|requiero)\b',  # Urgencias
        r'\b(\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre))\b',  # Fechas específicas
        r'\b(operar|realizar|instalar|desmontar|programar|hacer|programación|configuración|instalación|montaje|mantenimiento|streaming|pantalla|tiras led|led|iluminación|luz|MA2|MA3|chamsys|resolume|novastar|procesador|escalador|sender|tarima|m|técnico de contenido|vimix|obs|h2|h5|h7)\b',  # Tareas/Equipos
    ]
    for pattern in patterns:
        if re.search(pattern, message, re.IGNORECASE):
            return True
    return False

def extract_relevant_messages(chat, color):
    messages = []
    for msg in chat["messages"]:
        messages.append({
            "datetime": msg["fecha"],
            "sender": msg["sender"],
            "text": msg["mensaje"],
            "color": color
        })
    return messages

def extract_location(text):
    """Extrae ubicación después de 'es en', 'estar en', o palabras clave como 'ubicación'"""
    matches = [
        re.search(r'\b(es|estar)\s+en\s+([^.\n]+)', text, re.IGNORECASE),
        re.search(r'\b(ubicación|dirección|lugar)\s*:?\s*([^.\n]+)', text, re.IGNORECASE)
    ]
    
    for match in matches:
        if match:
            return match.group(2).strip()
    
    return None

def extract_time(text):
    """Extrae hora después de 'a las', 'sobre la' o palabras clave como 'hora'"""
    matches = [
        re.search(r'\b(a las|sobre la|sobre las)\s+([0-2]\d:[0-5]\d)\b', text, re.IGNORECASE),
        re.search(r'\b(hora)\s*:?\s*([0-2]\d:[0-5]\d)\b', text, re.IGNORECASE)
    ]
  
    for match in matches:
        if match:
            return match.group(2)
    
    return None

def highlight_keywords(text):
    """
    Resalta palabras clave en el mensaje con colores y estilos específicos.
    Prioriza los patrones contextuales.
    """
    # Definir todos los patrones combinados
    # Los patrones contextuales van PRIMERO para tener prioridad
    patterns = []

    # --- AÑADIR PATRONES CONTEXTUALES PRIMERO ---
    # Contexto de Hora
    patterns.extend([
        (r'\b(a\s+la\s+(?:[01]?\d|2[0-3])[:.][0-5]\d)\b', '#00bfff', 'bold'), # Azul cielo para hora contextual
        (r'\b(a\s+las\s+(?:[01]?\d|2[0-3])[:.][0-5]\d)\b', '#00bfff', 'bold'),
        (r'\b(sobre\s+la\s+(?:[01]?\d|2[0-3])[:.][0-5]\d)\b', '#00bfff', 'bold'),
        (r'\b(sobre\s+las\s+(?:[01]?\d|2[0-3])[:.][0-5]\d)\b', '#00bfff', 'bold'),
        # Opcional: Detectar rangos "de 10:00 a 17:00" (más complejo, requiere cuidado para no solapar)
        # (r'\b(de\s+(?:[01]?\d|2[0-3])[:.][0-5]\d\s+a\s+(?:[01]?\d|2[0-3])[:.][0-5]\d)\b', '#0099cc', 'bold'),
    ])

    # --- Contexto de Fecha ---
    patterns.extend([
        (r'\b(el\s+d[ií]a\s+\d{1,2}\s+de\s+\w+)\b', '#66cc66', 'bold'), # Verde suave para fecha contextual
        (r'\b(el\s+\d{1,2}[\/\-\.]\d{1,2}(?:[\/\-\.]\d{2,4})?)\b', '#66cc66', 'bold'), # "el 15/09"
        (r'\b(los\s+d[ií]as\s+\d{1,2}\s+al\s+\d{1,2})\b', '#66cc66', 'bold'), # "los días 10 al 15"
        (r'\b(los\s+d[ií]as\s+(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo))\b', '#66cc66', 'bold'), # "los días lunes"
    ])

    # Contexto de Ubicación
    patterns.extend([
        (r'\b(en\s+(?:el|la)\s+(?:\w+)(?:\s+\w+){0,4})\b', '#32cd32', 'bold'), # Verde lima para ubicación contextual
        # Otra opción más restrictiva para nombres propios después de "en":
        (r'\b(en\s+[A-Z][a-z]*(?:\s+[A-Z][a-z]*){0,3})\b', '#32cd32', 'bold'),
    ])

    # --- AÑADIR PATRONES GENÉRICOS DESPUÉS ---

    # Presupuestos y montos con IVA
    patterns.extend([
        (r'\b\d{1,3}[,.]?\d{1,2}\s*[€$£¥₩]\s*\+\s*IVA\b', '#ffbf00', 'bold'),
        (r'\b(?:[€$£¥₩]\d{1,3}[,.]?\d{1,2}\s*\+\s*IVA)\b', '#ffbf00', 'bold'),
        (r'\b\d{1,3}[,.]?\d{1,2}\s*[€$£¥₩]|(?:[€$£¥₩]\d{1,3}[,.]?\d{1,2})\b', '#ffbf00', 'bold'),
    ])
    
    patterns.extend([
        # Fechas sueltas (genéricas)
        (r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+de\s+\w+)\b', '#0077ff', 'bold'),
        # Días de la semana/relativos
        (r'\b(hoy|mañana|pasado|próximo|lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\b', '#0077ff', 'bold'),
        # Horas sueltas (genéricas)
        (r'\b(?:[01]?\d|2[0-3])[:.][0-5]\d\b', '#00d4ff', 'bold'),
        # Urgencias
        (r'\b(urgente|inmediato|necesito|prioridad|ya|ahora|requiero|revisar|[úu]ltima|[úu]ltimo)\b', '#ff5c00', 'bold'),
        # Eventos
        (r'\b(evento|reuni[oó]n|presentaci[oó]n|taller|concierto|obra|feria|muestra)\b', "#00ff88", 'bold'),
        # Tareas/Equipos - Asegurado que MA#, h#, etc. estén cubiertos
        (r'\b(operar|realizar|instalar|desmontar|programar|hacer|programaci[oó]n|configuraci[oó]n|instalaci[oó]n|montaje|mantenimiento|streaming|pantalla|tiras\s+led|led|iluminaci[oó]n|luz|MA\d+|chamsys|resolume|novastar|procesador|escalador|sender|tarima|m|t[eé]cnico\s+de\s+contenido|vimix|obs|h\d+)\b', '#9200ff', 'bold'),
        # Ubicaciones genéricas (verde claro)
        (r'\b(ubicaci[oó]n|direcci[oó]n|lugar|env[ií]o|localizaci[oó]n|sede|oficina|local|calle|avenida|paseo|nave|hotel|plaza)\b', '#00ff32', 'bold'),
    ])

    # --- 2. Aplicar los patrones existentes para marcar texto ya resaltado ---
    highlighted_spans = set() # Para llevar la cuenta de qué caracteres ya fueron resaltados

    # Aplicar patrones y registrar las posiciones resaltadas
    for pattern, color, weight in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.UNICODE):
            start, end = match.span()
            # Registrar cada carácter del span como resaltado
            highlighted_spans.update(range(start, end))
            
    # --- 3. Buscar y resaltar números sueltos (máx. 2 dígitos, sin decimales)
    number_pattern = r'\b\d{1,2}\b'
    
    # Encontrar todas las coincidencias de números sueltos
    potential_date_matches = list(re.finditer(number_pattern, text))
    
    # Filtrar solo aquellas que NO estén completamente dentro de un span ya resaltado
    final_number_matches = []
    for match in potential_date_matches:
        start, end = match.span()
        # Comprobar si alguno de los caracteres del número ya está resaltado
        if not any(i in highlighted_spans for i in range(start, end)):
            final_number_matches.append(match)

    # --- 4. Añadir los números sueltos como nuevos patrones a aplicar ---
    for match in final_number_matches:
         escaped_number = re.escape(match.group())
         patterns.append((rf'\b{escaped_number}\b', '#0077ff', 'bold')) 
         
    # --- 5. Aplicar TODOS los patrones (incluyendo los números sueltos añadidos) al texto ---
    highlighted_text = text
    for pattern, color, weight in patterns:
        highlighted_text = re.sub(
            pattern,
            lambda m: f'<span style="color: {color}; font-weight: {weight}">{m.group(0)}</span>',
            highlighted_text,
            flags=re.IGNORECASE | re.UNICODE
        )

    return highlighted_text

def load_chats(directory="data/chats"):
    chats = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            chat_name = os.path.splitext(filename)[0]
            chat_data = {"nombre": chat_name, "messages": []}
            
            with open(os.path.join(directory, filename), "r", encoding="utf-8") as file:
                for line in file:
                    # ✅ Acepta 1 o 2 dígitos en día/mes/hora/minuto
                    match = re.match(r'(\d{1,2}/\d{1,2}/\d{2}), (\d{1,2}:\d{2}) - ([^:]+): (.+)', line.strip())
                    if match:
                        date_str, time_str, sender, message = match.groups()
                        # Normalizar a 2 dígitos (opcional, para consistencia)
                        try:
                            dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%y %H:%M")
                            normalized_date = dt.strftime("%d/%m/%y")
                            normalized_time = dt.strftime("%H:%M")
                        except:
                            normalized_date = date_str
                            normalized_time = time_str
                        chat_data["messages"].append({
                            "date": normalized_date,
                            "time": normalized_time,
                            "sender": sender,
                            "message": message
                        })
            chats.append(chat_data)
    return chats

def infer_date(text):
    """
    Intenta inferir una fecha y una hora desde un texto.
    Args:
        text (str): El texto del mensaje.
    Returns:
        tuple: Una tupla (fecha, hora) donde:
            - fecha es un objeto datetime.date.
            - hora es un objeto datetime.time.
    """
    today = dttime.now().date() # Asumiendo dttime es datetime.datetime

    # 1. Intentar parseo general con dateparser para obtener fecha y hora
    try:
        parsed_dt = dateparser.parse(text, languages=['es'], settings={'DATE_ORDER': 'DMY'})
        if parsed_dt:
            print(f"[DEBUG] dateparser encontró: {parsed_dt}")
            # dateparser.parse puede devolver datetime o date, asegurémonos de devolver (date, time)
            if isinstance(parsed_dt, dttime): # Si es un datetime
                return parsed_dt.date(), parsed_dt.time()
            elif isinstance(parsed_dt, date): # Si es solo una fecha (date)
                # Devolver la fecha con una hora por defecto
                return parsed_dt, time(9, 0) # Hora por defecto 09:00
            # Si es otro tipo (raro, pero por si acaso), fallback
    except Exception as e:
        print(f"[WARNING] Error al parsear con dateparser: {e}")

    # 2. Lógica específica para "12 de agosto" u otros formatos no capturados por dateparser
    # (Aunque dateparser debería capturar esto, por si acaso...)
    match = re.search(r'\b(\d{1,2})\s+de\s+(\w+)\b', text, re.IGNORECASE)
    if match:
        day_str = match.group(1)
        month_str = match.group(2)
        try:
            # Intentar parsear solo "12 agosto"
            parsed_d = dateparser.parse(f"{day_str} {month_str}", languages=['es'], settings={'DATE_ORDER': 'DMY'})
            if parsed_d:
                 # Asegurar devolución de (date, time)
                if isinstance(parsed_d, dttime):
                    return parsed_d.date(), parsed_d.time()
                elif isinstance(parsed_d, date):
                    return parsed_d, time(9, 0) # Hora por defecto
        except Exception as e:
             print(f"[WARNING] Error al parsear patrón específico 'dia de mes': {e}")
    
    # 3. Lógica para palabras clave
    lowered = text.lower()
    if "mañana" in lowered:
        print("[DEBUG] Palabra clave 'mañana' encontrada.")
        return today + timedelta(days=1), time(9, 0)
    elif "próximo" in lowered: # Simplificación
        print("[DEBUG] Palabra clave 'próximo' encontrada.")
        return today + timedelta(weeks=1), time(9, 0)
    elif "dentro de" in lowered:
        match = re.search(r'dentro de (\d+)', lowered)
        if match:
            days = int(match.group(1))
            print(f"[DEBUG] Palabra clave 'dentro de {days} días' encontrada.")
            return today + timedelta(days=days), time(9, 0)

    # 4. Fallback: Si no se encuentra nada específico, usar dateparser una última vez
    # y si eso falla, usar hoy.
    try:
        # Intentar dateparser una vez más sin restricciones
        parsed_final = dateparser.parse(text, languages=['es'])
        if parsed_final:
             if isinstance(parsed_final, dttime):
                return parsed_final.date(), parsed_final.time()
             elif isinstance(parsed_final, date):
                return parsed_final, time(9, 0)
    except Exception as e:
        print(f"[WARNING] Error en fallback dateparser: {e}")

    # 5. Último Fallback: Hoy a las 09:00
    return today, time(9, 0)         
             
def handle_chat_message(message, calendar_window):
    inferred_date, time_str_unused = infer_date(message)
    if not inferred_date:
        return "No se entendió la fecha."
    
    # Extraer horario y ubicación
    time_str = extract_time(message)
    location = extract_location(message)
    
    # Usar horario extraído o por defecto
    start_time = datetime.datetime.strptime(time_str, "%H:%M").time() if time_str else datetime.time(9, 0)
    end_time = (datetime.datetime.combine(datetime.date.today(), start_time) + datetime.timedelta(hours=10)).time()  # 10 horas
    
    # Crear datetime completo
    start_dt = dttime.combine(inferred_date, start_time)
    end_dt = dttime.combine(inferred_date, end_time)
    
    if check_availability(start_dt, end_dt, calendar_window):
        return f"Disponible para {location or 'ubicación no especificada'} a las {time_str or '09:00-19:00'}. ¿Crear evento?"
    else:
        return "No hay disponibilidad en ese horario."

def check_availability(start_dt, end_dt, calendar_window):
    events = get_events()
    start_date = start_dt.date()
    end_date = end_dt.date()
    
    for event in events:
        try:
            event_start = dateparser.parse(event['start']['dateTime']).date()
            event_end = dateparser.parse(event['end']['dateTime']).date()
            
            if start_date < event_end and end_date > event_start:
                return False  # Hay conflicto
        except KeyError:
            continue
    return True

def generate_summary(messages):
    """
    Generar un resumen de las tareas y horarios basados en los mensajes relevantes.
    """
    summary_dict = {}
    for message in messages:
        date = message['date']
        if date not in summary_dict:
            summary_dict[date] = []
        summary_dict[date].append(message)

    summary = ""
    last_date = None
    last_chat = None
    for date in sorted(summary_dict.keys()):
        if last_date and last_date != date:
            summary += "<br><br>"  # Doble salto de línea al cambiar de fecha
        summary += f"El día {date}: "
        for message in summary_dict[date]:
            if last_chat and last_chat != message['color']:
                summary += "<br>"  # salto de línea al cambiar de chat
            # Generar texto natural con spaCy
            doc = nlp(message['text'])
            summary_text = " ".join([sent.text for sent in doc.sents])
            summary += f"<br> - {message['time']} - {message['sender']}: {summary_text} "
            last_chat = message['color']
        last_date = date
        summary += "<>"  # Salto de línea por cada mensaje diferente

    # Generar un resumen general con spaCy
    sender_texts = {}
    resumen_general = ""
    for msg in messages:
        sender = msg['sender']
        if sender not in sender_texts:
            sender_texts[sender] = []
        sender_texts[sender].append(msg['text'])
        
    for sender, value in sender_texts.items():
        
        value = "<br> ".join(string for string in value)
        doc = nlp(value)
        resumen_general += f"{sender}: ".join([f"{sent.text}<br><br>" for sent in doc.sents])
    summary += f"<br><br>Resumen General:<br><br>{resumen_general}"

    return summary
