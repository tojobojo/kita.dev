# =============================================================================
# Kita.dev Production Dockerfile
# Multi-stage build: React UI + Python API
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build React UI
# -----------------------------------------------------------------------------
FROM node:20-alpine AS ui-builder

WORKDIR /app/ui

# Install dependencies first (better caching)
COPY ui/package*.json ./
RUN npm ci --only=production

# Copy UI source and build
COPY ui/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Python API with built UI
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent/ ./agent/
COPY api/ ./api/
COPY config/ ./config/
COPY context/ ./context/
COPY github/ ./github/
COPY guardrails/ ./guardrails/
COPY llm/ ./llm/
COPY prompts/ ./prompts/
COPY sandbox/ ./sandbox/
COPY main.py ./

# Copy built React UI to static directory
COPY --from=ui-builder /app/ui/dist ./static/

# Create non-root user
RUN useradd --create-home --shell /bin/bash kita \
    && chown -R kita:kita /app

USER kita

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Start server
CMD ["sh", "-c", "uvicorn api.app:app --host 0.0.0.0 --port ${PORT}"]
