from module.camera_manager import CameraManager
from module.cv_processor import CVProcessor

def main():
    # 1. Khởi tạo
    cam_manager = CameraManager(queue_size=30, skip_ratio=3)
    cv_engine = CVProcessor()

    cv_engine.clear_live_image()

    # 2. Bật nguồn (Thread chạy ngầm)
    cam_manager.start()
    print("✅ Hệ thống đã sẵn sàng. Chờ nhận luồng dữ liệu...")

    # 3. KỊCH BẢN 2: DUYỆT GENERATOR
    # Vòng for này sẽ chạy vĩnh viễn, mỗi lần cam_manager "yield" ảnh, nó sẽ nhận
    for frame in cam_manager.stream():
        
        # Xử lý các cờ báo hiệu từ Queue
        if isinstance(frame, str) and frame == "EMPTY":
            continue
            
        if frame is None:
            cv_engine.clear_live_image() # Báo động mất mạng
            continue

        # Đẩy ảnh vào hệ thống AI
        cv_engine.process_frame(frame)

if __name__ == "__main__":
    main()