import attr


@attr.s
class CoinMarketData:
    current_price = attr.ib()
    price_high_24h = attr.ib()
    price_low_24h = attr.ib()
    price_change_24h = attr.ib()
    price_change_percentage_24h = attr.ib()
    market_cap_rank = attr.ib()
    total_volume = attr.ib()

    @staticmethod
    def from_cg_market_data(market_data, currency="usd"):
        return CoinMarketData(
            current_price=market_data["current_price"][currency],
            price_high_24h=market_data["high_24h"][currency],
            price_low_24h=market_data["low_24h"][currency],
            price_change_24h=market_data["price_change_24h_in_currency"][currency],
            price_change_percentage_24h=market_data["price_change_percentage_24h_in_currency"][
                currency
            ],
            market_cap_rank=market_data["market_cap_rank"],
            total_volume=market_data["total_volume"][currency],
        )


@attr.s
class Coin:
    symbol = attr.ib()
    name = attr.ib()
    home_page_url = attr.ib()
    symbol_image_url = attr.ib()
    market_data = attr.ib()

    @staticmethod
    def from_cg_coin_data(coin_data):
        home_page_urls = coin_data["links"]["homepage"]

        market_data = None
        if "market_data" in coin_data:
            market_data = CoinMarketData.from_cg_market_data(coin_data["market_data"])

        return Coin(
            symbol=coin_data["symbol"],
            name=coin_data["name"],
            home_page_url=home_page_urls[0] if home_page_urls else None,
            symbol_image_url=coin_data["image"]["large"],
            market_data=market_data,
        )
