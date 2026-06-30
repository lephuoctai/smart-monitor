# module/cv_processor.py
import os
import cv2
import time
import json
import pymongo
from datetime import datetime, timezone
import mediapipe as mp

# Nạp các gói Extension
from module.extensions.fall_detection import FallDetectionExt
from module.extensions.sleep_tracking import SleepTrackingExt
from module.extensions.drink_water import DrinkWaterExt
from module.extensions.walk_time import WalkTimeExt

LIVE_IMG_PATH = '/app/evidence/live.jpg'
HISTORY_JSON_PATH = '/app/evidence/history.json'
EVIDENCE_DIR = '/app/evidence/'

def getTimelog():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class CVProcessor:
    def __init__(self):
        self.frame_count = 0
        
        # 1. Khởi tạo MediaPipe
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.8, min_tracking_confidence=0.8)
        self.mp_draw = mp.solutions.drawing_utils
        
        # 2. Đăng ký các gói Extensions
        self.extensions = [
            FallDetectionExt(),
            SleepTrackingExt(),
            DrinkWaterExt(),
            WalkTimeExt()
        ]
        
        # 3. Bộ đếm tĩnh để nuôi giao diện Dashboard (Raw Data)
        self.session_stats = {
            "FALL_DETECTED": 0,
            "RESTLESS_SLEEP": 0,
            "DRINK_WATER": 0,
            "WALKING_DETECTED": 0
        }
        
        # 4. Kết nối MongoDB
        try:
            self.mongo_client = pymongo.MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=2000)
            self.mongo_client.admin.command('ping')
            self.db = self.mongo_client["monitor_db"]
            self.events_collection = self.db["patient_events"]
            print(f"✅ [{getTimelog()}] KẾT NỐI MONGODB THÀNH CÔNG!")
        except Exception as e:
            print(f"⚠️ [{getTimelog()}] LỖI MONGODB: Hệ thống sẽ chỉ ghi log JSON. Chi tiết: {e}")
            self.events_collection = None

    def clear_live_image(self):
        if os.path.exists(LIVE_IMG_PATH):
            try: os.remove(LIVE_IMG_PATH)
            except Exception: pass

    def _sync_to_nginx_ui(self, event_name, desc, filename, metadata):
        """Ghi JSON chứa Raw Data và Stats cho giao diện Web"""
        
        # Cập nhật số đếm thống kê
        if event_name in self.session_stats:
            self.session_stats[event_name] += 1
            
        # Tạo bản ghi log mới
        alert_data = {
            "time": time.strftime("%H:%M:%S", time.localtime()),
            "tag": event_name,
            "desc": desc,
            "image": filename,
            "metadata": metadata # Đổ trực tiếp Raw Data từ AI vào đây
        }
        
        # Cấu trúc Wrapper mới cho history.json
        data_wrapper = {
            "stats": self.session_stats, 
            "events": []
        }
        
        # Đọc dữ liệu cũ (nếu có)
        if os.path.exists(HISTORY_JSON_PATH):
            try:
                with open(HISTORY_JSON_PATH, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                    # Chỉ lấy lại mảng events cũ
                    data_wrapper["events"] = old_data.get("events", [])
            except Exception: pass
        
        # Nhét sự kiện mới lên đầu và giới hạn 20 phần tử
        data_wrapper["events"].insert(0, alert_data) 
        data_wrapper["events"] = data_wrapper["events"][:20] 
        
        # Ghi đè file
        with open(HISTORY_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data_wrapper, f, ensure_ascii=False, indent=4)

    def process_frame(self, frame):
        self.frame_count += 1
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(img_rgb)
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            frame_shape = frame.shape
            
            # --- THE DISPATCHER: CHIA PHÁT DỮ LIỆU CHO EXTENSIONS ---
            for ext in self.extensions:
                current_time = time.time()
                
                # Gọi logic của Extension (Nhận lại dictionary metadata)
                metadata = ext.process(landmarks, frame_shape)
                
                # Nếu phát hiện sự kiện VÀ qua thời gian hồi chiêu
                if metadata and (current_time - ext.last_triggered > ext.cooldown):
                    ext.last_triggered = current_time
                    
                    # 1. Chụp Bằng Chứng
                    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"{ext.event_name.lower()}_{timestamp_str}.jpg"
                    filepath = os.path.join(EVIDENCE_DIR, filename)
                    
                    # Vẽ khung xương lên ảnh
                    self.mp_draw.draw_landmarks(frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                    cv2.imwrite(filepath, frame)
                    
                    # 2. Cập nhật giao diện Web (Truyền metadata vào)
                    desc = metadata.get("description", "Có sự kiện bất thường")
                    self._sync_to_nginx_ui(ext.event_name, desc, filename, metadata)
                    
                    # 3. Ghi vào MongoDB (Polymorphic JSON)
                    if self.events_collection is not None:
                        doc = {
                            "patient_id": "PT_001",
                            "timestamp": datetime.now(timezone.utc),
                            "event_type": ext.event_name,
                            "image_evidence": f"/evidence/{filename}",
                            "metadata": metadata
                        }
                        self.events_collection.insert_one(doc)
                        
                    print(f"🚨 [{getTimelog()}] {ext.event_name} -> Đã đẩy UI & MongoDB")

        # Xuất ảnh Live mượt mà (Hệ số chẵn lẻ giảm tải)
        if self.frame_count % 2 == 0:
            cv2.imwrite(LIVE_IMG_PATH, frame)