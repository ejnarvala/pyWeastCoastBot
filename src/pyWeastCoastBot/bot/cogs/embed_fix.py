import logging

import discord
from discord import Option, slash_command
from discord.ext import commands

from pyWeastCoastBot.lib.embed_fix.fixer import fix_links, fix_url


class EmbedFix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Fix a social media link so it embeds properly")
    async def fixembed(self, ctx, url: Option(str, "The link to fix")):
        fixed = fix_url(url)
        if not fixed:
            await ctx.respond("That link isn't from a site I can fix.", ephemeral=True)
            return
        await ctx.respond(fixed)

    @discord.message_command(name="Fix Embed")
    async def fix_embed_context(self, ctx, message: discord.Message):
        # Interaction commands receive message content without the Message Content
        # privileged intent, which is why this route works while a passive
        # on_message listener would not.
        fixed = fix_links(message.content)
        if not fixed:
            await ctx.respond("No fixable links found in that message.", ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        # Post the fixed link(s) as a reply so it threads under the original.
        try:
            await message.reply("\n".join(fixed), mention_author=False)
        except discord.Forbidden:
            await ctx.followup.send("I don't have permission to post in this channel.", ephemeral=True)
            return

        # Best-effort: hide the original's broken preview. Requires Manage Messages;
        # skip quietly if we can't (the fixed reply still stands on its own).
        try:
            await message.edit(suppress=True)
        except discord.Forbidden:
            pass

        await ctx.followup.send("Fixed ✅", ephemeral=True)

    @fixembed.error
    async def fixembed_error(self, ctx, error):
        logging.error(f"EmbedFix Error: {error}")
        await ctx.respond("Something went wrong fixing that link.", ephemeral=True)


def setup(bot):
    bot.add_cog(EmbedFix(bot))
