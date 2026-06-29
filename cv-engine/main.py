import os
import cv2
import time

# RTSP_URL = "rtsp://100.108.35.54:8554/live"
RTSP_URL = "rtsp://192.168.1.98:8554/live"

RTSP_TRANSPORT_METHODS = ["tcp", "udp", "http"]
cached_method = None  
# Để in time cùng các dòng print log
def getTimelog():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def connect_camera():
    global cached_method 
    print(f"\n🔄 [{getTimelog()}] Đang nỗ lực kết nối tới: {RTSP_URL}")
    
    if cached_method:
        print(f"\n[{getTimelog()}]  Ưu tiên thử lại giao thức cũ: [ {cached_method.upper()} ]...")
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{cached_method}"
        cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
        if cap.isOpened():
            print(f"✅ [{getTimelog()}] THÀNH CÔNG: Đã nối lại luồng bằng {cached_method.upper()}!")
            return cap
        cap.release()
        cached_method = None  
            
    for method in RTSP_TRANSPORT_METHODS:
        print(f"👉 [{getTimelog()}] Thử dò giao thức [ {method.upper()} ]...")
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{method}"
        cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
        if cap.isOpened():
            cached_method = method  
            print(f"✅ [{getTimelog()}] THÀNH CÔNG: Đã bắt được luồng RTSP bằng giao thức {method.upper()}!")
            return cap
        cap.release()
            
    print(f"🚫 [{getTimelog()}] THẤT BẠI: Camera từ chối tất cả các giao thức.")
    return None

# --- MAIN LOOP ---
cap = None
frame_count = 0

print(f"🚀 [{getTimelog()}] Khởi động hệ thống CV Engine...")

while True:
    if cap is None or not cap.isOpened():
        cap = connect_camera()
        if cap is None:
            time.sleep(5)
            continue 

    # Nếu kẹt ở đây, chứng tỏ gói tin UDP đang bị tường lửa chặn chặn sạch
    ret, frame = cap.read()
    
    if not ret:
        print(f"🔴 [{getTimelog()}] MẤT TÍN HIỆU: Đang đọc thì rớt luồng! Kết nối lại...")
        cap.release() 
        cap = None    
        continue

    frame_count += 1
    
    # In log ngay lập tức khi đọc được frame đầu tiên để chứng minh luồng không bị nghẽn
    if frame_count == 1:
        print(f"📸 [{getTimelog()}] Đã đọc được frame đầu tiên từ Camera! Tiến hành xuất file lên Web...")

    # Xuất ảnh ra thư mục map với evidence_data trên máy host
    if frame_count % 2 == 0:
        cv2.imwrite('/app/evidence/live.jpg', frame)

    if frame_count % 30 == 0:
        print(f"🟢 [{getTimelog()}] Đang nhận dữ liệu mượt mà... (Frame hiện tại: {frame_count})")
        cv2.imwrite('/app/evidence/test_fallback.jpg', frame)