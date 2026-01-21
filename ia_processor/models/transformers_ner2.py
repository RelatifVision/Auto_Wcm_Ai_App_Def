# ia_processor/models/transformers_ner.py
from transformers import pipeline
from .base_model import BaseModel

class TransformersNERModel(BaseModel):
    def __init__(self, model_name: str = "PlanTL-GOB-ES/roberta-base-bne-finetuned-ner"):
        self.model_name = model_name
        self.nlp = pipeline(
            "ner",
            model=model_name,
            tokenizer=model_name,
            aggregation_strategy="simple"
        )
        print(f"[INFO] Cargado modelo Hugging Face: {model_name}")

    def predict(self, text: str) -> list:
        results = self.nlp(text)
        entities = []
        for ent in results:
            # Convertir a formato compatible
            entities.append({
                "text": ent["word"],
                "label": ent["entity_group"],  # PER, ORG, LOC, MISC
                "start": ent["start"],
                "end": ent["end"]
            })
        return entities

    def get_info(self) -> dict:
        return {"name": self.model_name, "type": "Hugging Face", "source": "transformers"}
