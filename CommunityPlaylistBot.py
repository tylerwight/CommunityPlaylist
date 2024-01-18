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
#from flask import Flask, render_template, request, redirect, session
#from flask_session import Session
import threading
from random import randint
import mysql.connector
#from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
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

    @staticmethod
    def album_to_tracks(album_ids, spotify_obj):
        result1 = []
        final_result = []
        for ids in album_ids:
            result1.append(spotify_obj.album_tracks(f'{ids}'))
        for item in result1:
            for x in item['items']:
                final_result.append(x['uri'])
        return final_result
    
    @staticmethod
    def URIconverter(inp):
        if re.search("/track/", inp):
            processed = inp.split('track/')
            uri = "spotify:track:" + processed[-1][0:22]
            return uri
        elif re.search("/album/", inp):
            processed = inp.split('album/')
            uri = "spotify:album:"+processed[-1][0:22]
            return uri
        elif re.search(":playlist:", inp):
            processed = inp.split('playlist:')
            url = "https://open.spotify.com/playlist/" + processed[-1][0:22]
            return url
        
    @staticmethod
    def GetPlaylistID(username, playname, spotify_obj):
        playid = ''
        playlists = spotify_obj.user_playlists(username)
        for playlist in playlists['items']:  # iterate through playlists I follow
            if playlist['name'] == playname:  # filter for newly created playlist
                playid = playlist['id']
        return playid


    async def send_message(self, message, id):
        channel = self.get_channel(id)
        await channel.send(message)

    async def on_ipc_ready(self):
        print("IPC Server Ready")
    
    async def on_ipc_error(self, endpoint, error):
        print(f"{endpoint} raised {error}")

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

    
    async def setup_hook(self):
        await self.ipc.start()
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loaded Cog: {filename[:-3]}")
            else:
                print("Unable to load pycache folder.")

    #=============
    #On Ready
    #=============
    async def on_ready(self):
        logging.info(f'{self.user} has connected to Discord!')
        
        try:
            mydb = mysql.connector.connect(host = "localhost", user = self.sqluser, password = self.sqlpass, database = "discord")
            cursor = mydb.cursor()
        except Exception as e:
            logging.error(f'error connecting to Mysql DB error: {e}')

        cursor.execute("SELECT guild_id FROM guilds")
        existing_guilds = cursor.fetchall()

        for guild in self.guilds:
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

                        self.guild_data.append(listed_records[0])
            

            #Guild does not exist in DB, create it in the DB
            if (duplicate == 0):
                logging.info("New Guild detected, adding to DB")

                sql = "INSERT INTO guilds (guild_id,name,enabled) VALUES (%s, %s, %s)"
                val = (str(guild.id),str(guild), 0)
                cursor.execute(sql, val)
                mydb.commit()

                logging.info(f'I inserted {cursor.rowcount} rows using {guild.id} and {guild}')

                item = [str(guild.id), str(guild), None, None, 0, None, None]

                self.guild_data.append(item)


            if (duplicate > 1):
                logging.error("Found duplicate guilds in the database? Something is wrong")

        cursor.close()
        mydb.close()      

        logging.info("===========================")
        logging.info(f"All guild data loaded or created:")
        for loadedguild in self.guild_data:
            logging.info(loadedguild)
        logging.info("===========================")

       
    #=============
    #On Guild Join
    #=============

    async def on_guild_join(self, guild):
        logging.info('===========================')
        logging.info(f'{guild} has  just added the discord bot!!')
        logging.info('===========================')

        try:
            mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
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

                    self.guild_data.append(listed_records[0]) 

        #Guild does not exist in DB, create it in the DB
        if (duplicate == 0):
            logging.info("New Guild detected, adding to DB")

            sql = "INSERT INTO guilds (guild_id,name,enabled) VALUES (%s, %s, %s)"
            val = (str(guild.id),str(guild), 0)
            cursor.execute(sql, val)
            mydb.commit()

            logging.info(f'I inserted {cursor.rowcount} rows using {guild.id} and {guild}')

            item = [str(guild.id), str(guild), None, None, 0, None, None]
            self.guild_data.append(item)
        
        if (duplicate > 1):
            logging.info("Found duplicate guilds in the database? Something is wrong")
        

        cursor.close()
        mydb.close()      

    #=============
    #On message
    #=============
    async def on_message(self, message):
        #ignore messages from the bot
        if str(message.author.id) == str(self.user.id):
            return
        
        #get information about the guild this message applies to
        id = message.guild.id
        for i in self.guild_data:
            if (int(i[0]) == id):
                current_guild = i


        #set Spotify username for auth from guild info/db
        username=current_guild[2]

        logging.info(f"Message detected on guild: {current_guild}")
        
        #vairable setup to search for spotify links
        channel = str(message.channel.id)
        channel_name = self.get_channel(message.channel.id)
        textSearch = "spotify.com/track"
        textSearch2 = "spotify.com/album"

        #Check if monitoring is enabled for this guild.
        if current_guild[4] != 1:
            logging.info("Guild has bot disabled, skipping...")
            await self.process_commands(message)
            return

        #Check if the message came from the channel we want to monitor
        if channel != current_guild[3]:
            logging.info("Not the monitored channel for this guild, skipping...")
            await self.process_commands(message)
            return

        #check if data exists for playlist and user



        #if a spotify link is detected
        if message.content.find(textSearch) != -1 or message.content.find(textSearch2) !=-1:
            extracted = []
            extracted.append(re.search("(?P<url>https?://[^\s]+)", message.content).group("url"))

            if current_guild[2] == None:
                await channel_name.send('There is no spotify user setup to use. Please use the auth_me command')
                return
            if current_guild[5] == None:
                await channel_name.send('There is no playlist setup to use. Please use the set_playlist command')
                return

            logging.info("Found this link: ")
            logging.info(extracted)
            logging.info(f"creating auth manager with username {username}")
            
            #try to auth to spotify
            try:
                cache_handler = spotipy.cache_handler.CacheFileHandler(username=current_guild[0])
                auth_manager=SpotifyOAuth(client_id=self.spotify_cid, client_secret=self.spotify_secret, redirect_uri=self.callbackurl, scope=self.spotify_scope, cache_handler=cache_handler)

                #auth_manager=SpotifyOAuth(client_id=self.spotify_cid, client_secret=self.spotify_secret, redirect_uri=self.callbackurl, scope=self.spotify_scope, open_browser=True, show_dialog=True,cache_handler=cache_handler)
                
                if not cache_handler.get_cached_token() == None:
                    print("Found cached token")
                    spotify = spotipy.Spotify(auth_manager=auth_manager)
                    print(spotify.me())
                else:
                    print("NO CACHED TOKEN!")

                #spotify = spotipy.Spotify(auth_manager=auth_manager)
                logging.info("Trying to print spotify connection:")
                logging.info(spotify.current_user())
            except:
                await channel_name.send(' Found a spotify link, but failed spotify authentication. Please login to the website and check that you are authenticated to Spotify?')
                logging.error("Could not authenticate to spotify")
                return

            if 'spotify.com/album' in extracted[0]:
                logging.info("Album found, adding all tracks")

                
                extracted = self.album_to_tracks(extracted, spotify)
                resulttrack = ''
                resultartist = ''
            else:
                resulttrack = spotify.track(extracted[0], market=None)
                resultartist = resulttrack['artists'][0]['name']
                resulttrack = resulttrack['name']
            
            
            logging.info(f'adding {resulttrack} by {resultartist}')

            logging.info(f"attempting to add song to playlist id {current_guild[6]}")
            spotify.user_playlist_add_tracks(username, current_guild[6], extracted )

            await channel_name.send('I have added song ' + resulttrack + ' by ' + resultartist + ' to the playlist ' + current_guild[6] + ': ' + "<" + self.URIconverter("spotify:playlist:" + current_guild[6]) + ">")



        await self.process_commands(message)

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





        @self.command(brief='Authenticate your Spotify Account to allow it to create/add to playlists')
        async def auth_me(ctx, *, name):
            id = ctx.message.guild.id
            for index,i in enumerate(self.guild_data):
                if (int(i[0]) == id):
                    current_guild = i
                    guild_index = index
            
            self.guild_data[guild_index][2] = name

            try:
                mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
                cursor = mydb.cursor()
            except:
                logging.error(f'error connecting to Mysql DB')

            sql = "UPDATE guilds set spotipy_username = %s where guild_id = %s"
            val = (name, current_guild[0])
            cursor.execute(sql, val)
            mydb.commit()

            logging.info(f"trying to auth to spotify with username {name}")

            try:
                auth_manager=SpotifyOAuth(client_id=self.spotify_cid, client_secret=self.spotify_secret, redirect_uri=self.callbackurl, scope=self.spotify_scope, open_browser=True, show_dialog=True, username=name)
            except:
                ctx.channel.send(f" Tried to auth to spotify with user {name} but it failed. Not sure why")
                return

            
            auth_url = auth_manager.get_authorize_url()
            logging.info(f"telling user to go here: {auth_url}")
            await ctx.channel.send(f"You are attempting to authenticate Spotify user {name}. Please visit this URL while logged into that account:\n {auth_url}")
            self.sp_cred_queue.append(name)






if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    load_dotenv()

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

    