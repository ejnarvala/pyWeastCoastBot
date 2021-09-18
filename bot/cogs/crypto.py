import attr
import logging
from discord.ext import commands
from discord import Embed, File
from lib.crypto.cg import CoinGeckoClient
from lib.utils.errors import NotFound

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

    @staticmethod
    def _format_money(value):
        result = f"${abs(value):,.2f}"
        if value < 0:
            result = f"-{result}"
        return result

    @staticmethod
    def _format_percent(value):
        return f"{value:.2f}%"

    @property
    def price_chart_file(self):
        return File(self.price_chart, filename="image.png")

    def to_embed(self):
        embed = Embed(title=self.coin.name, url=self.coin.home_page_url)
        embed.set_image(url="attachment://image.png")
        embed.set_thumbnail(url=self.coin.symbol_image_url)
        embed.add_field(
            name="Price", value=self._format_money(self.coin.market_data.current_price), inline=True
        )
        embed.add_field(
            name="Percent Change",
            value=self._format_percent(self.coin.market_data.price_change_percentage_24h),
            inline=True,
        )
        embed.add_field(
            name="Absolute Change",
            value=self._format_money(self.coin.market_data.price_change_24h),
            inline=True,
        )
        embed.add_field(
            name="24 Hour High",
            value=self._format_money(self.coin.market_data.price_high_24h),
            inline=True,
        )
        embed.add_field(
            name="24 Hour Low",
            value=self._format_money(self.coin.market_data.price_low_24h),
            inline=True,
        )
        embed.add_field(name="Volume", value=self.coin.market_data.total_volume, inline=True)
        embed.add_field(
            name="Market Cap Rank", value=self.coin.market_data.market_cap_rank, inline=True
        )
        return embed


def setup(bot):
    bot.add_cog(Crypto(bot))
