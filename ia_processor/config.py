# ia_processor/config.py
from pathlib import Path


# ia_processor.extraction.extract_entities_from_pdfs
# ia_processor.generate_training_data
# ia_processor.training.train_ner_model
# ia_processor.evaluation.evaluate_model

# --- Directorios base ---
BASE_DIR = Path(__file__).resolve().parent.parent  # raíz del proyecto
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdf"
IMAGES_DIR = DATA_DIR / "imagenes"


# --- Directorios de procesamiento ---
IA_PROCESSOR_DIR = BASE_DIR / "ia_processor"
TRAINING_DIR = IA_PROCESSOR_DIR / "training"
OUTPUT_DIR = IA_PROCESSOR_DIR / "output"
CLASSIFIED_DIR = OUTPUT_DIR / "classified"
RESULTS_DIR = IA_PROCESSOR_DIR / "results"
FACTURA_DIR = PDF_DIR / "FACTURA" 
FACTURA_OUT_DIR = OUTPUT_DIR / "FACTURA"
#
ENTITIES_OUT_DIR = OUTPUT_DIR / "ENTIDADES"
EVALUATION_OUT_DIR = OUTPUT_DIR / "EVALUACIONES"
# --- Modelos ---
MODELS_DIR = IA_PROCESSOR_DIR / "models"
MODEL_PATH = MODELS_DIR / "spacy_model"  # ruta al modelo entrenado
MODEL_OUTPUT_DIR = MODEL_PATH  # alias para compatibilidad

# --- Archivos de datos ---
TRAINING_DATA_FILE = TRAINING_DIR / "training_data.json"

# RESULTS_FILE = OUTPUT_DIR / "entidades_reconocidas.json"

# --- Crear carpetas críticas si no existen ---
OUTPUT_DIR.mkdir(exist_ok=True)
CLASSIFIED_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)