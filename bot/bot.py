import os
import django
from django.conf import settings
from discord.ext.commands import Bot

import logging

bot = Bot(command_prefix=settings.COMMAND_PREFIX_OVERRIDE or "/")


def run():
    bot.run(settings.BOT_TOKEN)


@bot.event
async def on_ready():
    logging.info(f"I am {bot.user.name} (logger)")
    django.setup()
    for file in os.listdir("cogs"):
        if file.endswith(".py"):
            name = file[:-3]
            bot.load_extension(f"cogs.{name}")


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    run()
