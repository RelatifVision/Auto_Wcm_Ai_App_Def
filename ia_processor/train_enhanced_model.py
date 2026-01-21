# ia_processor/train_enhanced_model.py
import json
# CORREGIDO: Importar desde el submódulo training dentro de ia_processor
# Preferir import relativo cuando el módulo se ejecuta como paquete
try:
    from ia_processor.train_ner_model import train_spacy_model, convert_to_spacy_format
    from .config import TRAINING_DATA_FILE, MODEL_OUTPUT_DIR
except Exception:
    # Fallback: cuando ejecutas el archivo directamente (no como paquete)
    from ia_processor.train_ner_model import train_spacy_model, convert_to_spacy_format
    from ia_processor.config import TRAINING_DATA_FILE, MODEL_OUTPUT_DIR

def train_enhanced_model():
    """Entrenar modelo con datos mejorados"""
    
    # Generar datos virtuales
    try:
        from ia_processor.generate_virtual_examples import generate_virtual_examples
        enhanced_data = generate_virtual_examples()
    except ImportError:
        # Si no existe, crear uno simple
        print("Generando datos virtuales básicos...")
        # Aquí iría tu lógica de generación básica
        
        # Cargar datos reales
        with open(TRAINING_DATA_FILE, "r", encoding="utf-8") as f:
            real_data = json.load(f)
        
        # Simplemente usar los datos reales
        enhanced_data = real_data
    
    # Guardar datos mejorados
    with open("enhanced_training_data.json", "w", encoding="utf-8") as f:
        json.dump(enhanced_data, f, ensure_ascii=False, indent=4)
    
    # Entrenar con datos mejorados
    train_data = convert_to_spacy_format(enhanced_data)
    
    print("=== Entrenando modelo con datos mejorados ===")
    # Asegúrate de guardar en una ruta distinta si quieres tener ambos modelos
    # Por ejemplo, puedes pasar MODEL_OUTPUT_DIR + "_enhanced" o usar un nombre fijo como "spacy_model_enhanced"
    from pathlib import Path
    enhanced_model_path = Path(MODEL_OUTPUT_DIR).parent / "spacy_model_enhanced" # Cambia el nombre
    train_spacy_model(train_data, model_name="es_core_news_lg", n_iter=100, output_path=enhanced_model_path) # Pasar la ruta específica
    
    print("Modelo mejorado entrenado y guardado")

if __name__ == "__main__":
    train_enhanced_model()