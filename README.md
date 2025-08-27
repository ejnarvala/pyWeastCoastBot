# pyWeastCoastBot

This project is the python version of WeastCoastBot because my friends are picky and don't like nodejs

## Recent Updates
- 🔄 **Migrated from Poetry to UV** for faster dependency management
- 📈 **Updated yfinance** to latest version (0.2.65) for improved stock data
- 🐳 **Updated Docker setup** to use UV for consistent environments
- 🧹 **Cleaned up build artifacts** and improved .gitignore

# Getting Started
## Requirements
* Docker
* [UV](https://github.com/astral-sh/uv) (for local Python development)


## Local Development

### With Docker (Recommended)
1. Create a `.env` file in `/bot` by copying `.env.example` and populating the variables with your values
2. Start up the app by running `docker compose up --build`
   * this will run db migrations and hot reload for any code changes
3. Start coding!

### With UV (Local Python Development)
This project uses [UV](https://github.com/astral-sh/uv) for fast Python package management.

1. Install UV if you haven't already:
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or with brew
   brew install uv
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run the bot locally:
   ```bash
   # Set up your database URL first
   export DATABASE_URL="sqlite:///local.db"
   
   # Run migrations
   uv run python manage.py migrate
   
   # Start the bot
   uv run python run_bot.py
   ```

4. Add new dependencies:
   ```bash
   uv add package-name
   ```

5. Run tests or Django commands:
   ```bash
   uv run python manage.py check
   uv run python manage.py shell
   ```

### Adding a Cog
1. in `/bot/cogs` copy the cog template at `cog.py.example` and rename it to the command you'll be adding
2. Add a method that is named your command and annotate the method with `@commands.command()`
   * the parameters for this method will first be the discord context followed by command parameters

More info here - [Discord Cogs](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html)

### Troubleshooting

**Docker issues:** Try a fresh build with
```bash
docker compose down -v
docker compose up --build
```

**UV issues:** Reset the virtual environment
```bash
rm -rf .venv
uv sync
```

**Python version issues:** UV will automatically download the right Python version if needed
