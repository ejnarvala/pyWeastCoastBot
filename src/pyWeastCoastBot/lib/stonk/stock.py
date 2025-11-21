from functools import cached_property

import attr
import pandas as pd

from pyWeastCoastBot.utils.graph import generate_line_plot_image
from pyWeastCoastBot.utils.math import get_percent_change


@attr.s
class StockInfo:
    name = attr.ib()
    symbol = attr.ib()
    industry = attr.ib()
    price_current = attr.ib()
    price_open = attr.ib()
    price_last_low = attr.ib()
    price_last_high = attr.ib()
    market_change = attr.ib()
    market_change_percentage = attr.ib()

    @staticmethod
    def from_yf_ticker_info(ticker_info):
        symbol = ticker_info["symbol"]
        try:
            price_current = (
                ticker_info.get("currentPrice")
                or ticker_info.get("postMarketPrice")
                or ticker_info.get("regularMarketPrice")
            )
            price_open = ticker_info.get("open") or ticker_info.get("regularMarketOpen")
            market_change = price_current - price_open
            market_change_percentage = get_percent_change(current=price_current, previous=price_open)
            name = ticker_info.get("shortName") or ticker_info.get("longName")
            industry = ticker_info.get("industry", "")
            price_last_low = ticker_info.get("dayLow") or ticker_info("regularMarketDayLow")
            price_last_high = ticker_info.get("dayHigh") or ticker_info("regularMarketDayHigh")
        except Exception as e:
            raise ValueError(f"Invalid Stock: {symbol}") from e

        return StockInfo(
            name=name,
            symbol=symbol,
            industry=industry,
            price_current=price_current,
            price_open=price_open,
            price_last_low=price_last_low,
            price_last_high=price_last_high,
            market_change=market_change,
            market_change_percentage=market_change_percentage,
        )


@attr.s
class StockHistory:
    high = attr.ib()
    low = attr.ib()
    first_open = attr.ib()
    last_close = attr.ib()
    market_change = attr.ib()
    market_change_percentage = attr.ib()
    start_date = attr.ib()
    end_date = attr.ib()
    _data = attr.ib()

    @cached_property
    def price_graph_image(self):
        history = self._data
        price = (history["High"] + history["Low"]) / 2
        time = [f"{time:%Y-%m-%d %H:%M:%S}" for time in history.index.to_pydatetime()]
        df = pd.DataFrame(dict(price=price, time=time))
        return generate_line_plot_image(df, x="time", y="price", labels=dict(time="Time", price="Price (USD)"))

    @staticmethod
    def from_yf_ticker_history(history):
        first_entry = history.iloc[0]
        last_entry = history.iloc[-1]

        first_open = first_entry["Open"]
        last_close = last_entry["Close"]
        market_change = last_close - first_open
        market_change_percentage = get_percent_change(current=last_close, previous=first_open)
        return StockHistory(
            high=history["High"].max(),
            low=history["Low"].min(),
            first_open=first_open,
            last_close=last_close,
            market_change=market_change,
            market_change_percentage=market_change_percentage,
            start_date=first_entry.name.to_pydatetime(),
            end_date=last_entry.name.to_pydatetime(),
            data=history,
        )
