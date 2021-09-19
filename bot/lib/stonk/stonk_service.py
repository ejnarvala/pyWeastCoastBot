import time
from functools import lru_cache

import yfinance as yf
from lib.stonk.stock import StockHistory, StockInfo


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

    def get_stock_info(self, ticker):
        ticker = yf.Ticker(ticker)
        ticker_info = self._get_cached_info(ticker, ttl_hash=self.ttl_hash())
        return StockInfo.from_yf_ticker_info(ticker_info)

    def get_stock_history(self, ticker, period, interval):
        ticker = yf.Ticker(ticker)
        history = self._get_cached_history(
            ticker, period=period, interval=interval, ttl_hash=self.ttl_hash()
        )
        return StockHistory.from_yf_ticker_history(history)
