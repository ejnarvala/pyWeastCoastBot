import os
import discord
import django
from pyWeastCoastBot import settings as app_settings

import logging
import threading
from health_check import start_health_server

bot = discord.Bot()


def run():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pyWeastCoastBot.settings")
    django.setup()
    
    # Start health check server in background thread
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    load_cogs()
    bot.run(app_settings.BOT_TOKEN)


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
