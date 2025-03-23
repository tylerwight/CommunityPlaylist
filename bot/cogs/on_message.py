import discord
from discord.ext import commands
import logging
import mysql.connector
import spotipy
import spotipy.util as util
import re
from spotipy.oauth2 import SpotifyOAuth
from utils import album_to_tracks, URIconverter


class on_message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #  Triggers when any message is sent on any connected guild 
    @commands.Cog.listener()
    async def on_message(self, message):
        #ignore messages from the bot
        if str(message.author.id) == str(self.bot.user.id):
            return
            
        if message.content.startswith("!"):
            return
        
        #get information about the guild this message applies to
        id = message.guild.id
        for i in self.bot.guild_data:
            if (int(i[0]) == id):
                current_guild = i


        #set Spotify username for auth from guild info/db
        username=current_guild[2]

        logging.info(f"Message detected on guild: {current_guild}")
        
        #vairable setup to search for spotify links
        channel = str(message.channel.id)
        channel_name = self.bot.get_channel(message.channel.id)
        textSearch = "spotify.com/track"
        textSearch2 = "spotify.com/album"

        #Check if monitoring is enabled for this guild.
        if current_guild[4] != 1:
            logging.info("Guild has bot disabled, skipping...")
            return

        #Check if the message came from the channel we want to monitor
        if channel != current_guild[3]:
            logging.info("Not the monitored channel for this guild, skipping...")
            return

        #check if data exists for playlist and user



        #if a spotify link is detected
        if message.content.find(textSearch) != -1 or message.content.find(textSearch2) !=-1:
            extracted = []
            extracted.append(re.search("(?P<url>https?://[^\s]+)", message.content).group("url"))

            logging.info("Found this link: ")
            logging.info(extracted)
            logging.info(f"creating auth manager with username {username}")
            
            #try to auth to spotify
            try:
                logging.info(f"ON_MESSAGE: trying to auth to spotify with:")

                cache_handler = spotipy.cache_handler.CacheFileHandler(username=current_guild[0])
                auth_manager=SpotifyOAuth(client_id=self.bot.spotify_cid, client_secret=self.bot.spotify_secret, redirect_uri=self.bot.callbackurl, scope=self.bot.spotify_scope, cache_handler=cache_handler)

                #auth_manager=SpotifyOAuth(client_id=self.spotify_cid, client_secret=self.spotify_secret, redirect_uri=self.callbackurl, scope=self.spotify_scope, open_browser=True, show_dialog=True,cache_handler=cache_handler)
                
                if not cache_handler.get_cached_token() == None:
                    print("Found cached token")
                    spotify = spotipy.Spotify(auth_manager=auth_manager)
                    print(spotify.me())
                else:
                    print("NO CACHED TOKEN!")
                    await channel_name.send(' Found a spotify link, but failed spotify authentication. Please login to the website and check that you are authenticated to Spotify?')
                    return

                #spotify = spotipy.Spotify(auth_manager=auth_manager)
                logging.info("Trying to print spotify connection:")
                logging.info(spotify.current_user())
            except:
                await channel_name.send(' Found a spotify link, but failed spotify authentication. Please login to the website and check that you are authenticated to Spotify?')
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
            await channel_name.send(f"I have added the song {resulttrack} by {resultartist} to this playlist: <{URIconverter('spotify:playlist:' + current_guild[6])}>")





async def setup(bot):
    await bot.add_cog(on_message(bot))