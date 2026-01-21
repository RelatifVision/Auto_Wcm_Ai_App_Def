# ia_processor/generate_training_data.py
import json
from pathlib import Path
from .config import TRAINING_DATA_FILE, OUTPUT_DIR


def extract_entities_from_factura(text: str):
    """Extrae entidades con posiciones absolutas correctas."""
    entities = []
    
    # Buscar número de factura: "FACTURA: 182454"
    # Usar regex más robusto
    import re
    pattern = r'(?:FACTURA|FACTURA Nº):\s*(\d+|[A-Z0-9\-\/]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        entities.append([match.start(1), match.end(1), "NUMERO_FACTURA"])
    
    # Buscar fecha: "Fecha: 31/12/2024"
    pattern = r'Fecha:\s*([\d\/\-\.]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        entities.append([match.start(1), match.end(1), "FECHA_EMISION"])
    
    # Buscar importe total: "TOTAL Euros2.116,66"
    pattern = r'(?:TOTAL|Total):\s*€?\s*([\d,\.]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        entities.append([match.start(1), match.end(1), "IMPORTE_TOTAL"])
    
    # Buscar email: info@freelance.es
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.finditer(email_pattern, text)
    for match in email_matches:
        entities.append([match.start(), match.end(), "EMAIL"])
    
    # Eliminar solapamientos
    entities = remove_overlapping_entities(entities)
    
    return entities

def remove_overlapping_entities(entities):
    """Elimina entidades que se solapan."""
    if not entities:
        return entities
    
    # Ordenar por posición de inicio
    sorted_entities = sorted(entities, key=lambda x: x[0])
    filtered_entities = []
    
    for current in sorted_entities:
        # Verificar si se solapa con alguna ya agregada
        overlaps = False
        for existing in filtered_entities:
            # Si se solapan
            if current[0] < existing[1] and current[1] > existing[0]:
                overlaps = True
                break
        
        # Solo agregar si no se solapa
        if not overlaps:
            filtered_entities.append(current)
    
    return filtered_entities

def main():
    training_data = []
    
    # Ruta a tus facturas procesadas
    factura_dir = OUTPUT_DIR / "FACTURA"
    print(f"[INFO] Procesando facturas desde: {factura_dir}")
    
    if factura_dir.exists():
        print(f"[INFO] Leyendo archivos TXT en: {factura_dir}")
        for txt_file in factura_dir.glob("*.txt"):
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()
            
            entities = extract_entities_from_factura(text)
            if entities:
                # Validar posiciones
                valid_entities = []
                text_len = len(text)
                print(f"[DEBUG] Procesada factura: {txt_file.name}")
                print(f"  Longitud texto: {text_len}")
                
                for start, end, label in entities:
                    if 0 <= start <= end <= text_len:
                        extracted_text = text[start:end]
                        print(f"    [{start}, {end}, '{label}']: '{extracted_text}' (OK)")
                        valid_entities.append([start, end, label])
                    else:
                        print(f"    [ERROR] Índice fuera de rango [{start}, {end}] en texto de longitud {text_len}")
                
                if valid_entities:
                    training_data.append({"text": text, "entities": valid_entities})
                    print(f"[INFO] Añadida al dataset: {txt_file.name}")
                else:
                    print(f"[WARNING] No hay entidades válidas en: {txt_file.name}")
            else:
                print(f"[WARNING] No se encontraron entidades en: {txt_file.name}")
    else:
        print(f"[WARNING] Carpeta de facturas no encontrada: {factura_dir}")

    # Guardar
    with open(TRAINING_DATA_FILE, "w", encoding="utf-8") as f: 
        json.dump(training_data, f, ensure_ascii=False, indent=4)
    print(f"[INFO] ✅ training_data.json generado con {len(training_data)} ejemplos.")
    print(f"[INFO] Archivo: {TRAINING_DATA_FILE}")

if __name__ == "__main__":
    main()