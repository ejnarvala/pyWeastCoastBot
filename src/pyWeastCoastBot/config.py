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
DEBUG = get("DEBUG").lower() == "true"
LOGGING_FORMAT_TIME_ENABLED = get("LOGGING_FORMAT_TIME_ENABLED", "true").lower() != "false"
LOGGING_FORMAT_NAME_ENABLED = get("LOGGING_FORMAT_NAME_ENABLED", "true").lower() != "false"
LOGGING_FORMAT_LEVEL_ENABLED = get("LOGGING_FORMAT_LEVEL_ENABLED", "true").lower() != "false"
LOGGING_LEVEL = (get("LOGGING_LEVEL") or "INFO").upper()
# Logging Configuration

log_format = ""
if LOGGING_FORMAT_TIME_ENABLED:
    log_format += "%(asctime)s "
if LOGGING_FORMAT_NAME_ENABLED:
    log_format += " %(name)s "
if LOGGING_FORMAT_LEVEL_ENABLED:
    log_format += " %(levelname)s "
log_format += " %(message)s"

if log_format and log_format[0] == " ":
    log_format = log_format[1:]

if DEBUG or LOGGING_LEVEL == "DEBUG":
    level = logging.DEBUG
elif LOGGING_LEVEL == "INFO":
    level = logging.INFO
elif LOGGING_LEVEL == "WARNING":
    level = logging.WARNING
elif LOGGING_LEVEL == "ERROR":
    level = logging.ERROR
else:
    level = logging.INFO

logging.basicConfig(
    format=log_format,
    level=level,
    datefmt="%Y-%m-%d %H:%M:%S",
)

# suppress kaleido & choreographer noisy logs
if not DEBUG:
    logging.getLogger("kaleido.kaleido").setLevel(logging.WARNING)
    logging.getLogger("kaleido._kaleido_tab").setLevel(logging.WARNING)
    logging.getLogger("choreographer.browsers.chromium").setLevel(logging.WARNING)
    logging.getLogger("choreographer.browser_async").setLevel(logging.WARNING)
    logging.getLogger("choreographer.utils._tmpfile").setLevel(logging.WARNING)
