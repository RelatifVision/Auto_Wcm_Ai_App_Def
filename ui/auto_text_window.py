# ui/auto_text_window.py
import re
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QWidget, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from calendar_api_setting.calendar_api import get_events
from utils.excel_utils import load_dataframe
from utils.company_utils import get_company_data, normalize_company_name, get_coop_data
from utils.common_functions import show_error_dialog
from ia_processor.utils.ocr_utils import extract_text_from_file
from config import EXCEL_FILE_PATH, EMAIL_ADDRESS, TASK_OPTIONS
from datetime import datetime

# Mapeo inteligente: empresa → tarea típica
EMPRESA_TAREA_DEFAULT = {
    "IDOIPE": "Técnico de Video",
    "TELEPIXEL S.L.U.": "Técnico de Video",
    "VISUALMAX S.L.": "Técnico pantalla Led",
    "CRAMBO ALQUILER S.L.": "Técnico pantalla Led",
    "LAST LAP S.L.": "Técnico pantalla Led",
    "DAIGON": "Técnico pantalla Led",
    "KENZO STUDIO": "Técnico de Streaming",
    "MADWORKS": "LedMapping",
    "PEAK ENTERTAINMENT S.L.U.": "LedMapping",
    
}

class AutoTextWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Textos Predefinidos")
        self.setGeometry(150, 150, 600, 400)
        
        layout = QVBoxLayout()
        self.option_list = QListWidget()
        self.option_list.addItems(["Dar alta S.S.", "Pedir Factura", "Enviar Factura"])
        layout.addWidget(self.option_list)
        
        # Botón para adjuntar factura (solo para "Enviar Factura")
        self.btn_attach_invoice = QPushButton("Adjuntar Factura")
        self.btn_attach_invoice.clicked.connect(self.attach_invoice_and_check)
        self.btn_attach_invoice.setVisible(False)  # Oculto por defecto
        layout.addWidget(self.btn_attach_invoice)
        
        self.btn_select = QPushButton("Seleccionar")
        self.btn_select.clicked.connect(self.select_option)
        layout.addWidget(self.btn_select)
        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    # Selections
    def select_option(self):
        item = self.option_list.currentItem()
        if not item:
            return
        option = item.text()
        if option == "Dar alta S.S.":
            self._generate_text_alta_ss()
        elif option == "Pedir Factura":
            self._generate_text_pedir_factura()
        elif option == "Enviar Factura":
            self._generate_text_enviar_factura()
            # Mostrar botón de adjuntar factura
            self.btn_attach_invoice.setVisible(True)
    
    def _select_company_from_excel(self):
        """Selecciona una empresa desde Excel y devuelve (nombre, datos)."""
        try:
            df = load_dataframe(EXCEL_FILE_PATH, sheet_name='datos_empresa')
            if df is None or df.empty:
                raise ValueError("Archivo Excel vacío o no encontrado.")
            company_names = df['Nombre_Empresa'].tolist()
            company_name, ok = QInputDialog.getItem(
                self, "Seleccionar Empresa", "Empresa:", company_names, 0, False
            )
            if not ok or not company_name:
                return None, None
            company_data = get_company_data(company_name, df)
            return company_name, company_data
        except Exception as e:
            show_error_dialog(self, "Error", f"Error al cargar empresas: {e}")
            return None, None

    def _select_company_from_calendar(self):
        """Selecciona una empresa desde eventos reales del calendario."""
        try:
            events = get_events()
            if not events:
                QMessageBox.warning(self, "Advertencia", "No hay eventos en el calendario.")
                return None, None, None

            # Extraer empresas únicas con datos reales
            empresas_eventos = {}
            for ev in events:
                desc = ev.get('description', '')
                if '€' in desc:
                    parts = desc.split('€', 1)
                    if len(parts) == 2:
                        tarifa = parts[0].strip()
                        empresa = parts[1].strip()
                        empresas_eventos[empresa] = tarifa

            if not empresas_eventos:
                QMessageBox.warning(self, "Advertencia", "No se encontraron empresas en los eventos.")
                return None, None, None

            empresa, ok = QInputDialog.getItem(
                self, "Seleccionar Empresa", "Empresa (desde eventos):",
                list(empresas_eventos.keys()), 0, False
            )
            if not ok or not empresa:
                return None, None, None

            tarifa = empresas_eventos[empresa]
            return empresa, tarifa, None  # empresa, tarifa_real, datos_excel (opcional)

        except Exception as e:
            show_error_dialog(self, "Error", f"Error al cargar eventos: {e}")
            return None, None, None

    # Format 
    def _format_days_spanish(self, days_list, month_name):
        """
        Convierte una lista de días [1, 2, 3, 5, 7, 8, 9] en texto legible:
        "1 al 3, 5 y del 7 al 9 de enero"
        """
        if not days_list:
            return "[días]"

        # Ordenar y eliminar duplicados
        days = sorted(set(days_list))
        ranges = []
        start = days[0]
        end = days[0]

        for day in days[1:]:
            if day == end + 1:
                end = day
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start} al {end}")
                start = day
                end = day

        # Añadir último rango
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start} al {end}")

        # Formatear según número de rangos
        if len(ranges) == 1:
            result = ranges[0]
        elif len(ranges) == 2:
            result = f"{ranges[0]} y {ranges[1]}"
        else:
            result = ", ".join(ranges[:-1]) + f" y {ranges[-1]}"

        return f"{result} de {month_name.lower()}"

    def _format_bank_accounts(self, raw_text):
        """
        Formatea una cadena de cuentas bancarias separadas por '; ' en líneas individuales.
        Ej: "CaixaBank: ES12...; Santander: ES34..." → "CaixaBank: ES12...\nSantander: ES34..."
        """
        if not raw_text or raw_text == "[Cuenta Bancaria]":
            return raw_text
        # Separar por '; ' y unir con saltos de línea
        accounts = raw_text.split(", ")
        return "\n".join(accounts)
  
    # Generate
    def _generate_text_alta_ss(self):
        # 1. Seleccionar empresa
        empresa, tarifa, _ = self._select_company_from_calendar()
        if not empresa:
            return

        # 2. Seleccionar mes/año - Permitir año actual y anterior
        from PyQt6.QtWidgets import QInputDialog
        from datetime import datetime

        current_year = datetime.now().year
        # Añadir el año anterior a las opciones
        years = [str(y) for y in range(current_year - 1, current_year + 2)]  # Ej: 2024, 2025, 2026
        months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        # Seleccionar mes
        month_name, ok = QInputDialog.getItem(
            self, "Seleccionar Mes", "Mes:", months, 0, False
        )
        if not ok:
            return
        month_num = months.index(month_name) + 1

        # Seleccionar año - Ahora incluye el año anterior
        year_str, ok = QInputDialog.getItem(
            self, "Seleccionar Año", "Año:", years, 0, False
        )
        if not ok:
            return
        year = int(year_str)

        # 3. Filtrar fechas del calendario para ese mes/año y empresa
        events = get_events()
        target_dates = set()
        for ev in events:
            desc = ev.get('description', '')
            if f"€ {empresa}" in desc or f"{tarifa}€ {empresa}" in desc:
                start = ev['start'].get('dateTime', ev['start'].get('date'))
                if start:
                    fecha = start.split('T')[0]  # YYYY-MM-DD
                    ev_year, ev_month, _ = map(int, fecha.split('-'))
                    if ev_year == year and ev_month == month_num:
                        target_dates.add(fecha)

        if not target_dates:
            from utils.common_functions import show_info_dialog
            show_info_dialog(self, "Información", f"No hay eventos para {empresa} en {month_name} {year}.")
            return

        # 4. Formatear fechas inteligentemente
        dias = sorted([int(d.split('-')[2]) for d in target_dates])  # Solo el día del mes
        texto_fechas = self._format_days_spanish(dias, month_name)

        subject = "Alta en S.S."
        text = (
            f"Hola buenos días\n\n"
            f"Querría darme de alta para los días {texto_fechas}.\n\n"
            f"Muchas gracias,\nUn saludo,\nJavier"
        )
        self._apply_text(subject, text)  

    def _generate_text_pedir_factura(self):
        # 1. Seleccionar empresa
        empresa, tarifa, _ = self._select_company_from_calendar()
        if not empresa:
            return

        # 2. Seleccionar mes/año - Permitir año actual y anterior
        from PyQt6.QtWidgets import QInputDialog
        from datetime import datetime

        current_year = datetime.now().year
        # Añadir el año anterior a las opciones
        years = [str(y) for y in range(current_year - 1, current_year + 2)]  # Ej: 2024, 2025, 2026
        months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        month_name, ok = QInputDialog.getItem(self, "Mes", "Selecciona mes:", months, 0, False)
        if not ok:
            return
        month_num = months.index(month_name) + 1

        year_str, ok = QInputDialog.getItem(self, "Año", "Selecciona año:", years, 0, False)
        if not ok:
            return
        year = int(year_str)

        # 3. Cargar datos de Excel para CIF y dirección
        try:
            df = load_dataframe(EXCEL_FILE_PATH, sheet_name='datos_empresa')
            company_data = get_company_data(empresa, df)
        except:
            company_data = {}

        nombre_empresa = empresa
        cif = company_data.get('CIF', "[CIF]")
        direccion = company_data.get('Direccion', "[Dirección]")

        # 4. Extraer importe total del calendario para ese mes/empresa
        events = get_events()
        total_importe = 0.0
        for ev in events:
            desc = ev.get('description', '')
            summary = ev.get('summary', '')
            if f"€ {empresa}" in desc or f"{tarifa}€ {empresa}" in desc:
                start = ev['start'].get('dateTime', ev['start'].get('date'))
                if start:
                    ev_year, ev_month, _ = map(int, start.split('T')[0].split('-'))
                    if ev_year == year and ev_month == month_num:
                        # Buscar importe en description o summary
                        importe = self._extract_amount_from_text(desc + " " + summary)
                        total_importe += importe

        importe_str = f"{total_importe:.2f}" if total_importe > 0 else "[importe]"

        # 5. Determinar tarea típica
        from utils.company_utils import normalize_company_name
        tarea = EMPRESA_TAREA_DEFAULT.get(normalize_company_name(empresa), "servicios")

        subject = f"Pedir Factura {nombre_empresa} {month_name} {year}"
        text = (
            f"Hola buenos días\n\n"
            f"Querría hacer una factura de {importe_str}€ + IVA,\n"
            f"para el evento [nombre_evento] en [location], como {tarea},\n\n"
            f"Por favor indiquen concepto de referencia en la factura [ref_cliente]\n\n"
            f"Os dejo los datos del cliente:\n"
            f"Nombre: {nombre_empresa}\n"
            f"CIF: {cif}\n"
            f"Dirección: {direccion}\n\n"
            f"Muchas gracias\nUn saludo\nJavier"
        )
        self._apply_text(subject, text)

    def _generate_text_enviar_factura(self):
        # 1. Seleccionar empresa y mes/año
        empresa, tarifa, _ = self._select_company_from_calendar()
        if not empresa:
            return

        current_year = datetime.now().year
        # Añadir el año anterior a las opciones
        years = [str(y) for y in range(current_year - 1, current_year + 2)]  # Ej: 2024, 2025, 2026
        months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        month_name, ok = QInputDialog.getItem(self, "Mes", "Selecciona mes:", months, 0, False)
        if not ok:
            return
        month_num = months.index(month_name) + 1

        year_str, ok = QInputDialog.getItem(self, "Año", "Selecciona año:", years, 0, False)
        if not ok:
            return
        year = int(year_str)

        # 2. Calcular importe total del mes
        events = get_events()
        total_importe = 0.0
        for ev in events:
            desc = ev.get('description', '')
            if f"€ {empresa}" in desc or f"{tarifa}€ {empresa}" in desc:
                start = ev['start'].get('dateTime', ev['start'].get('date'))
                if start:
                    ev_year, ev_month, _ = map(int, start.split('T')[0].split('-'))
                    if ev_year == year and ev_month == month_num:
                        importe = self._extract_amount_from_text(desc + " " + ev.get('summary', ''))
                        total_importe += importe

        importe_str = f"{total_importe:.2f}" if total_importe > 0 else "[importe]"

        # 3. Seleccionar cooperativa y obtener datos
        try:
            df_coop = load_dataframe(EXCEL_FILE_PATH, sheet_name='datos_cooperativas')
            coop_names = df_coop['Nombre_Cooperativa'].tolist()
            coop_name, ok = QInputDialog.getItem(self, "Cooperativa", "Selecciona:", coop_names, 0, False)
            if not ok:
                return
            coop_data = get_coop_data(coop_name, df_coop)
            email_coop = coop_data.get('Mails', '').strip()

            # Métodos de pago
            metodos_raw = coop_data.get('Metodo_de_pago', "[Métodos]")
            if metodos_raw and metodos_raw != "[Métodos]":
                metodos = f"Transferencia Bancaria:\n{metodos_raw}"
            else:
                metodos = "Transferencia Bancaria:\n[Métodos]"

            # Cuentas bancarias (opcional)
            cuentas_raw = coop_data.get('Cuenta_Bancaria', "").strip()
            cuentas_section = ""
            if cuentas_raw and cuentas_raw != "[Cuenta Bancaria]":
                if ';' in cuentas_raw:
                    cuentas_lista = [c.strip() for c in cuentas_raw.split(';')]
                    cuentas = "\n".join(cuentas_lista)
                else:
                    cuentas = cuentas_raw
                cuentas_section = f"Cuenta bancaria:\n{cuentas}\n\n"

        except Exception as e:
            show_error_dialog(self, "Error", f"Error al cargar datos de cooperativa: {e}")
            return

        # 4. Tarea típica
        tarea = EMPRESA_TAREA_DEFAULT.get(normalize_company_name(empresa), "servicios")

        # 5. Generar texto y asunto
        subject = f"Factura {empresa} {month_name} {year} [ref_cliente]"
        text = (
            f"Hola buenos días\n\n"
            f"Os mando la factura {month_name} {year} con un importe total de {importe_str}€ + IVA,\n"
            f"para el evento [nombre_evento] en [location], como {tarea}.\n\n"
            f"Por favor indiquen concepto de referencia en la factura [ref_coop].\n\n"
            f"{metodos}\n\n"
            f"{cuentas_section}"
            f"Muchas gracias\nUn saludo\nJavier"
        )

        # 6. Aplicar texto y establecer destinatario
        self._apply_text(subject, text, email_coop)
        
        # Activar modo de validación de factura
        if hasattr(self.parent_window, 'sendfactura'):
            self.parent_window.sendfactura = True
        
    # Extract
    def _extract_amount_from_invoice_text(self, invoice_text):
        """
        Extrae el importe total de un texto de factura.
        Busca patrones como 'TOTAL: 1234.56€' o '(Total: 1234,56€)'
        """
        import re
        
        # Patrones comunes para importe total en facturas
        patterns = [
            r'(?:TOTAL|Total|Importe Total|IMPORTE TOTAL)[^\w\n]*([0-9.,]+)\s*€',
            r'\(Total:\s*([0-9.,]+)\s*€\)',
            r'(?:TOTAL|Total):\s*€?\s*([0-9.,]+)',
            r'(?:IMPORTE|Importe):\s*([0-9.,]+)\s*€'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, invoice_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        # Convertir a número (manejar comas como decimales)
                        amount_str = match.replace('.', '').replace(',', '.')  # 1.234,56 -> 1234.56
                        return float(amount_str)
                    except ValueError:
                        continue
        
        return None

    def _extract_amount_from_text(self, text):
        """
        Extrae el importe más alto de un texto, buscando:
        - Números seguidos de '€'
        - Números entre paréntesis al final: (Total: XXX€)
        """
        amounts = []

        # Buscar todos los importes con €
        for match in re.finditer(r'(\d+(?:[.,]\d+)?)\s*€', text):
            try:
                amount = float(match.group(1).replace(',', '.'))
                amounts.append(amount)
            except ValueError:
                continue

        # Buscar total entre paréntesis
        total_match = re.search(r'\(Total:\s*(\d+(?:[.,]\d+)?)\s*€\)', text)
        if total_match:
            try:
                total = float(total_match.group(1).replace(',', '.'))
                amounts.append(total)
            except ValueError:
                pass

        return max(amounts) if amounts else 0.0
    
    def _extract_amount_from_message_text(self, message_text):
        """
        Extrae el importe del mensaje del correo.
        Busca patrones como 'importe total de 1234.56€'
        """
        import re
        
        # Patrones comunes para importe en mensajes
        patterns = [
            r'(?:importe total|total|importe)\s*de?\s*([0-9.,]+)\s*€',
            r'([0-9.,]+)\s*€\s*(?:\+?\s*IVA)?',
            r'(?:factura|monto)\s*de\s*([0-9.,]+)\s*€'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        # Convertir a número (manejar comas como decimales)
                        amount_str = match.replace('.', '').replace(',', '.')  # 1.234,56 -> 1234.56
                        return float(amount_str)
                    except ValueError:
                        continue
        
        return None

    # Attach, check & Validate
    def attach_invoice_and_check(self):
        """
        Adjuntar factura y verificar que coincida con el mensaje.
        """
        from utils.file_utils import select_files
        from utils.common_functions import show_info_dialog, show_warning_dialog, confirm_action
        import os

        # 1. Seleccionar archivo PDF
        invoice_paths = select_files(
            parent=self,
            file_types=["PDF"],
            list_widget=None  # No añadir a una lista, solo obtener la ruta
        )
        
        if not invoice_paths:
            show_warning_dialog(self, "Advertencia", "No se seleccionó ninguna factura.")
            return
        
        invoice_path = invoice_paths[0]  # Tomar solo el primero si se seleccionan varios
        print(f"[INFO] Factura seleccionada: {invoice_path}")

        # 2. Obtener texto del mensaje actual
        message_text = self.parent_window.compose_area.toPlainText()
        if not message_text:
            show_warning_dialog(self, "Advertencia", "El mensaje está vacío. No se puede verificar la factura.")
            return

        # 3. Verificar factura
        success, message = self.validate_invoice_before_send()
        
        if success:
            show_info_dialog(self, "Éxito", "La factura adjunta coincide con el mensaje.")
            # Añadir a la lista de adjuntos
            self.parent_window.attached_files.append(invoice_path)
            self.parent_window.attach_list.addItem(os.path.basename(invoice_path))
        else:
            show_warning_dialog(self, "Error", f"Validación fallida: {message}")

    def check_attached_invoice(self, invoice_path: str, message_text: str) -> tuple:
        """
        Verifica si el número de factura adjunto coincide con el texto del mensaje.
        Args:
            invoice_path (str): Ruta al PDF de la factura adjunta.
            message_text (str): Texto del mensaje del email.
        Returns:
            tuple: (bool, list) - (True/False si coinciden, lista de advertencias)
        """
        print(f"[INFO] Verificando factura adjunta: {invoice_path}")
        warnings = []
        
        # 1. Extraer texto del PDF adjunto
        from ia_processor.utils.ocr_utils import extract_text_from_file
        invoice_text = extract_text_from_file(invoice_path)
        if not invoice_text:
            print(f"[WARNING] No se pudo extraer texto de la factura adjunta.")
            warnings.append("No se pudo extraer texto de la factura PDF")
            return False, warnings
        
        # 2. Extraer número de factura del PDF adjunto (usando regex)
        import re
        invoice_number_match = re.search(r'(?:Factura|Nº)[:\s]*([A-Z0-9\-\/]+)', invoice_text, re.IGNORECASE)
        if not invoice_number_match:
            print(f"[WARNING] No se encontró número de factura en el PDF adjunto.")
            warnings.append("No se encontró número de factura en el PDF")
            return False, warnings
        
        invoice_number = invoice_number_match.group(1).strip()
        print(f"[INFO] Número de factura adjunta: {invoice_number}")

        # 3. Buscar ese número en el texto del mensaje
        if invoice_number in message_text:
            print(f"[INFO] ✅ El número de factura '{invoice_number}' coincide con el mensaje.")
        else:
            print(f"[INFO] ❌ El número de factura '{invoice_number}' NO coincide con el mensaje.")
            warnings.append(f"Número de factura '{invoice_number}' no encontrado en el mensaje")
            
        # 4. Extraer importe de la factura
        importe_match = re.search(r'(?:total)[^\w\n]*euros?[^\w\n]*([0-9.,]+)', invoice_text, re.IGNORECASE)
        if importe_match:
            factura_importe = importe_match.group(1).replace('.', '').replace(',', '.')
            try:
                factura_importe_float = float(factura_importe)
                print(f"[INFO] Importe de factura: {factura_importe_float}€")
                
                # 5. Extraer importe del mensaje
                mensaje_importe_match = re.search(r'(\d+(?:[.,]\d+)?)\s*€', message_text)
                if mensaje_importe_match:
                    mensaje_importe = mensaje_importe_match.group(1).replace('.', '').replace(',', '.')
                    mensaje_importe_float = float(mensaje_importe)
                    
                    # 6. Comparar importes
                    if abs(factura_importe_float - mensaje_importe_float) < 0.01:  # Diferencia menor a 1 céntimo
                        print(f"[INFO] ✅ Importes coinciden: {factura_importe_float}€")
                    else:
                        print(f"[INFO] ❌ Importes no coinciden: factura={factura_importe_float}€, mensaje={mensaje_importe_float}€")
                        warnings.append(f"Importe no coincide: factura {factura_importe_float}€ vs mensaje {mensaje_importe_float}€")
                else:
                    print(f"[WARNING] No se encontró importe en el mensaje")
                    warnings.append("No se encontró importe en el mensaje")
            except ValueError:
                print(f"[WARNING] Error convirtiendo importe")
        else:
            print(f"[WARNING] No se encontró importe en la factura")
            warnings.append("No se encontró importe en la factura")
        return len(warnings) == 0, warnings
    
    def validate_invoice_before_send(self):
        """
        Valida que haya factura adjunta y que coincida con el mensaje antes de enviar.
        Returns:
            tuple: (bool, str) - (True/False si pasa validación, mensaje de resultado)
        """
        from utils.common_functions import show_warning_dialog, show_info_dialog, confirm_action
        import re
        import os

        # 1. Verificar que hay archivos adjuntos
        if not self.parent_window.attached_files:
            show_warning_dialog(self, "Advertencia", "Debe adjuntar una factura PDF antes de enviar.")
            return False, "No hay factura adjunta"

        # 2. Verificar que haya un PDF adjunto
        pdf_found = False
        pdf_path = None
        for file_path in self.parent_window.attached_files:
            if file_path.lower().endswith('.pdf'):
                pdf_found = True
                pdf_path = file_path
                break

        if not pdf_found:
            show_warning_dialog(self, "Advertencia", "Debe adjuntar una factura PDF antes de enviar.")
            return False, "No hay factura PDF adjunta"

        # 3. Verificar que el PDF exista
        if not os.path.exists(pdf_path):
            show_warning_dialog(self, "Error", f"El archivo PDF no existe: {pdf_path}")
            return False, f"Archivo PDF no existe: {pdf_path}"

        # 4. Obtener texto del mensaje
        message_text = self.parent_window.compose_area.toPlainText()
        if not message_text:
            show_warning_dialog(self, "Advertencia", "El mensaje está vacío. No se puede verificar la factura.")
            return False, "Mensaje vacío"

        # 5. Extraer importe de la factura PDF
        from ia_processor.utils.ocr_utils import extract_text_from_file
        invoice_text = extract_text_from_file(pdf_path)
        if not invoice_text:
            show_warning_dialog(self, "Error", "No se pudo extraer texto de la factura PDF.")
            return False, "No se pudo leer la factura PDF"

        # 6. Buscar importe total en la factura
        importe_factura = self._extract_amount_from_invoice_text(invoice_text)
        if importe_factura is None:
            show_warning_dialog(self, "Advertencia", "No se encontró importe total en la factura PDF.")
            return False, "No se encontró importe en la factura"

        # 7. Buscar importe en el mensaje
        importe_mensaje = self._extract_amount_from_message_text(message_text)
        if importe_mensaje is None:
            show_warning_dialog(self, "Advertencia", "No se encontró importe en el mensaje del correo.")
            return False, "No se encontró importe en el mensaje"

        # 8. Comparar importes (permitir pequeña diferencia por redondeo)
        difference = abs(importe_factura - importe_mensaje)
        if difference > 0.01:  # Más de 1 céntimo de diferencia
            warning_msg = f"""
    Se encontró discrepancia en los importes:
    - Importe en factura PDF: {importe_factura:.2f}€
    - Importe en mensaje: {importe_mensaje:.2f}€
    - Diferencia: {difference:.2f}€

    ¿Desea continuar con el envío a pesar de la discrepancia?
            """.strip()
            if confirm_action(self, "Discrepancia encontrada", warning_msg):
                show_info_dialog(self, "Continuando", "Factura enviada a pesar de discrepancia de importe.")
                return True, "Validación pasada con discrepancia aceptada"
            else:
                return False, "Discrepancia de importe rechazada por el usuario"
        else:
            # Importes coinciden
            show_info_dialog(self, "Éxito", "La factura adjunta coincide con el mensaje.")
            return True, "Validación completada exitosamente"

    def _apply_text(self, subject, text, to_email=None):
        """Enviar datos a la ventana principal y cerrar"""
        if hasattr(self.parent_window, "set_auto_text"):
            # Asegúrate de que set_auto_text también acepte to_email
            self.parent_window.set_auto_text(subject, text, to_email)
        else:
            show_error_dialog(self, "Error", "La ventana principal no tiene set_auto_text.")
        self.close()