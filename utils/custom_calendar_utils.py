from PyQt6.QtWidgets import QCalendarWidget, QStyleOption, QStyle
from PyQt6.QtGui import QPainter, QColor, QFont, QTextCharFormat
from PyQt6.QtCore import QDate, Qt
from utils.company_utils import get_company_color
from models.chat_parser import check_availability
from datetime import datetime, timedelta


class CustomCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._events_by_date = {}
        self.today = QDate.currentDate()  # Resaltar el día actual
        self.setGridVisible(True)  # Mostrar cuadrícula
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)  
        self.selectionChanged.connect(self.update)  # Forzar repintado al cambiar selección

    def set_events_by_date(self, events_by_date):
        self._events_by_date = events_by_date
        self.update()  # Forzar repintado

    def paintCell(self, painter, rect, date):
        painter.save()
        
        # Dibujar colores de eventos primero (fondo completo)
        if date in self._events_by_date:
            events = self._events_by_date[date]
            num_events = len(events)
            chunk_height = rect.height() // num_events
            
            for i, event in enumerate(events):
                color_hex = get_company_color(event["company"]) or "#333333"
                color = QColor(color_hex)
                
                # Aumentar brillo si está seleccionado
                if date == self.selectedDate():
                    color = color.lighter(150)  # Brillo +50% 
                
                y = rect.y() + i * chunk_height
                painter.fillRect(
                    rect.x(),
                    y,
                    rect.width(),
                    chunk_height,
                    color
                )
        else:
            # Fondo gris oscuro si no hay eventos
            painter.fillRect(rect, QColor("#333333"))
        
        # Llamar al pintado original para mantener texto y cuadrícula
        super().paintCell(painter, rect, date)  # ¡Clave para conservar estilo!
        
        # Resaltar el día actual
        if date == self.today:
            today_format = QTextCharFormat()
            today_format.setBackground(QColor("#465068"))
            today_format.setForeground(QColor("black"))
            self.setDateTextFormat(date, today_format)
        
        painter.restore()
        
    def show_availability(self):
        selected_qdate = self.calendar.selectedDate()
        selected_date = datetime(
            selected_qdate.year(), 
            selected_qdate.month(), 
            selected_qdate.day()
        ).date()
        
        # Verificar disponibilidad (9:00-17:00)
        start = datetime.combine(selected_date, datetime.min.time())
        end = start + timedelta(days=1)
        
        if check_availability(start, end, self):
            self.availability_result.setText(f"Disponible el {selected_date.strftime('%d/%m/%Y')}")
        else:
            self.availability_result.setText("No hay disponibilidad en ese horario.")
            
    def highlight_availability(self, date):
        start_dt = datetime(date.year(), date.month(), date.day())
        end_dt = start_dt + timedelta(days=1)
        
        if check_availability(start_dt, end_dt, self.parent()):
            color = QColor("#4CAF50")
        else:
            color = QColor("#FF5722")
        
        format = QTextCharFormat()
        format.setBackground(color)
        self.setDateTextFormat(date, format)
