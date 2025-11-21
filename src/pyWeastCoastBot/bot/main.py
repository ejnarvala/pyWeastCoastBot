import logging
from pathlib import Path

import discord

import pyWeastCoastBot.config as config

bot = discord.Bot()


def run():
    load_cogs()
    bot.run(config.BOT_TOKEN)


def load_cogs():
    # Resolve cogs directory relative to this file
    cogs_dir = Path(__file__).parent / "cogs"

    for file in cogs_dir.glob("*.py"):
        if file.name == "__init__.py":
            continue

        cog_name = f"pyWeastCoastBot.bot.cogs.{file.stem}"
        try:
            bot.load_extension(cog_name)
            logging.info(f"Registered Cog: {cog_name}")
        except Exception as e:
            logging.error(f"Failed to load extension {cog_name}.", exc_info=e)


@bot.event
async def on_ready():
    logging.info(f"I am {bot.user.name}.")
