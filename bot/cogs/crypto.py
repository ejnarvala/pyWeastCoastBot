import logging

import attr
from discord import Colour, Embed, File
from discord.ext import commands
from lib.crypto.cg import CoinGeckoClient
from lib.utils.consts import HexColors
from lib.utils.errors import NotFound
from lib.utils.string import format_money, format_percent

client = CoinGeckoClient()


class Crypto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        brief="Look up a coin",
        usage="<coin>",
        description="Crypto coin price summary over the last 24hrs",
    )
    async def crypto(self, ctx, coin_search):
        coin_id = client.lookup_coin_id(coin_search)
        coin = client.get_coin_market_data(coin_id)
        price_chart = client.get_coin_price_graph_image(coin_id)
        response = CryptoCoinResponse(coin=coin, price_chart=price_chart)
        await ctx.send(embed=response.to_embed(), file=response.price_chart_file)

    @crypto.error
    async def crypto_error(self, ctx, error):
        logging.error(f"Crypto Error: {error}")
        if isinstance(error.original, NotFound):
            await ctx.reply("Could not find coin")
        else:
            await ctx.reply(f"Crypto Error: {error.original}")


@attr.s
class CryptoCoinResponse:

    coin = attr.ib()
    price_chart = attr.ib()

    @property
    def price_chart_file(self):
        return File(self.price_chart, filename="image.png")

    @property
    def _color(self):
        return Colour.green() if self.coin.market_data.price_change_24h > 0 else Colour.red()

    def to_embed(self):
        embed = Embed(title=self.coin.name, url=self.coin.home_page_url, color=self._color)
        embed.set_image(url="attachment://image.png")
        embed.set_thumbnail(url=self.coin.symbol_image_url)
        embed.add_field(
            name="Price", value=format_money(self.coin.market_data.current_price), inline=True
        )
        embed.add_field(
            name="Percent Change",
            value=format_percent(self.coin.market_data.price_change_percentage_24h),
            inline=True,
        )
        embed.add_field(
            name="Absolute Change",
            value=format_money(self.coin.market_data.price_change_24h),
            inline=True,
        )
        embed.add_field(
            name="24 Hour High",
            value=format_money(self.coin.market_data.price_high_24h),
            inline=True,
        )
        embed.add_field(
            name="24 Hour Low",
            value=format_money(self.coin.market_data.price_low_24h),
            inline=True,
        )
        embed.add_field(name="Volume", value=self.coin.market_data.total_volume, inline=True)
        embed.add_field(
            name="Market Cap Rank", value=self.coin.market_data.market_cap_rank, inline=True
        )
        return embed


def setup(bot):
    bot.add_cog(Crypto(bot))
