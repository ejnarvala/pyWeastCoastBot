FROM python:3.9-slim-buster

ARG POETRY_VERSION=2.1.2

RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root

COPY . .

ENV DJANGO_ALLOW_ASYNC_UNSAFE=true

CMD poetry run python run_bot.py