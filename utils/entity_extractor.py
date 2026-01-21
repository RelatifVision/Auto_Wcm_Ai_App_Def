# utils/entity_extractor.py

import re
from datetime import datetime

def extract_entities_from_text(text: str, doc_type: str) -> list:
    """
    Extrae entidades reales de un texto según el tipo de documento.
    Devuelve una lista de tuplas (start, end, label).
    """
    entities = []
    
    if doc_type == "FACTURA":
        # TIPO_DOCUMENTO
        start = text.find("FACTURA")
        if start != -1:
            end = start + len("FACTURA")
            entities.append((start, end, "TIPO_DOCUMENTO"))
        
        # NUMERO_FACTURA
        num_match = re.search(r'(?:Factura|Nº)[:\s]*([A-Z0-9\-\/]+)', text, re.IGNORECASE)
        if num_match:
            start, end = num_match.span(1)
            entities.append((start, end, "NUMERO_FACTURA"))
        
        # FECHA_EMISION
        fecha_match = re.search(r'(?:Fecha)[:\s]*([\d\/\-\.]+)', text, re.IGNORECASE)
        if fecha_match:
            start, end = fecha_match.span(1)
            entities.append((start, end, "FECHA_EMISION"))
        
        # NOMBRE_CLIENTE
        cliente_match = re.search(r'(?:Cliente|Nombre)[:\s]*([^\n]+)', text, re.IGNORECASE)
        if cliente_match:
            start, end = cliente_match.span(1)
            entities.append((start, end, "NOMBRE_CLIENTE"))
        
        # CIF_CLIENTE
        cif_match = re.search(r'[A-Z]\d{8}[A-Z]', text)
        if cif_match:
            start, end = cif_match.span()
            entities.append((start, end, "CIF_CLIENTE"))
        
        # IMPORTE_TOTAL
        importe_match = re.search(r'(?:Total|Importe\s*Total)[:\s]*€?\s*([\d,\.]+)', text, re.IGNORECASE)
        if importe_match:
            start, end = importe_match.span(1)
            entities.append((start, end, "IMPORTE_TOTAL"))
    
    elif doc_type == "ALTA":
        # TIPO_DOCUMENTO
        start = text.find("ALTA")
        if start != -1:
            end = start + len("ALTA")
            entities.append((start, end, "TIPO_DOCUMENTO"))
        
        # FECHAS_DE_ALTA
        alta_matches = re.findall(r'(\d{2}[\/\-\.]\d{2}[\/\-\.]\d{2,4})', text)
        for match in alta_matches:
            start = text.find(match)
            if start != -1:
                end = start + len(match)
                entities.append((start, end, "FECHAS_DE_ALTA"))
    
    elif doc_type == "LIQUIDACION":
        # TIPO_DOCUMENTO
        start = text.find("Liquidación")
        if start != -1:
            end = start + len("Liquidación")
            entities.append((start, end, "TIPO_DOCUMENTO"))
        
        # PERIODO_LIQUIDACION
        periodo_match = re.search(r'(?:Liquidaci[oó]n\s*de\s*)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{4})', text, re.IGNORECASE)
        if periodo_match:
            start, end = periodo_match.span(0)
            entities.append((start, end, "PERIODO_LIQUIDACION"))
        
        # IMPORTE_BRUTO
        bruto_match = re.search(r'(?:Importe\s*Bruto|Base\s*Imponible)[:\s]*€?\s*([\d,\.]+)', text, re.IGNORECASE)
        if bruto_match:
            start, end = bruto_match.span(1)
            entities.append((start, end, "IMPORTE_BRUTO"))
        
        # IMPORTE_NETO
        neto_match = re.search(r'(?:Importe\s*Neto|Total\s*Neto)[:\s]*€?\s*([\d,\.]+)', text, re.IGNORECASE)
        if neto_match:
            start, end = neto_match.span(1)
            entities.append((start, end, "IMPORTE_NETO"))
        
        # RETENCIONES
        ret_match = re.search(r'(?:Retenci[oó]n|IRPF)[:\s]*€?\s*([\d,\.]+)', text, re.IGNORECASE)
        if ret_match:
            start, end = ret_match.span(1)
            entities.append((start, end, "RETENCIONES"))
    
    elif doc_type == "OTROS":
        # TIPO_DOCUMENTO genérico
        start = text.find("Ticket")
        if start != -1:
            end = start + len("Ticket")
            entities.append((start, end, "TIPO_DOCUMENTO"))
        
        # FECHA_TICKET
        fecha_match = re.search(r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})', text)
        if fecha_match:
            start, end = fecha_match.span()
            entities.append((start, end, "FECHA_TICKET"))
        
        # IMPORTE_TOTAL
        importe_match = re.search(r'(?:Total|Importe)[:\s]*€?\s*([\d,\.]+)', text, re.IGNORECASE)
        if importe_match:
            start, end = importe_match.span(1)
            entities.append((start, end, "IMPORTE_TOTAL"))
    
    return entities
