FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

WORKDIR /app

# deps first, WITHOUT the project itself (its source doesn't exist yet,
# so hatchling couldn't build it) -- cached layer: code edits skip re-download
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# now the code, then install the project on top of the cached deps
COPY simulator/ simulator/
RUN uv sync --frozen --no-dev

COPY config.toml .

# stream stdout live (no block buffering) so docker compose logs is useful
ENV PYTHONUNBUFFERED=1

CMD ["/app/.venv/bin/python", "-m", "simulator.main"]
