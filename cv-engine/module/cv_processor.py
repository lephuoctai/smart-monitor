import os
import cv2
import time
import mediapipe as mp

from module.extensions.fall_detection import FallDetectionExt
from module.extensions.sleep_tracking import SleepTrackingExt
from module.extensions.drink_water import DrinkWaterExt
from module.extensions.walk_time import WalkTimeExt

LIVE_IMG_PATH = '/app/evidence/live.jpg'
EVIDENCE_DIR = '/app/evidence/'

# Debug mode: Vẽ các điểm landmark trực tiếp lên ảnh Live để dễ quan sát
DEBUG_DRAW_LIVE_NODES = True

def getTimelog():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class CVProcessor:
    def __init__(self, data_manager):
        self.frame_count = 0
        self.data_manager = data_manager # Nhận module quản lý data từ bên ngoài truyền vào
        
        # Khởi tạo MediaPipe
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.8, min_tracking_confidence=0.8)
        self.mp_draw = mp.solutions.drawing_utils
        
        # Đăng ký các gói Extensions
        self.extensions = [
            FallDetectionExt(),
            SleepTrackingExt(),
            DrinkWaterExt(),
            WalkTimeExt()
        ]

    def clear_live_image(self):
        if os.path.exists(LIVE_IMG_PATH):
            try: os.remove(LIVE_IMG_PATH)
            except Exception: pass

    def process_frame(self, frame):
        self.frame_count += 1
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(img_rgb)

        if DEBUG_DRAW_LIVE_NODES:
            self.mp_draw.draw_landmarks(frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            frame_shape = frame.shape
            
            for ext in self.extensions:
                current_time = time.time()
                metadata = ext.process(landmarks, frame_shape)
                
                if metadata and (current_time - ext.last_triggered > ext.cooldown):
                    ext.last_triggered = current_time
                    
                    # 1. Chụp Bằng Chứng
                    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"{ext.event_name.lower()}_{timestamp_str}.jpg"
                    filepath = os.path.join(EVIDENCE_DIR, filename)
                    
                    self.mp_draw.draw_landmarks(frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                    cv2.imwrite(filepath, frame)
                    
                    # 2. UỶ QUYỀN CHO DATA MANAGER XỬ LÝ LƯU TRỮ
                    desc = metadata.get("description", "Có sự kiện bất thường")
                    self.data_manager.save_event(ext.event_name, desc, filename, metadata)
                        
                    print(f"🚨 [{getTimelog()}] AI_ENGINE: {ext.event_name} -> Đã chuyển cho Data Manager")

        # Xuất ảnh Live
        if self.frame_count % 2 == 0:
            cv2.imwrite(LIVE_IMG_PATH, frame)