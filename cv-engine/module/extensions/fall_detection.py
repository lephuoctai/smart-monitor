from .base_extension import BaseExtension
import mediapipe as mp

class FallDetectionExt(BaseExtension):
    event_name = "FALL_DETECTED"
    cooldown = 5 # 5 giây báo 1 lần

    def __init__(self):
        super().__init__()
        self.mp_pose = mp.solutions.pose

    def process(self, landmarks, frame_shape):
        h, w, _ = frame_shape
        
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        # BỘ LỌC ĐIỂM MÙ
        if nose.visibility < 0.5:
            return None
            
        x_coords = [lm.x for lm in landmarks]
        y_coords = [lm.y for lm in landmarks]
        width = (max(x_coords) - min(x_coords)) * w
        height = (max(y_coords) - min(y_coords)) * h
        
        if height > 0:
            ratio = width / height
            mid_hip_y = (left_hip.y + right_hip.y) / 2.0
            vertical_distance = abs(mid_hip_y - nose.y)
            
            # Logic té ngã kép
            if (ratio > 1.2) and (vertical_distance < 0.2):
                return {
                    "impact_ratio": round(ratio, 2),
                    "vertical_distance": round(vertical_distance, 2),
                    "severity": "CRITICAL",
                    "description": "Phát hiện bệnh nhân ngã trên sàn"
                }
        return None