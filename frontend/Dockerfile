# ==========================================
# BrandShield AI - Frontend Production Build
# React 19 + Vite + Tailwind CSS + Nginx
# ==========================================

# Stage 1: Build React SPA bundle
FROM node:20-alpine AS builder

WORKDIR /app

# Vite embeds public VITE_* values into the generated browser bundle.
ARG VITE_GOOGLE_CLIENT_ID=
ENV VITE_GOOGLE_CLIENT_ID=${VITE_GOOGLE_CLIENT_ID}
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Copy package definitions and install dependencies
COPY package*.json ./
RUN npm ci || npm install

# Copy source code and build production distribution
COPY . .
RUN npm run build

# Stage 2: Serve optimized assets with Nginx
FROM nginx:1.27-alpine

# Remove default Nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom reverse proxy & SPA routing configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
