# utils/offline_utils.py
import os
import json
from datetime import datetime

def save_offline_data(data, filename):
    """Guardar datos localmente para modo offline"""
    try:
        if not os.path.exists("data"):
            os.makedirs("data")
        
        filepath = os.path.join("data", filename)
        with open(filepath, "w") as f:
            json.dump(data, f, default=str, indent=2)
        print(f"[INFO] Datos guardados en {filename}")
        return True
    except Exception as e:
        print(f"[ERROR] Error guardando datos offline: {e}")
        return False

def load_offline_data(filename):
    """Cargar datos localmente"""
    try:
        filepath = os.path.join("data", filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"[ERROR] Error cargando datos offline: {e}")
        return None

def queue_offline_action(action_type, data):
    """Agregar acción a cola offline"""
    queue_data = load_offline_data("offline_queue.json") or []
    queue_data.append({
        "type": action_type,
        "timestamp": datetime.now().isoformat(),
        "data": data
    })
    save_offline_data(queue_data, "offline_queue.json")
    print(f"[INFO] Acción {action_type} añadida a cola offline")
