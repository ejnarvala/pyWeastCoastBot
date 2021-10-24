from datetime import datetime

import requests
from lib.balldontlie.params import BallDontLieParams

SEASON_START_DATE_2021 = datetime(2021, 10, 18)  # TODO update this next year(FY2023)


class BallDontLieClient:

    BASE_URL = "https://www.balldontlie.io/api/v1/"

    @property
    def current_season(self):
        return datetime.utcnow().year

    def _request(self, path, params=BallDontLieParams(), **kwargs):
        if not isinstance(params, BallDontLieParams):
            raise TypeError

        url = f"{self.BASE_URL}/{path}"

        resp = requests.request(kwargs.get("method", "GET"), url, params=params.to_dict(), **kwargs)

        resp.raise_for_status()

        return resp.json()

    def _request_data(self, *args, **kwargs):
        return self._request(*args, **kwargs)["data"]

    def _request_data_generator(self, path, params=BallDontLieParams(), **kwargs):
        params.page = 0
        params.per_page = 100

        has_more = True
        while has_more:
            page = self._request(path, params, **kwargs)
            for d in page["data"]:
                yield d
            has_more = page["meta"]["next_page"] is not None

    def _has_next_page(page):
        if page["meta"]["next_page"]:
            return True
        return False

    def all_teams(self):
        return list(self._request_data_generator("teams"))

    def games(self, params=BallDontLieParams()):
        return self._request_data_generator("games", params)
