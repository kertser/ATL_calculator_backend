FROM python:3.11-slim AS base

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------
# Install system dependencies
# ------------------------------------------------
RUN apt-get update && apt-get install -y \
    gcc libc6-dev libffi-dev libssl-dev pkg-config libjson-c5 patchelf curl \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------
# Install uv using pip (not from image)
# This ensures it uses system Python 3.11
# ------------------------------------------------
RUN pip install --no-cache-dir uv==0.4.24

# ------------------------------------------------
# Environment settings to force correct interpreter
# ------------------------------------------------
ENV UV_PYTHON_PREFERENCE=system \
    UV_NO_DOWNLOADS=1 \
    PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 \
    PATH="/root/.local/bin:$PATH"

# ------------------------------------------------
# Copy dependency definitions and install
# ------------------------------------------------
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# ------------------------------------------------
# Copy actual application code
# ------------------------------------------------
COPY . .

# Copy required shared library to resources
RUN cp $(find /lib/x86_64-linux-gnu -name "libjson-c.so*" | grep -E "libjson-c\.so\.[0-9]+$") /app/resources/libjson-c.so.5 && \
    cd /app/resources && chmod +x libjson-c.so.5

EXPOSE 5000

CMD ["uv", "run", "python", "server.py"]
