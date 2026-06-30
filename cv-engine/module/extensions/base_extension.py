from abc import ABC, abstractmethod

class BaseExtension(ABC):
    @property
    @abstractmethod
    def event_name(self):
        pass

    @property
    @abstractmethod
    def cooldown(self):
        """Thời gian hồi (giây) để tránh spam cùng 1 sự kiện liên tục"""
        pass

    def __init__(self):
        self.last_triggered = 0

    @abstractmethod
    def process(self, landmarks, frame_shape):
        """
        landmarks: Danh sách các điểm khớp từ AI
        frame_shape: Kích thước ảnh (height, width, channels)
        Trả về metadata (dict) nếu phát hiện, hoặc None nếu không có gì.
        """
        pass