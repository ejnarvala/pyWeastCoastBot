import os
import dj_database_url
import logging


def get(key):
    return os.environ.get(key)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Timezone settings
USE_TZ = True
TIME_ZONE = "UTC"

# Database configuration with SQLite fallback
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.config(conn_max_age=600)}
else:
    # Default to SQLite for local/Raspberry Pi deployments
    # Use /app/data directory in Docker, or local directory otherwise
    db_dir = "/app/data" if os.path.exists("/app/data") else os.path.dirname(BASE_DIR)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(db_dir, "db.sqlite3"),
        }
    }

INSTALLED_APPS = ("bot", "db", "lib", "domain")

OMDB_API_SECRET = get("OMDB_API_SECRET")

FITBIT_CLIENT_ID = get("FITBIT_CLIENT_ID")
FITBIT_CLIENT_SECRET = get("FITBIT_CLIENT_SECRET")
BOT_TOKEN = get("BOT_TOKEN")


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
