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

# Set up shared library environment - Remove any broken symlinks first
RUN rm -f /app/resources/libred_api.so /app/resources/libjson-c.so && \
    chmod +x resources/*.so* || true && \
    # Create proper symlinks using absolute paths
    ln -sf /app/resources/libred_api.so.1 /app/resources/libred_api.so && \
    ln -sf /app/resources/libjson-c.so.5 /app/resources/libjson-c.so && \
    # Verify symlinks were created correctly
    echo "=== Verifying symlinks ===" && \
    ls -la /app/resources/libred_api.so /app/resources/libjson-c.so && \
    file /app/resources/libred_api.so /app/resources/libjson-c.so && \
    echo "=== Testing symlink targets ===" && \
    test -f /app/resources/libred_api.so.1 && echo "libred_api.so.1 exists" || echo "libred_api.so.1 missing" && \
    test -f /app/resources/libjson-c.so.5 && echo "libjson-c.so.5 exists" || echo "libjson-c.so.5 missing" && \
    # Add the resources directory to the library path
    echo "/app/resources" > /etc/ld.so.conf.d/app-libs.conf && \
    ldconfig

# Set environment variables for library loading
ENV LD_LIBRARY_PATH="/app/resources"

# Expose port
EXPOSE 5000

# Run the application
CMD ["uv", "run", "python", "server.py"]
