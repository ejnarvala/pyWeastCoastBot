from dotenv import load_dotenv
import os

load_dotenv()

def get(key):
    return os.environ.get(key)

BOT_TOKEN = get("BOT_TOKEN")
OMDB_API_SECRET = get("OMDB_API_SECRET")
COMMAND_PREFIX = get("COMMAND_PREFIX")