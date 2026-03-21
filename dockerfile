# Dùng Python base image
FROM python:3.10-slim

# Tạo thư mục app
WORKDIR /app

# Copy file requirements trước (tối ưu cache)
COPY requirements.txt .

# Cài thư viện
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code
COPY . .

# Expose port (Render dùng PORT env)
ENV PORT=10000

# Chạy app
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]