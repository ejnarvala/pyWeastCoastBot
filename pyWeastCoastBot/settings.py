import os
import dj_database_url
import logging


def get(key):
    return os.environ.get(key)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

DATABASES = {"default": dj_database_url.config(conn_max_age=600)}

INSTALLED_APPS = ("bot", "db", "lib", "domain")

OMDB_API_SECRET = get("OMDB_API_SECRET")

FITBIT_CLIENT_ID = get("FITBIT_CLIENT_ID")
FITBIT_CLIENT_SECRET = get("FITBIT_CLIENT_SECRET")


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
