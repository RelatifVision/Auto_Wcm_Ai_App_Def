import sys
import spacy
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
import os

def check_internet_connection():
    """Verificación más robusta de conexión a Internet"""
    try:
        import socket
        # Prueba con múltiples servidores y métodos
        test_hosts = [
            ("8.8.8.8", 53),      # Google DNS
            ("1.1.1.1", 53),      # Cloudflare DNS
            ("httpbin.org", 80),   # Servicio de prueba HTTP
        ]
        
        for host, port in test_hosts:
            try:
                socket.setdefaulttimeout(3)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    print(f"[INFO] Conexión exitosa a internet")
                    return True
            except Exception:
                continue
                
        print("[INFO] No se pudo establecer conexión a ningún servidor de prueba")
        return False
        
    except Exception as e:
        print(f"[ERROR] Error en verificación de conexión: {e}")
        return False

def main():
    print("Iniciando la aplicación...")  
    app = QApplication(sys.argv)
    # Verificar conexión antes de crear la ventana principal
    has_internet = check_internet_connection()
    # Crear la ventana principal pasando el estado de conexión
    window = MainWindow(has_internet=has_internet)
    # Mostrar mensaje de advertencia solo si no hay conexión
    if not has_internet:
        from utils.common_functions import show_warning_dialog
        show_warning_dialog(window, "Conexión Limitada", "No hay conexión a Internet. Algunas funciones estarán limitadas.")
    
    window.show()  # Mostrar la ventana
    sys.exit(app.exec())  

if __name__ == "__main__":
    main()