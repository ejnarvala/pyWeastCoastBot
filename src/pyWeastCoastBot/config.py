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
DEBUG = get("DEBUG") == "true"
# Logging Configuration

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
    level=logging.INFO if not DEBUG else logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

# suppress kaleido & choreographer noisy logs
if not DEBUG:
    logging.getLogger("kaleido.kaleido").setLevel(logging.WARNING)
    logging.getLogger("kaleido._kaleido_tab").setLevel(logging.WARNING)
    logging.getLogger("choreographer.browsers.chromium").setLevel(logging.WARNING)
    logging.getLogger("choreographer.browser_async").setLevel(logging.WARNING)
    logging.getLogger("choreographer.utils._tmpfile").setLevel(logging.WARNING)
