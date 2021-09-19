import logging
import tempfile
import time
from functools import lru_cache

import pandas as pd
import plotly.express as px
import yfinance as yf
from lib.utils.consts import HexColors
from lib.utils.errors import NotFound
from lib.stonk.stock import Stock

class StonkService:
    @classmethod
    @lru_cache
    def _get_cached_history(cls, ticker, ttl_hash, **params):
        del ttl_hash
        return ticker.history(**params)

    @classmethod
    @lru_cache
    def _get_cached_info(cls, ticker, ttl_hash):
        return ticker.info

    @staticmethod
    def ttl_hash(seconds=1):
        return round(time.time() / seconds)

    def get_stock_data(self, ticker, period, interval):
        ticker = yf.Ticker(ticker)
        ticker_info = self._get_cached_info(ticker, ttl_hash=self.ttl_hash())

        regular_market_price = ticker_info.get("regularMarketPrice")
        if not regular_market_price:
            raise NotFound(f"Invalid Stock: {ticker}")

        history = self._get_cached_history(
            ticker, period=period, interval=interval, ttl_hash=self.ttl_hash()
        )

        if history.empty:
            raise Exception("Stock history could not be fetched")

        return Stock.from_yf_ticker(ticker_info, history)

    def get_price_graph_image(self, ticker, period, interval):
        ticker = yf.Ticker(ticker)
        history = self._get_cached_history(
            ticker, ttl_hash=self.ttl_hash(), period=period, interval=interval
        )
        price = (history["High"] + history["Low"]) / 2
        time = [f"{time:%Y-%m-%d %H:%M:%S}" for time in history.index.to_pydatetime()]
        df = pd.DataFrame(dict(price=price, time=time))
        fig = px.line(df, x="time", y="price", labels=dict(time="Time", price="Price (USD)"))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=HexColors.WHITE, size=16),
        )
        fig.update_traces(line=dict(width=3))
        img_bytes = fig.to_image(format="png")
        file = tempfile.TemporaryFile()
        file.write(img_bytes)
        file.seek(0)
        return file
