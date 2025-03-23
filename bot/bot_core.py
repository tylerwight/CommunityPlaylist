import os
import re
import discord
from discord.ext import commands
from typing import Dict
from dotenv import load_dotenv
import logging
import mysql.connector
import json


class CommunityPlaylistBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callbackurl = kwargs.pop('callbackurl', 'http://localhost:8080/')
        self.flaskport = kwargs.pop('flaskport', '8080')
        self.sqluser = kwargs.pop('sqluser', 'root')
        self.sqlpass = kwargs.pop('sqlpass', None)
        self.spotify_cid = kwargs.pop('spotify_cid', None)
        self.spotify_secret = kwargs.pop('spotify_secret', None)


        #self.guild_data = [] #State of the guilds in memory {guild_id, name, Spotipy_username, watch_channel, enabled, playlist_name, playlist_id}
        self.guilds_state = {} # global state of all guilds (so we don't have to pull from mysql every time we need data)
        self.idx_guild_id = 0 #index id of guild_data to make more readable (probably should just use a dict)
        self.idx_guild_name = 1
        self.idx_spot_username = 2
        self.idx_watch_channel = 3
        self.idx_enabled = 4
        self.idx_playlist_name = 5
        self.idx_playlist_id = 6

        self.spotify_scope = 'playlist-modify-public'


    async def get_guild_data(self, guild_id):
        for guild in self.guild_data:
            if guild[self.idx_guild_id] == guild_id:
                logging.info(f"Found global guild data for:{guild_id}\n\t returning: {guild}")
                return guild
        logging.warning(f"couldn't find global guild data for {guild_id}")
        return None


    async def update_guild(self, guild_id):
        logging.info(f"Reading from DB and updating internal state")
        guild = self.get_guild(guild_id)
        if guild is None: return None

        try:
            mydb = mysql.connector.connect(host = "localhost", user = self.sqluser, password = self.sqlpass, database = "discord")
            cursor = mydb.cursor()
        except Exception as e:
            logging.error(f'Error connecting to Mysql DB error: {e}')


        for x in self.guild_data:
            if x[self.idx_guild_id] == str(guild.id):
                cursor.execute("SELECT * FROM guilds where guild_id=%s",([x[0]]))
                record = cursor.fetchall()

                logging.debug(f"Trying to update from DB: updating x[0] {x} with this data: {record[0]}")

                x[self.idx_guild_name]    = record[0][self.idx_guild_name]
                x[self.idx_spot_username] = record[0][self.idx_spot_username]
                x[self.idx_watch_channel] = record[0][self.idx_watch_channel]
                x[self.idx_enabled]       = record[0][self.idx_enabled]
                x[self.idx_playlist_name] = record[0][self.idx_playlist_name]
                x[self.idx_playlist_id]   = record[0][self.idx_playlist_id]
                print(x)
        
        cursor.close()
        mydb.close()

        return None

 
    async def setup_hook(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loaded Cog: {filename[:-3]}")
        

    async def commit_to_db(self, guild_id, columns):
        if not columns:
            logging.warning("commit_to_db: No columns provided for DB update")
            return

        current_guild = await self.get_guild_data(guild_id)
        if not current_guild:
            logging.warning(f"commit_to_db: Guild data not found for {guild_id}")
            return

        column_index_map = {
            "name": self.idx_guild_name,
            "spotipy_username": self.idx_spot_username,
            "watch_channel": self.idx_watch_channel,
            "enabled": self.idx_enabled,
            "playlist_name": self.idx_playlist_name,
            "playlist_id": self.idx_playlist_id
        }

        try:
            mydb = mysql.connector.connect(
                host="localhost",
                user=self.sqluser,
                password=self.sqlpass,
                database="discord"
            )
            cursor = mydb.cursor()

            set_clause = ", ".join(f"{col} = %s" for col in columns)
            values = []

            for col in columns:
                if col in column_index_map:
                    values.append(current_guild[column_index_map[col]])
                else:
                    logging.warning(f"commit_to_db: Unknown column '{col}' requested")
                    return

            values.append(guild_id)

            sql = f"UPDATE guilds SET {set_clause} WHERE guild_id = %s"
            logging.info(f"commit_to_db: executing {sql}")
            logging.info(f"\twith values: {values}")
            
            cursor.execute(sql, values)
            mydb.commit()

        except Exception as e:
            logging.error(f"Error committing to DB for guild {guild_id}: {e}")

        finally:
            cursor.close()
            mydb.close()