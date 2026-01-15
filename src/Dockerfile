# Use Python 3.14 slim image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install system dependencies including uv
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY app/pyproject.toml app/uv.lock ./

# Install Python dependencies using uv
# Use --system to install directly without creating a virtual environment
RUN uv sync --frozen --no-cache --system

# Copy application code
COPY app/ .

# Create data directory for SQLite database
RUN mkdir -p /data && chmod 777 /data

# Create a non-root user to run the app
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app /data

USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Define environment variables
ENV FASTAPI_APP=app:app
ENV PORT=8000
ENV DATABASE_PATH=/data/timstapaper.db

# Run the application with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]