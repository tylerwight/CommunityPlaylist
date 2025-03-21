import discord
from discord.ext import commands
import logging
import mysql.connector
import spotipy
import spotipy.util as util
import re
from spotipy.oauth2 import SpotifyOAuth


class on_ready(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f'{self.bot.user} has connected to Discord!')
        
        try:
            mydb = mysql.connector.connect(host = "localhost", user = self.bot.sqluser, password = self.bot.sqlpass, database = "discord")
            cursor = mydb.cursor()
        except Exception as e:
            logging.error(f'error connecting to Mysql DB error: {e}')

        cursor.execute("SELECT guild_id FROM guilds")
        existing_guilds = cursor.fetchall()

        for guild in self.bot.guilds:
            logging.info(f'Connected to {guild}')
            duplicate = 0

            #Check for guilds in DB
            for x in existing_guilds:
                for y in x:
                    if str(guild.id) in y:
                        duplicate = duplicate + 1
                        logging.info(f"Found guild {guild} in DB. Loading it's information from DB")

                        cursor.execute("SELECT * FROM guilds where guild_id=%s",([y]))
                        records = cursor.fetchall()

                        listed_records = [list(row) for row in records]
                        logging.info(f"Data loaded from DB: {listed_records[0]}")

                        self.bot.guild_data.append(listed_records[0])
            

            #Guild does not exist in DB, create it in the DB
            if (duplicate == 0):
                logging.info("New Guild detected, adding to DB")

                sql = "INSERT INTO guilds (guild_id,name,enabled, spotipy_username) VALUES (%s, %s, %s, %s)"
                val = (str(guild.id),str(guild), 0, "tmp")
                cursor.execute(sql, val)
                mydb.commit()

                logging.info(f'I inserted {cursor.rowcount} rows using {guild.id} and {guild}')

                item = [str(guild.id), str(guild), "tmp", None, 0, None, None]

                self.bot.guild_data.append(item)


            if (duplicate > 1):
                logging.error("Found duplicate guilds in the database? Something is wrong")

        cursor.close()
        mydb.close()      

        logging.info("===========================")
        logging.info(f"All guild data loaded or created:")
        for loadedguild in self.bot.guild_data:
            logging.info(loadedguild)
        logging.info("===========================")   



async def setup(bot):
    await bot.add_cog(on_ready(bot))