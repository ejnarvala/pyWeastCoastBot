import attr
from lib.utils.consts import STONKMAN_DOWN_URL, STONKMAN_UP_URL
from lib.utils.math import get_percent_change

@attr.s
class Stock:

    name = attr.ib()
    symbol = attr.ib()
    sector = attr.ib()
    current_price = attr.ib()
    high = attr.ib()
    low = attr.ib()
    high_last_trade_day = attr.ib()
    low_last_trade_day = attr.ib()
    market_change = attr.ib()
    market_change_percentage = attr.ib()
    start_date = attr.ib()
    end_date = attr.ib()

    @property
    def yf_link(self):
        return f"https://finance.yahoo.com/quote/{self.symbol}"

    @property
    def stonkman_image_url(self):
        if self.market_change < 0:
            return STONKMAN_DOWN_URL
        else:
            return STONKMAN_UP_URL

    @staticmethod
    def from_yf_ticker(ticker_info, history):
        first_entry = history.iloc[0]
        last_entry = history.iloc[-1]

        first_open = first_entry["Open"]
        last_close = last_entry["Close"]
        market_change = last_close - first_open
        market_change_percentage = get_percent_change(current=last_close, previous=first_open)
        return Stock(
            name=ticker_info["shortName"],
            symbol=ticker_info["symbol"],
            sector=ticker_info["sector"],
            current_price=ticker_info["regularMarketPrice"],
            low_last_trade_day=ticker_info["regularMarketDayLow"],
            high_last_trade_day=ticker_info["regularMarketDayHigh"],
            high=history["High"].max(),
            low=history["Low"].min(),
            market_change=market_change,
            market_change_percentage=market_change_percentage,
            start_date=first_entry.name.to_pydatetime(),
            end_date=last_entry.name.to_pydatetime(),
        )
