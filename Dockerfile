FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for native libraries
RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    libjson-c5 \
    patchelf \
    && rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ✅ Force uv to use system Python (3.11)
ENV UV_PYTHON_PREFERENCE=system

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code and resources
COPY . .

# Set up shared library environment using the system libjson-c and fix library paths
RUN cp $(find /lib/x86_64-linux-gnu -name "libjson-c.so*" | grep -E "libjson-c\.so\.[0-9]+$") /app/resources/libjson-c.so.5 && \
    cd /app/resources && \
    chmod +x *.so* && \
    # Create proper symlinks for libraries
    if [ -f "libred_api.so.1.0" ]; then \
        patchelf --set-rpath '\$ORIGIN' libred_api.so.1.0 && \
        ln -sf libred_api.so.1.0 libred_api.so && \
        ln -sf libred_api.so.1.0 libred_api.so.1; \
    elif [ -f "libred_api.so.1" ]; then \
        patchelf --set-rpath '\$ORIGIN' libred_api.so.1 && \
        ln -sf libred_api.so.1 libred_api.so; \
    fi && \
    # Create symlink for JSON library
    ln -sf libjson-c.so.5 libjson-c.so

# Set environment variables for library loading
ENV LD_LIBRARY_PATH="/app/resources"

# Expose port
EXPOSE 5000

# Run the application
CMD ["uv", "run", "python", "server.py"]
