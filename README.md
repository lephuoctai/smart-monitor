# Hệ Thống Giám Sát Bệnh Nhân Thông Minh (Smart Patient Monitor)

Hệ thống AI ứng dụng Computer Vision theo dõi trạng thái bệnh nhân thời gian thực, cảnh báo té ngã, trăn trở. Chạy hoàn toàn trên nền tảng Docker (Microservices).

## Cấu trúc dự án
- `cv-engine/`: Chứa mã nguồn AI (Python, OpenCV, MediaPipe).
- `evidence_data/`: Chứa giao diện Web (Dashboard) và lưu trữ ảnh cảnh báo.
- `docker-compose.yml`: File cấu hình triển khai hạ tầng.

## Yêu Cầu Hệ Thống
- Docker & Docker Compose.

## Hướng Dẫn Setup & Khởi Chạy

**1. Khởi động hạ tầng (Nginx & Môi trường AI):**
Mở Terminal tại thư mục gốc dự án và chạy:

```bash
docker-compose up -d
```
2. Kích hoạt Lõi AI (Computer Vision Engine):
Truy cập vào container và chạy thuật toán nhận diện:

```bash
docker exec -it monitor_cv python main.py
```

3. Xem Dashboard Giám Sát:
Mở trình duyệt và truy cập vào địa chỉ:
http://localhost:9000/evidence/index.html (Hoặc thay localhost bằng IP mạng LAN).

# Bổ sung:
**Truy vấn cơ sở dữ liệu**
Database: monitor_db
```bash
sudo docker exec -it monitor_db mongosh
```