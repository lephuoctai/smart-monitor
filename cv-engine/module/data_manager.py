import os
import time
import threading
import pymongo
from datetime import datetime, timezone

EVIDENCE_DIR = '/app/evidence'

def getTimelog():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class DataManager:
    def __init__(self, retention_days=7):
        self.retention_days = retention_days
        self.events_collection = None
        
        # 1. KẾT NỐI MONGODB
        try:
            self.mongo_client = pymongo.MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=2000)
            self.mongo_client.admin.command('ping')
            self.db = self.mongo_client["monitor_db"]
            self.events_collection = self.db["patient_events"]
            
            # Kích hoạt Bom hẹn giờ (TTL) cho Dữ liệu lạnh (90 ngày)
            self.events_collection.create_index("timestamp", expireAfterSeconds=7776000)
            
            print(f"✅ [{getTimelog()}] DATA_MANAGER: Kết nối MongoDB thành công! Đã nạp chính sách lưu trữ 90 ngày.")
        except Exception as e:
            print(f"⚠️ [{getTimelog()}] DATA_MANAGER: Lỗi MongoDB. Giao diện Web sẽ không có dữ liệu! Chi tiết: {e}")

    def start_cleanup_worker(self):
        """Kích hoạt luồng chạy ngầm tự dọn ảnh cũ trên ổ cứng"""
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
                        # Bỏ qua ảnh live stream trực tiếp
                        if filename == "live.jpg":
                            continue
                            
                        filepath = os.path.join(EVIDENCE_DIR, filename)
                        if os.path.isfile(filepath):
                            file_age_days = (now - os.path.getmtime(filepath)) / (24 * 3600)
                            
                            if file_age_days > self.retention_days:
                                os.remove(filepath)
                                deleted_count += 1
                                
                if deleted_count > 0:
                    print(f"🗑️ [{getTimelog()}] DATA_MANAGER: Đã dọn dẹp {deleted_count} ảnh cũ hơn {self.retention_days} ngày.")
            except Exception:
                pass
                
            # Ngủ 12 tiếng rồi quét tiếp
            time.sleep(43200)

    # 2. GHI DỮ LIỆU (WRITE)
    def save_event(self, event_name, desc, filename, metadata, patient_id="PT_001"):
        """Ghi sự kiện trực tiếp vào MongoDB, tối ưu tốc độ cho Core AI"""
        if self.events_collection is not None:
            try:
                doc = {
                    "patient_id": patient_id,
                    "timestamp": datetime.now(timezone.utc),
                    "time": time.strftime("%H:%M:%S", time.localtime()), # Giữ lại field này để Web hiển thị
                    "tag": event_name,
                    "desc": desc,
                    "image": filename,
                    "metadata": metadata
                }
                self.events_collection.insert_one(doc)
            except Exception as e:
                print(f"[{getTimelog()}] DATA_MANAGER: Lỗi ghi MongoDB - {e}")

    # 3. ĐỌC DỮ LIỆU (READ) - Cung cấp cho FastAPI
    def get_recent_events(self, limit=200):
        """Truy xuất danh sách sự kiện mới nhất phục vụ API Web"""
        if self.events_collection is None:
            return []
            
        try:
            # Sort theo timestamp giảm dần (mới nhất lên đầu)
            # Loại bỏ cột _id và timestamp khỏi kết quả vì JSON mặc định không parse được object Datetime
            cursor = self.events_collection.find(
                {}, 
                {"_id": 0, "timestamp": 0, "patient_id": 0}
            ).sort("timestamp", -1).limit(limit)
            
            return list(cursor)
        except Exception as e:
            print(f"[{getTimelog()}] DATA_MANAGER: Lỗi đọc MongoDB - {e}")
            return []