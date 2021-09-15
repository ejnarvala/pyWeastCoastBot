import logging
from datetime import datetime

from discord.ext import commands, tasks

from db.models import Reminder
from lib.utils.time import parse_datetime


class Reminders(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.poll_for_reminder.start()

    def cog_unload(self):
        self.poll_for_reminder.cancel()

    @staticmethod
    def format_remind_time(remind_time):
        return remind_time.strftime('%m/%d/%Y %H:%M:%S')

    @tasks.loop(seconds=30)
    async def poll_for_reminder(self):
        try:
            reminders = Reminder.objects.filter(remind_time__lte=datetime.now())
            for reminder in reminders:
                logging.info(f"Handling reminder {reminder}")
                channel = await self.bot.fetch_channel(reminder.channel_id)
                discord_message = None
                try:
                    discord_message = await channel.fetch_message(reminder.message_id)
                    response = f"> {reminder.message}" if response.message else "Here's your reminder! :alarm_clock:"
                    await discord_message.reply(response)
                except Exception as e:
                    logging.error(f"Could not get message {reminder.message_id}: {e}")
                
                reminder.delete()
                logging.info(f"Reminder Deleted: {reminder}")
        except Exception as e:
            logging.error(f"Error polling reminders: {e}")

    @poll_for_reminder.before_loop
    async def before_poll(self):
        await self.bot.wait_until_ready()

    @commands.command(brief="Set reminders", usage="<time> [, message]")
    async def remindme(self, ctx, *args):
        if not args:
            return
        command = " ".join(args).split(",")
        
        reminder_datetime = parse_datetime(command[0])
        message = command[1] if len(command) > 1 else None

        reminder = Reminder.objects.create(
            user_id = ctx.message.author.id,
            channel_id = ctx.message.channel.id,
            message_id = ctx.message.id,
            message = message,
            remind_time = reminder_datetime
        )

        logging.info(f"Reminder created: {reminder}")
        
        response_message = f"Reminder set for ~{self.format_remind_time(reminder.remind_time)}"
        if reminder.message:
            response_message += f"\n> {reminder.message}"
        
        await ctx.reply(response_message)

    @remindme.error
    async def remindme_error(self, ctx, error):
        logging.error(f"Remindme Error: {error}")
        await ctx.reply(f"Sorry, couldn't process reminder: {error.original}")

def setup(bot):
    bot.add_cog(Reminders(bot))