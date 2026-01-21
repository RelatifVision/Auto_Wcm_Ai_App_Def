# utils/stats_utils.py
from calendar_api_setting.calendar_api import get_events, get_events_by_month, get_events_by_year
from utils.common_functions import show_info_dialog, show_error_dialog
from utils.business_manager import BusinessManager
from ui.stats_window import StatsWindow

COMPANY_MAPPINGS = {
    # Para CRAMBO
    "CRAMBO ALQUILER SL": "CRAMBO ALQUILER S.L.",
    "Crambo Alquiler SL": "CRAMBO ALQUILER S.L.",
    "crambo alquiler sl": "CRAMBO ALQUILER S.L.",
    # Para BEDINPARIS
    "BedInParis": "BEDINPARIS",
    "bedinparis": "BEDINPARIS",
    # Puedes añadir más aquí según aparezcan
}

def merge_company_stats(original_data_dict):
    """
    Agrupa las estadísticas de empresas que tienen nombres similares,
    usando el diccionario COMPANY_MAPPINGS para decidir cuál nombre mantener.
    Devuelve un nuevo diccionario con los nombres corregidos y valores combinados.
    """
    merged = {}
    for company_name, value in original_data_dict.items():
        # Buscar si este nombre debe ser mapeado a otro
        mapped_name = COMPANY_MAPPINGS.get(company_name, company_name)  # Si no está en el mapeo, queda igual
        if mapped_name not in merged:
            merged[mapped_name] = value
        else:
            # Combinar valores
            if isinstance(value, (int, float)):
                merged[mapped_name] += value
            elif isinstance(value, list):
                merged[mapped_name].extend(value)
            # Si es otro tipo, podrías necesitar lógica adicional
    return merged

def show_company_stats(parent_window=None, year="Todos"):
    """
    Mostrar estadísticas de horas/días por empresa y tarea en una nueva ventana.
    Args:
        parent_window: La ventana padre (puede ser cualquier QMainWindow o None).
        year: El año para filtrar los eventos (por defecto "Todos").
    """
    try:
        # 1. Obtener eventos
        events = get_events()
        if not events:
            show_info_dialog(parent_window, "Estadísticas", "No se encontraron eventos.")
            return

        # --- NUEVO: Filtrar eventos por año ---
        if year != "Todos":
            # Convertir year a int
            year_int = int(year)
            # Filtrar eventos por año
            events = [event for event in events if 'start' in event and 'dateTime' in event['start'] and event['start']['dateTime'].startswith(str(year_int))]
            # Si no hay eventos para el año seleccionado, mostrar un mensaje
            if not events:
                show_info_dialog(parent_window, "Estadísticas", f"No se encontraron eventos para el año {year}.")
                return

        # 2. Procesar eventos con BusinessManager
        manager = BusinessManager()
        manager.load_events(events)

        # 3. Calcular estadísticas
        hours_per_company = manager.calculate_hours_per_company()
        import_per_company = manager.calculate_import_per_company()
        days_per_company = manager.calculate_days_per_company()
        tasks_per_company = manager.calculate_tasks_per_company()

        # 4. Agrupar empresas similares en cada métrica usando el mapeo manual
        hours_per_company_merged = merge_company_stats(hours_per_company)
        import_per_company_merged = merge_company_stats(import_per_company)
        days_per_company_merged = merge_company_stats(days_per_company)
        tasks_per_company_merged = merge_company_stats(tasks_per_company)

        # 5. Preparar datos finales para la ventana de estadísticas
        stats_data = {
            "hours_per_company": hours_per_company_merged,
            "import_per_company": import_per_company_merged,
            "days_per_company": days_per_company_merged,
            "tasks_per_company": tasks_per_company_merged
        }

        # 6. Crear y mostrar ventana de estadísticas
        if not hasattr(parent_window, 'stats_window') or parent_window.stats_window is None:
            parent_window.stats_window = StatsWindow(stats_data, parent=parent_window, year=year)
        else:
            # Si ya existe, actualizar los datos y el título
            parent_window.stats_window.update_stats_data(stats_data, year)
        parent_window.stats_window.show()

    except Exception as e:
        error_msg = f"Error al calcular estadísticas: {str(e)}"
        print(f"[ERROR] {error_msg}")
        show_error_dialog(parent_window, "Error", error_msg)

def show_company_stats_month(parent_window, month_str):
    """Mostrar estadísticas para un mes específico en una nueva ventana."""
    try:
        events = get_events_by_month(month_str)
        if not events:
            show_info_dialog(parent_window, "Estadísticas", f"No se encontraron eventos para el mes {month_str}.")
            return

        manager = BusinessManager()
        manager.load_events(events)

        # Calcular estadísticas
        hours_per_company = manager.calculate_hours_per_company()
        import_per_company = manager.calculate_import_per_company()
        days_per_company = manager.calculate_days_per_company()
        tasks_per_company = manager.calculate_tasks_per_company()

        # Agrupar empresas similares
        hours_per_company_merged = merge_company_stats(hours_per_company)
        import_per_company_merged = merge_company_stats(import_per_company)
        days_per_company_merged = merge_company_stats(days_per_company)
        tasks_per_company_merged = merge_company_stats(tasks_per_company)

        # Preparar datos para la ventana de estadísticas
        stats_data = {
            "hours_per_company": hours_per_company_merged,
            "import_per_company": import_per_company_merged,
            "days_per_company": days_per_company_merged,
            "tasks_per_company": tasks_per_company_merged
        }

        # Crear y mostrar ventana de estadísticas
        stats_window = StatsWindow(stats_data, parent=parent_window)
        stats_window.setWindowTitle(f"Estadísticas del mes {month_str}")
        stats_window.show()
        print(f"[INFO] Ventana de estadísticas del mes {month_str} mostrada.")

    except Exception as e:
        error_msg = f"Error al calcular estadísticas para {month_str}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        show_error_dialog(parent_window, "Error", error_msg)
        
def show_company_stats_year(parent_window, year_str):
    """Mostrar estadísticas para un año específico en una nueva ventana."""
    try:
        events = get_events_by_year(year_str)
        if not events:
            show_info_dialog(parent_window, "Estadísticas", f"No se encontraron eventos para el año {year_str}.")
            return

        manager = BusinessManager()
        manager.load_events(events)

        # Calcular estadísticas
        hours_per_company = manager.calculate_hours_per_company()
        import_per_company = manager.calculate_import_per_company()
        days_per_company = manager.calculate_days_per_company()
        tasks_per_company = manager.calculate_tasks_per_company()

        # Agrupar empresas similares
        hours_per_company_merged = merge_company_stats(hours_per_company)
        import_per_company_merged = merge_company_stats(import_per_company)
        days_per_company_merged = merge_company_stats(days_per_company)
        tasks_per_company_merged = merge_company_stats(tasks_per_company)

        # Preparar datos para la ventana de estadísticas
        stats_data = {
            "hours_per_company": hours_per_company_merged,
            "import_per_company": import_per_company_merged,
            "days_per_company": days_per_company_merged,
            "tasks_per_company": tasks_per_company_merged
        }

        # Crear y mostrar ventana de estadísticas
        stats_window = StatsWindow(stats_data, parent=parent_window)
        stats_window.setWindowTitle(f"Estadísticas del mes {month_str}")
        stats_window.show()
        print(f"[INFO] Ventana de estadísticas del mes {month_str} mostrada.")

    except Exception as e:
        error_msg = f"Error al calcular estadísticas para {month_str}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        show_error_dialog(parent_window, "Error", error_msg)
