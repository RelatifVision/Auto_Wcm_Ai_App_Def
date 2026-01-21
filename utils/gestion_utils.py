from PyQt6.QtWidgets import QMessageBox, QDialog, QFormLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidgetItem, QTableWidget, QWidget, QColorDialog
from PyQt6.QtGui import QColor
import pandas as pd
import re
from utils.excel_utils import load_dataframe
from config import EXCEL_FILE_PATH

class ColorPreviewButton(QPushButton):
    """Botón que muestra un color y abre un selector al hacer clic."""
    def __init__(self, initial_color="#333333", parent=None):
        super().__init__(parent)
        self.set_color(initial_color)
        self.clicked.connect(self._open_color_dialog)

    def set_color(self, color_hex):
        self.color_hex = color_hex
        self.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #000;")

    def _open_color_dialog(self):
        color = QColorDialog.getColor(QColor(self.color_hex), self, "Seleccionar Color")
        if color.isValid():
            self.color_hex = color.name()
            self.set_color(self.color_hex)
            if hasattr(self, 'on_color_selected'):
                self.on_color_selected(self.color_hex)

class ColorWidget(QWidget):
    """Widget que muestra un cuadrado de color y permite cambiarlo."""
    def __init__(self, color_hex="#000000", parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # Cuadrado de color
        self.color_preview = QPushButton()
        self.color_preview.setFixedSize(20, 20)
        self.set_color(color_hex)

        # Campo de texto (opcional, para ver/editar el código hex)
        self.color_input = QLineEdit(color_hex)
        self.color_input.setFixedWidth(80)
        self.color_input.textChanged.connect(self._on_text_changed)

        # Conectar clic al selector de color
        self.color_preview.clicked.connect(self._open_color_dialog)

        self.layout.addWidget(self.color_preview)
        self.layout.addWidget(self.color_input)

    def set_color(self, color_hex):
        self.color_hex = color_hex
        self.color_preview.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #000;")

    def _open_color_dialog(self):
        color = QColorDialog.getColor(QColor(self.color_hex), self, "Seleccionar Color")
        if color.isValid():
            self.color_hex = color.name()
            self.set_color(self.color_hex)
            self.color_input.setText(self.color_hex)

    def _on_text_changed(self, text):
        if re.match(r'^#[A-Fa-f0-9]{6}$', text):
            self.color_hex = text
            self.set_color(text)

    def get_color(self):
        return self.color_hex

def load_gestion_data(window):
    try:
        window.df_empresa = load_dataframe(EXCEL_FILE_PATH, sheet_name='datos_empresa')
        window.df_cooperativa = load_dataframe(EXCEL_FILE_PATH, sheet_name='datos_cooperativas')
        window.display_data()
    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error al cargar datos: {e}")

def display_table(table, df):
    """
    Mostrar los datos en una tabla específica.
    """
    table.clear()
    table.setRowCount(0)
    table.setColumnCount(len(df.columns))
    table.setHorizontalHeaderLabels(df.columns)
    table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
    for i, row in df.iterrows():
        table.insertRow(i)
        for j, value in enumerate(row):
            if df.columns[j] == "Color":
                # Crear widget de color
                color_widget = ColorWidget(value if pd.notna(value) else "#000000")
                table.setCellWidget(i, j, color_widget)
            else:
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                table.setItem(i, j, item)
    # Ajustar el tamaño de las columnas para que se muestren completas
    table.resizeColumnsToContents()
    table.resizeRowsToContents()

def create_entry(window, entry_type):
    dialog = QDialog(window)
    form_layout = QFormLayout(dialog)
    inputs = {}
    fields = get_fields(entry_type)

    for field in fields:
        if field == "Color":
            color_input = QLineEdit("#333333")
            color_preview = ColorPreviewButton("#333333")
            def make_callback(preview=color_preview, line_edit=color_input):
                def callback(hex_color):
                    line_edit.setText(hex_color)
                return callback
            color_preview.on_color_selected = make_callback()
            color_layout = QHBoxLayout()
            color_layout.addWidget(color_input)
            color_layout.addWidget(color_preview)
            form_layout.addRow("Color:", color_layout)
            inputs[field] = color_input
        else:
            inputs[field] = QLineEdit(dialog)
            form_layout.addRow(f"{field.replace('_', ' ').title()}:", inputs[field])

    btn_save = QPushButton("Guardar")
    btn_save.clicked.connect(lambda: save_entry(window, dialog, entry_type, inputs))
    form_layout.addWidget(btn_save)
    dialog.setLayout(form_layout)
    dialog.setWindowTitle(f"Crear Entrada {entry_type.title()}")
    dialog.exec()

def edit_entry(window, entry_type):
    selected_row = get_selected_row(window, entry_type)
    if selected_row < 0:
        QMessageBox.warning(window, "Advertencia", "Seleccione una fila para editar.")
        return

    dialog = QDialog(window)
    form_layout = QFormLayout(dialog)
    inputs = {}
    fields = get_fields(entry_type)

    for i, field in enumerate(fields):
        current_value = get_item_text(window, entry_type, selected_row, i)
        if field == "Color":
            color_input = QLineEdit(current_value)
            color_preview = ColorPreviewButton(current_value)
            def make_callback(preview=color_preview, line_edit=color_input):
                def callback(hex_color):
                    line_edit.setText(hex_color)
                return callback
            color_preview.on_color_selected = make_callback()
            color_layout = QHBoxLayout()
            color_layout.addWidget(color_input)
            color_layout.addWidget(color_preview)
            form_layout.addRow("Color:", color_layout)
            inputs[field] = color_input
        else:
            inputs[field] = QLineEdit(dialog)
            inputs[field].setText(current_value)
            form_layout.addRow(f"{field.replace('_', ' ').title()}:", inputs[field])

    btn_save = QPushButton("Guardar")
    btn_save.clicked.connect(lambda: save_edited_entry(window, dialog, entry_type, selected_row, inputs))
    form_layout.addWidget(btn_save)
    dialog.setLayout(form_layout)
    dialog.setWindowTitle(f"Editar Entrada {entry_type.title()}")
    dialog.exec()

def save_entry(window, dialog, entry_type, inputs):
    try:
        new_entry = {field: inputs[field].text() for field in inputs}
        new_entry = validate_entry(new_entry, entry_type)
        if new_entry is None:
            return

        df = load_dataframe(EXCEL_FILE_PATH, sheet_name=f'datos_{entry_type}')
        if df is None:
            df = pd.DataFrame([new_entry])
        else:
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)

        with pd.ExcelWriter(EXCEL_FILE_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=f'datos_{entry_type}', index=False)
        load_gestion_data(window)
        dialog.accept()
    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error al guardar la entrada: {e}")
        dialog.reject()

def save_edited_entry(window, dialog, entry_type, selected_row, inputs):
    try:
        updated_entry = {field: inputs[field].text() for field in inputs}
        updated_entry = validate_entry(updated_entry, entry_type)
        if updated_entry is None:
            return

        df = getattr(window, f'df_{entry_type}')
        for field in inputs:
            df.at[selected_row, field] = updated_entry[field]

        with pd.ExcelWriter(EXCEL_FILE_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=f'datos_{entry_type}', index=False)
        load_gestion_data(window)
        dialog.accept()
    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error al guardar los cambios: {e}")
        dialog.reject()

def save_inline_entry(window, entry_type):
    try:
        df = getattr(window, f'df_{entry_type}')
        table = window.table_empresa if entry_type == 'empresa' else window.table_coop

        if table.rowCount() != len(df):
            QMessageBox.warning(window, "Advertencia", "El número de filas no coincide. Recargue los datos.")
            return

        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                if df.columns[col] == "Color":
                    # Obtener el widget de color
                    color_widget = table.cellWidget(row, col)
                    if color_widget:
                        new_value = color_widget.get_color()
                    else:
                        new_value = ""
                else:
                    item = table.item(row, col)
                    new_value = item.text().strip() if item and item.text() else ""

                # Solo actualizar si el valor ha cambiado
                if str(df.iloc[row, col]) != new_value:
                    df.iloc[row, col] = new_value

        with pd.ExcelWriter(EXCEL_FILE_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=f'datos_{entry_type}', index=False)

        QMessageBox.information(window, "Éxito", f"Datos de {entry_type} guardados correctamente.")
        load_gestion_data(window)

    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error al guardar los cambios: {str(e)}")

def delete_entry(window, entry_type):
    selected_row = get_selected_row(window, entry_type)
    if selected_row < 0:
        QMessageBox.warning(window, "Advertencia", "Seleccione una fila para borrar.")
        return

    confirm = QMessageBox.question(
        window,
        "Confirmar Eliminación",
        "¿Está seguro de que desea eliminar esta entrada?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    if confirm != QMessageBox.StandardButton.Yes:
        return

    df = getattr(window, f'df_{entry_type}')
    df.drop(index=selected_row, inplace=True)
    df.reset_index(drop=True, inplace=True)

    with pd.ExcelWriter(EXCEL_FILE_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=f'datos_{entry_type}', index=False)
    load_gestion_data(window)

def get_fields(entry_type):
    if entry_type == 'empresa':
        return ["ID_Empresa", "Nombre_Empresa", "CIF", "Direccion", "Color", "Email", "Telefono", "Jornada_Precio", "Jornada_Horas", "Precio_Hora"]
    elif entry_type == 'cooperativa':
        return ["ID_Coop", "Nombre_Cooperativa", "Metodo_de_pago", "Mails", "Telefono", "CIF"]
    return []

def validate_entry(entry, entry_type):
    if entry_type == 'empresa':
        if not entry["ID_Empresa"].isdigit():
            QMessageBox.warning(None, "Advertencia", "El ID de la empresa debe ser un número entero.")
            return None
        # Validar campos numéricos
        for field in ["Jornada_Precio", "Jornada_Horas", "Precio_Hora"]:
            if entry[field] and not re.match(r'^\d*\.?\d*$', entry[field]):
                QMessageBox.warning(None, "Advertencia", f"El campo '{field}' debe ser un número válido.")
                return None
    elif entry_type == 'cooperativa':
        if not entry["ID_Coop"].isdigit():
            QMessageBox.warning(None, "Advertencia", "El ID de la cooperativa debe ser un número entero.")
            return None
    return entry

def get_selected_row(window, entry_type):
    if entry_type == 'empresa':
        return window.table_empresa.currentRow()
    elif entry_type == 'cooperativa':
        return window.table_coop.currentRow()
    return -1

def get_item_text(window, entry_type, row, column):
    if entry_type == 'empresa':
        item = window.table_empresa.item(row, column)
    elif entry_type == 'cooperativa':
        item = window.table_coop.item(row, column)
    return item.text() if item is not None else ""
