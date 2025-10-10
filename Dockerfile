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
# Use a reliable Debian mirror (optional, Israel mirror)
# ------------------------------------------------------
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's|deb.debian.org|mirror.isoc.org.il|g' /etc/apt/sources.list.d/debian.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
        sed -i 's|deb.debian.org|mirror.isoc.org.il|g' /etc/apt/sources.list; \
    fi

# ------------------------------------------------------
# Install system dependencies safely and reliably
# ------------------------------------------------------
RUN set -eux; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*.deb /tmp/*; \
    apt-get clean; \
    apt-get update -o Acquire::Retries=5 -o Acquire::CompressionTypes::Order::=gz; \
    apt-get install -y --no-install-recommends \
        gcc libc6-dev libffi-dev libssl-dev pkg-config \
        libjson-c5 patchelf curl; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*.deb

# ------------------------------------------------------
# Install uv (Python dependency manager)
# ------------------------------------------------------
RUN pip install --no-cache-dir uv==0.4.24

# ------------------------------------------------------
# Copy project files
# ------------------------------------------------------
COPY pyproject.toml uv.lock ./

# ------------------------------------------------------
# Install Python dependencies using uv
# ------------------------------------------------------
RUN uv sync --frozen --no-cache

# ------------------------------------------------------
# Copy the full application
# ------------------------------------------------------
COPY . .

# ------------------------------------------------------
# Copy required native library
# ------------------------------------------------------
RUN cp "$(find /lib/x86_64-linux-gnu -name 'libjson-c.so*' | grep -E 'libjson-c\.so\.[0-9]+$')" /app/resources/libjson-c.so.5 && \
    chmod +x /app/resources/libjson-c.so.5

EXPOSE 5000

CMD ["uv", "run", "python", "server.py"]