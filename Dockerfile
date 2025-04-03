FROM python:3.9-slim-buster

ARG POETRY_VERSION=2.1.2

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_CACHE_DIR=/opt/.cache

RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

COPY . .

ENV DJANGO_ALLOW_ASYNC_UNSAFE=true
ENV PATH="/app/.venv/bin:$PATH"

CMD poetry run python run_bot.py