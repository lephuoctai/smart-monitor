from .base_extension import BaseExtension
import mediapipe as mp

class WalkTimeExt(BaseExtension):
    event_name = "WALKING_DETECTED"
    cooldown = 10 

    def __init__(self):
        super().__init__()
        self.mp_pose = mp.solutions.pose
        self.prev_x = None

    def process(self, landmarks, frame_shape):
        h, w, _ = frame_shape
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        if left_hip.visibility < 0.7:
            return None
            
        mid_hip_x = (left_hip.x + right_hip.x) / 2.0
        
        # Cần check tỷ lệ Bounding Box (phải đang đứng thẳng)
        x_coords = [lm.x for lm in landmarks]
        y_coords = [lm.y for lm in landmarks]
        width = (max(x_coords) - min(x_coords)) * w
        height = (max(y_coords) - min(y_coords)) * h
        
        if height > 0 and (width / height) < 0.8: # Dáng đứng
            if self.prev_x is not None:
                movement = abs(mid_hip_x - self.prev_x)
                # Đang di chuyển ngang
                if movement > 0.02: 
                    self.prev_x = mid_hip_x
                    return {
                        "movement_speed": round(movement, 3),
                        "description": "Bệnh nhân đang đi lại trong phòng"
                    }
            self.prev_x = mid_hip_x
        return None