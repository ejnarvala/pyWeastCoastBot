import logging

from discord import Option, slash_command
from discord.ext import commands, tasks
from humanize import naturaltime
from sqlmodel import select

from pyWeastCoastBot.db.models import Reminder
from pyWeastCoastBot.db.session import get_session
from pyWeastCoastBot.utils.time import parse_utc_datetime, utc_now


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
            async for session in get_session():
                stmt = select(Reminder).where(Reminder.remind_time <= utc_now())
                result = await session.exec(stmt)
                reminders = result.all()

                for reminder in reminders:
                    logging.info(f"Handling reminder {reminder}")
                    try:
                        channel = await self.bot.fetch_channel(int(reminder.channel_id))

                        message = f"<@{reminder.user_id}> :alarm_clock: Here's your reminder!"
                        if reminder.message:
                            message += f"\n> {reminder.message}"

                        await channel.send(message)
                    except Exception as e:
                        logging.error(f"Error handling reminder: {e}")

                    await session.delete(reminder)
                    logging.info(f"Reminder Deleted: {reminder}")
                await session.commit()
        except Exception as e:
            logging.error(f"Error polling reminders: {e}")

    @poll_for_reminder.before_loop
    async def before_poll(self):
        await self.bot.wait_until_ready()

    @slash_command(description="Set reminders - recommended to specify timezone - delete to cancel")
    async def remind_me(
        self,
        ctx,
        time: Option(str, "Time (specify"),
        message: Option(str, "Optional message to send in reminder") = None,
    ):
        reminder_datetime = parse_utc_datetime(time)
        if reminder_datetime < utc_now():
            raise Exception("Parsed time is in the past")

        reminder = Reminder(
            user_id=str(ctx.author.id),
            channel_id=str(ctx.channel_id),
            message=message,
            message_id=str(ctx.interaction.id),  # Using interaction ID as message ID placeholder
            remind_time=reminder_datetime,
        )

        async for session in get_session():
            session.add(reminder)
            await session.commit()
            await session.refresh(reminder)

        logging.info(f"Reminder created: {reminder}")

        response_message = f"Reminder set for ~{self.format_remind_time(reminder.remind_time)}"
        if reminder.message:
            response_message += f"\n> {reminder.message}"

        await ctx.respond(response_message)

    @remind_me.error
    async def remindme_error(self, ctx, error):
        logging.error(f"Remindme Error: {error}")
        # Handle InvokeError wrapping the actual exception
        original_error = getattr(error, "original", error)
        await ctx.respond(f"Sorry, couldn't process reminder: {original_error}", ephemeral=True)


def setup(bot):
    bot.add_cog(Reminders(bot))
