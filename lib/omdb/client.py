import logging
from typing import Dict

import requests
from pyWeastCoastBot import settings
from lib.omdb.imdb_file import ImdbFilm


class OmdbClient(object):

    api_key = settings.OMDB_API_SECRET
    base_url = "http://www.omdbapi.com"

    @classmethod
    def _request(cls, path="", params=dict(), method="GET", **kwargs) -> Dict:
        url = f"{cls.base_url}/{path}"

        params.update(dict(apikey=settings.OMDB_API_SECRET))

        response = requests.request(method=method, url=url, params=params, **kwargs)

        response.raise_for_status()

        response_json = response.json()
        logging.debug(f"OMDB Response: {response_json}")
        if response_json["Response"] == "False":
            raise OmdbError(response_json["Error"])
        return response_json

    @classmethod
    def find_by_title_or_id(cls, title, imdb_id, year) -> ImdbFilm:
        params = dict(t=title, i=imdb_id, y=year)
        params = {k: v for k, v in params.items() if v}
        response_json = cls._request(params=params)
        return ImdbFilm.from_json(response_json)


class OmdbError(Exception):
    pass
