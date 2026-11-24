# ==============================================================================
# Multi-stage Dockerfile for Python FastAPI Backend
# Small runtime footprint, non-root user execution, persistent /data volume mount
# ==============================================================================

# Stage 1: Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final minimal runtime stage
FROM python:3.11-slim AS runner

WORKDIR /app

# Create a non-root system user and /data volume directory
RUN groupadd -r appgroup && useradd -r -g appgroup -d /home/appuser -m appuser \
    && mkdir -p /data /app \
    && chown -R appuser:appgroup /data /app

# Copy installed Python packages from builder stage
COPY --chown=appuser:appgroup --from=builder /root/.local /home/appuser/.local

# Copy application source code
COPY --chown=appuser:appgroup . /app

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////data/app.db

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
