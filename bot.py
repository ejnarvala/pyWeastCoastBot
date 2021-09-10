import os
import asyncio
from threading import Thread
from discord.ext.commands import Bot

import settings
import logging

bot = Bot(command_prefix="/")

def run():
    bot.run(settings.BOT_TOKEN)

def run_async():
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start(settings.BOT_TOKEN))
    return Thread(target=loop.run_forever).start()

@bot.event
async def on_ready():
    logging.info(f"I am {bot.user.name} (logger)")
    print(f"I am {bot.user.name}")

    for file in os.listdir("cogs"):
        if file.endswith(".py"):
            name = file[:-3]
            bot.load_extension(f"cogs.{name}")