import os
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
import time
import asyncio
from flask import Flask, render_template, request, redirect, session
#from flask_session import Session
import threading
from random import randint
import mysql.connector
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class SpotWatcher(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callbackurl = kwargs.pop('callbackurl', 'http://localhost:8080/')
        self.flaskport = kwargs.pop('flaskport', '8080')
        self.sqluser = kwargs.pop('sqluser', 'root')
        self.sqlpass = kwargs.pop('sqlpass', None)
        self.spotify_cid = kwargs.pop('spotify_cid', None)
        self.spotify_secret = kwargs.pop('spotify_secret', None)
        

        self.guild_data = []
        self.spotify_scope = 'playlist-modify-public'

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


    #=============
    #On Ready
    #=============
    async def on_ready(self):
        logging.info(f'{self.user} has connected to Discord!')
        
        try:
            mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
            cursor = mydb.cursor()
        except:
            logging.error(f'error connecting to Mysql DB')

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

                    selfguild_data.append(listed_records[0]) 

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
            await bot.process_commands(message)
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
                auth_manager=SpotifyOAuth(client_id=self.spotify_cid, client_secret=self.spotify_secret, redirect_uri=self.callbackurl, scope=self.spotify_scope, open_browser=True, show_dialog=True, username=username)
                spotify = spotipy.Spotify(auth_manager=auth_manager)
                logging.info("Trying to print spotify connection:")
                logging.info(spotify.current_user())
            except:
                await channel_name.send(' Found a spotify link, but failed spotify authentication. Did you use auth_me command?')
                logging.error("Could not authenticate to spotify")
                return

            if 'spotify.com/album' in extracted[0]:
                logging.info("Album found, adding all tracks")

                
                extracted = album_to_tracks(extracted, spotify)
                resulttrack = ''
                resultartist = ''
            else:
                resulttrack = spotify.track(extracted[0], market=None)
                resultartist = resulttrack['artists'][0]['name']
                resulttrack = resulttrack['name']
            
            
            logging.info(f'adding {resulttrack} by {resultartist}')

            logging.info(f"attempting to add song to playlist id {current_guild[6]}")
            spotify.user_playlist_add_tracks(username, current_guild[6], extracted )

            await channel_name.send('I have added song ' + resulttrack + ' by ' + resultartist + ' to the playlist ' + current_guild[6] + ': ' + "<" + SpotWatcher.URIconverter("spotify:playlist:" + current_guild[6]) + ">")



        await bot.process_commands(message)






if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    load_dotenv()

    callbackurl = os.getenv('CALLBACK')
    port = os.getenv('PORT')
    sqluser = os.getenv('MYSQL_USER')
    sqlpass = os.getenv('MYSQL_PASS')
    cid = os.getenv('SPOTIPY_CLIENT_ID')
    secret = os.getenv('SPOTIPY_CLIENT_SECRET')

    intents = discord.Intents.all()
    bot = SpotWatcher(command_prefix="!",intents=intents, callbackurl=callbackurl, flaskport=port, sqluser=sqluser, sqlpass=sqlpass, spotify_cid=cid, spotify_secret=secret)

#        self.spotify_cid = kwargs.pop('spotify_cid', None)
#        self.spotify_secret = kwargs.pop('spotify_secret', None)
        


    TOKEN = os.getenv('DISCORD_TOKEN')
    bot.run(TOKEN)