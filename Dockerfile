# syntax=docker/dockerfile:1.7-labs

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install only dependencies (do not install the app into the venv)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Download Firefox browser binaries (keep system deps for runtime stage)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv run playwright install firefox



FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    HOME=/home/app \
    XDG_CACHE_HOME=/home/app/.cache \
    MOZ_DISABLE_CONTENT_SANDBOX=1 \
    MOZ_DISABLE_GMP_SANDBOX=1

WORKDIR /app

# Create dedicated user before copying files (for ownership)
RUN groupadd --system app && useradd --system --gid app app

# Bring in dependency venv and downloaded browsers
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /ms-playwright /ms-playwright

# Install system dependencies for Firefox; keep browser cache intact
RUN uv run playwright install-deps firefox && \
    mkdir -p /home/app/.cache/fontconfig /var/cache/fontconfig && \
    chown -R app:app /home/app/.cache && \
    chmod 777 /var/cache/fontconfig && \
    fc-cache -fv && \
    rm -rf /var/lib/apt/lists/*

# Copy application source at the end (app-as-source, not installed into venv)
COPY --chown=app:app . /app

# Default to root to avoid Firefox user namespace sandbox errors; override with
# `--user app` only if the host allows unprivileged user namespaces.
USER root

EXPOSE 8000

CMD ["gunicorn", "entry:app", "-c", "gunicorn.conf.py", "-k", "worker.ConfigurableUvicornWorker", "-b", "0.0.0.0:8000"]
