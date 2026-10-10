# ==========================================
# BrandShield AI - Backend Production Dockerfile
# FastAPI + Uvicorn + Motor (Async MongoDB)
# ==========================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies (curl for healthchecks, gcc/libffi if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source code
COPY app ./app

# Ensure static directories exist for persistent brand logos and uploads
RUN mkdir -p app/static/logos

# Create a non-root system user for security
RUN useradd -u 1001 -m brandshield && \
    chown -R brandshield:brandshield /app
USER brandshield

# Expose backend port
EXPOSE 8000

# Container Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
