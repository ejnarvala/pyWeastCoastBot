from dotenv import load_dotenv
import os

load_dotenv()

def get(key):
    return os.environ.get(key)

def parse_boolean(text):
    if not text:
        return False
    return text.lower() == "true"

BOT_TOKEN = get("BOT_TOKEN")
OMDB_API_SECRET = get("OMDB_API_SECRET")
FLASK_DEBUG = parse_boolean(get("FLASK_DEBUG"))