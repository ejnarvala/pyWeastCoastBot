from logging import error
import dateparser
import logging

def parse_datetime(string_to_parse):
    try:
        return dateparser.parse(string_to_parse, languages=['en'])
    except Exception as e:
        logging.error(f"Could not parse date from '{string_to_parse}': {e}")
        raise ValueError(f"Could not parse datetime from {string_to_parse}")
