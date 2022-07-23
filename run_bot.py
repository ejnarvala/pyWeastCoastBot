import os
import discord
import django
from pyWeastCoastBot import settings as app_settings

import logging

DEBUG_GUILD = os.environ.get("DEBUG_GUILD")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot_kwargs = dict()
if DEBUG_GUILD:
    bot_kwargs["debug_guilds"] = [int(DEBUG_GUILD)]
logging.info(f"Bot kwargs: {bot_kwargs}")
bot = discord.Bot(**bot_kwargs)


def run():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pyWeastCoastBot.settings")
    django.setup()
    load_cogs()
    bot.run(BOT_TOKEN)


def load_cogs():
    for file in os.listdir("bot/cogs"):
        if file.endswith(".py"):
            name = file[:-3]
            cog_name = f"bot.cogs.{name}"
            bot.load_extension(cog_name)
            logging.info(f"Registered Cog: {cog_name}")


@bot.event
async def on_ready():
    logging.info(f"I am {bot.user.name} (logger)")


if __name__ == "__main__":
    run()
