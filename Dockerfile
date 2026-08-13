# syntax=docker/dockerfile:1

# --- Frontend build: Node only, discarded after this stage ---
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# vite.config.ts writes the build to ../src/bookersoft/static relative to
# frontend/ — i.e. /src/bookersoft/static from this stage's root.

# --- Runtime: Python only. Node never ships in this image. ---
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app

# Dependencies first, without the project itself, so this layer only
# rebuilds when pyproject.toml/uv.lock change — not on every source edit.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src/ ./src/
COPY --from=frontend /src/bookersoft/static ./src/bookersoft/static
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:${PATH}"

# Shell form, not exec form: ${PORT} must be expanded by the shell at
# container start (Railway assigns it dynamically) — the JSON-array exec
# form would pass the literal string "${PORT}" through unexpanded.
# --proxy-headers plus --forwarded-allow-ips='*' make uvicorn trust
# X-Forwarded-For/-Proto from Railway's edge proxy: without it, every
# request looks like it comes from the proxy's own address, which breaks
# the per-IP login rate limiting (see the code-review step for detail).
CMD uvicorn bookersoft.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'
