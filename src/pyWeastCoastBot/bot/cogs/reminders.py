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

    def format_reminders_list(self, reminders, include_user=False):
        """Format a list of reminders for display.

        Args:
            reminders: List of Reminder objects to format
            include_user: If True, include user mention in each reminder line

        Returns:
            Formatted string with all reminders
        """
        response = ""
        for i, reminder in enumerate(reminders, 1):
            time_str = self.format_remind_time(reminder.remind_time)
            if include_user:
                response += f"{i}. <@{reminder.user_id}> - {time_str}"
            else:
                response += f"{i}. {time_str}"
            if reminder.message:
                response += f"\n   > {reminder.message}"
            response += "\n\n"
        return response

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
        await ctx.defer()
        logging.info(f"Remind me called with time: {time}, message: {message}")
        reminder_datetime = parse_utc_datetime(time)
        if reminder_datetime < utc_now():
            raise Exception("Parsed time is in the past")

        reminder = Reminder(
            user_id=str(ctx.author.id),
            guild_id=str(ctx.guild_id),
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

        await ctx.followup.send(response_message)

    @remind_me.error
    async def remindme_error(self, ctx, error):
        logging.error(f"Remindme Error: {error}")
        # Handle InvokeError wrapping the actual exception
        original_error = getattr(error, "original", error)
        await ctx.respond(f"Sorry, couldn't process reminder: {original_error}", ephemeral=True)

    @slash_command(description="List your active reminders in this server")
    async def my_reminders(self, ctx):
        await ctx.defer(ephemeral=True)
        logging.info(f"List reminders called by user: {ctx.author.id} in guild: {ctx.guild_id}")

        async for session in get_session():
            stmt = (
                select(Reminder)
                .where(Reminder.user_id == str(ctx.author.id))
                .where(Reminder.guild_id == str(ctx.guild_id))
                .order_by(Reminder.remind_time)
            )
            result = await session.exec(stmt)
            reminders = result.all()

        if not reminders:
            await ctx.followup.send("You have no active reminders in this server.", ephemeral=True)
            return

        response = f"**Your Active Reminders in This Server ({len(reminders)}):**\n\n"
        response += self.format_reminders_list(reminders, include_user=False)

        await ctx.followup.send(response, ephemeral=True)

    @slash_command(description="List all active reminders in this server")
    async def all_reminders(self, ctx):
        await ctx.defer()
        logging.info(f"Server reminders called by user: {ctx.author.id} in guild: {ctx.guild_id}")

        async for session in get_session():
            stmt = select(Reminder).where(Reminder.guild_id == str(ctx.guild_id)).order_by(Reminder.remind_time)
            result = await session.exec(stmt)
            reminders = result.all()

        if not reminders:
            await ctx.followup.send("There are no active reminders in this server.")
            return

        response = f"**All Active Reminders in This Server ({len(reminders)}):**\n\n"
        response += self.format_reminders_list(reminders, include_user=True)

        await ctx.followup.send(response)


def setup(bot):
    bot.add_cog(Reminders(bot))
