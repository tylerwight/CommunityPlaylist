import discord
from discord.ext import commands
import mysql.connector
import logging



class enable(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='start watching specified channel')
    async def enable(self, ctx):
        id = ctx.message.guild.id
        for index,i in enumerate(self.bot.guild_data):
            if (int(i[0]) == id):
                current_guild = i
                guild_index = index


        if (self.bot.guild_data[guild_index][4] == 0):
            self.bot.guild_data[guild_index][4] = 1
            await ctx.channel.send(f"Enabled and monitoring for guild {self.bot.guild_data[guild_index][1]}")
        else:
            await ctx.channel.send(f"Disabled and not monitoring for guild {self.bot.guild_data[guild_index][1]}")
            self.bot.guild_data[guild_index][4] = 0

        try:
            mydb = mysql.connector.connect(host = "localhost", user = self.bot.sqluser, password = self.bot.sqlpass, database = "discord")
            cursor = mydb.cursor()
        except:
            logging.error(f'error connecting to Mysql DB')

        sql = "UPDATE guilds set enabled = %s where guild_id = %s"
        val = (self.bot.guild_data[guild_index][4], self.bot.guild_data[guild_index][0])
        cursor.execute(sql, val)
        mydb.commit()
        cursor.close()
        mydb.close()

async def setup(bot):
    await bot.add_cog(enable(bot))