import cv2
import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PySide6.QtCore import QRect

class VideoWidget(QWidget):
    roi_selected_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1280, 720)
        self.roi_start = None
        self.roi_end = None
        self.roi_selected = False
        self.selecting_roi = False
        self.dragging_corner = None
        self.roi_visible = True
        self.current_frame = None
        
    def set_frame(self, frame):
        self.current_frame = frame
        self.update()
        
    def paintEvent(self, event):
        if self.current_frame is not None:
            painter = QPainter(self)
            
            height, width, channel = self.current_frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(self.current_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(0, 0, scaled_pixmap)
            
            if self.roi_visible and self.roi_start and self.roi_end:
                pen = QPen(QColor(0, 255, 0), 2)
                painter.setPen(pen)
                painter.drawRect(QRect(self.roi_start, self.roi_end))
                
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.selecting_roi:
                self.roi_start = event.pos()
                self.roi_end = event.pos()
                self.roi_selected = False
            elif self.roi_selected:
                if self.is_near_corner(event.pos(), self.roi_start):
                    self.dragging_corner = 'start'
                elif self.is_near_corner(event.pos(), self.roi_end):
                    self.dragging_corner = 'end'
                    
    def mouseMoveEvent(self, event):
        if self.selecting_roi:
            self.roi_end = event.pos()
            self.update()
        elif self.dragging_corner:
            if self.dragging_corner == 'start':
                self.roi_start = event.pos()
            elif self.dragging_corner == 'end':
                self.roi_end = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.selecting_roi:
            self.roi_end = event.pos()
            self.roi_selected = True
            self.selecting_roi = False
            if hasattr(self, 'roi_selected_signal'):
                self.roi_selected_signal.emit()
        self.dragging_corner = None
        
    def is_near_corner(self, pos, corner):
        if corner is None:
            return False
        return abs(pos.x() - corner.x()) < 10 and abs(pos.y() - corner.y()) < 10
        
    def clear_roi(self):
        self.roi_start = None
        self.roi_end = None
        self.roi_selected = False
        self.update()
        
    def toggle_roi_visibility(self):
        self.roi_visible = not self.roi_visible
        self.update() 