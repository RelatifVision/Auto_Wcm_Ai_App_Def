# ia_processor/final_comparison.py
import json
import time
import spacy
from pathlib import Path
from ia_processor.config import MODEL_OUTPUT_DIR

def compare_all_models():
    """Comparar todos los modelos entrenados con detalles"""
    
    models_to_test = [
        ("modelo_original", "ia_processor/models/spacy_model"),
        ("modelo_mejorado", "ia_processor/models/spacy_model_enhanced")
    ]
    
    results = {}
    
    for model_name, model_path in models_to_test:
        if Path(model_path).exists():
            print(f"\n=== Evaluando {model_name} ===")
            
            # Cargar modelo
            start_time = time.time()
            nlp = spacy.load(model_path)
            load_time = time.time() - start_time
            
            # Obtener información del modelo
            labels = nlp.get_pipe("ner").labels
            print(f"Etiquetas reconocidas: {labels}")
            
            # Verificar entidades
            test_text = "FACTURA: 182454 Fecha: 31/12/2024 TOTAL Euros2.116,66"
            doc = nlp(test_text)
            detected_entities = [(ent.text, ent.label_) for ent in doc.ents]
            print(f"Entidades detectadas: {detected_entities}")
            
            # Guardar resultados detallados
            results[model_name] = {
                "load_time": load_time,
                "labels": list(labels),
                "detected_entities": detected_entities,
                "status": "loaded_successfully"
            }
            
            print(f"Modelo cargado en {load_time:.2f}s")
        else:
            print(f"Modelo no encontrado: {model_path}")
            results[model_name] = {"status": "not_found"}
    
    # Guardar resultados detallados
    with open("final_model_comparison.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print("\n=== Comparación Final ===")
    for model_name, data in results.items():
        if data.get("status") == "loaded_successfully":
            print(f"✓ {model_name}:")
            print(f"  - Tiempo de carga: {data['load_time']:.2f}s")
            print(f"  - Etiquetas: {', '.join(data['labels'])}")
            print(f"  - Entidades detectadas: {len(data['detected_entities'])}")
        else:
            print(f"✗ {model_name}: No encontrado")
    
    print("\nComparación final completada")
    return results

if __name__ == "__main__":
    compare_all_models()