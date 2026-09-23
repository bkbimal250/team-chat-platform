FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /usr/local/bin/uv
COPY pyproject.toml .
RUN uv sync --no-dev --no-install-project
COPY . .
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
RUN useradd -r conversation
USER conversation
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8003"]
