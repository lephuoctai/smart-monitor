from module.camera_manager import CameraManager

# Tạm thời chúng ta khởi tạo CameraManager ở đây.
# Sau này data_manager và cv_processor cũng có thể được khởi tạo tại đây
# để thư mục api/ có thể gọi trực tiếp lấy dữ liệu.
cam_manager = CameraManager(target_fps=15)