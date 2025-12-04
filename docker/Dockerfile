# syntax=docker/dockerfile:1

FROM debian:bookworm-slim

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Install Python and dependencies using mounted uv binary
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv sync \
        --locked \
        --no-default-groups \
        --group prod \
        --no-install-project

# Create non-root user and data directory
RUN useradd -r -M -s /bin/false appuser \
    && mkdir -p /data/static /data/media \
    && chown -R appuser:appuser /data

# Copy application code
COPY --chown=appuser:appuser app /app/

# Copy entrypoint
COPY --chown=appuser:appuser docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Environment
ENV PORT=8000 \
    PATH="/app/.venv/bin:$PATH"

USER appuser
WORKDIR /app

ENTRYPOINT ["/entrypoint.sh"]
