import os
import time
import json
import threading
import pymongo
from datetime import datetime, timezone

EVIDENCE_DIR = '/app/evidence'
HISTORY_JSON_PATH = '/app/evidence/history.json'

def getTimelog():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class DataManager:
    def __init__(self, retention_days=7):
        self.retention_days = retention_days
        
        # Bộ đếm tĩnh để nuôi Dashboard (Raw Data)
        self.session_stats = {
            "FALL_DETECTED": 0,
            "RESTLESS_SLEEP": 0,
            "DRINK_WATER": 0,
            "WALKING_DETECTED": 0
        }
        
        # Kết nối MongoDB và cấu hình TTL (Tự xóa sau 90 ngày)
        try:
            self.mongo_client = pymongo.MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=2000)
            self.mongo_client.admin.command('ping')
            self.db = self.mongo_client["monitor_db"]
            self.events_collection = self.db["patient_events"]
            
            # Kích hoạt Bom hẹn giờ (TTL) cho Dữ liệu lạnh
            self.events_collection.create_index("timestamp", expireAfterSeconds=7776000)
            
            print(f"✅ [{getTimelog()}] DATA_MANAGER: Kết nối MongoDB thành công! Đã nạp chính sách lưu trữ 90 ngày.")
        except Exception as e:
            print(f"⚠️ [{getTimelog()}] DATA_MANAGER: Lỗi MongoDB. Hệ thống sẽ chỉ ghi log JSON. Chi tiết: {e}")
            self.events_collection = None

    def start_cleanup_worker(self):
        """Kích hoạt luồng chạy ngầm tự dọn ảnh cũ"""
        cleaner_thread = threading.Thread(target=self._cleanup_task, daemon=True)
        cleaner_thread.start()
        
    def _cleanup_task(self):
        print(f"🧹 [{getTimelog()}] DATA_MANAGER: Thợ săn rác kích hoạt. Giữ ảnh tối đa {self.retention_days} ngày.")
        while True:
            now = time.time()
            deleted_count = 0
            try:
                if os.path.exists(EVIDENCE_DIR):
                    for filename in os.listdir(EVIDENCE_DIR):
                        if filename in ["live.jpg", "history.json"]:
                            continue
                            
                        filepath = os.path.join(EVIDENCE_DIR, filename)
                        if os.path.isfile(filepath):
                            file_age_days = (now - os.path.getmtime(filepath)) / (24 * 3600)
                            
                            if file_age_days > self.retention_days:
                                os.remove(filepath)
                                deleted_count += 1
                                
                if deleted_count > 0:
                    print(f"🗑️ [{getTimelog()}] DATA_MANAGER: Đã dọn dẹp {deleted_count} ảnh cũ hơn {self.retention_days} ngày.")
            except Exception as e:
                pass
                
            # Ngủ 12 tiếng rồi quét tiếp
            time.sleep(43200)

    def save_event(self, event_name, desc, filename, metadata, patient_id="PT_001"):
        """Xử lý đồng thời cả giao diện Web (JSON) và MongoDB"""
        
        # 1. CẬP NHẬT JSON (DỮ LIỆU NÓNG CHO WEB)
        if event_name in self.session_stats:
            self.session_stats[event_name] += 1
            
        alert_data = {
            "time": time.strftime("%H:%M:%S", time.localtime()),
            "tag": event_name,
            "desc": desc,
            "image": filename,
            "metadata": metadata
        }
        
        data_wrapper = {"stats": self.session_stats, "events": []}
        
        if os.path.exists(HISTORY_JSON_PATH):
            try:
                with open(HISTORY_JSON_PATH, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                    data_wrapper["events"] = old_data.get("events", [])
            except Exception: pass
        
        data_wrapper["events"].insert(0, alert_data) 
        data_wrapper["events"] = data_wrapper["events"][:20] 
        
        try:
            with open(HISTORY_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(data_wrapper, f, ensure_ascii=False, indent=4)
        except Exception: pass

        # 2. CẬP NHẬT MONGODB (DỮ LIỆU LẠNH/BÁO CÁO)
        if self.events_collection is not None:
            try:
                doc = {
                    "patient_id": patient_id,
                    "timestamp": datetime.now(timezone.utc),
                    "event_type": event_name,
                    "image_evidence": f"/evidence/{filename}",
                    "metadata": metadata
                }
                self.events_collection.insert_one(doc)
            except Exception as e:
                print(f"[{getTimelog()}] DATA_MANAGER: Lỗi ghi MongoDB - {e}")