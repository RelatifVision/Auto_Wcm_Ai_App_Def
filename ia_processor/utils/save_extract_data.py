# ia_processor/save_extracted_data.py

import os
import json
from pathlib import Path
import pandas as pd
from ..config import OUTPUT_DIR, RESULTS_DIR


def save_results_to_json(results, filename="extracted_data.json"):
    """Guardar resultados en un archivo JSON."""
    filepath = RESULTS_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"[INFO] Resultados guardados en: {filepath}")

def save_results_to_excel(results, filename="extracted_data.xlsx"):
    """Guardar resultados en un archivo Excel."""
    filepath = RESULTS_DIR / filename
    
    # Convertir resultados a DataFrame
    df_list = []
    for result in results:
        for entity in result["entities"]:
            df_list.append({
                "nombre_archivo": result["nombre_archivo"],
                "tipo_documento": result["tipo_documento"],
                "texto_extraido": result["texto_extraido"][:100] + "...",
                "entidad": entity["text"],
                "tipo_entidad": entity["label"],
                "posicion": f"{entity['start']}-{entity['end']}"
            })
    
    df = pd.DataFrame(df_list)
    df.to_excel(filepath, index=False)
    print(f"[INFO] Resultados guardados en: {filepath}")

def main():
    """Función principal para guardar resultados."""
    print("[INFO] Guardando resultados de extracción de entidades...")
    
    # Cargar resultados de procesamiento
    output_files = list(OUTPUT_DIR.glob("*.json"))
    if not output_files:
        print("[INFO] No se encontraron archivos de resultados para guardar.")
        return
    
    all_results = []
    for file in output_files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_results.extend(data)
    
    if not all_results:
        print("[INFO] No hay resultados para guardar.")
        return
    
    # Guardar en JSON y Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_results_to_json(all_results, f"extracted_data_{timestamp}.json")
    save_results_to_excel(all_results, f"extracted_data_{timestamp}.xlsx")
    
    print("[INFO] Guardado de resultados completado.")

if __name__ == "__main__":
    from datetime import datetime
    main()