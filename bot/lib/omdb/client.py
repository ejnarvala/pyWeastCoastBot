from typing import Dict
import requests
import settings
from lib.omdb.imdb_file import ImdbFilm

class OmdbClient(object):

    api_key = settings.OMDB_API_SECRET
    base_url = f"http://www.omdbapi.com"

    @classmethod
    def _request(cls, path="", params=dict(), method="GET", **kwargs) -> Dict:
        url = f"{cls.base_url}/{path}"

        params.update(dict(apikey=settings.OMDB_API_SECRET))

        response = requests.request(method=method, url=url, params=params, **kwargs)

        response.raise_for_status()

        response_json = response.json()
        if response_json['Response'] == "False":
            raise OmdbError(response_json["Error"])
            
        return response_json

    @classmethod
    def find_by_title(cls, title_search_text) -> ImdbFilm:
        params = dict(t=title_search_text)
        response_json = cls._request(params=params)
        return ImdbFilm.from_json(response_json)


class OmdbError(Exception):
    pass