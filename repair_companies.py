# repair_companies.py

from calendar_api_setting.calendar_api import get_events, edit_event_api
from utils.company_utils import get_company_name, get_company_color
from utils.business_manager import BusinessManager
import re

# Mapeo de nombres incorrectos a correctos
COMPANY_CORRECTIONS = {
    r'(?i)^crambo\s+rental$': 'CRAMBO ALQUILER S.L.',
    r'(?i)^madworks$': 'MADWORKS',
    r'(?i)^last\s+lap\s*sl$': 'LAST LAP S.L.',
    r'(?i)^last\s+lap\s*s\.l\.$': 'LAST LAP S.L.',
    r'(?i)^last\s+lap$': 'LAST LAP S.L.',
}

def normalize_company_name(company_name):
    """Normaliza el nombre de la empresa según las reglas de corrección."""
    if not company_name:
        return company_name
    for pattern, corrected in COMPANY_CORRECTIONS.items():
        if re.match(pattern, company_name.strip()):
            return corrected
    return company_name

def repair_company_names_in_calendar():
    """Repara los nombres de empresa en todos los eventos del calendario."""
    events = get_events()
    count_repaired = 0

    for event in events:
        original_company = get_company_name(event)
        if not original_company:
            continue

        corrected_company = normalize_company_name(original_company)
        if corrected_company != original_company:

            # Obtener datos actuales del evento
            summary = event.get('summary', '')
            description = event.get('description', '')
            location = event.get('location', '')
            start = event['start']
            end = event['end']
            color_hex = get_company_color(corrected_company) or "#333333"

            # ⭐️ Actualizar la descripción si contiene el nombre de la empresa
            # Asumimos que la descripción tiene formato: "{tarifa}€ {empresa}"
            if description and '€' in description:
                parts = description.split('€', 1)
                if len(parts) == 2:
                    rate = parts[0].strip()
                    old_company_in_desc = parts[1].strip()
                    # Reemplazar solo si coincide con el nombre original
                    if old_company_in_desc.lower() == original_company.lower():
                        new_description = f"{rate}€ {corrected_company}"
                    else:
                        new_description = description  # No tocar si no coincide
                else:
                    new_description = description
            else:
                new_description = description

            new_event_data = {
                "summary": summary,
                "location": location,
                "description": new_description,  # 👈 Actualizado
                "start": start,
                "end": end,
                "transparency": "opaque",
                "company": corrected_company,  # Actualizar campo personalizado
                "task": get_task(event),       # Mantener tarea
                "color": color_hex             # Actualizar color según nueva empresa
            }

            try:
                edit_event_api(event['id'], new_event_data)
                count_repaired += 1
                print(f"✅ Evento {event['id']} actualizado.")
            except Exception as e:
                print(f"❌ Error al editar evento {event['id']}: {e}")

    print(f"\n🎉 Reparación completada. Se corrigieron {count_repaired} eventos.")

def get_task(event):
    """Obtener la tarea desde extendedProperties."""
    return event.get('extendedProperties', {}).get('private', {}).get('task', 'Sin tarea')

if __name__ == "__main__":
    repair_company_names_in_calendar()