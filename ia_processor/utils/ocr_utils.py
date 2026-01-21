# ia_processor/utils/ocr_utils.py
import os
import pdfplumber
import pytesseract
from PIL import Image

def extract_text_from_file(file_path: str) -> str:
    """
    Extrae texto de un archivo (PDF o imagen) usando la herramienta adecuada.
    
    Args:
        file_path (str): Ruta al archivo.
        
    Returns:
        str: Texto extraído o cadena vacía si falla.
    """
    if not os.path.exists(file_path):
        print(f"[ERROR] El archivo no existe: {file_path}")
        return ""

    try:
        if file_path.lower().endswith('.pdf'):
            return extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            return extract_text_from_image(file_path)
        else:
            print(f"[WARNING] Formato de archivo no soportado: {file_path}")
            return ""
    except Exception as e:
        print(f"[ERROR] Error al extraer texto de {file_path}: {e}")
        return ""

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae texto de un PDF usando pdfplumber."""
    texto = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina + "\n"
    except Exception as e:
        print(f"[ERROR] pdfplumber falló en {pdf_path}: {e}")
    return texto

def extract_text_from_image(image_path: str) -> str:
    """Extrae texto de una imagen usando Tesseract OCR."""
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img, lang='spa')
    except Exception as e:
        print(f"[ERROR] Tesseract falló en {image_path}: {e}")
        return ""