# ia_processor/training/train_ner_model.py

import os
import json
import spacy
import random
import re
from spacy.training import Example
from spacy.util import minibatch, compounding
from pathlib import Path
from spacy.training.iob_utils import offsets_to_biluo_tags
from .config import BASE_DIR, CLASSIFIED_DIR,  MODELS_DIR, MODEL_OUTPUT_DIR, TRAINING_DATA_FILE, OUTPUT_DIR

# En train_ner_model.py
def check_entity_alignment(training_data):
    """Verifica que las entidades estén correctamente alineadas con el texto."""
    print("[INFO] Verificando alineación de entidades...")
    nlp = spacy.load("es_core_news_lg")  

    errores = []
    for i, item in enumerate(training_data):
        text = item["text"]
        entities = item["entities"]
        
        # Crear doc
        doc = nlp.make_doc(text)
        
        # Verificar alineación
        try:
            # Solo mostrar warnings, no fallar
            tags = offsets_to_biluo_tags(doc, entities)
            if '-' in tags:
                # Contar cuántos '-' hay (entidades mal alineadas)
                misaligned_count = tags.count('-')
                if misaligned_count > 0:
                    print(f"[WARNING] {misaligned_count} entidades mal alineadas en item {i+1}")
                    # No agregar a errores si no es crítico
        except Exception as e:
            print(f"[ERROR] Error al verificar alineación en item {i+1}: {e}")
            errores.append(i+1)

    if errores:
        print(f"\n[INFO] Se encontraron errores en {len(errores)} items.")
        print(f"[INFO] Revisa los items: {errores}")
    else:
        print("[INFO] ✅ La mayoría de entidades están correctamente alineadas.")
       
def load_training_data():
    """Cargar datos de entrenamiento desde training_data.json."""
    print(f"[INFO] Cargando datos de entrenamiento desde: {TRAINING_DATA_FILE}")
    if not TRAINING_DATA_FILE.exists():
        print(f"[ERROR] Archivo no encontrado: {TRAINING_DATA_FILE}")
        return []

    with open(TRAINING_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

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
            # Si se solapan (intervalos se intersectan)
            if current[0] < existing[1] and current[1] > existing[0]:
                overlaps = True
                break
        
        # Solo agregar si no se solapa
        if not overlaps:
            filtered_entities.append(current)
    
    return filtered_entities

def convert_to_spacy_format(data):
    """
    Convierte datos con formato {"text": "...", "entities": [[start, end, label], ...]}
    a formato spaCy: (text, {"entities": [(start, end, label), ...]})
    """
    TRAIN_DATA = []
    for item in data:
        text = item["text"]
        entities = item["entities"]  # ya debe ser una lista de [start, end, label]
        
        # Limpiar entidades solapadas
        cleaned_entities = remove_overlapping_entities(entities)
        
        # Validar formato
        formatted_entities = []
        for ent in cleaned_entities:
            if len(ent) == 3:
                start, end, label = ent
                if isinstance(start, int) and isinstance(end, int) and isinstance(label, str):
                    formatted_entities.append((start, end, label))
                else:
                    print(f"[WARNING] Entidad mal formada: {ent}")
            else:
                print(f"[WARNING] Entidad con formato incorrecto: {ent}")
        TRAIN_DATA.append((text, {"entities": formatted_entities}))
    return TRAIN_DATA

def train_spacy_model(train_data, model_name="es_core_news_lg", n_iter=100, output_path=None):
    """
    Entrena un modelo NER de spaCy con los datos proporcionados.
    Permite especificar una ruta de salida opcional.
    """
    # Cargar modelo base
    if model_name is None:
        nlp = spacy.blank("es")  # Crear modelo en blanco si no hay base
        print("[INFO] Creando modelo en blanco para español.")
    else:
        nlp = spacy.load(model_name)
        print(f"[INFO] Cargando modelo base: {model_name}")

    # Añadir componente NER si no existe
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")

    # Añadir etiquetas
    for _, annotations in train_data:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    # Deshabilitar otros pipes durante el entrenamiento
    pipe_exceptions = ["ner", "trf_wordpiecer", "trf_tok2vec"]
    unaffected_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
    
    # Comenzar entrenamiento
    with nlp.disable_pipes(*unaffected_pipes):  # Solo entrenar NER
        print("[INFO] Iniciando entrenamiento...")
        for itn in range(n_iter):
            print(f"Iteración {itn + 1}/{n_iter}")
            random.shuffle(train_data)
            losses = {}
            # Crear batches
            batches = minibatch(train_data, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                examples = []
                for text, annotations in batch:
                    try:
                        examples.append(Example.from_dict(nlp.make_doc(text), annotations))
                    except Exception as e:
                        print(f"[WARNING] Error al crear ejemplo: {e}")
                        continue
                if examples:  # Solo actualizar si hay ejemplos válidos
                    nlp.update(examples, drop=0.5, losses=losses)
            print(f"Losses: {losses}")

    # --- MODIFICACIÓN AQUÍ ---
    # Usar output_path si se proporciona, de lo contrario usar MODEL_OUTPUT_DIR
    save_path = Path(output_path) if output_path else MODEL_OUTPUT_DIR
    # -----------------------

    # Guardar modelo
    nlp.to_disk(save_path)
    print(f"[INFO] Modelo guardado en: {save_path}")

def main():
    """
    Función principal que orquesta el entrenamiento.
    """
    print("[INFO] Iniciando entrenamiento de modelo spaCy...")
    
    # Cargar datos de entrenamiento
    if not TRAINING_DATA_FILE.exists():
        print(f"[ERROR] Archivo no encontrado: {TRAINING_DATA_FILE}")
        return

    with open(TRAINING_DATA_FILE, "r", encoding="utf-8") as f:
        training_data = json.load(f)
        
    # Verificar alineación de entidades
    check_entity_alignment(training_data) 
    
    # Convertir a formato spaCy
    print("[INFO] Convirtiendo datos a formato spaCy...")
    train_data = convert_to_spacy_format(training_data)
    if not train_data:
        print("[ERROR] No se pudo convertir los datos a formato spaCy.")
        return
    
    # Entrenar modelo
    print("[INFO] Entrenando modelo...")
    train_spacy_model(train_data, model_name="es_core_news_lg", n_iter=100)
    
    print("[INFO] Entrenamiento completado.")
    
if __name__ == "__main__":
    main()