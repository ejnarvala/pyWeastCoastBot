import os
import dj_database_url


def get(key):
    return os.environ.get(key)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

DATABASES = {"default": dj_database_url.config(conn_max_age=600)}
INSTALLED_APPS = ("db", "bot")

BOT_TOKEN = get("BOT_TOKEN")
OMDB_API_SECRET = get("OMDB_API_SECRET")
COMMAND_PREFIX_OVERRIDE = get("COMMAND_PREFIX_OVERRIDE")

FITBIT_CLIENT_ID = get("FITBIT_CLIENT_ID")
FITBIT_CLIENT_SECRET = get("FITBIT_CLIENT_SECRET")
