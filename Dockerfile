FROM python:3.10-slim

WORKDIR /app

COPY . .

# 👉 cài đúng path
RUN pip install --no-cache-dir -r tutor-web/requirements.txt

WORKDIR /app/tutor-web

ENV PORT=10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]