# ==============================================================
# BrandShield AI - All-In-One Unified Production Container
# Builds React frontend and serves alongside FastAPI via Nginx
# Ideal for single-container cloud hosts (Render, Railway, Fly.io)
# ==============================================================

# Stage 1: Build React 19 Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
ARG VITE_GOOGLE_CLIENT_ID=
ENV VITE_GOOGLE_CLIENT_ID=${VITE_GOOGLE_CLIENT_ID}
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
COPY frontend/package*.json ./
RUN npm ci || npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Unified Runtime with Python 3.12, Nginx & Supervisor
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive
ENV ENVIRONMENT=production

WORKDIR /app

# Install system dependencies, Nginx, and Supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend application source
COPY backend/app ./backend/app
RUN mkdir -p ./backend/app/static/logos

# Copy compiled frontend SPA to Nginx document root
COPY --from=frontend-builder /frontend/dist /usr/share/nginx/html

# Copy custom Nginx and Supervisor configuration
COPY nginx.all-in-one.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose HTTP port
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start Supervisor to run both Uvicorn and Nginx
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
