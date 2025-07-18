import sys
import cv2
import datetime
import os
import json
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QComboBox,
                               QMenuBar, QMenu, QStatusBar, QGroupBox, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction

from src.core.video_thread import VideoThread
from src.core.detection_engine import DetectionEngine
from src.ui.video_widget import VideoWidget
from src.ui.dialogs import (CameraSettingsDialog, DetectionSettingsDialog, 
                           SocketSetupDialog, PalletSetupDialog, DefectsWindow)
from src.utils.database_manager import DatabaseManager
from src.utils.camera_manager import CameraManager
from src.utils.template_manager import TemplateManager

class VideoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Misaligned Boards Application")
        self.setGeometry(100, 100, 1600, 900)
        
        self.video_thread = None
        self.camera_index = None
        self.defects = []
        self.defects_window = None
        
        self.detection_engine = DetectionEngine()
        self.database_manager = DatabaseManager()
        self.camera_manager = CameraManager()
        self.template_manager = TemplateManager()
        
        self.camera_settings = {
            'exposure': -4,
            'gain': 0,
            'fps': 30,
            'resolution': (1280, 720),
            'global_shutter': True
        }
        
        self.board_count = 0
        self.pallet_count = 0
        self.last_signal_time = time.time()
        self.low_signal_duration = 1.0
        self.target_board_count = 5
        
        self.setup_ui()
        self.setup_menu()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        toolbar = QWidget()
        toolbar.setFixedWidth(200)
        toolbar_layout = QVBoxLayout(toolbar)
        
        roi_group = QGroupBox("ROI Tools")
        roi_layout = QVBoxLayout()
        
        self.btn_select_roi = QPushButton("Select ROI")
        self.btn_select_roi.clicked.connect(self.enable_roi_selection)
        roi_layout.addWidget(self.btn_select_roi)
        
        self.btn_clear_roi = QPushButton("Clear ROI")
        self.btn_clear_roi.clicked.connect(self.clear_roi_selection)
        roi_layout.addWidget(self.btn_clear_roi)
        
        self.btn_toggle_roi = QPushButton("Hide ROI")
        self.btn_toggle_roi.clicked.connect(self.toggle_roi_visibility)
        roi_layout.addWidget(self.btn_toggle_roi)
        
        roi_group.setLayout(roi_layout)
        toolbar_layout.addWidget(roi_group)
        
        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout()
        
        self.btn_save_frame = QPushButton("Save Frame")
        self.btn_save_frame.clicked.connect(self.save_current_frame)
        tools_layout.addWidget(self.btn_save_frame)
        
        self.btn_toggle_grid = QPushButton("Toggle Grid")
        self.btn_toggle_grid.clicked.connect(self.toggle_grid)
        tools_layout.addWidget(self.btn_toggle_grid)
        
        tools_group.setLayout(tools_layout)
        toolbar_layout.addWidget(tools_group)
        
        counters_group = QGroupBox("Counters")
        counters_layout = QVBoxLayout()
        
        self.board_count_label = QLabel("Board Count: 0")
        counters_layout.addWidget(self.board_count_label)
        
        self.pallet_count_label = QLabel("Pallet Count: 0")
        counters_layout.addWidget(self.pallet_count_label)
        
        counters_group.setLayout(counters_layout)
        toolbar_layout.addWidget(counters_group)
        
        template_group = QGroupBox("Templates")
        template_layout = QVBoxLayout()
        
        self.template_combo = QComboBox()
        self.template_manager.update_template_combo(self.template_combo)
        template_layout.addWidget(self.template_combo)
        
        template_group.setLayout(template_layout)
        toolbar_layout.addWidget(template_group)
        
        toolbar_layout.addStretch()
        main_layout.addWidget(toolbar)
        
        self.video_widget = VideoWidget()
        self.video_widget.roi_selected_signal.connect(self.on_roi_selected)
        main_layout.addWidget(self.video_widget)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def setup_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("File")
        
        select_video_action = QAction("Select Video", self)
        select_video_action.triggered.connect(self.select_video)
        file_menu.addAction(select_video_action)
        
        select_camera_action = QAction("Select Camera", self)
        select_camera_action.triggered.connect(self.select_camera)
        file_menu.addAction(select_camera_action)
        
        upload_image_action = QAction("Upload Image", self)
        upload_image_action.triggered.connect(self.upload_image)
        file_menu.addAction(upload_image_action)
        
        file_menu.addSeparator()
        
        pallet_manager_action = QAction("Pallet Manager", self)
        pallet_manager_action.triggered.connect(self.open_pallet_setup)
        file_menu.addAction(pallet_manager_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        settings_menu = menubar.addMenu("Settings")
        
        camera_settings_action = QAction("Camera Settings", self)
        camera_settings_action.triggered.connect(self.open_camera_settings)
        settings_menu.addAction(camera_settings_action)
        
        detection_settings_action = QAction("Detection Settings", self)
        detection_settings_action.triggered.connect(self.open_detection_settings)
        settings_menu.addAction(detection_settings_action)
        
        view_menu = menubar.addMenu("View")
        
        view_defects_action = QAction("View Defects", self)
        view_defects_action.triggered.connect(self.open_defects_window)
        view_menu.addAction(view_defects_action)
        
        sensor_menu = menubar.addMenu("Sensor")
        
        setup_socket_action = QAction("Setup Socket", self)
        setup_socket_action.triggered.connect(self.open_socket_setup)
        sensor_menu.addAction(setup_socket_action)
        
        pallet_menu = menubar.addMenu("Pallet")
        
        setup_pallet_action = QAction("Setup Pallet Detection", self)
        setup_pallet_action.triggered.connect(self.open_pallet_setup)
        pallet_menu.addAction(setup_pallet_action)
        
    def select_video(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            try:
                if self.video_thread is not None:
                    self.video_thread.stop()
                    self.video_thread.wait()
                
                self.video_thread = VideoThread()
                self.video_thread.set_video_file(file_path)
                self.video_thread.frame_ready.connect(self.process_frame)
                self.video_thread.error_occurred.connect(self.handle_camera_error)
                self.video_thread.start()
                
                self.status_bar.showMessage(f"Playing video: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Video Error", f"Error opening video: {str(e)}")
                
    def select_camera(self):
        camera_index = self.camera_manager.select_camera_dialog(self)
        if camera_index is not None:
            self.start_camera(camera_index)
            
    def start_camera(self, camera_index):
        try:
            if self.video_thread is not None:
                self.video_thread.stop()
                self.video_thread.wait()
                
            self.video_thread = VideoThread(camera_index)
            self.video_thread.set_camera_settings(self.camera_settings)
            self.video_thread.frame_ready.connect(self.process_frame)
            self.video_thread.error_occurred.connect(self.handle_camera_error)
            self.video_thread.start()
            
            self.camera_index = camera_index
            self.status_bar.showMessage(f"Connected to Camera {camera_index}")
            
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Camera Error", f"Error starting camera: {str(e)}")
            
    def process_frame(self, frame):
        if self.video_widget.roi_selected and self.video_widget.roi_start and self.video_widget.roi_end:
            x1, y1 = self.video_widget.roi_start.x(), self.video_widget.roi_start.y()
            x2, y2 = self.video_widget.roi_end.x(), self.video_widget.roi_end.y()
            
            x1 = max(0, min(x1, frame.shape[1]))
            y1 = max(0, min(y1, frame.shape[0]))
            x2 = max(0, min(x2, frame.shape[1]))
            y2 = max(0, min(y2, frame.shape[0]))
            
            if x1 < x2 and y1 < y2:
                roi = frame[y1:y2, x1:x2]
                processed_roi, defects = self.detection_engine.detect_and_draw_lines_with_angles(roi)
                frame[y1:y2, x1:x2] = processed_roi
                
                for defect in defects:
                    self.database_manager.log_fault(
                        fault_type="Board Alignment",
                        image_index=1,
                        details=defect['details'],
                        measurement=defect['angle']
                    )
                    self.defects.append((defect['timestamp'], defect['angle'], defect['image_path']))
                    
                    if self.defects_window is not None:
                        self.defects_window.update_defects(self.defects)
                
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.video_widget.set_frame(frame_rgb)
        
    def handle_camera_error(self, error_message):
        self.status_bar.showMessage(error_message)
        
    def enable_roi_selection(self):
        self.video_widget.selecting_roi = True
        self.video_widget.roi_start = None
        self.video_widget.roi_end = None
        self.video_widget.roi_selected = False
        self.status_bar.showMessage("Click and drag to select ROI")
        self.btn_select_roi.setText("ROI Selection Active")
        self.btn_select_roi.setStyleSheet("background-color: yellow;")
        
    def clear_roi_selection(self):
        self.video_widget.clear_roi()
        self.status_bar.showMessage("ROI cleared")
        
    def on_roi_selected(self):
        self.btn_select_roi.setText("Select ROI")
        self.btn_select_roi.setStyleSheet("")
        self.status_bar.showMessage("ROI selected")
        
    def toggle_roi_visibility(self):
        self.video_widget.toggle_roi_visibility()
        if self.video_widget.roi_visible:
            self.btn_toggle_roi.setText("Hide ROI")
        else:
            self.btn_toggle_roi.setText("Show ROI")
            
    def save_current_frame(self):
        if self.video_widget.current_frame is not None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"frame_{timestamp}.png"
            frame_bgr = cv2.cvtColor(self.video_widget.current_frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename, frame_bgr)
            self.status_bar.showMessage(f"Frame saved as {filename}")
            
    def toggle_grid(self):
        self.status_bar.showMessage("Grid toggle - not implemented")
        
    def upload_image(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_path:
            image = cv2.imread(file_path)
            if image is not None:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.video_widget.set_frame(image_rgb)
                self.status_bar.showMessage(f"Image loaded: {file_path}")
                
    def open_camera_settings(self):
        dialog = CameraSettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            resolution_str = dialog.resolution_combo.currentText()
            width, height = map(int, resolution_str.split('x'))
            self.camera_settings['resolution'] = (width, height)
            self.camera_settings['exposure'] = dialog.exposure_slider.value()
            self.camera_settings['gain'] = dialog.gain_slider.value()
            self.camera_settings['fps'] = dialog.fps_slider.value()
            self.camera_settings['global_shutter'] = not dialog.auto_exposure_check.isChecked()
            
            if self.video_thread is not None:
                self.video_thread.set_camera_settings(self.camera_settings)
                
    def open_detection_settings(self):
        dialog = DetectionSettingsDialog(self)
        dialog.standard_angle_spin.setValue(self.detection_engine.standard_angle)
        dialog.tolerance_spin.setValue(self.detection_engine.tolerance)
        dialog.min_defect_angle_spin.setValue(self.detection_engine.min_defect_angle)
        dialog.max_defect_angle_spin.setValue(self.detection_engine.max_defect_angle)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.detection_engine.set_detection_settings(
                dialog.standard_angle_spin.value(),
                dialog.tolerance_spin.value(),
                dialog.min_defect_angle_spin.value(),
                dialog.max_defect_angle_spin.value()
            )
            
    def open_socket_setup(self):
        dialog = SocketSetupDialog(self)
        dialog.exec()
        
    def open_pallet_setup(self):
        dialog = PalletSetupDialog(self)
        dialog.low_signal_duration_spin.setValue(self.low_signal_duration)
        dialog.target_board_count_spin.setValue(self.target_board_count)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.low_signal_duration = dialog.low_signal_duration_spin.value()
            self.target_board_count = dialog.target_board_count_spin.value()
            
    def open_defects_window(self):
        if self.defects_window is None or not self.defects_window.isVisible():
            self.defects_window = DefectsWindow(self)
            self.defects_window.update_defects(self.defects)
        self.defects_window.show()
        self.defects_window.raise_()
        
    def closeEvent(self, event):
        if self.video_thread is not None:
            self.video_thread.stop()
            self.video_thread.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = VideoApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 