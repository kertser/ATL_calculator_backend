# ======================================================
#   UV Calculator API – Production Dockerfile
# ======================================================

FROM python:3.13-slim AS base

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive \
    UV_PYTHON_PREFERENCE=system \
    UV_NO_DOWNLOADS=1 \
    PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 \
    PATH="/root/.local/bin:$PATH"

# Install system dependencies
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
        libffi-dev \
        libssl-dev \
        pkg-config \
        libjson-c5 \
        patchelf \
        curl \
        iputils-ping \
        netcat-openbsd; \
    rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv==0.4.24

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY . .

# Copy required native library
RUN cp "$(find /lib/x86_64-linux-gnu -name 'libjson-c.so*' | grep -E 'libjson-c\.so\.[0-9]+$')" /app/resources/libjson-c.so.5 && \
    chmod 644 /app/resources/libjson-c.so.5

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 5000

CMD ["uv", "run", "python", "server.py"]