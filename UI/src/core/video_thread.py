import cv2
import numpy as np
import time
from PySide6.QtCore import QThread, Signal

class VideoThread(QThread):
    frame_ready = Signal(np.ndarray)
    error_occurred = Signal(str)
    
    def __init__(self, camera_index=None):
        super().__init__()
        self.camera_index = camera_index
        self.video_file = None
        self.cap = None
        self.running = False
        self.camera_settings = {
            'exposure': -4,
            'gain': 0,
            'fps': 30,
            'resolution': (1280, 720),
            'global_shutter': True
        }
        
    def set_camera_settings(self, settings):
        self.camera_settings = settings
        
    def set_video_file(self, file_path):
        self.video_file = file_path
        self.camera_index = None
        
    def run(self):
        if self.camera_index is None and self.video_file is None:
            return
            
        try:
            if self.video_file is not None:
                self.cap = cv2.VideoCapture(self.video_file)
                if not self.cap.isOpened():
                    raise Exception("Failed to open video file")
            elif self.camera_index is not None:
                self.cap = cv2.VideoCapture(int(self.camera_index))
                if not self.cap.isOpened():
                    raise Exception("Failed to open camera")
                
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_settings['resolution'][0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_settings['resolution'][1])
                self.cap.set(cv2.CAP_PROP_FPS, self.camera_settings['fps'])
                
                if self.camera_settings['global_shutter']:
                    self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
                    self.cap.set(cv2.CAP_PROP_EXPOSURE, self.camera_settings['exposure'])
                else:
                    self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
                    
                self.cap.set(cv2.CAP_PROP_GAIN, self.camera_settings['gain'])
            
            self.running = True
            consecutive_failures = 0
            max_failures = 5
            
            while self.running:
                try:
                    ret, frame = self.cap.read()
                    if ret:
                        consecutive_failures = 0
                        frame = cv2.resize(frame, (1280, 720))
                        self.frame_ready.emit(frame)
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_failures:
                            raise Exception("Failed to read frame multiple times")
                            
                except Exception as e:
                    print(f"Error in video processing: {str(e)}")
                    self.error_occurred.emit("Connection lost. Attempting to reconnect...")
                    
                    try:
                        if self.cap is not None:
                            self.cap.release()
                        time.sleep(1)
                        
                        if self.video_file is not None:
                            self.cap = cv2.VideoCapture(self.video_file)
                        elif self.camera_index is not None:
                            self.cap = cv2.VideoCapture(int(self.camera_index))
                            
                        if not self.cap.isOpened():
                            raise Exception("Failed to reconnect")
                            
                        if self.camera_index is not None:
                            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_settings['resolution'][0])
                            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_settings['resolution'][1])
                            self.cap.set(cv2.CAP_PROP_FPS, self.camera_settings['fps'])
                            
                            if self.camera_settings['global_shutter']:
                                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
                                self.cap.set(cv2.CAP_PROP_EXPOSURE, self.camera_settings['exposure'])
                            else:
                                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
                                
                            self.cap.set(cv2.CAP_PROP_GAIN, self.camera_settings['gain'])
                        
                        self.error_occurred.emit("Reconnected successfully")
                        consecutive_failures = 0
                    except Exception as reconnect_error:
                        print(f"Failed to reconnect: {str(reconnect_error)}")
                        self.error_occurred.emit("Failed to reconnect")
                        break
                        
                time.sleep(0.01)
                
        except Exception as e:
            self.error_occurred.emit(f"Error starting: {str(e)}")
            
    def stop(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
        self.wait() 