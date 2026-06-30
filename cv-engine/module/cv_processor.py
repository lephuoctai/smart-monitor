import os
import cv2
import time
import json
import mediapipe as mp

LIVE_IMG_PATH = '/app/evidence/live.jpg'
HISTORY_JSON_PATH = '/app/evidence/history.json'
EVIDENCE_DIR = '/app/evidence/'

def getTimelog():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class CVProcessor:
    def __init__(self):
        self.frame_count = 0
        
        # 1. Khởi tạo "Bộ não" MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )
        self.mp_draw = mp.solutions.drawing_utils # Công cụ vẽ bộ xương
        
        # 2. Bộ đếm chống Spam cảnh báo
        self.last_alert_time = 0
        self.cooldown_seconds = 5 # Cách nhau 5 giây mới báo động 1 lần

    def clear_live_image(self):
        if os.path.exists(LIVE_IMG_PATH):
            try:
                os.remove(LIVE_IMG_PATH)
                print(f"🗑️ [{getTimelog()}] Đã xoá ảnh live do mất kết nối.")
            except Exception:
                pass

    def _log_to_json(self, reason, image_filename):
        """Hàm nội bộ: Ghi lịch sử ra file JSON cho Web Dashboard đọc"""
        alert_data = {
            "time": time.strftime("%H:%M:%S", time.localtime()),
            "reason": reason,
            "image": image_filename
        }
        
        history = []
        if os.path.exists(HISTORY_JSON_PATH):
            try:
                with open(HISTORY_JSON_PATH, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception:
                pass
        
        # Nhét cảnh báo mới nhất lên đầu danh sách
        history.insert(0, alert_data) 
        # Chỉ giữ lại 20 cảnh báo gần nhất để Web không bị nặng
        history = history[:20] 
        
        with open(HISTORY_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)

    def process_frame(self, frame):
        self.frame_count += 1
        is_falling = False
        
        # --- BƯỚC 1: ĐƯA ẢNH CHO AI XỬ LÝ ---
        # MediaPipe yêu cầu hệ màu RGB, trong khi OpenCV dùng BGR
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(img_rgb)
        
        # --- BƯỚC 2: PHÂN TÍCH LOGIC TÉ NGÃ ---
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            h, w, c = frame.shape
            
            # 1. BỘ LỌC ĐIỂM MÙ (Visibility Filter)
            # Lấy điểm tin cậy của Vai (11, 12) và Hông (23, 24)
            left_shoulder_vis = landmarks[11].visibility
            right_shoulder_vis = landmarks[12].visibility
            left_hip_vis = landmarks[23].visibility
            right_hip_vis = landmarks[24].visibility
            
            # Tính trung bình độ tin cậy của phần thân mình
            body_visibility = (left_shoulder_vis + right_shoulder_vis + left_hip_vis + right_hip_vis) / 4.0

            # Chỉ xử lý nếu AI chắc chắn > 60% đây là thân người
            if body_visibility > 0.6:
                
                # Tính khung chữ nhật
                x_coords = [lm.x for lm in landmarks]
                y_coords = [lm.y for lm in landmarks]
                
                width = (max(x_coords) - min(x_coords)) * w
                height = (max(y_coords) - min(y_coords)) * h
                
                # 2. BỘ LỌC KÍCH THƯỚC (Area Filter)
                # Kích thước người chiếm ít nhất bao nhiêu % khung hình (Ví dụ: 10%)
                screen_area = w * h
                person_area = width * height
                
                if person_area > (screen_area * 0.10): 
                    
                    # Tùy chọn: Vẽ khung xương lên ảnh khi đã qua bộ lọc để dễ debug
                    self.mp_draw.draw_landmarks(frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                    
                    # 3. LOGIC TÉ NGÃ CỐT LÕI
                    if height > 0:
                        ratio = width / height
                        if ratio > 1.2:
                            is_falling = True

        # --- BƯỚC 3: KÍCH HOẠT LƯU BẰNG CHỨNG ---
        current_time = time.time()
        # Nếu ngã VÀ đã qua thời gian hồi chiêu (5s)
        if is_falling and (current_time - self.last_alert_time > self.cooldown_seconds):
            self.last_alert_time = current_time
            
            # Tạo tên file bằng chứng
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"alert_{timestamp}.jpg"
            filepath = os.path.join(EVIDENCE_DIR, filename)
            
            # Đóng mộc đỏ lên ảnh
            cv2.putText(frame, "CANH BAO: PHAT HIEN TE NGA!", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            
            # Lưu ảnh & Cập nhật UI Web
            cv2.imwrite(filepath, frame)
            self._log_to_json("Cảnh báo: Bệnh nhân nằm trên sàn!", filename)
            
            print(f"🚨 [{getTimelog()}] PHÁT HIỆN TÉ NGÃ! Đã lưu: {filename}")

        # --- BƯỚC 4: XUẤT ẢNH LIVE CHO WEB ---
        if self.frame_count % 2 == 0:
            cv2.imwrite(LIVE_IMG_PATH, frame)