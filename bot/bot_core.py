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
        self.spotify_scope = 'playlist-modify-public'

        self.guilds_state = {} # global state of all guilds (so we don't have to pull from mysql every time we need data)

       


    async def get_guild_data(self, guild_id):
        guild_id_str = str(guild_id)
        guild_data = self.bot.guilds_state.get(guild_id_str)
        if guild_data is None:
            logging.warning(f"Couldn't find global guild data for {guild_id_str}")
            return None

        logging.info(f"Found global guild data for: {guild_id_str}\n\t returning: {guild_data}")
        return guild_data

    async def update_guild(self, guild_id):
        logging.info(f"Reading from DB and updating internal state for guild_id {guild_id}")
        guild_obj = self.get_guild(guild_id)
        logging.info(f"found guild_obj: {guild_obj}")
        if guild_obj is None:
            logging.error(f"trying to update guild {guild_id}, but couldn't find guild connected to bot")
            return None
        
        try:
            mydb = mysql.connector.connect(
                host="localhost",
                user=self.sqluser,
                password=self.sqlpass,
                database="discord"
            )
            cursor = mydb.cursor()
        except Exception as e:
            logging.error(f"Error connecting to MySQL DB: {e}")
            return None

        guild_id_str = str(guild_id)

        try:
            cursor.execute("SELECT * FROM guilds WHERE guild_id=%s", (guild_id_str,))
            record = cursor.fetchone()
            if not record:
                logging.warning(f"No DB record found for guild_id {guild_id_str}")
                return None
            
            #read data from DB into memory
            self.guilds_state[guild_id_str] = {
                "guild_id":         record[0],
                "name":             record[1],
                "spotipy_token":    record[2],
                "watch_channel":    record[3],
                "enabled":          record[4],
                "playlist_name":    record[5],
                "playlist_id":      record[6],
            }

            logging.info(f"Updated guild data in memory: {self.guilds_state[guild_id_str]}")

        except Exception as e:
            logging.error(f"Error during SELECT or dict update: {e}")
        finally:
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


        db_col_map = {
            "name": "name",
            "spotipy_token": "spotipy_token",
            "watch_channel": "watch_channel",
            "enabled": "enabled",
            "playlist_name": "playlist_name",
            "playlist_id": "playlist_id"
        }

        try:
            mydb = mysql.connector.connect(
                host="localhost",
                user=self.sqluser,
                password=self.sqlpass,
                database="discord"
            )
            cursor = mydb.cursor()

            set_clause = ", ".join(f"{db_col_map[col]} = %s" for col in columns)
            values = []

            for col in columns:
                if col not in db_col_map:
                    logging.warning(f"commit_to_db: Unknown column '{col}' requested.")
                    return

                values.append(current_guild[col])

            values.append(str(guild_id))

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