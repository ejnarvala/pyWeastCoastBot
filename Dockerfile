FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_CACHE_DIR=/opt/.cache

# Install UV
RUN pip install uv

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock /app/
COPY bin/migrate-and-start.sh /app/migrate-and-start.sh
RUN chmod +x /app/migrate-and-start.sh


# Install dependencies
RUN uv sync --frozen && rm -rf $UV_CACHE_DIR

COPY . .

ENV DJANGO_ALLOW_ASYNC_UNSAFE=true
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "python", "run_bot.py"]
