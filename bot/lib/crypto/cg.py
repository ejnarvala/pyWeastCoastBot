from datetime import datetime
from functools import cached_property

import pandas as pd
from lib.crypto.coin import Coin
from lib.utils.errors import NotFound
from lib.utils.graph import generate_line_plot_image
from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()
# https://www.coingecko.com/en/api/documentation


class CoinGeckoClient:
    @cached_property
    def all_coins(self):
        # format: [{
        #     "id": "bitcoin",
        #     "symbol": "btc",
        #     "name": "Bitcoin"
        #   }]
        return cg.get_coins_list()

    @property
    def coin_id_by_symbol(self):
        return {coin["symbol"]: coin["id"] for coin in self.all_coins}

    @property
    def all_coin_ids(self):
        return {coin["id"] for coin in self.all_coins}

    def lookup_coin_id(self, search):
        search = search.lower()
        if search in self.all_coin_ids:
            return search
        if search in self.coin_id_by_symbol:
            return self.coin_id_by_symbol[search]
        raise NotFound("Could not find coin by name or symbol")

    def get_coin_market_data(self, coin_id):
        params = dict(
            localization=False,
            tickers=False,
            market_data=True,
            community_data=False,
            developer_data=False,
            sparkline=False,
        )

        coin_data = cg.get_coin_by_id(coin_id, **params)
        return Coin.from_cg_coin_data(coin_data)

    def get_coin_price_graph_image(self, coin_id):
        params = dict(vs_currency='usd', days=1)
        chart_data = cg.get_coin_market_chart_by_id(coin_id, **params)
        df = pd.DataFrame(chart_data["prices"], columns=["time", "price"])
        df["time"] = [
            datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S") for ts in df["time"]
        ]
        return generate_line_plot_image(df, x="time", y="price", labels=dict(time="Time", price="Price (USD)"))
