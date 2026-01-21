# utils/file_utils.py
import os
from PyQt6.QtWidgets import QFileDialog, QListWidgetItem, QListWidget
from PyQt6.QtCore import Qt

def select_files(parent, file_types=None, list_widget=None):
    """
    Abre un diálogo para seleccionar archivos y los añade a la lista de adjuntos.
    """
    filters = {
        "Images": "Images (*.png *.jpg *.jpeg *.gif *.bmp)",
        "Videos": "Videos (*.mp4 *.avi *.mov *.mkv)",
        "PDF": "PDF Files (*.pdf)",
        "Word": "Word Documents (*.docx *.doc)",
        "Excel": "Excel Files (*.xlsx *.xls)",
        "PowerPoint": "PowerPoint Files (*.pptx *.ppt)",
        "Text": "Text Files (*.txt)",
        "All": "All Files (*.*)"
    }
    
    if not file_types:
        file_types = list(filters.keys())
    
    file_filter = ";;".join([filters.get(t, f"{t} Files (*)") for t in file_types])
    file_filter += ";;All Files (*)"

    file_paths, _ = QFileDialog.getOpenFileNames(
        parent,
        "Adjuntar archivos",
        os.path.expanduser("~"),
        file_filter
    )
    
    # Asegurarse de que parent tenga el atributo attached_files (debe ser una lista)
    if not hasattr(parent, 'attached_files'):
         parent.attached_files = [] 
    elif not isinstance(parent.attached_files, list):
        # Si existe pero no es una lista, reinicializarlo
        parent.attached_files = []
    # Esto permite adjuntar múltiples lotes de archivos
    parent.attached_files.extend(file_paths) 

    # --- MOSTRAR SOLO LOS NOMBRES EN LA LISTA VISUAL (attach_list) ---
    if list_widget is not None:
        # list_widget.clear() # <- Comentado para no borrar adjuntos previos
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(file_name)
            # Opcional: añadir tooltip con la ruta completa
            # item.setToolTip(file_path)
            list_widget.addItem(item)

    return file_paths
    
def clear_whatsapp_message(compose_area, destination_input, attach_list=None):
    """
    Limpia área de mensaje, destinatario y adjuntos (si existen).
    """
    compose_area.clear()
    destination_input.clear()
    if attach_list:
        attach_list.clear()
        if hasattr(compose_area.parent(), "attached_files"):
            compose_area.parent().attached_files = []
