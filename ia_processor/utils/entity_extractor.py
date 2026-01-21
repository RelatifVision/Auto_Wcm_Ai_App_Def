# ia_processor/utils/entity_extractor.py
import re

def extract_entities_from_text(text: str, doc_type: str) -> list:
    entities = []
    if doc_type == "FACTURA":
        # NUMERO_FACTURA: "FACTURA: 182454"
        for match in re.finditer(r'FACTURA[:\s]*(\d+|[A-Z0-9\-\/]+)', text, re.IGNORECASE):
            entities.append((match.start(1), match.end(1), "NUMERO_FACTURA"))
        # FECHA_EMISION: "Fecha: 31/12/2024"
        for match in re.finditer(r'Fecha[:\s]*([\d\/\-\.]+)', text, re.IGNORECASE):
            entities.append((match.start(1), match.end(1), "FECHA_EMISION"))
        # IMPORTE_TOTAL: "TOTAL Euros2.116,66"
        for match in re.finditer(r'(?:TOTAL|Total)[:\s]*€?\s*([\d,\.]+)', text, re.IGNORECASE):
            entities.append((match.start(1), match.end(1), "IMPORTE_TOTAL"))
        # EMAIL
        for match in re.finditer(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            entities.append((match.start(), match.end(), "EMAIL"))
    elif doc_type == "LIQUIDACION":
        # PERIODO_LIQUIDACION: "enero 2025"
        for match in re.finditer(r'(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{4})', text, re.IGNORECASE):
            entities.append((match.start(), match.end(), "PERIODO_LIQUIDACION"))
        # IMPORTE_BRUTO
        for match in re.finditer(r'(?:Bruto|Base\s*Imponible)[:\s]*€?\s*([\d,\.]+)', text, re.IGNORECASE):
            entities.append((match.start(1), match.end(1), "IMPORTE_BRUTO"))
        # IMPORTE_NETO
        for match in re.finditer(r'(?:Neto|Total\s*Neto)[:\s]*€?\s*([\d,\.]+)', text, re.IGNORECASE):
            entities.append((match.start(1), match.end(1), "IMPORTE_NETO"))
        # RETENCIONES
        for match in re.finditer(r'(?:Retenci[oó]n|IRPF)[:\s]*€?\s*([\d,\.]+)', text, re.IGNORECASE):
            entities.append((match.start(1), match.end(1), "RETENCIONES"))
    return entities
