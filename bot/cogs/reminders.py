import logging

from db.models import Reminder
from discord.ext import commands, tasks
from django.core.exceptions import ValidationError
from humanize import naturaltime
from lib.utils.time import parse_utc_datetime, utc_now


class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll_for_reminder.start()

    def cog_unload(self):
        self.poll_for_reminder.cancel()

    @staticmethod
    def format_remind_time(remind_time):
        return naturaltime(remind_time, future=True, minimum_unit="seconds", when=utc_now())

    @tasks.loop(seconds=30)
    async def poll_for_reminder(self):
        try:
            reminders = Reminder.objects.filter(remind_time__lte=utc_now())
            for reminder in reminders:
                logging.info(f"Handling reminder {reminder}")
                try:
                    channel = await self.bot.fetch_channel(reminder.channel_id)
                    discord_message = await channel.fetch_message(reminder.message_id)
                    response = (
                        f"> {reminder.message}"
                        if reminder.message
                        else ":alarm_clock: Here's your reminder!"
                    )
                    await discord_message.reply(response)
                except Exception as e:
                    logging.error(f"Error handling reminder: {e}")

                reminder.delete()
                logging.info(f"Reminder Deleted: {reminder}")
        except Exception as e:
            logging.error(f"Error polling reminders: {e}")

    @poll_for_reminder.before_loop
    async def before_poll(self):
        await self.bot.wait_until_ready()

    @commands.command(
        brief="Set reminders",
        usage="<time> [, message]",
        help="Times are stored in UTC, specify timezone "
        "if you are inputting a specific date/time string "
        "e.g. '9/15/21 3:00 PM EST'. Reminders are polled "
        "for every 30s. Deleting a remindme command will remove the reminder.",
        description="Set reminders",
    )
    async def remindme(self, ctx, *args):
        if not args:
            return
        command = " ".join(args).split(",")

        reminder_datetime = parse_utc_datetime(command[0])
        if reminder_datetime < utc_now():
            raise Exception("Parsed time is in the past")

        message = command[1] if len(command) > 1 else None

        reminder = Reminder.objects.create(
            user_id=ctx.message.author.id,
            channel_id=ctx.message.channel.id,
            message_id=ctx.message.id,
            message=message,
            remind_time=reminder_datetime,
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
