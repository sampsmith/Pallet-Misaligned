import cv2
import numpy as np
import datetime
import os
import sqlite3

class DetectionEngine:
    def __init__(self):
        self.standard_angle = 90
        self.tolerance = 5
        self.min_defect_angle = 80
        self.max_defect_angle = 100
        
    def set_detection_settings(self, standard_angle, tolerance, min_defect_angle, max_defect_angle):
        self.standard_angle = standard_angle
        self.tolerance = tolerance
        self.min_defect_angle = min_defect_angle
        self.max_defect_angle = max_defect_angle
        
    def detect_and_draw_lines_with_angles(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)

        defects = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                if angle > 90:
                    angle = 180 - angle
                
                if abs(angle - self.standard_angle) > self.tolerance:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    image_path = self.save_defect_frame(frame.copy(), timestamp)
                    
                    defect_info = {
                        'timestamp': timestamp,
                        'angle': angle,
                        'image_path': image_path,
                        'details': f"Board angle {angle:.1f}° deviates from standard {self.standard_angle}° by {abs(angle - self.standard_angle):.1f}°"
                    }
                    defects.append(defect_info)

        return frame, defects
        
    def save_defect_frame(self, frame, timestamp):
        if not os.path.exists("defect_images"):
            os.makedirs("defect_images")

        filename = f"defect_images/defect_{timestamp.replace(':', '-')}.png"
        cv2.imwrite(filename, frame)
        return filename
        
    def log_fault_to_database(self, fault_type, image_index, details, measurement=None):
        conn = sqlite3.connect('faults.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO faults (timestamp, fault_type, image_index, details, measurement)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
              fault_type, image_index, details, measurement))
        conn.commit()
        conn.close() 