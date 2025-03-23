import discord
from discord.ext import commands
import mysql.connector
import logging



class enable(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='start watching specified channel')
    async def enable(self, ctx):
        guild_id = str(ctx.message.guild.id)

        #get current guild data in memory
        current_guild = await self.bot.get_guild_data(guild_id)
        if current_guild == None:
            logging.error(f"Couldn't find guild!")
            return
        
        logging.info(f"Enable: working on guild: {current_guild[self.bot.idx_guild_id]}")

        #change global guild data in memory
        if (current_guild[self.bot.idx_enabled] == 0):
            current_guild[self.bot.idx_enabled] = 1
            await ctx.channel.send(f"Enabled and monitoring for guild {current_guild[self.bot.idx_guild_name]}")
        else:
            await ctx.channel.send(f"Disabled and not monitoring for guild {current_guild[self.bot.idx_guild_name]}")
            current_guild[self.bot.idx_enabled] = 0
        
        #have bot commit current guilds enabled status to the DB
        await self.bot.commit_to_db(guild_id, ["enabled"])

async def setup(bot):
    await bot.add_cog(enable(bot))