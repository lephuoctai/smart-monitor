FROM python:3.10-slim

# Cài đặt thư viện đồ họa hệ thống cho OpenCV
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Để CMD trống tạm thời để code không bị tắt, ta sẽ chạy main.py thủ công
CMD ["tail", "-f", "/dev/null"]
