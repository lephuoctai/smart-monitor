from .base_extension import BaseExtension
import mediapipe as mp
import math

class DrinkWaterExt(BaseExtension):
    event_name = "DRINK_WATER"
    cooldown = 30 # Cách nhau 30s mới tính là 1 lần uống mới

    def __init__(self):
        super().__init__()
        self.mp_pose = mp.solutions.pose

    def process(self, landmarks, frame_shape):
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        
        if nose.visibility < 0.6:
            return None
            
        # Tính khoảng cách Euclidean
        dist_right = math.hypot(nose.x - right_wrist.x, nose.y - right_wrist.y)
        dist_left = math.hypot(nose.x - left_wrist.x, nose.y - left_wrist.y)
        
        min_dist = min(dist_right, dist_left)
        
        # Nếu cổ tay đưa sát vào mũi (khoảng cách < 0.05 tỷ lệ màn hình)
        if min_dist < 0.05:
            return {
                "distance": round(min_dist, 3),
                "hand_used": "RIGHT" if dist_right < dist_left else "LEFT",
                "description": "Bệnh nhân đang uống nước hoặc dùng thuốc"
            }
        return None