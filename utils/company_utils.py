# utils/company_utils.py
import pandas as pd
from PyQt6.QtGui import QColor
from utils.excel_utils import load_dataframe
from config import EXCEL_FILE_PATH
from utils.common_functions import show_error_dialog  

def get_coop_data(coop_name, df_coops):
    """Obtener datos de una cooperativa desde su DataFrame."""
    try:
        if df_coops is None or df_coops.empty:
            return {
                'Nombre_Cooperativa': "[Nombre_Cooperativa]",
                'Metodo_de_pago': "[Metodos_de_pago]",
                'Email': "[Mails]"
            }
        row = df_coops[df_coops['Nombre_Cooperativa'] == coop_name].iloc[0]
        return row.to_dict()
    except IndexError:
        return {
            'Nombre_Cooperativa': "[Nombre_Cooperativa]",
            'Metodo_de_pago': "[Metodos_de_pago]",
            'Email': "[Mails]"
        }
    except Exception as e:
        print(f"[ERROR] en get_coop_data: {e}")
        return {
            'Nombre_Cooperativa': "[Nombre_Cooperativa]",
            'Metodo_de_pago': "[Metodos_de_pago]",
            'Email': "[Mails]"
        }
    
def build_event_description(rate: str, company: str) -> str:
    return f"{rate}€ {company}"

#___COMPANY_UTILS___

def normalize_company_name(name: str) -> str:
    """
    Normaliza el nombre de una empresa para evitar duplicados.
    """
    if not name or not isinstance(name, str):
        return "Empresa desconocida"
    
    # Eliminar espacios extra y convertir a mayúsculas para comparación
    clean_name = name.strip().upper()
    
    # Mapeo explícito de variantes a nombre canónico
    corrections = {
        "CRAMBO RENTAL": "CRAMBO ALQUILER S.L.",
        "CRAMBO ALQUILER SL": "CRAMBO ALQUILER S.L.",
        "CRAMBO ALQUILERSL": "CRAMBO ALQUILER S.L.",
        "CRAMBO ALQUILER S.L.": "CRAMBO ALQUILER S.L.",
        "CRAMBO ALQUILERS.L.": "CRAMBO ALQUILER S.L.",
        "MADWORKS": "MADWORKS",
        "LAST LAP SL": "LAST LAP S.L.",
        "LAST LAP S.L.": "LAST LAP S.L.",
        "LAST LAP": "LAST LAP S.L.",
        "BedInParis": "BEDINPARIS",
        "BED IN PARIS": "BEDINPARIS",
        "BEDINPARIS": "BEDINPARIS",
    }
    
    return corrections.get(clean_name, clean_name)

def get_company_data(company_name, df_comp):
    """Obtener datos de una empresa desde su DataFrame."""
    try:
        if df_comp is None or df_comp.empty:
            return {'Color': '#000000'}

        row = df_comp[df_comp['Nombre_Empresa'] == company_name].iloc[0]
        result = row.to_dict()

        # Convertir campos numéricos a float
        for key in ['Jornada_Precio', 'Jornada_Horas', 'Precio_Hora']:
            if key in result and result[key] is not None:
                try:
                    result[key] = float(result[key])
                except (ValueError, TypeError):
                    result[key] = 0.0
        return result
    except IndexError:
        # Si la empresa no existe
        return {'Color': '#000000', 'Jornada_Precio': 0.0, 'Jornada_Horas': 8.0, 'Precio_Hora': 0.0}
    except Exception as e:
        print(f"[ERROR] en get_company_data: {e}")
        return {'Color': '#000000', 'Jornada_Precio': 0.0, 'Jornada_Horas': 8.0, 'Precio_Hora': 0.0}
    
def get_company_name(event):
    """Obtener el nombre de la empresa desde extendedProperties o la descripción."""
    try:
        return event['extendedProperties']['private']['company']
    except (KeyError, TypeError):
        pass
    try:
        description = event.get('description', '')
        if description and '€' in description:
            return description.split('€', 1)[1].strip()
    except Exception:
        pass
    return "Empresa desconocida"

def get_company_color(company_name):
    """Obtener el color asociado a una empresa (usa nombre normalizado)."""
    normalized = normalize_company_name(company_name)
    try:
        df_comp = load_dataframe(EXCEL_FILE_PATH, sheet_name='datos_empresa')
        if df_comp is None or df_comp.empty:
            return "#333333"
        company_colors = dict(zip(df_comp['Nombre_Empresa'], df_comp['Color']))
        return company_colors.get(normalized, "#333333")
    except Exception as e:
        print(f"[ERROR] al cargar color para '{company_name}': {e}")
        return "#222222"

def update_company_color(self):
    """Actualizar el color de la empresa seleccionada en la interfaz."""
    try:
        df_empresa = load_dataframe(EXCEL_FILE_PATH, sheet_name='datos_empresa')
        # Verificar que el DataFrame no esté vacío
        if df_empresa is None or df_empresa.empty:
            print("[WARNING] DataFrame de empresas está vacío.")
            return
            
        selected_company = self.company_input.currentText()
        # Verificar que la empresa seleccionada exista en el DataFrame
        if selected_company not in df_empresa['Nombre_Empresa'].values:
            print(f"[WARNING] Empresa '{selected_company}' no encontrada en el DataFrame.")
            return
            
        # Obtener el color de la empresa seleccionada
        color_hex = df_empresa.loc[df_empresa['Nombre_Empresa'] == selected_company, 'Color'].values[0]
        self.company_color = QColor(color_hex)  # <<--- Convierte a QColor
        print(f"[INFO] Color de la empresa {selected_company}: {color_hex}")  # Depuración
    except IndexError:
        # Si no se encuentra el color en el DataFrame
        print(f"[ERROR] No se encontró el color para la empresa seleccionada.")
    except Exception as e:
        show_error_dialog(self, "Error", f"Error al actualizar el color de la empresa: {e}")

def get_task(event):
    """Obtener la tarea desde extendedProperties o descripción."""
    try:
        # Priorizar extendedProperties
        return event['extendedProperties']['private']['task']
    except KeyError:
        # Si no existe, usar descripción o tarea por defecto
        description = event.get('description', '')
        for keyword in ["video", "iluminación", "streaming", "contenido", "montaje", "desmontaje", "instalación", "mantenimiento", "programación", "configuración"]:
            if keyword in description.lower():
                return f"Técnico de {keyword.capitalize()}"
        return "Tarea por defecto"

def get_task_color(task):
    """Obtener color asociado a una tarea."""
    task_colors = {
        "Técnico de Video": "#FF5722",      # Rojo
        "Técnico de Iluminación": "#4CAF50", # Verde
        "Técnico de Streaming": "#2196F3",   # Azul
        "Técnico de Contenido": "#9C27B0",   # Púrpura
        "Montaje": "#FFC107",               # Ámbar
        "Desmontaje": "#795548",            # Marrón
        "Instalación": "#00BCD4",           # Cian
        "Mantenimiento": "#8BC34A",         # Verde claro
        "Programación": "#E91E63",          # Rosa
        "Configuración": "#3F51B5",         # Índigo
        # Tarea por defecto
        "Tarea por defecto": "#607D8B"      # Gris azulado
    }
    return task_colors.get(task, "#607D8B") # Gris por defecto si no se encuentra

def get_rate_company(description):
    """Obtener la tarifa y el nombre de la empresa desde la descripción del evento."""
    # Validar que description exista y no esté vacía
    if not description:
        return None, None
        
    parts = description.split('€')
    if len(parts) != 2:
        # Si no hay exactamente 2 partes, no se puede parsear
        return None, None
    
    rate = parts[0].strip()
    company = parts[1].strip()
    return rate, company