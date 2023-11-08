import discord
from discord.ext import commands



class ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong")

async def setup(bot):
    await bot.add_cog(ping(bot))