FROM python:3.10-slim

WORKDIR /app

# COPY toàn bộ project trước
COPY . .

# vào đúng folder chứa code
WORKDIR /app/tutor-web

# cài thư viện
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]