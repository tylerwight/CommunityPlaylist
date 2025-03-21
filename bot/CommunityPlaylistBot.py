import nest_asyncio
nest_asyncio.apply()
import os
import re
import discord
from discord.ext import commands
from discord.ext.ipc.server import Server
from discord.ext.ipc.objects import ClientPayload
from typing import Dict
from dotenv import load_dotenv
import logging
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
from cogs.ping import ping
import time
import asyncio
import threading
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

        self.ipc = Server(self, secret_key = "test")        

        self.guild_data = []
        self.sp_cred_queue = []
        self.spotify_scope = 'playlist-modify-public'
        self.register_commands()


    async def on_ipc_ready(self):
        print("IPC Server Ready")
    
    async def on_ipc_error(self, endpoint, error):
        print(f"{endpoint} raised {error}")

    async def update_guild(self, guild_id):
        print("=========== MAIN GUILD UPDATE")
        guild = self.get_guild(guild_id)
        if guild is None: return None

        try:
            mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
            cursor = mydb.cursor()
        except Exception as e:
            logging.error(f'error connecting to Mysql DB error: {e}')

        for x in self.guild_data:
            if x[0] == str(guild.id):
                cursor.execute("SELECT * FROM guilds where guild_id=%s",([x[0]]))
                record = cursor.fetchall()
                print(f"trying to update x[0] {x} with this data: {record[0]}")
                x[1] = record[0][1]
                x[2] = record[0][2]
                x[3] = record[0][3]
                x[4] = record[0][4]
                x[5] = record[0][5]
                x[6] = record[0][6]
                print(x)
        cursor.close()
        mydb.close()

        return None


    @Server.route()
    async def get_guild_data(self,data: ClientPayload) -> Dict:
        out = []
        for guild in self.guilds:
            out.append(guild.id)
        print(out)
        out = json.dumps(out)
        print(out)
        return out
    
    @Server.route()
    async def get_gld(self,data: ClientPayload) -> Dict:
        print(f"trying to get guild with this id: {data.guild_id}")
        guild = self.get_guild(data.guild_id)
        
        if guild is None: return None

        print(f'this is the guild we got: {guild}')

        out = {
            "name": str(guild),
            "id": str(guild.id),
            "prefix" : "?"
        }

        out = json.dumps(out)
        print(out)
        return out
    
    @Server.route()
    async def get_channels(self,data: ClientPayload) -> Dict:
        print(f"trying to get channels from guild with this id: {data.guild_id}")
        guild = self.get_guild(data.guild_id)
        if guild is None: return None
        text_channels = guild.text_channels
        text_channels = [(channel.id, channel.name) for channel in text_channels]
            
        print("TEXT CHANNELS LISTED")
        print(text_channels)
        print(json.dumps(text_channels))
        return json.dumps(text_channels)
    
    @Server.route()
    async def update_guild_ipc(self,data: ClientPayload) -> Dict:
        print("============================")
        print(f"trying update from db for guild: {data.guild_id}")
        await self.update_guild(data.guild_id)

        return None


    
    async def setup_hook(self):
        await self.ipc.start()
        for filename in os.listdir('./cogs'):
            if '__init__.py' in filename:
                continue
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loaded Cog: {filename[:-3]}")
            else:
                print("Unable to load pycache folder.")


    def register_commands(self):

        """@self.ipc.route()
        async def get_guild(data):
            guild = self.get_guild(data.guild_id)
            if guild is None: return None

            guild_data = {
                "name": guild.name,
                "id": guild.id,
                "prefix" : "?"
            }

            return guild_data

        @self.ipc.route()
        async def get_guild_ids(data):
            final = []
            for guild in self.guilds:
                final.append(guild.id)
            return final # returns the guild ids to the client
        
        @self.ipc.route()
        async def get_guild_count(data):
            return len(self.guilds)"""








if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path)

    callbackurl = os.getenv('CALLBACK')
    port = os.getenv('PORT')
    sqluser = os.getenv('MYSQL_USER')
    sqlpass = os.getenv('MYSQL_PASS')
    cid = os.getenv('SPOTIPY_CLIENT_ID')
    secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    TOKEN = os.getenv('DISCORD_TOKEN')

    intents = discord.Intents.all()
    bot = CommunityPlaylistBot(command_prefix="!",intents=intents, callbackurl=callbackurl, flaskport=port, sqluser=sqluser, sqlpass=sqlpass, spotify_cid=cid, spotify_secret=secret)
    
    bot.run(TOKEN)

    