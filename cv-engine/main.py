# import time
# from module.camera_manager import CameraManager
# from module.data_manager import DataManager
# from module.cv_processor import CVProcessor

# def main():
#     print("🚀 Đang khởi động Core Engine...")
    
#     # 1. Khởi tạo Module Quản lý Dữ liệu
#     data_manager = DataManager(retention_days=7)
#     data_manager.start_cleanup_worker() # Bật luồng dọn rác ngầm
    
#     # 2. Khởi tạo Camera
#     cam_manager = CameraManager(queue_size=30, skip_ratio=3)
    
#     # 3. Khởi tạo AI Engine (Bơm data_manager vào)
#     cv_engine = CVProcessor(data_manager=data_manager)
#     cv_engine.clear_live_image()
    
#     # 4. Bật nguồn luồng Camera
#     cam_manager.start()
#     print("✅ Hệ thống đã sẵn sàng. Chờ nhận luồng dữ liệu...")
    
#     # 5. Vòng lặp xử lý dữ liệu chính
#     for frame in cam_manager.stream():
#         if isinstance(frame, str) and frame == "EMPTY":
#             continue
            
#         if frame is None:
#             cv_engine.clear_live_image() 
#             continue
            
#         cv_engine.process_frame(frame)

# if __name__ == "__main__":
#     main()
# Cập nhật file: main.py
import threading
import time
import cv2
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import nguyên vẹn các Module cũ của bạn
from module.camera_manager import CameraManager
from module.data_manager import DataManager
from module.cv_processor import CVProcessor

# 1. KHỞI TẠO HẠ TẦNG HỆ THỐNG (Biến toàn cục để API và AI cùng nhìn thấy)
data_manager = DataManager(retention_days=7)
cam_manager = CameraManager(target_fps=15) # Mặc định khởi động ở 15 FPS cho mượt
cv_engine = CVProcessor(data_manager=data_manager)
app = FastAPI(title="Smart Monitor API bọc ngoài Core AI", version="1.0.0")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Đang khởi động Core Engine dưới lớp vỏ FastAPI...")
    
    data_manager.start_cleanup_worker()
    cv_engine.clear_live_image()
    cam_manager.start()
    
    # KÍCH HOẠT LUỒNG AI CHẠY SONG SONG
    ai_thread = threading.Thread(target=ai_worker_loop, daemon=True)
    ai_thread.start()
    print("✅ Hệ thống đã sẵn sàng. FastAPI Server và AI Engine đang chạy đồng thời!")    
    yield

# 2. LUỒNG AI WORKER (Bản thể nâng cấp từ hàm main() cũ của bạn)
def ai_worker_loop():
    print("🧠 [AI WORKER] Luồng xử lý AI Engine bắt đầu chạy song song...")
    cv_engine.clear_live_image()
    
    for frame in cam_manager.stream():
        if frame is None:
            cv_engine.clear_live_image() 
            continue
            
        # Chạy lõi xử lý AI (uống nước, ngã, ngủ...) của bạn
        cv_engine.process_frame(frame)

# 3. VÒNG ĐỜI KHỞI ĐỘNG (Ứng với các bước 1, 4 của main cũ)
@app.on_event("startup")
def startup_event():
    print("🚀 Đang khởi động Core Engine dưới lớp vỏ FastAPI...")
    
    data_manager.start_cleanup_worker() # Bật dọn rác ngầm của bạn
    cv_engine.clear_live_image()
    cam_manager.start()                 # Bật nguồn đọc Camera
    
    # KÍCH HOẠT LUỒNG AI CHẠY SONG SONG
    ai_thread = threading.Thread(target=ai_worker_loop, daemon=True)
    ai_thread.start()
    
    print("✅ Hệ thống đã sẵn sàng. FastAPI Server và AI Engine đang chạy đồng thời!")

# 4. CÁC API PHỤC VỤ DASHBOARD WEB/MOBILE
def mjpeg_generator():
    """Đọc ảnh từ bộ nhớ chia sẻ (latest_frame) đẩy ra Web mà không cướp frame của AI"""
    while True:
        frame = cam_manager.latest_frame
        if frame is not None:
            ret, jpeg_buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_buffer.tobytes() + b'\r\n')
        else:
            # Nếu mất mạng hoặc chưa có ảnh, gửi ảnh đen hoặc sleep nhẹ chờ kết nối lại
            time.sleep(0.2)
        
        # Đồng bộ tốc độ nhả ảnh ra Web theo biến target_fps
        time.sleep(1.0 / cam_manager.target_fps)

@app.get("/api/stream/live")
async def get_live_stream():
    return StreamingResponse(mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/system/status")
def get_system_status():
    return {
        "status": "ONLINE" if cam_manager.cap and cam_manager.cap.isOpened() else "OFFLINE",
        "current_target_fps": cam_manager.target_fps,
        "ai_queue_pending": cam_manager.frame_queue.qsize()
    }

class ConfigUpdate(BaseModel):
    target_fps: int

@app.post("/api/system/config")
def update_config(config: ConfigUpdate):
    if not (1 <= config.target_fps <= 30):
        raise HTTPException(status_code=400, detail="FPS phải từ 1 đến 30")
    cam_manager.update_fps(config.target_fps)
    return {"status": "success", "message": f"Đã khóa cứng Target FPS ở mức: {config.target_fps}"}

# --- NHÓM 2: DATA API ---
@app.get("/api/events")
def get_events(limit: int = 200):
    """Lấy danh sách các sự kiện mới nhất đổ ra Web"""
    events = data_manager.get_recent_events(limit)
    return {"events": events}

if __name__ == "__main__":
    # Mở cổng 8000 ra ngoài host Docker
    uvicorn.run(app, host="0.0.0.0", port=1000)