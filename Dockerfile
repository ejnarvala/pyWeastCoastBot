# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

# Install build dependencies for packages that need compilation
# (psycopg2-binary, numpy, pandas, plotly, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    libffi-dev \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD ./ /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Make scripts executable
RUN chmod +x /app/bin/migrate-and-start.sh /app/bin/wait-for-it.sh

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Django environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ALLOW_ASYNC_UNSAFE=true

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the Discord bot
CMD ["python", "run_bot.py"]
