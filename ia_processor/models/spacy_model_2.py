# /ia_processor/model/spacy_model.py
from pathlib import Path
import spacy
from .base_model import BaseModel
from ia_processor.config import MODEL_PATH

class SpacyModel(BaseModel):
    def __init__(self, model_name_or_path: str):
        self.model_name_or_path = model_name_or_path
        if model_name_or_path == "spacy_custom":
            self.model_path = MODEL_PATH
        else:
            self.model_path = model_name_or_path  # ej. "es_core_news_lg"
        self.nlp = spacy.load(str(self.model_path))
        print(f"[INFO] Cargado modelo spaCy: {model_name_or_path}")

    def predict(self, text: str) -> list:
        doc = self.nlp(text)
        return [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            }
            for ent in doc.ents
        ]

    def get_info(self) -> dict:
        name = "Modelo Personalizado" if self.model_name_or_path == "spacy_custom" else self.model_name_or_path
        return {"name": name, "type": "spaCy", "path": str(self.model_path)}
