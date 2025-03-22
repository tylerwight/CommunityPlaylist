import discord
from discord.ext import commands
import logging
import mysql.connector
import spotipy
import spotipy.util as util
import re
from spotipy.oauth2 import SpotifyOAuth

class on_guild_join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logging.info('===========================')
        logging.info(f'{guild} has  just added the discord bot!!')
        logging.info('===========================')

        try:
            mydb = mysql.connector.connect(host = "localhost", user = self.bot.sqluser, password = self.bot.sqlpass, database = "discord")
            cursor = mydb.cursor()
        except:
            logging.error(f'error connecting to Mysql DB')

        duplicate = 0
        cursor.execute("SELECT guild_id FROM guilds")
        existing_guilds = cursor.fetchall()

        for x in existing_guilds:
            for y in x:
                if str(guild.id) in y:
                    duplicate = duplicate + 1
                    logging.info("This newly joined guild already exists in the DB? Loading it's data")

                    #get data from DB for existing guild
                    cursor.execute("SELECT * FROM guilds where guild_id=%s",([y]))
                    records = cursor.fetchall()
                    #convert to list because it's a list of tuples by default
                    listed_records = [list(row) for row in records]
                    logging.info(f"data loaded for guild: {listed_records[0]}")

                    self.bot.guild_data.append(listed_records[0]) 

        #Guild does not exist in DB, create it in the DB
        if (duplicate == 0):
            logging.info("New Guild detected, adding to DB")

            sql = "INSERT INTO guilds (guild_id,name,enabled) VALUES (%s, %s, %s)"
            val = (str(guild.id),str(guild), 0)
            cursor.execute(sql, val)
            mydb.commit()

            logging.info(f'I inserted {cursor.rowcount} rows using {guild.id} and {guild}')

            item = [str(guild.id), str(guild), 'tmp', None, 0, None, None]
            self.bot.guild_data.append(item)
        
        if (duplicate > 1):
            logging.info("Found duplicate guilds in the database? Something is wrong")
        

        cursor.close()
        mydb.close()      



async def setup(bot):
    await bot.add_cog(on_guild_join(bot))