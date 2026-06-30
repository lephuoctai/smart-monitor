from .base_extension import BaseExtension
import mediapipe as mp
import collections

class SleepTrackingExt(BaseExtension):
    event_name = "RESTLESS_SLEEP"
    cooldown = 60 # Chỉ báo cáo 1 lần mỗi phút để tránh spam

    def __init__(self):
        super().__init__()
        self.mp_pose = mp.solutions.pose
        # Lưu vết tọa độ X của vai trong 30 frame (khoảng 3 giây)
        self.shoulder_x_history = collections.deque(maxlen=30)

    def process(self, landmarks, frame_shape):
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        
        # Nếu đang nằm (tọa độ Y thường lớn) hoặc độ hiển thị thấp thì mới tính là ngủ
        if left_shoulder.visibility < 0.5:
            return None
            
        mid_shoulder_x = (left_shoulder.x + right_shoulder.x) / 2.0
        self.shoulder_x_history.append(mid_shoulder_x)
        
        if len(self.shoulder_x_history) == 30:
            # Tính độ lệch (Delta) cao nhất trong 3 giây qua
            min_x = min(self.shoulder_x_history)
            max_x = max(self.shoulder_x_history)
            delta = max_x - min_x
            
            # Nếu vai dao động lớn hơn 15% chiều rộng khung hình liên tục
            if delta > 0.15:
                # Xóa lịch sử để đo lại từ đầu
                self.shoulder_x_history.clear()
                return {
                    "toss_amplitude": round(delta, 2),
                    "severity": "WARNING",
                    "description": "Bệnh nhân trăn trở, dao động tư thế liên tục"
                }
        return None