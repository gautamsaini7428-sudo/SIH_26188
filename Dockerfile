# ── Backend Dockerfile — SIH26188 ──
FROM python:3.12-slim

# System dependencies for OpenCV, Pillow, and DeepFace
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/
COPY verifications.db .
COPY audit_log.json .

# Create uploads directory
RUN mkdir -p uploads

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite+aiosqlite:///./verifications.db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
