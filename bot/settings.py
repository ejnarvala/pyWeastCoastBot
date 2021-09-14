import os
import dj_database_url

def get(key):
    return os.environ.get(key)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_AUTO_FIELD='django.db.models.AutoField'

DATABASES = {'default': dj_database_url.config(conn_max_age=600)}
INSTALLED_APPS = ("db",)

BOT_TOKEN = get("BOT_TOKEN")
OMDB_API_SECRET = get("OMDB_API_SECRET")