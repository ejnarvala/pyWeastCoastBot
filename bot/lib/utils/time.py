from datetime import datetime, timezone
from logging import error
import dateparser
import logging

def parse_utc_datetime(string_to_parse):
    try:
        return dateparser.parse(
            string_to_parse, 
            languages=['en'], 
            settings={
                'TIMEZONE': 'UTC',
                'TO_TIMEZONE': 'UTC',
                'RETURN_AS_TIMEZONE_AWARE': True
                }
            )
    except Exception as e:
        logging.error(f"Could not parse date from '{string_to_parse}': {e}")
        raise ValueError(f"Could not parse datetime from {string_to_parse}")


def utc_now():
    return datetime.now(timezone.utc)