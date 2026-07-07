import cv2
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

# Import đối tượng camera đã được khởi tạo từ hệ thống cũ
from module.state import cam_manager

router = APIRouter(prefix="/api/stream", tags=["Streaming"])

def mjpeg_generator():
    """Hàm biến đổi ảnh numpy array thành luồng byte MJPEG"""
    for frame in cam_manager.stream():
        if frame is None:
            continue
        
        # Mã hóa frame thành định dạng JPEG để đẩy lên Web
        ret, jpeg_buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if not ret:
            continue
            
        frame_bytes = jpeg_buffer.tobytes()
        
        # Nhả byte ra theo chuẩn multipart HTTP của MJPEG
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@router.get("/live")
async def get_live_stream():
    """API nhả luồng Video MJPEG trực tiếp cho App/Web"""
    return StreamingResponse(
        mjpeg_generator(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )