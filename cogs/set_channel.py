import discord
from discord.ext import commands
import logging
import mysql.connector
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth


class set_channel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(brief='Set which text channel to watch for spotify links')
    async def set_channel(self, ctx, *, channel_id):
        id = ctx.message.guild.id
        for index,i in enumerate(self.bot.guild_data):
            if (int(i[0]) == id):
                current_guild = i
                guild_index = index
        
        
        logging.info(f"trying to set guild: {current_guild} channel id to {channel_id}")

        self.bot.guild_data[guild_index][3] = channel_id

        try:
            mydb = mysql.connector.connect(host = "localhost", user = self.bot.sqluser, password = self.bot.sqlpass, database = "discord")
            cursor = mydb.cursor()
        except:
            logging.error(f'error connecting to Mysql DB')

        sql = "UPDATE guilds set watch_channel = %s where guild_id = %s"
        val = (channel_id, current_guild[0])
        cursor.execute(sql, val)
        mydb.commit()
        await ctx.channel.send(f'I have set your watch channel to {self.bot.guild_data[guild_index][3]}')

async def setup(bot):
    await bot.add_cog(set_channel(bot))