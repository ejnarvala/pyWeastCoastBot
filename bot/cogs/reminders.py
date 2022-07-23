import logging

from db.models import Reminder
from discord import slash_command, Option
from discord.ext import commands, tasks
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

                    message = f"<@{reminder.user_id}> :alarm_clock: Here's your reminder!"
                    if reminder.message:
                        message += f"\n> {reminder.message}"

                    await channel.send(message)
                except Exception as e:
                    logging.error(f"Error handling reminder: {e}")

                reminder.delete()
                logging.info(f"Reminder Deleted: {reminder}")
        except Exception as e:
            logging.error(f"Error polling reminders: {e}")

    @poll_for_reminder.before_loop
    async def before_poll(self):
        await self.bot.wait_until_ready()

    @slash_command(
        description="Set reminders - recommended to specify timezone - delete to cancel",
        debug_guilds=[896903198172930058],
    )
    async def remind_me(
        self,
        ctx,
        time: Option(str, "Time (specify"),
        message: Option(str, "Optional message to send in reminder") = None,
    ):
        reminder_datetime = parse_utc_datetime(time)
        if reminder_datetime < utc_now():
            raise Exception("Parsed time is in the past")
        reminder = Reminder.objects.create(
            user_id=ctx.author.id,
            channel_id=ctx.channel_id,
            message=message,
            remind_time=reminder_datetime,
        )

        logging.info(f"Reminder created: {reminder}")

        response_message = f"Reminder set for ~{self.format_remind_time(reminder.remind_time)}"
        if reminder.message:
            response_message += f"\n> {reminder.message}"

        await ctx.respond(response_message)

    @remind_me.error
    async def remindme_error(self, ctx, error):
        logging.error(f"Remindme Error: {error}")
        await ctx.respond(f"Sorry, couldn't process reminder: {error.original}", ephemeral=True)


def setup(bot):
    bot.add_cog(Reminders(bot))
