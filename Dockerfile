# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
  gcc \
  libc6-dev \
  binutils \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pyinstaller

# Copy application code
COPY . .

# Create necessary directories if they don't exist
RUN mkdir -p templates static

# Compile to binary with static linking
RUN pyinstaller --onefile \
  --name dashboards-service \
  --distpath /app/dist \
  --workpath /app/build \
  --specpath /app \
  --clean \
  --noconfirm \
  --hidden-import=uvicorn.lifespan.on \
  --hidden-import=uvicorn.lifespan.off \
  --hidden-import=uvicorn.protocols.websockets.auto \
  --hidden-import=uvicorn.protocols.http.auto \
  --collect-all=uvicorn \
  --collect-all=fastapi \
  main.py

# Production stage - используем тот же базовый образ для совместимости
FROM python:3.11-slim AS production

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
  curl \
  ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get clean

# Copy binary from builder
COPY --from=builder --chown=appuser:appuser /app/dist/dashboards-service /app/

# Set permissions
RUN chmod +x /app/dashboards-service

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8050

# Expose port
EXPOSE 8050

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8050/healthz || exit 1

# Start the binary
CMD ["./dashboards-service"]

# Metadata
LABEL maintainer="Dovganik Daniil"
LABEL version="1.2.4"
LABEL description="Dashboards Service Binary (Python Compiled)"
