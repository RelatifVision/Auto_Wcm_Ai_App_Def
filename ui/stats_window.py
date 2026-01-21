# ui/stats_window.py (Versión corregida - Solo Facturas - Importaciones Relativas Correctas)

import sys
import os
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, \
    QWidget, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QApplication, QComboBox, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QIcon
from config import ICON_DIR 
from utils.company_utils import get_company_color, normalize_company_name
from utils.business_manager import BusinessManager
from calendar_api_setting.calendar_api import get_events, get_events_by_month

class StatsWindow(QMainWindow):
    def __init__(self, stats_data, parent=None, year="Todos"):
        super().__init__(parent)
        """
        Inicializa una ventana de estadísticas con los datos proporcionados.

        Args:
            stats_data (dict): Diccionario con los datos de las estadísticas.
                               Debe contener: hours_per_company, days_per_company, import_per_company, tasks_per_company.
                               Ej: {
                                   "hours_per_company": {"Visualmax Producciones SL": 40.5, "Peak Produccion Tecnica SL": 20.0},
                                   "days_per_company": {"Visualmax Producciones SL": 5, "Peak Produccion Tecnica SL": 3},
                                   "import_per_company": {"Visualmax Producciones SL": 2000.0, "Peak Produccion Tecnica SL": 1000.0},
                                   "tasks_per_company": {"visualmax_producciones_sl": ["Tarea1", "Tarea2"], "peak_produccion_tecnica_sl": ["Tarea3"]}
                               }
            parent (QMainWindow, optional): Ventana padre de la ventana actual. Defaults to None.
            year (str, optional): Año para filtrar los datos. Defaults to "Todos".
        """

        self.stats_data = stats_data
        self.main_window = parent
        self.selected_year = year # Guardar el año seleccionado
        self.setWindowTitle("Estadísticas de Empresas")
        self.setWindowIcon(QIcon(os.path.join("data", "icon", "stats.png"))) # Asegúrate de que la ruta sea correcta
        self.setGeometry(150, 150, 900, 700)
        self.setStyleSheet("background-color: #212121; color: white;")

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Título y botón Refresh
        title_layout = QHBoxLayout() # Nuevo layout horizontal para título y botón
        title_label = QLabel("Estadísticas de Empresas", alignment=Qt.AlignmentFlag.AlignLeft) # Alineado a la izquierda
        title_label.setStyleSheet("font-size: 24px; color: #ffffff; margin: 20px 0;")
        title_layout.addWidget(title_label)

        # Botón Refresh
        self.btn_refresh = QPushButton(" Refresh")
        icono_refresh = QIcon(os.path.join(ICON_DIR, "refresh.png")) # Asegúrate de que ICON_DIR esté definido en config.py
        # Si no, puedes usar: icono_refresh = QIcon(os.path.join("data", "icon", "refresh.png"))
        self.btn_refresh.setIcon(icono_refresh)
        self.btn_refresh.setStyleSheet("background-color: #333333; color: white;")
        self.btn_refresh.setFixedSize(80, 40)
        # Conectar el botón al método refresh_stats
        self.btn_refresh.clicked.connect(self.refresh_stats)
        title_layout.addWidget(self.btn_refresh, alignment=Qt.AlignmentFlag.AlignRight) # Alineado a la derecha

        main_layout.addLayout(title_layout) # Añadir el layout horizontal al principal

        # Mostrar estadísticas por empresa con colores
        self.display_company_stats(main_layout)

        # Botón cerrar
        close_btn = QPushButton(" Cerrar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: 2px solid #111111;
                border-radius: 5px;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Navbar (sin 'stats', pero con 'apagar' incluido)
        # from utils.gui_utils import create_navbar # Asegúrate de tener esta función o importarla desde el lugar correcto
        # navbar = create_navbar("stats", self.main_window)
        # main_layout.addWidget(navbar)

    def display_company_stats(self, main_layout):
        # Crear tabla para mostrar estadísticas
        stats_table = QTableWidget()
        # Guardar la referencia para poder limpiarla y volver a llenarla en refresh_stats
        self.stats_table = stats_table
        stats_table.setColumnCount(5)
        stats_table.setHorizontalHeaderLabels([
            "Empresa", "Horas Trabajadas", "Días Trabajados", "Importe Total", "Tareas"
        ])

        # Estilo de la tabla
        stats_table.setStyleSheet("""
            QTableWidget {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #444444;
                color: white;
                padding: 8px;
                border: 1px solid #666666;
            }
        """)

        # Configurar encabezado
        header = stats_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # --- Llenar tabla con datos calculados desde el calendario ---
        # Obtener todas las empresas calculadas (ya normalizadas y posiblemente fusionadas por BusinessManager)
        # Usar las claves de uno de los diccionarios de stats_data como fuente única de empresas
        # Asegurarse de que todas las claves de los diccionarios (hours, days, importe, tasks) sean consistentes
        # entre sí (es decir, que BusinessManager las haya normalizada de la misma manera).
        # Por ejemplo, usando hours_per_company como base para iterar
        all_companies_calculated = set(self.stats_data.get("hours_per_company", {}).keys()) | \
                                  set(self.stats_data.get("days_per_company", {}).keys()) | \
                                  set(self.stats_data.get("import_per_company", {}).keys()) | \
                                  set(self.stats_data.get("tasks_per_company", {}).keys())

        companies_to_show = sorted(list(all_companies_calculated))


        stats_table.setRowCount(len(companies_to_show))

        for row, company in enumerate(companies_to_show):
            # Usar el nombre 'company' (la clave normalizada de BusinessManager) directamente
            # color_hex = get_company_color(company) or "#333333" # <-- Usar el nombre original para el color si es necesario
            color_hex = get_company_color(company) or "#333333" # <-- O usar la clave del diccionario (que es normalizada)
            company_item = QTableWidgetItem(company) # <-- Mostrar la clave del diccionario (ya normalizada)
            company_item.setBackground(QColor(color_hex))
            company_item.setForeground(QColor("white"))
            company_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            stats_table.setItem(row, 0, company_item)

            # Horas trabajadas (desde stats_data calculado)
            hours = self.stats_data.get("hours_per_company", {}).get(company, 0)
            hours_item = QTableWidgetItem(f"{hours:.2f} horas")
            hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            stats_table.setItem(row, 1, hours_item)

            # Días trabajados (desde stats_data calculado)
            days = self.stats_data.get("days_per_company", {}).get(company, 0)
            days_item = QTableWidgetItem(f"{days} días")
            days_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            stats_table.setItem(row, 2, days_item)

            # Importe total (desde stats_data calculado)
            importe = self.stats_data.get("import_per_company", {}).get(company, 0)
            importe_item = QTableWidgetItem(f"{importe:.2f} €")
            importe_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            stats_table.setItem(row, 3, importe_item)

            # Tareas (desde stats_data calculado, usando nombre normalizado como clave)
            # Asegurar que la clave usada para tasks_per_company sea la misma que la de otras métricas
            # BusinessManager debe guardar tasks_per_company usando la clave normalizada de la empresa.
            # Por ejemplo, si la clave en hours_per_company es "VISUALMAX PRODUCCIONES SL",
            # la clave en tasks_per_company también debe ser "VISUALMAX PRODUCCIONES SL" (o su versión normalizada interna, pero debe coincidir).
            tasks_data = self.stats_data.get("tasks_per_company", {}).get(company, [])
            # Convertir a string dependiendo del tipo de datos recibido
            if isinstance(tasks_data, list):
                # Si es una lista (comportamiento anterior), unirla
                tasks_str = ", ".join(tasks_data) if tasks_data else "Sin tareas"
            elif isinstance(tasks_data, str):
                # Si es un string (nuevo comportamiento, tarea más frecuente), úsalo directamente
                tasks_str = tasks_data if tasks_data else "Sin tareas"
            else:
                # Por si acaso, por ejemplo si tasks_data es None
                tasks_str = "Sin tareas"

            tasks_item = QTableWidgetItem(tasks_str)
            tasks_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            stats_table.setItem(row, 4, tasks_item)

        main_layout.addWidget(stats_table)

        # Mostrar resumen general
        summary_layout = QHBoxLayout() # Nuevo layout horizontal para el título y el selector de año
        summary_label = QLabel("Resumen General", alignment=Qt.AlignmentFlag.AlignLeft)
        summary_label.setStyleSheet("font-size: 18px; color: #ffffff; margin: 20px 0 10px 0;")
        summary_layout.addWidget(summary_label)
        
        self.year_combo = QComboBox()
        self.year_combo.addItems(["Todos", "2024", "2025", "2026"]) # Ajusta los años según tu calendario
        self.year_combo.currentTextChanged.connect(self.update_summary_by_year) # <-- Conectar al nuevo método
        self.year_combo.setStyleSheet("background-color: #333333; color: white;")
        self.year_combo.setFixedWidth(80) # Reducir el ancho
        self.year_combo.setCurrentText(self.selected_year) # Establecer el año seleccionado
        summary_layout.addWidget(self.year_combo)

        # Añadir un espaciador para empujar el selector de año a la derecha
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        summary_layout.addItem(spacer)

        main_layout.addLayout(summary_layout)

        summary_area = QTextEdit()
        # Guardar la referencia para poder actualizarla en refresh_stats
        self.summary_area = summary_area
        summary_area.setReadOnly(True)
        summary_area.setStyleSheet("""
            QTextEdit {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                padding: 10px;
                font-size: 14px;
            }
        """)
        summary_area.setHtml(self.generate_summary_text())
        main_layout.addWidget(summary_area)

    def generate_summary_text(self):
        html_summary = "<div style='line-height: 1.6;'>"

        # Total de horas
        total_hours = sum(self.stats_data.get("hours_per_company", {}).values())
        html_summary += f"<p><strong>Total de horas trabajadas:</strong> {total_hours:.2f} horas</p>"

        # Total de días
        total_days = sum(self.stats_data.get("days_per_company", {}).values())
        html_summary += f"<p><strong>Total de días trabajados:</strong> {total_days} días</p>"

        # Total de importe
        total_importe = sum(self.stats_data.get("import_per_company", {}).values())
        html_summary += f"<p><strong>Importe total generado:</strong> {total_importe:.2f} €</p>"

        # Empresas más activas
        hours_per_company = self.stats_data.get("hours_per_company", {})
        if hours_per_company:
            top_company = max(hours_per_company, key=hours_per_company.get)
            html_summary += f"<p><strong>Empresa más activa:</strong> {top_company} ({hours_per_company[top_company]:.2f} horas)</p>"

        html_summary += "</div>"
        return html_summary

    def update_summary_by_year(self, year_text):
        """
        Actualiza el resumen según el año seleccionado.
        Recalcula las estadísticas filtrando por el año seleccionado.
        """
        # Actualizar el atributo de la clase con el nuevo año
        self.selected_year = year_text
        # Llamar al método que recarga los datos y actualiza la UI, usando el nuevo año
        self.refresh_stats(year=self.selected_year)

    def refresh_stats(self, year=None):
        """
        Recarga los datos de estadísticas y actualiza la interfaz.
        Si se proporciona un año, lo usa para filtrar. Sino, usa self.selected_year.
        """

        # OPCIÓN 2: Duplicar lógica aquí para actualizar *esta* instancia
        try:
            # Usar el año proporcionado como parámetro, o el de la instancia si no se proporciona
            year_to_use = year if year is not None else self.selected_year

            # 1. Obtener eventos
            events = get_events()
            if not events:
                # Opcional: Mostrar un mensaje si no hay eventos
                # show_info_dialog(self, "Estadísticas", "No se encontraron eventos.")
                return # No hay nada que actualizar

            # --- NUEVO: Filtrar eventos por año ---
            if year_to_use != "Todos":
                # Convertir year a int
                year_int = int(year_to_use)
                # Filtrar eventos por año
                events = [event for event in events if 'start' in event and 'dateTime' in event['start'] and event['start']['dateTime'].startswith(str(year_int))]
                # Si no hay eventos para el año seleccionado, mostrar un mensaje
                if not events:
                    print(f"[INFO] No se encontraron eventos para el año {year_to_use}.")
                    # Limpiar datos y actualizar UI
                    self.stats_data = {
                        "hours_per_company": {},
                        "import_per_company": {},
                        "days_per_company": {},
                        "tasks_per_company": {}
                    }
                    self.refresh_ui()
                    return

            # 2. Procesar eventos con BusinessManager
            manager = BusinessManager()
            manager.load_events(events)

            # 3. Calcular estadísticas 
            hours_per_company = manager.calculate_hours_per_company()
            import_per_company = manager.calculate_import_per_company()
            days_per_company = manager.calculate_days_per_company()
            tasks_per_company = manager.calculate_tasks_per_company() # Asumiendo que ya devuelve string
            from utils.stats_utils import merge_company_stats

            # 4. Agrupar empresas similares en cada métrica (como en show_company_stats)
            hours_per_company_grouped = merge_company_stats(hours_per_company)
            import_per_company_grouped = merge_company_stats(import_per_company)
            days_per_company_grouped = merge_company_stats(days_per_company)
            tasks_per_company_grouped = merge_company_stats(tasks_per_company) # Asumiendo que merge_company_stats maneja strings correctamente


            # 5. Actualizar el atributo stats_data de esta instancia
            self.stats_data = {
                "hours_per_company": hours_per_company_grouped,
                "import_per_company": import_per_company_grouped,
                "days_per_company": days_per_company_grouped,
                "tasks_per_company": tasks_per_company_grouped
            }

            # 6. Limpiar y actualizar la tabla y el resumen
            self.refresh_ui()

        except Exception as e:
            print(f"[ERROR] Error al refrescar estadísticas: {str(e)}")

    def refresh_ui(self):
        """
        Actualiza la interfaz de usuario con los datos actuales de self.stats_data.
        """
        # Limpiar la tabla
        self.stats_table.clearContents()
        # Obtener empresas para mostrar
        all_companies_calculated = set(self.stats_data.get("hours_per_company", {}).keys()) | \
                                  set(self.stats_data.get("days_per_company", {}).keys()) | \
                                  set(self.stats_data.get("import_per_company", {}).keys()) | \
                                  set(self.stats_data.get("tasks_per_company", {}).keys())
        companies_to_show = sorted(list(all_companies_calculated))
        self.stats_table.setRowCount(len(companies_to_show))

        # Volver a llenar la tabla con los nuevos datos
        for row, company in enumerate(companies_to_show):
            color_hex = get_company_color(company) or "#333333"
            company_item = QTableWidgetItem(company)
            company_item.setBackground(QColor(color_hex))
            company_item.setForeground(QColor("white"))
            company_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.stats_table.setItem(row, 0, company_item)

            # Horas trabajadas
            hours = self.stats_data.get("hours_per_company", {}).get(company, 0)
            hours_item = QTableWidgetItem(f"{hours:.2f} horas")
            hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stats_table.setItem(row, 1, hours_item)

            # Días trabajados
            days = self.stats_data.get("days_per_company", {}).get(company, 0)
            days_item = QTableWidgetItem(f"{days} días")
            days_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stats_table.setItem(row, 2, days_item)

            # Importe total
            importe = self.stats_data.get("import_per_company", {}).get(company, 0)
            importe_item = QTableWidgetItem(f"{importe:.2f} €")
            importe_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stats_table.setItem(row, 3, importe_item)

            # Tareas
            tasks_data = self.stats_data.get("tasks_per_company", {}).get(company, [])
            if isinstance(tasks_data, list):
                tasks_str = ", ".join(tasks_data) if tasks_data else "Sin tareas"
            elif isinstance(tasks_data, str):
                tasks_str = tasks_data if tasks_data else "Sin tareas"
            else:
                tasks_str = "Sin tareas"
            tasks_item = QTableWidgetItem(tasks_str)
            tasks_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            self.stats_table.setItem(row, 4, tasks_item)

        # Actualizar el área de resumen
        self.summary_area.setHtml(self.generate_summary_text())

    def update_stats_data(self, new_stats_data, year="Todos"):
        """
        Actualiza los datos de la ventana de estadísticas.
        """
        self.stats_data = new_stats_data
        self.selected_year = year
        self.refresh_ui()

    # Métodos para el navbar (ajusta según tu estructura de MainWindow)
    def show_main_screen(self):
        if self.main_window:
            pass # <-- Implementar según tu estructura de MainWindow

    def show_calendar(self):
        if self.main_window:
            pass # <-- Implementar según tu estructura de MainWindow

    def show_email(self):
        if self.main_window:
            pass # <-- Implementar según tu estructura de MainWindow

    def show_gestion(self):
        if self.main_window:
            pass # <-- Implementar según tu estructura de MainWindow

    def close_application(self):
        try:
            from utils.common_functions import close_application # Asumiendo que common_functions.py está en la carpeta utils
            close_application(self)
        except ImportError:
            try:
                # Si está en la raíz del proyecto
                sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
                from common_functions import close_application
                close_application(self)
            except ImportError:
                print("[ERROR] No se pudo importar close_application.")
                self.close() # Cerrar la ventana como fallback

if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("Este archivo no debería ejecutarse directamente.")