# import os
# import cv2
# import time
# import threading
# import queue

# RTSP_URL = "rtsp://100.121.202.41:8554/live"
# # RTSP_URL = "rtsp://admin:camera123@192.168.1.2:554/onvif2"
# RTSP_TRANSPORT_METHODS = ["tcp", "udp", "http"]

# def getTimelog():
#     return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# class CameraManager:
#     def __init__(self, queue_size=30, skip_ratio=3):
#         self.frame_queue = queue.Queue(maxsize=queue_size)
#         self.skip_ratio = skip_ratio # Cứ 3 ảnh lấy 1 (10 FPS)
#         self.cap = None
#         self.cached_method = None
#         self.running = False
#         self.thread = None

#     def connect(self):
#         # ... (Toàn bộ hàm connect dò TCP/UDP giữ nguyên như cũ) ...
#         print(f"\n🔄 [{getTimelog()}] Đang nỗ lực kết nối tới: {RTSP_URL}")
#         for method in RTSP_TRANSPORT_METHODS:
#             os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{method}|fflags;discardcorrupt|max_delay;500000|stimeout;5000000|buffer_size;10240000"
#             cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
#             if cap.isOpened():
#                 self.cached_method = method
#                 print(f"✅ [{getTimelog()}] THÀNH CÔNG (Giao thức {method.upper()})!")
#                 return cap
#             cap.release()
#         return None

#     def start(self):
#         """Kích hoạt luồng đọc Camera chạy ngầm"""
#         self.running = True
#         self.thread = threading.Thread(target=self._read_loop, daemon=True)
#         self.thread.start()

#     def _read_loop(self):
#         print(f"🚀 [{getTimelog()}] Luồng Camera Reader đã khởi động...")
#         total_frames = 0
        
#         while self.running:
#             if self.cap is None or not self.cap.isOpened():
#                 self.cap = self.connect()
#                 if self.cap is None:
#                     self.frame_queue.put(None) # Nhét cờ báo mất mạng
#                     time.sleep(5)
#                     continue

#             ret, frame = self.cap.read()
#             if not ret:
#                 print(f"🔴 [{getTimelog()}] MẤT TÍN HIỆU! Kết nối lại...")
#                 self.cap.release()
#                 self.cap = None
#                 self.frame_queue.put(None) # Nhét cờ báo mất mạng
#                 continue
            
#             total_frames += 1
            
#             # 1. TỐI ƯU DOWN-SAMPLING TẠI NGUỒN (Lấy 1 bỏ 2)
#             if total_frames % self.skip_ratio != 0:
#                 continue 

#             # 2. XỬ LÝ NGHẼN QUEUE (Bỏ cũ lấy mới)
#             if self.frame_queue.full():
#                 try: self.frame_queue.get_nowait() 
#                 except queue.Empty: pass
            
#             self.frame_queue.put(frame)

#     def stream(self):
#         """KỊCH BẢN 2: GENERATOR (Nhả frame liên tục ra ngoài)"""
#         while self.running:
#             try:
#                 # Đợi tối đa 1s để lấy ảnh. Lấy được thì 'yield' (nhả) ra.
#                 frame = self.frame_queue.get(timeout=1.0)
#                 yield frame
#             except queue.Empty:
#                 # Nếu hàng đợi trống (mạng lag nhẹ), nhả ra một cờ rỗng
#                 yield "EMPTY"
# Cập nhật file: module/camera_manager.py
import os
import cv2
import time
import threading
import queue

RTSP_URL = "rtsp://100.121.202.41:8554/live"
# RTSP_URL = "rtsp://admin:camera123@192.168.1.2:554/onvif2"
RTSP_TRANSPORT_METHODS = ["tcp", "udp", "http"]

def getTimelog():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class CameraManager:
    def __init__(self, target_fps=30, queue_size=30):
        self.frame_queue = queue.Queue(maxsize=queue_size)
        self.target_fps = target_fps     # Cố định cấu hình FPS qua biến này như bạn muốn
        self.latest_frame = None         # BẢO BỐI: Nơi lưu ảnh mới nhất cho Web Stream đọc ké
        self.cap = None
        self.cached_method = None
        self.running = False
        self.thread = None

    def connect(self):
        print(f"\n🔄 [{getTimelog()}] Đang nỗ lực kết nối tới: {RTSP_URL}")
        for method in RTSP_TRANSPORT_METHODS:
            # Cấu hình FFMPEG tối ưu giảm delay và tăng khả năng chịu lỗi mạng
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{method}|fflags;discardcorrupt|max_delay;500000|stimeout;5000000|buffer_size;10240000"
            cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
            if cap.isOpened():
                self.cached_method = method
                print(f"✅ [{getTimelog()}] THÀNH CÔNG (Giao thức {method.upper()})!")
                return cap
            cap.release()
        return None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def update_fps(self, new_fps):
        """Hàm hỗ trợ đổi biến FPS nóng từ API điều khiển"""
        if 1 <= new_fps <= 30:
            self.target_fps = new_fps

    def _read_loop(self):
        print(f"🚀 [{getTimelog()}] Luồng Camera Reader đã khởi động...")
        last_frame_time = 0
        
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                self.cap = self.connect()
                if self.cap is None:
                    self.latest_frame = None
                    self.frame_queue.put(None) # Cờ báo mất tín hiệu cho AI
                    time.sleep(5)
                    continue

            ret, frame = self.cap.read()
            if not ret:
                print(f"🔴 [{getTimelog()}] MẤT TÍN HIỆU! Kết nối lại...")
                self.cap.release()
                self.cap = None
                self.latest_frame = None
                self.frame_queue.put(None)
                continue
            
            # 1. ĐIỀU CHỈNH CỐ ĐỊNH FPS BẰNG THỜI GIAN THỰC (Thay cho đếm số dư skip_ratio)
            current_time = time.time()
            if (current_time - last_frame_time) < (1.0 / self.target_fps):
                continue
            last_frame_time = current_time
            
            # Cập nhật bộ nhớ chia sẻ cho luồng Web API đọc
            self.latest_frame = frame 
            
            # 2. XỬ LÝ NGHẼN QUEUE CHO LUỒNG AI
            if self.frame_queue.full():
                try: self.frame_queue.get_nowait() 
                except queue.Empty: pass
            
            self.frame_queue.put(frame)

    def stream(self):
        """Dành riêng cho luồng AI Worker gặm tuần tự từng frame"""
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1.0)
                yield frame
            except queue.Empty:
                yield None