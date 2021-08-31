#playlist_updater.py
#Tyler Wight
#Waits for an event (discord message in this case) and if it has a spotify link it in, it adds it to a given playlist
import os
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
import time
load_dotenv()
#=============
#Functions
#=============
def URIconverter(inp):
    if re.search("/track/", inp):
        processed = inp.split('track/')
        uri = "spotify:track:" + processed[-1][0:22]
        #uri = processed[-1][0:22]
        return uri
    elif re.search("/album/", inp):
        processed = inp.split('album/')
        uri = "spotify:album:"+processed[-1][0:22]
        return uri
    elif re.search(":playlist:", inp):
        #user = re.search(':user:(.*):playlist:', inp).group(1)
        processed = inp.split('playlist:')
        #playlist = inp.split('playlist:')
        url = "https://open.spotify.com/playlist/" + processed[-1][0:22]
        return url

def album_to_tracks(album_ids):
    result1 = []
    final_result = []
    #print(album_ids)
    for ids in album_ids:
        result1.append(spotify.album_tracks(f'{ids}'))
    for item in result1:
        for x in item['items']:
            final_result.append(x['uri'])
    return final_result

def flatten_list(inputlist):
    flat_list = []
    for element in inputlist:
        if type(element) is list:
            for item in element:
                flat_list.append(item)
        else:
            flat_list.append(element)
    return flat_list

def GetPlaylistID(username, playname):
    playid = ''
    playlists = spotify.user_playlists(username)
    for playlist in playlists['items']:  # iterate through playlists I follow
        if playlist['name'] == playname:  # filter for newly created playlist
            playid = playlist['id']
    return playid

#=============
#DISCORD auth
#=============
TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client()
bot = commands.Bot(command_prefix="_")

#=============
#Spotify auth
#=============
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
username = os.getenv('SPOTIPY_USERNAME')
scope = 'playlist-modify-public'
auth_test=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri="http://localhost:8080", scope=scope, username=username, open_browser=False)
spottoken = util.prompt_for_user_token(username, scope, client_id=cid, client_secret=secret, redirect_uri="http://localhost:8080", oauth_manager=auth_test)
spotify = spotipy.Spotify(auth=spottoken)


bot.playlist_name = "Discord Playlist"
bot.playlist_id = GetPlaylistID(username, bot.playlist_name)
bot.watch = 0
bot.user_id = '882038663054241822'
bot.watchchannel = '578243936078790659'
debug = 0





@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        print(f'{guild}')

@bot.event
async def on_message(message):
    #ignore messages from the bot
    if str(message.author.id) == str(bot.user_id):
        
        return

    channel = str(message.channel.id)
    channel_name = bot.get_channel(message.channel.id)
    
    textSearch = "spotify.com/track"
    textSearch2 = "spotify.com/album"
    print("watchchannel / channel",bot.watchchannel,channel)
    if bot.watch == 1:
        if channel == bot.watchchannel:
            if message.content.find(textSearch) != -1 or message.content.find(textSearch2) !=-1:
                extracted = []
                extracted.append(re.search("(?P<url>https?://[^\s]+)", message.content).group("url"))
                print("matched with")
                print(extracted)
                if debug == 0:
                    spotify.user_playlist_add_tracks(username, bot.playlist_id, extracted )
                    if 'spotify.com/album' in extracted[0]:
                        print("this is an album")
                        resulttrack = ''
                        resultartist = ''
                    else:
                        resulttrack = spotify.track(extracted[0], market=None)
                        print(resulttrack['name'])
                        print(resulttrack['artists'][0]['name'])
                        resultartist = resulttrack['artists'][0]['name']
                        resulttrack = resulttrack['name']
                    await channel_name.send('I have added song ' + resulttrack + ' by ' + resultartist + ' to the playlist: ' + bot.playlist_name + ' with id: ' + bot.playlist_id)

    else:
        print("not watching")

    await bot.process_commands(message)


@bot.command(brief='start watching specified channel')
async def watch_channel(ctx):
    if bot.watch == 0:
        bot.watch = 1
        await ctx.channel.send("I am now watching the text channel specified in code for spotify links")
    else:
        bot.watch = 0
        await ctx.channel.send("I am no longer watching a text channel")

@bot.command(brief='print playlist currently uploading to')
async def get_playlist(ctx):
    convert="spotify:playlist:" + bot.playlist_id
    output_link=URIconverter(convert)
    await ctx.channel.send(" I am currently adding songs to this playlist: " + output_link)


@bot.command(brief='param: name. Will create a new playlist if none exists or attach to an existing with the same name')
async def setplaylist(ctx , *, name):
    duplicate = 0
    playlists = spotify.user_playlists(username)
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            #print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'], playlist['name']))
            if playlist['name'] == name:
                print("playlist name already exists, will add to it")
                duplicate = 1
                bot.playlist_id = playlist['uri']
                bot.playlist_name = name
        if playlists['next']:
            playlists = spotify.next(playlists)
        else:
            playlists = None
    if duplicate == 0:
        bot.playlist_name = name
        spotify.user_playlist_create(username, name=bot.playlist_name)
        bot.playlist_id = GetPlaylistID(username, bot.playlist_name)
    await ctx.channel.send("Found or created a playlist named: " + str(bot.playlist_name) + " with id: " + str(bot.playlist_id))



bot.run(TOKEN)

