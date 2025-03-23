import discord
from discord.ext import commands
from utils import URIconverter


class get_playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Show the playlist currently being added to')
    async def get_playlist(self, ctx):
        guild_id = str(ctx.guild.id) 
        current_guild = self.bot.guilds_state.get(guild_id)

        if not current_guild:
            await ctx.send("Bot doesn't regonize this guild, something is very wrong.")
            logging.error(f"get_playlist: Guild {guild_id} not found in guilds_state.")
            return

        playlist_id = current_guild["playlist_id"]
        if not playlist_id:
            await ctx.send("No playlist is set, loging to webiste to set this up.")
            return

        convert = "spotify:playlist:" + playlist_id
        output_link = URIconverter(convert)
        await ctx.send("The current Community Playlist is: " + output_link)

async def setup(bot):
    await bot.add_cog(get_playlist(bot))