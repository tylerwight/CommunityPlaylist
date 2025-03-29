import os
import re
import discord
from discord.ext import commands
from typing import Dict
from dotenv import load_dotenv
import logging
import mysql.connector
import json
import community_playlist.db as db


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
            logging.error(f"Trying to update guild {guild_id}, but couldn't find guild connected to bot")
            return None

        guild_id_str = str(guild_id)
        guild_data = db.guild.get_full_guild(guild_id_str)

        if not guild_data:
            logging.warning(f"No DB record found for guild_id {guild_id_str}")
            return None

        self.guilds_state[guild_id_str] = guild_data
        logging.info(f"Updated guild data in memory: {self.guilds_state[guild_id_str]}")

        return None

 
    async def setup_hook(self):
        cog_dir = os.path.join(os.path.dirname(__file__), 'cogs')

        for filename in os.listdir(cog_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                ext = f'community_playlist.bot.cogs.{filename[:-3]}'
                await self.load_extension(ext)
                print(f"Loaded Cog: {ext}")
        

    async def commit_to_db(self, guild_id, columns):
        if not columns:
            logging.warning("commit_to_db: No columns provided for DB update")
            return

        current_guild = await self.get_guild_data(guild_id)
        if not current_guild:
            logging.warning(f"commit_to_db: Guild data not found for {guild_id}")
            return

        values_to_update = {}
        for col in columns:
            if col not in current_guild:
                logging.warning(f"commit_to_db: Unknown or missing column '{col}' in cached guild data.")
                return
            values_to_update[col] = current_guild[col]

        affected = db.guild.update_guild_columns(guild_id, values_to_update)
        if affected == 0:
            logging.warning(f"commit_to_db: No rows affected when updating guild {guild_id}")
