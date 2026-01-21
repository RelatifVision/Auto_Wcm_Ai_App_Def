# utils/business_manager.py
from datetime import datetime, timedelta
from utils.company_utils import get_rate_company, get_company_name, get_task, get_company_data, normalize_company_name
from utils.excel_utils import load_dataframe
from config import EXCEL_FILE_PATH
import os
import re  # Importar 're' al inicio del archivo, no dentro de funciones

class BusinessManager:
    def __init__(self):
        self.events = []

    def load_events(self, events):
        """Carga los eventos obtenidos de la API."""
        self.events = events

    def get_date_from_event(self, event, field):
        """Devuelve la fecha en formato YYYY-MM-DD como string."""
        if 'dateTime' in event.get(field, {}):
            return event[field]['dateTime'][:10]  # Ej: "2025-04-05"
        elif 'date' in event.get(field, {}):
            return event[field]['date']  # Para eventos de día entero
        return None

    def calculate_hours_per_company(self):
        """Calcular las horas totales por empresa usando la duración entre start y end.
        Si la duración es <= 0, usa 8 horas como valor por defecto."""
        hours_data = {}
        for event in self.events:
            company = get_company_name(event)
            if not company or company == "Empresa desconocida":
                continue
            company = normalize_company_name(company)
            if company is None or company == "Empresa desconocida":
                import logging
                # logging.debug(f"Empresa no encontrada para evento: {event.get('summary', 'Sin título')}")
                continue

            try:
                start_date_str = self.get_date_from_event(event, 'start')
                end_date_str = self.get_date_from_event(event, 'end')
                if start_date_str is None or end_date_str is None:
                    print(f"Advertencia: Fecha no encontrada para evento: {event.get('summary', 'Sin título')}")
                    continue

                # Verificar si el evento tiene dateTime (con hora) o solo date (todo el día)
                has_datetime_start = 'dateTime' in event.get('start', {})
                has_datetime_end = 'dateTime' in event.get('end', {})

                duration = 0.0  # Inicializar

                if has_datetime_start and has_datetime_end:
                    # Caso 1: Evento con hora definida (dateTime)
                    start_dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                    duration = (end_dt - start_dt).total_seconds() / 3600
                    # Si la duración calculada es <= 0, usar 8 horas como valor por defecto
                    if duration <= 0:
                        duration = 8.0

                else:
                    # Caso 2: Evento de todo el día (date).
                    # Calcular número de días y asumir 24 horas por día.
                    start_date = datetime.fromisoformat(start_date_str).date()
                    end_date = datetime.fromisoformat(end_date_str).date()
                    num_days = (end_date - start_date).days + 1 # +1 para incluir ambos días
                    duration = num_days * 24.0

                # Acumular horas
                hours_data[company] = hours_data.get(company, 0) + duration

            except Exception as e:
                print(f"Error al calcular horas para {company}: {e}")
                continue
        return hours_data
    
    def calculate_hours_per_task(self):
        """Calcular las horas totales por tarea usando la duración entre start y end."""
        tasks_data = {}
        for event in self.events:
            task = get_task(event)
            if task is None:
                task = "Sin tarea"

            try:
                start_date_str = self.get_date_from_event(event, 'start')
                end_date_str = self.get_date_from_event(event, 'end')
                if start_date_str is None or end_date_str is None:
                    print(f"Advertencia: Fecha no encontrada para evento: {event.get('summary', 'Sin título')}")
                    continue

                if 'T' in start_date_str: # Es un dateTime
                    start_dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                    duration = (end_dt - start_dt).total_seconds() / 3600
                    if duration <= 0:
                         print(f"[WARNING] Duración calculada <= 0 para evento con hora (tarea {task}): {event.get('summary', 'Sin título')}. Usando 0.0 horas.")
                         duration = 0.0 # O podrías asignar un valor predeterminado si lo prefieres
                else: # Es un date (todo el día)
                    start_date = datetime.fromisoformat(start_date_str).date()
                    end_date = datetime.fromisoformat(end_date_str).date()
                    num_days = (end_date - start_date).days + 1
                    duration = num_days * 24.0 # Asumir 24h por día completo

                tasks_data[task] = tasks_data.get(task, 0) + duration
            except Exception as e:
                print(f"Error al calcular horas para tarea {task}: {e}")
                continue
        return tasks_data

    def calculate_days_per_company(self):
        """
        Calcula los días únicos trabajados por empresa (sin importar el mes).
        Cada día calendario cuenta como 1, incluso si hay múltiples eventos ese día.
        """
        # Diccionario: empresa_normalizada -> set de fechas (date)
        days_data = {}

        for event in self.events:
            company = get_company_name(event)
            if not company or company == "Empresa desconocida":
                continue

            try:
                start_date_str = self.get_date_from_event(event, 'start')
                end_date_str = self.get_date_from_event(event, 'end')
                if not start_date_str or not end_date_str:
                    continue

                # Convertir a objetos date (asumiendo formato YYYY-MM-DD)
                start_date = datetime.fromisoformat(start_date_str).date()
                end_date = datetime.fromisoformat(end_date_str).date()

                current = start_date
                while current <= end_date:
                    normalized_company = normalize_company_name(company)
                    if normalized_company not in days_data:
                        days_data[normalized_company] = set()
                    days_data[normalized_company].add(current)
                    current += timedelta(days=1)

            except Exception as e:
                print(f"[ERROR] Al procesar días para {company}: {e}")
                continue

        # Convertir sets a conteos
        result = {}
        for company, date_set in days_data.items():
            result[company] = len(date_set)
        return result

    def calculate_import_per_company(self):
        """Calcular el importe total por empresa extrayendo el valor de la descripción del evento."""
        importe_data = {}
        for event in self.events:
            company = get_company_name(event) # Obtiene la empresa del título
            if company is None or company == "Empresa desconocida":
                continue

            try:
                # Obtener la descripción del evento
                description = event.get('description', '') # <-- Usamos la descripción
                if not description:
                    print(f"Advertencia: Evento '{event.get('summary', 'Sin título')}' no tiene descripción.")
                    continue

                import re # Asegúrate de tener 'import re' al inicio del archivo
                match = re.search(r'(\d+(?:,\d{2})?)\s*€', description)
                if not match:
                    continue

                # Obtener el valor como string y convertirlo a float
                amount_str = match.group(1)
                # Reemplazar coma por punto para que Python lo convierta correctamente
                amount_str_for_float = amount_str.replace(',', '.')
                try:
                    importe_valor = float(amount_str_for_float)
                except ValueError:
                    print(f"Advertencia: Valor de importe no válido en la descripción del evento '{event.get('summary', 'Sin título')}': '{amount_str}'")
                    continue

                # Acumular el importe para la empresa (usando el nombre de la empresa del título, ya normalizado)
                normalized_company = normalize_company_name(company)
                importe_data[normalized_company] = importe_data.get(normalized_company, 0) + importe_valor

            except Exception as e:
                print(f"Error al calcular importe para {company}: {e}")
                continue
        return importe_data

    def calculate_import_per_task(self):
            """Calcular el importe total por tarea."""
            tasks_importe_data = {}
            for event in self.events:
                task = get_task(event)
                if task is None:
                    task = "Sin tarea"

                try:
                    # Obtener tarifa del evento
                    rate_str, company = get_rate_company(event.get('description', ''))
                    if rate_str is None:
                        continue

                    try:
                        rate_value = float(str(rate_str).replace('€', '').strip())
                    except ValueError:
                        continue

                    # Calcular duración (usando la misma lógica que otras funciones)
                    start_date_str = self.get_date_from_event(event, 'start')
                    end_date_str = self.get_date_from_event(event, 'end')
                    if start_date_str is None or end_date_str is None:
                        print(f"Advertencia: Fecha no encontrada para evento (importe tarea): {event.get('summary', 'Sin título')}")
                        continue

                    if 'T' in start_date_str: # Es un dateTime
                        start_dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                        duration_hours = (end_dt - start_dt).total_seconds() / 3600
                        if duration_hours <= 0:
                            print(f"[WARNING] Duración calculada <= 0 para evento con hora (importe tarea {task}): {event.get('summary', 'Sin título')}. Usando 0.0 horas.")
                            duration_hours = 0.0 # O podrías asignar un valor predeterminado si lo prefieres
                    else: # Es un date (todo el día)
                        start_date = datetime.fromisoformat(start_date_str).date()
                        end_date = datetime.fromisoformat(end_date_str).date()
                        num_days = (end_date - start_date).days + 1
                        duration_hours = num_days * 24.0 # Asumir 24h por día completo

                    importe = rate_value * duration_hours
                    tasks_importe_data[task] = tasks_importe_data.get(task, 0) + importe
                except Exception as e:
                    print(f"Error al calcular importe para tarea {task}: {e}")
                    continue
            return tasks_importe_data

    def calculate_tasks_per_company(self):
        """Calcular las 1 o 2 tareas más frecuentes por empresa (con nombres normalizados), excluyendo 'Tarea por defecto' y 'Sin tareas'.
        Si no hay tareas válidas, usa la primera tarea encontrada en los eventos de la empresa o 'Técnico de Video'."""
        # Diccionario temporal: empresa_normalizada -> {tarea: conteo}
        task_counts_per_company = {}

        # Diccionario para almacenar la primera tarea válida encontrada por empresa
        first_valid_task_per_company = {}

        for event in self.events:
            company = get_company_name(event)
            if company is None:
                continue
            normalized_company = normalize_company_name(company)  # ✅ Normalizar aquí
            task = get_task(event)
            if task is None:
                task = "Sin tarea"

            # --- NUEVA LÓGICA: Filtrar "Tarea por defecto" y "Sin tareas" ---
            # Si la tarea es "Tarea por defecto" o "Sin tareas", no la contamos.
            if task == "Tarea por defecto" or task == "Sin tarea":
                # Pero si aún no tenemos una tarea válida para esta empresa, guardar esta como fallback
                if normalized_company not in first_valid_task_per_company:
                    first_valid_task_per_company[normalized_company] = task
                continue  # Saltar esta tarea para el conteo

            # Inicializar el diccionario anidado si es necesario
            if normalized_company not in task_counts_per_company:
                task_counts_per_company[normalized_company] = {}
            # Contar la tarea (solo si no es "Tarea por defecto" ni "Sin tarea")
            task_counts_per_company[normalized_company][task] = task_counts_per_company[normalized_company].get(task, 0) + 1

            # Si aún no tenemos una tarea válida para esta empresa, guardar esta como fallback
            if normalized_company not in first_valid_task_per_company:
                first_valid_task_per_company[normalized_company] = task

        # Ahora, para cada empresa, encontrar las 1 o 2 tareas con el conteo más alto
        top_tasks_per_company = {}
        for company, task_counts in task_counts_per_company.items():
            if not task_counts:
                # Si no hay tareas contadas para esta empresa (porque todas eran "Tarea por defecto" o "Sin tareas"),
                # usar la primera tarea válida encontrada en los eventos de la empresa
                fallback_task = first_valid_task_per_company.get(company, "Técnico de Video")
                # Si la tarea de fallback es "Sin tarea" o "Tarea por defecto", usar "Técnico de Video"
                if fallback_task in ["Sin tarea", "Tarea por defecto"]:
                    fallback_task = "Técnico de Video"
                top_tasks_per_company[company] = [fallback_task]
            else:
                # Ordenar las tareas por conteo en orden descendente
                sorted_tasks = sorted(task_counts.items(), key=lambda x: x[1], reverse=True)
                # Tomar las 1 o 2 primeras tareas
                top_tasks = [task for task, count in sorted_tasks[:2]]  # Tomar las 2 más frecuentes
                top_tasks_per_company[company] = top_tasks

        return top_tasks_per_company # Devuelve un diccionario {empresa: [lista_de_1_o_2_tareas_más_frecuentes]}

    
