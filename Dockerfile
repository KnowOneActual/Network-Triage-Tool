# Multi-stage Dockerfile for Network Triage Tool
# Build: docker build -t network-triage .
# Run: docker run -it --rm network-triage

# Stage 1: Builder
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/
COPY README.md LICENSE ./

# Stage 2: Runtime
FROM python:3.14-slim-bookworm AS runtime

# Install system dependencies for network tools
RUN apt-get update && apt-get install -y \
    iputils-ping \
    traceroute \
    net-tools \
    nmap \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app
USER appuser

# Copy installed packages from builder
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv
COPY --from=builder --chown=appuser:appuser /app/src ./src
COPY --from=builder --chown=appuser:appuser /app/README.md /app/LICENSE ./

# Add .venv/bin to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 0), timeout=2)" || exit 1

# Default command
ENTRYPOINT ["network-triage"]

# Stage 3: Development (optional)
FROM builder AS dev

# Install development dependencies
RUN uv sync --frozen --all-extras

# Install additional development tools
RUN uv pip install \
    ipython \
    ipdb \
    watchdog \
    pytest-watch

# Create mount point for code
VOLUME ["/app/src"]

# Default command for development
CMD ["uv", "run", "pytest", "-v"]
