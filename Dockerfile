FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY . /app

RUN uv sync --frozen --no-cache

CMD [".venv/bin/fastapi", "run", "main.py", "--port", "80", "--host", "0.0.0.0"]