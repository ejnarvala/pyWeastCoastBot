import logging
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get(key: str) -> str | None:
    return os.environ.get(key)


# Configuration Constants
OMDB_API_SECRET = get("OMDB_API_SECRET")
FITBIT_CLIENT_ID = get("FITBIT_CLIENT_ID")
FITBIT_CLIENT_SECRET = get("FITBIT_CLIENT_SECRET")
BOT_TOKEN = get("BOT_TOKEN")

# Logging Configuration
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
