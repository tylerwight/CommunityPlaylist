import discord
from discord.ext import commands
import logging
import mysql.connector
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth


class set_playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Choose the playlist to add to. Will create a new playlist if none exists or attach to an existing with the same name')
    async def set_playlist(self, ctx , *, name):
        id = ctx.message.guild.id
        for index,i in enumerate(self.bot.guild_data):
            if (int(i[0]) == id):
                current_guild = i
                guild_index = index   
        
        duplicate = 0

        if current_guild[2] == None:
            await ctx.channel.send(" No spotify user set, did you use auth_me?")
            return

        try:
            username = current_guild[2]
            auth_manager=SpotifyOAuth(client_id=self.bot.spotify_cid, client_secret=self.bot.spotify_secret, redirect_uri=self.bot.callbackurl, scope=self.bot.spotify_scope, open_browser=True, show_dialog=True, username=username)
            spotify = spotipy.Spotify(auth_manager=auth_manager)
            logging.info(f'printing spotify current user: {spotify.current_user()}')
        except Exception as e:
            await ctx.channel.send("failed to auth to Spotify. Did you use auth_me?")
            logging.error(e)
            return


        playlists = spotify.user_playlists(username)
        while playlists:
            for i, playlist in enumerate(playlists['items']):
                if playlist['name'] == name:
                    logging.info("playlist already exists in Spotify, will add to it")
                    duplicate = 1
                    self.bot.guild_data[guild_index][6] = playlist['uri']
                    self.bot.guild_data[guild_index][5] = name
            if playlists['next']:
                playlists = spotify.next(playlists)
            else:
                playlists = None
        
        if duplicate == 0:
            self.bot.guild_data[guild_index][5] = name
            spotify.user_playlist_create(username, name=self.bot.guild_data[guild_index][5])
            self.bot.guild_data[guild_index][6] = self.bot.GetPlaylistID(username, self.bot.guild_data[guild_index][5], spotify)
        await ctx.channel.send("Found or created a playlist named: " + str(self.bot.guild_data[guild_index][5]) + " with id: " + str(self.bot.guild_data[guild_index][6]))

        self.bot.guild_data[guild_index][5] = name

        try:
            mydb = mysql.connector.connect(host = "localhost", user = self.bot.sqluser, password = self.bot.sqlpass, database = "discord")
            cursor = mydb.cursor()
        except:
            logging.error(f'error connecting to Mysql DB')

        sql = "UPDATE guilds set playlist_name = %s, playlist_id = %s where guild_id = %s"
        val = (name, self.bot.guild_data[guild_index][6], current_guild[0])
        try:
            cursor.execute(sql, val)
            mydb.commit()
        except:
            
            logging.error("failed to write set_playlist to DB")

async def setup(bot):
    await bot.add_cog(set_playlist(bot))