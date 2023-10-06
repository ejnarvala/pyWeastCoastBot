import logging
import attr
from discord import Colour, Embed, File, slash_command, Option
from discord.ext import commands
from lib.stonk.stonk_intervals import StonkIntervals
from lib.stonk.stonk_periods import StonkPeriods
from lib.stonk.stonk_service import StonkService
from lib.utils.consts import STONKMAN_DOWN_URL, STONKMAN_UP_URL
from lib.utils.errors import NotFound
from lib.utils.string import format_money, format_percent
from lib.utils.time import is_same_day

service = StonkService()


class Stonk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Stock price summary for a given period")
    async def stonk(
        self,
        ctx,
        ticker: Option(str, "Ticker to look up"),
        period: Option(
            StonkPeriods, "Period", choices=[p for p in StonkPeriods], default=StonkPeriods.one_day
        ),
        interval: Option(
            StonkIntervals,
            "Interval",
            choices=[i for i in StonkIntervals],
            default=StonkIntervals.fifteen_minute,
        ),
    ):
        await ctx.defer()
        stock_info = service.get_stock_info(ticker)
        stock_history = service.get_stock_history(ticker, period, interval)
        response = StonkResponse(stock_info, stock_history)
        await ctx.followup.send(embed=response.to_embed(), file=response.price_chart_file)

    @stonk.error
    async def stonk_error(self, ctx, error):
        logging.error(f"Stonk Error: {error}")
        message = f"Stonk Error: {error.original}"
        if isinstance(error.original, NotFound):
            message = ("Could not find stonk",)
        await ctx.respond(message, ephemeral=True)


@attr.s
class StonkResponse:

    stock_info = attr.ib()
    stock_history = attr.ib()

    @property
    def price_chart_file(self):
        return File(self.stock_history.price_graph_image, filename="image.png")

    @property
    def _dates(self):
        start = self.stock_history.start_date
        end = self.stock_history.end_date
        if is_same_day(start, end):
            return f"{start:%m/%d/%Y, %I:%M %p} - {end:%I:%M %p}"
        return f"{start:%m/%d/%Y, %H:%M} - {end:%m/%d/%Y, %H:%M}"

    @property
    def _market_price(self):
        return format_money(self.stock_info.price_current)

    @property
    def _market_change(self):
        price_change = format_money(self.stock_history.market_change)
        percent_change = format_percent(self.stock_history.market_change_percentage)
        return f"{price_change} ({percent_change})"

    @property
    def _low(self):
        return format_money(self.stock_history.low)

    @property
    def _high(self):
        return format_money(self.stock_history.high)

    @property
    def _title(self):
        return f"{self.stock_info.name} (${self.stock_info.symbol})"

    @property
    def _url(self):
        return f"https://finance.yahoo.com/quote/{self.stock_info.symbol}"

    @property
    def _description(self):
        return self.stock_info.industry

    @property
    def _color(self):
        if self.stock_history.market_change < 0:
            return Colour.red()
        else:
            return Colour.green()

    @property
    def _thumbnail(self):
        if self.stock_history.market_change < 0:
            return STONKMAN_DOWN_URL
        else:
            return STONKMAN_UP_URL

    def to_embed(self):
        embed = Embed(
            title=self._title,
            url=self._url,
            description=self._description,
            color=self._color,
        )
        embed.set_image(url="attachment://image.png")
        embed.set_thumbnail(url=self._thumbnail)
        embed.add_field(name="Current Price", value=self._market_price, inline=False)
        embed.add_field(name="Low", value=self._low, inline=True)
        embed.add_field(name="High", value=self._high, inline=True)
        embed.add_field(name="Change", value=self._market_change, inline=True)
        embed.add_field(name="When", value=self._dates, inline=False)

        return embed


def setup(bot):
    bot.add_cog(Stonk(bot))
