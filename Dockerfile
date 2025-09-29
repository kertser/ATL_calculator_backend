FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for native libraries
RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    file \
    && rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy application code and resources
COPY . .

# Debug: Check what files we have
RUN echo "=== Checking resources directory ===" && \
    ls -la resources/ && \
    echo "=== File types ===" && \
    file resources/*.so* && \
    echo "=== File sizes ===" && \
    ls -lh resources/*.so*

# Set up shared library environment
RUN chmod +x resources/*.so* || true && \
    # Change to resources directory and create symlinks with relative paths
    cd /app/resources && \
    ln -sf libred_api.so.1 libred_api.so && \
    ln -sf libjson-c.so.5 libjson-c.so && \
    # Verify symlinks
    echo "=== Checking symlinks ===" && \
    ls -la /app/resources/*.so && \
    file /app/resources/*.so && \
    echo "=== Verifying symlink targets ===" && \
    readlink /app/resources/libred_api.so && \
    readlink /app/resources/libjson-c.so && \
    # Add the resources directory to the library path
    echo "/app/resources" > /etc/ld.so.conf.d/app-libs.conf && \
    ldconfig

# Set environment variables for library loading
ENV LD_LIBRARY_PATH="/app/resources"

# Expose port
EXPOSE 5000

# Run the application
CMD ["uv", "run", "python", "server.py"]
