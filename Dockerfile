FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for native libraries
RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY . .

# Set up shared library environment
RUN chmod +x resources/*.so* || true && \
    # Create symlinks for the shared libraries to standard names
    ln -sf /app/resources/libred_api.so.1 /app/resources/libred_api.so && \
    ln -sf /app/resources/libjson-c.so.5 /app/resources/libjson-c.so && \
    # Add the resources directory to the library path
    echo "/app/resources" > /etc/ld.so.conf.d/app-libs.conf && \
    ldconfig

# Set environment variables for library loading
ENV LD_LIBRARY_PATH="/app/resources:$LD_LIBRARY_PATH"

# Expose port
EXPOSE 5000

# Run the application
CMD ["uv", "run", "python", "server.py"]
