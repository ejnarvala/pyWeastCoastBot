# pyWeastCoastBot

This project is the python version of WeastCoastBot because my friends are picky and don't like nodejs

## Features

- **Crypto**: Track cryptocurrency prices and charts via CoinGecko (`/crypto`).
- **Stonk**: Track stock market data and charts via Yahoo Finance (`/stonk`).
- **Fitbot**: Fitbit integration for tracking steps and active minutes with server leaderboards (`/fitbot_*`).
- **IMDB**: Movie and TV show information search (`/imdb`).
- **Reminders**: Set reminders for yourself or the channel (`/remind_me`).
- **Wiki**: Quick Wikipedia search (`/wiki`).
- **Ping**: Simple latency check (`/ping`).

## Getting Started

### Requirements
* [Docker](https://www.docker.com/) (Recommended)
* [UV](https://github.com/astral-sh/uv) (For local Python development)

### Configuration
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Fill in the required values in `.env`:
   * `BOT_TOKEN`: Your Discord Bot Token.
   * `OMDB_API_SECRET`: API key from OMDb.
   * `FITBIT_CLIENT_ID` & `FITBIT_CLIENT_SECRET`: OAuth credentials from Fitbit (if using Fitbot).
   * `DATABASE_URL`: Connection string for the database (default: SQLite).

## Running the Bot

### Using Docker (Recommended)
The easiest way to run the bot is with Docker Compose.

```bash
# Start the bot in development mode (with hot-reload)
make dev

# Start with Postgres instead of SQLite
make dev-postgres
```

### Using UV (Local Python)
If you prefer running the bot directly on your machine:

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Start the bot (runs migrations):
   ```bash
   make start
   ```

## Development

### Project Structure
* `src/pyWeastCoastBot/bot`: Core bot logic and Cogs.
* `src/pyWeastCoastBot/lib`: Domain-specific libraries (crypto, fitbot, etc.).
* `src/pyWeastCoastBot/utils`: General utility functions.
* `src/pyWeastCoastBot/db`: Database models and migrations.

### Commands
A `Makefile` is provided for common tasks:

* `make lint`: Run ruff for linting.
* `make format`: Format code with ruff.
* `make clean`: Clean up artifacts.

### Database Migrations
This project uses Alembic for migrations.

* **Create a new migration** (after modifying models):
  ```bash
  make migrate-gen MSG="description_of_changes"
  ```

* **Apply migrations**:
  ```bash
  make migrate-up
  ```

* **Downgrade migration**:
  ```bash
  make migrate-down
  ```
