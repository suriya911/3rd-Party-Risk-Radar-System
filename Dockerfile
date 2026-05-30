# syntax=docker/dockerfile:1

# ── Stage 1: build the React / Vite frontend ───────────────────────────────
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build          # → /fe/dist

# ── Stage 2: Python backend that also serves the built frontend ────────────
FROM python:3.11-slim AS app

# Hugging Face Spaces runs containers as UID 1000 — match it so files are writable.
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    DATABASE_URL=./risk_radar.db \
    VENDORS_CSV=./vendors.csv

USER user
WORKDIR /app

# Python deps first for layer caching
COPY --chown=user requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt

# Backend source, data, and boot script
COPY --chown=user backend/ ./backend/
COPY --chown=user vendors.csv seed_demo.py start.sh ./

# Writable dir for an optional persistent DB (used by docker-compose volume)
RUN mkdir -p /app/data

# Built frontend from stage 1 → served by FastAPI at /
COPY --chown=user --from=frontend /fe/dist ./frontend_dist

EXPOSE 7860
CMD ["sh", "start.sh"]
