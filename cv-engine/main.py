import time
from module.camera_manager import CameraManager
from module.data_manager import DataManager
from module.cv_processor import CVProcessor

def main():
    print("🚀 Đang khởi động Core Engine...")
    
    # 1. Khởi tạo Module Quản lý Dữ liệu
    data_manager = DataManager(retention_days=7)
    data_manager.start_cleanup_worker() # Bật luồng dọn rác ngầm
    
    # 2. Khởi tạo Camera
    cam_manager = CameraManager(queue_size=30, skip_ratio=3)
    
    # 3. Khởi tạo AI Engine (Bơm data_manager vào)
    cv_engine = CVProcessor(data_manager=data_manager)
    cv_engine.clear_live_image()
    
    # 4. Bật nguồn luồng Camera
    cam_manager.start()
    print("✅ Hệ thống đã sẵn sàng. Chờ nhận luồng dữ liệu...")
    
    # 5. Vòng lặp xử lý dữ liệu chính
    for frame in cam_manager.stream():
        if isinstance(frame, str) and frame == "EMPTY":
            continue
            
        if frame is None:
            cv_engine.clear_live_image() 
            continue
            
        cv_engine.process_frame(frame)

if __name__ == "__main__":
    main()