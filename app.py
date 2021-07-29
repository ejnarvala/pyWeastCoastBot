import bot
from web import app
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    bot.run_async()
    app.run()
