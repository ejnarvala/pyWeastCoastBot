import os
import django
from discord.ext.commands import Bot
from pyWeastCoastBot import settings as app_settings

import logging

COMMAND_PREFIX_OVERRIDE = os.environ.get("COMMAND_PREFIX_OVERRIDE")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Bot(command_prefix=COMMAND_PREFIX_OVERRIDE or "/")


def run():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pyWeastCoastBot.settings")
    django.setup()
    bot.run(BOT_TOKEN)


@bot.event
async def on_ready():
    logging.info(f"I am {bot.user.name} (logger)")
    for file in os.listdir("bot/cogs"):
        if file.endswith(".py"):
            name = file[:-3]
            bot.load_extension(f"bot.cogs.{name}")


if __name__ == "__main__":
    run()
