# ── Stage 1: build the React dashboard ───────────────────────────────────────
FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# vite.config.ts outputs to ../web/spa → redirect into /build/dist here
RUN npm run build -- --outDir dist

# ── Stage 2: Python runtime ───────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Copy built dashboard
COPY --from=frontend /build/dist ./web/spa

# Expose web dashboard port
EXPOSE 8080

# Run application
CMD ["python", "-m", "bot"]
