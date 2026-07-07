from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from module.state import cam_manager

router = APIRouter(prefix="/api/system", tags=["System Control"])

class ConfigUpdate(BaseModel):
    target_fps: int

@router.get("/status")
def get_system_status():
    """Kiểm tra sức khỏe hệ thống"""
    return {
        "status": "ONLINE" if cam_manager.cap and cam_manager.cap.isOpened() else "OFFLINE",
        "current_target_fps": cam_manager.target_fps,
        "queue_size": cam_manager.frame_queue.qsize()
    }

@router.post("/config")
def update_config(config: ConfigUpdate):
    """Thay đổi thông số Camera nóng (Runtime)"""
    if not (1 <= config.target_fps <= 30):
        raise HTTPException(status_code=400, detail="FPS phải từ 1 đến 30")
    
    # Do hàm update_fps chưa được thêm vào class CameraManager của bạn, 
    # tạm thời chúng ta gán trực tiếp biến. (Bạn có thể thêm hàm sau).
    cam_manager.target_fps = config.target_fps
    
    return {"status": "success", "message": f"Đã cập nhật Target FPS thành {config.target_fps}"}