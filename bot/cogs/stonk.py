import logging

from discord import Colour, Embed, File
from discord.ext import commands
from lib.stonk.stonk_intervals import StonkIntervals
from lib.stonk.stonk_periods import StonkPeriods
from lib.stonk.stonk_service import StonkService
from lib.utils.errors import NotFound
from lib.utils.string import format_money, format_percent
from lib.utils.time import is_same_day

service = StonkService()


class Stonk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        brief="Look up a stock",
        usage="<ticker>\n<period=1d [1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max]>\n<interval=30m [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]>",
        description="Stock price summary for a given period",
    )
    async def stonk(
        self, ctx, ticker, period=StonkPeriods.one_day, interval=StonkIntervals.thirty_minute
    ):
        stock = service.get_stock_data(ticker, period, interval)
        price_chart_image = service.get_price_graph_image(ticker, period, interval)
        response = StonkResponse(stock, price_chart_image)

        await ctx.send(embed=response.to_embed(), file=response.price_chart_file)

    @stonk.error
    async def stonk_error(self, ctx, error):
        logging.error(f"Crypto Error: {error}")
        if isinstance(error.original, NotFound):
            await ctx.reply("Could not find stonk")
        else:
            await ctx.send(f"Crypto Error: {error.original}")


class StonkResponse:
    def __init__(self, stock, price_chart_image):
        self.stock = stock
        self.price_chart_image = price_chart_image

    @property
    def price_chart_file(self):
        return File(self.price_chart_image, filename="image.png")

    @property
    def _dates(self):
        if is_same_day(self.stock.start_date, self.stock.end_date):
            return f"{self.stock.start_date:%Y-%m-%d, %I:%M %p} - {self.stock.end_date:%I:%M %p}"
        return f"{self.stock.start_date:%Y-%m-%d, %H:%M} - {self.stock.end_date:%Y-%m-%d, %H:%M}"

    @property
    def _color(self):
        return Colour.green() if self.stock.market_change > 0 else Colour.red()

    @property
    def _title(self):
        return f"{self.stock.name} - ${self.stock.symbol}"

    def to_embed(self):
        embed = Embed(
            title=self._title,
            url=self.stock.yf_link,
            description=self.stock.sector,
            color=self._color,
        )
        embed.set_image(url="attachment://image.png")
        embed.set_thumbnail(url=self.stock.stonkman_image_url)
        embed.add_field(
            name="Market Price", value=format_money(self.stock.current_price), inline=False
        )
        embed.add_field(
            name="Last Day Low",
            value=format_money(self.stock.low_last_trade_day),
            inline=True,
        )
        embed.add_field(
            name="Last Day High",
            value=format_money(self.stock.high_last_trade_day),
            inline=True,
        )
        embed.add_field(
            name="Market Change", value=format_money(self.stock.market_change), inline=False
        )
        embed.add_field(
            name="Percent Market Change",
            value=format_percent(self.stock.market_change_percentage),
            inline=False,
        )

        embed.add_field(name="When", value=self._dates, inline=False)

        return embed


def setup(bot):
    bot.add_cog(Stonk(bot))
