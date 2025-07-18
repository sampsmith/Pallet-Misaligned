import cv2
import platform
from PySide6.QtWidgets import QInputDialog, QMessageBox

class CameraManager:
    def __init__(self):
        self.is_linux = platform.system() == 'Linux'
        
    def list_available_cameras(self):
        available_cameras = []
        try:
            for i in range(2):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    name = f"Camera {i}"
                    path = str(i)
                    available_cameras.append((path, name))
                    print(f"Found camera: {name} at index {i}")
                    cap.release()
        except Exception as e:
            print(f"Error listing cameras: {str(e)}")
        
        return available_cameras
        
    def select_camera_dialog(self, parent):
        available_cameras = self.list_available_cameras()
        if available_cameras:
            camera_index, ok = QInputDialog.getItem(parent, "Select Camera", 
                                                  "Choose a camera:", 
                                                  [f"Camera {i}" for i in range(len(available_cameras))], 
                                                  0, False)
            if ok:
                try:
                    camera_num = int(camera_index.split()[-1])
                    return camera_num
                except ValueError:
                    QMessageBox.warning(parent, "Error", "Invalid camera selection")
                    return None
        else:
            QMessageBox.warning(parent, "No Cameras", "No cameras found")
            return None
            
    def get_camera_info(self, camera_index):
        try:
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                cap.release()
                return {
                    'width': width,
                    'height': height,
                    'fps': fps,
                    'index': camera_index
                }
        except Exception as e:
            print(f"Error getting camera info: {str(e)}")
        return None 