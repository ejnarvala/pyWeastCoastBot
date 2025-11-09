#!/bin/bash
set -e
uv run python manage.py migrate
uv run python run_bot.py
