# Use Python 3.12 or 3.13 (3.14 is currently in pre-release/experimental)
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# Added 'libmagic1' which is often needed by article parsers for file type detection
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    libmagic1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv from the official binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files FIRST to leverage Docker cache
# We assume pyproject.toml is inside your local 'app/' folder
COPY app/pyproject.toml app/uv.lock ./

# Install dependencies
# Using --system is correct here for a slim container
RUN uv pip install --system --no-cache -r pyproject.toml

# Create data directory and user BEFORE copying code to ensure permissions
RUN mkdir -p /data && \
    useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app /data

# Copy the rest of your application code
# Ensure the local 'app/' contents go into the container's '/app'
COPY app/ .

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 8000

# Environment variables
ENV PORT=8000
ENV DATABASE_PATH=/data/timstapaper.db
# Ensure Python doesn't buffer logs (critical for seeing Docker logs in real-time)
ENV PYTHONUNBUFFERED=1 

# Health check (Note: uses the port ENV)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]