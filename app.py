import bot
import web
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    bot.run_async()
    web.run()
