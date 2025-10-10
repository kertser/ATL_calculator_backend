# ======================================================
#   UV Calculator API – Stable Production Dockerfile
# ======================================================

FROM python:3.13-slim-bookworm AS base

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive \
    UV_PYTHON_PREFERENCE=system \
    UV_NO_DOWNLOADS=1 \
    PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 \
    PATH="/root/.local/bin:$PATH"

# ------------------------------------------------------
# Install base system packages and Python build deps
# ------------------------------------------------------
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        gcc libc6-dev libffi-dev libssl-dev pkg-config \
        libjson-c5 patchelf curl; \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------
# Install uv (build tool / dependency resolver)
# ------------------------------------------------------
RUN pip install --no-cache-dir uv==0.4.24

# ------------------------------------------------------
# Copy dependency files and install Python deps
# ------------------------------------------------------
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# ------------------------------------------------------
# Copy the application code
# ------------------------------------------------------
COPY . .

# ------------------------------------------------------
# Copy required native library
# ------------------------------------------------------
RUN cp "$(find /lib/x86_64-linux-gnu -name 'libjson-c.so*' | grep -E 'libjson-c\.so\.[0-9]+$')" /app/resources/libjson-c.so.5 && \
    chmod +x /app/resources/libjson-c.so.5

EXPOSE 5000

CMD ["uv", "run", "python", "server.py"]
