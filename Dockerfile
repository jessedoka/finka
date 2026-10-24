FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app
# Workspace layout: core/ plus the provider packages it bundles (integrations/*).
# The providers are installed non-editable so the final image carries them in
# /opt/venv without needing their source tree.
COPY pyproject.toml uv.lock ./
COPY core/pyproject.toml core/pyproject.toml
COPY integrations/ integrations/
RUN uv sync --frozen --no-dev --no-editable --package core

FROM python:3.13-slim

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY core/ .

RUN useradd --create-home appuser
USER appuser

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
