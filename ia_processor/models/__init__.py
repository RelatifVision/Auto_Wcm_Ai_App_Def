# ia_processor/models/__init__.py
from .spacy_model import SpacyModel
from .transformers_ner import TransformersNERModel
from .base_model import BaseModel

def get_model(model_key: str):
    if model_key == "custom":
        return SpacyModel("spacy_custom")
    elif model_key == "lg":
        return SpacyModel("es_core_news_lg")
    elif model_key == "plan_tl":
        return TransformersNERModel("PlanTL-GOB-ES/roberta-base-bne-finetuned-ner")
    elif model_key == "bert_spanish":
        return TransformersNERModel("mrm8488/bert-spanish-cased-finetuned-ner")
    else:
        raise ValueError(f"Modelo no soportado: {model_key}")
