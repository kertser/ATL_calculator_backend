# -------- Stage: Base Python image --------
FROM python:3.11-slim AS base

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install build/system dependencies
RUN apt-get update && apt-get install -y \
    gcc libc6-dev libffi-dev libssl-dev pkg-config libjson-c5 patchelf \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------------
# Ensure uv uses system Python (not CPython 3.14)
# ----------------------------------------------------------
ENV UV_PYTHON_PREFERENCE=system \
    UV_NO_DOWNLOADS=1 \
    PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 \
    PATH="/root/.local/bin:$PATH"

# Copy uv binaries from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy dependency definitions first (for layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies into virtual environment
RUN uv sync --frozen --no-cache

# Copy application source and resources
COPY . .

# Copy required shared library
RUN cp $(find /lib/x86_64-linux-gnu -name "libjson-c.so*" | grep -E "libjson-c\.so\.[0-9]+$") /app/resources/libjson-c.so.5 && \
    cd /app/resources && chmod +x libjson-c.so.5

EXPOSE 5000

# Default command: run FastAPI app via uv
CMD ["uv", "run", "python", "server.py"]
