import discord
from discord.ext import commands
from utils import URIconverter



class get_playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='show playlist currently being added to')
    async def get_playlist(self, ctx):
        id = ctx.message.guild.id
        for i in self.bot.guild_data:
            if (int(i[0]) == id):
                current_guild = i

        if current_guild[self.bot.idx_playlist_id] == None:
            await ctx.channel.send("No playlist setup to watch, please use the set_playlist command")
            return

        convert="spotify:playlist:" + current_guild[self.bot.idx_playlist_id]
        output_link=URIconverter(convert)
        await ctx.channel.send("I am currently adding songs to this playlist: " + output_link)

async def setup(bot):
    await bot.add_cog(get_playlist(bot))