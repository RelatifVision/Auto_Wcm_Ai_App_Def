# /ia_processor/model/base_model.py
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseModel(ABC):
    
    @abstractmethod
    def predict(self, text: str) -> List[Dict]:
        """Devuelve lista de entidades: [{'text': ..., 'label': ..., 'start': int, 'end': int}]"""
        pass

    @abstractmethod
    def get_info(self) -> dict:
        """Devuelve metadatos del modelo."""
        pass