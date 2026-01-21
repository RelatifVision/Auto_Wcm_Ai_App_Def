# ia_processor/generate_virtual_examples.py
import json
import re
from pathlib import Path
from ia_processor.config import TRAINING_DATA_FILE

def generate_virtual_examples():
    """Generar ejemplos virtuales a partir de los reales"""
    
    # Cargar ejemplos reales
    with open(TRAINING_DATA_FILE, "r", encoding="utf-8") as f:
        real_examples = json.load(f)
    
    # Generar algunos ejemplos virtuales básicos
    virtual_examples = []
    
    # Plantillas de formato
    templates = [
        "FACTURA: {numero}\nFecha: {fecha}\nTotal: {importe}€\n",
        "FACTURA Nº: {numero}\nFecha: {fecha}\nCliente: {cliente}\nTotal: {importe}€\n"
    ]
    
    # Ejemplos reales para extraer patrones
    patterns = {
        "numero": ["182454", "182689", "182909"],
        "fecha": ["31/12/2024", "15/01/2025", "24/01/2025"],
        "cliente": ["VISUALMAX S.L.", "PEAK PRODUCCION TÉCNICA SL", "TELEPIXEL S.L."],
        "importe": ["2.116,66", "847,00", "2.643,85"]
    }
    
    # Generar ejemplos virtuales
    for i, template in enumerate(templates):
        for num in patterns["numero"]:
            for fecha in patterns["fecha"]:
                for cliente in patterns["cliente"]:
                    for importe in patterns["importe"]:
                        try:
                            example = template.format(
                                numero=num,
                                fecha=fecha,
                                cliente=cliente,
                                importe=importe
                            )
                            
                            # Añadir entidades básicas
                            entities = []
                            # Extraer entidades de ejemplo generado
                            if "FACTURA:" in example:
                                match = re.search(r'FACTURA[:\s]*(\d+)', example)
                                if match:
                                    entities.append([match.start(1), match.end(1), "NUMERO_FACTURA"])
                            
                            if "Fecha:" in example:
                                match = re.search(r'Fecha[:\s]*([\d\/\-\.]+)', example)
                                if match:
                                    entities.append([match.start(1), match.end(1), "FECHA_EMISION"])
                            
                            if "Total:" in example:
                                match = re.search(r'Total[:\s]*€?([\d,\.]+)', example)
                                if match:
                                    entities.append([match.start(1), match.end(1), "IMPORTE_TOTAL"])
                            
                            if entities:
                                virtual_examples.append({
                                    "text": example,
                                    "entities": entities
                                })
                                
                        except Exception as e:
                            continue
    
    # Combinar con ejemplos reales
    combined_examples = real_examples + virtual_examples[:10]  # Limitar a 10 nuevos
    
    # Guardar
    with open("virtual_training_data.json", "w", encoding="utf-8") as f:
        json.dump(combined_examples, f, ensure_ascii=False, indent=4)
    
    print(f"Generados {len(virtual_examples)} ejemplos virtuales")
    print(f"Total ejemplos: {len(combined_examples)}")
    
    return combined_examples

if __name__ == "__main__":
    generate_virtual_examples()