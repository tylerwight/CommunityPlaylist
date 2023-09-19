#SpotWatcher.py
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
import asyncio
from flask import Flask, render_template, request
import threading

app = Flask(__name__)
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
intents = discord.Intents.all()
TOKEN = os.getenv('DISCORD_TOKEN')
#client = discord.Client()
bot = commands.Bot(command_prefix="_",intents=intents)

#=============
#Spotify auth
#=============
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
username = os.getenv('SPOTIPY_USERNAME')
scope = 'playlist-modify-public'


#=============
#Flask Functions
#=============
@app.route('/')
def home():
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return "Contact test"


@app.route('/open')
def open():
    return "Done"





spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri="http://localhost:8080", scope=scope, username=username, open_browser=False))
print(spotify)
#print("first token: ", spottoken)

# Default playlist name on init. This can be changed by bot command
bot.playlist_name = "pump_jams"
bot.playlist_id = GetPlaylistID(username, bot.playlist_name)
bot.watch = 1

# User ID of the bot, this is so the bot doesn't read it's own messages. If this doesn't match the bot user ID, it will see it's playlist messages as something to add.
bot.user_id = '882038663054241822'

#hard-coded channel to watch for links. This much be changed
bot.watchchannel = '578243936078790659' # actual  channel
#bot.watchchannel = '534427957452603402' # test channel
logging = 1





@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        print(f'{guild}')

@bot.event
async def on_message(message):
    #spottoken = util.prompt_for_user_token(username, scope, client_id=cid, client_secret=secret, redirect_uri="http://localhost:8080")
    #spotify = spotipy.Spotify(auth=spottoken)
    
    #ignore messages from the bot
    if str(message.author.id) == str(bot.user_id):
        return

    channel = str(message.channel.id)
    channel_name = bot.get_channel(message.channel.id)
    textSearch = "spotify.com/track"
    textSearch2 = "spotify.com/album"


    if bot.watch != 1:
        if logging == 1:
            print("Not in watch mode, skipping...")
        await bot.process_commands(message)
        return

    if channel != bot.watchchannel:
        if logging == 1:
            print("Not an enabled channel, skipping...")
        await bot.process_commands(message)
        return


    if message.content.find(textSearch) != -1 or message.content.find(textSearch2) !=-1:
        extracted = []
        extracted.append(re.search("(?P<url>https?://[^\s]+)", message.content).group("url"))
        if logging == 1:
            print("Found this link: ")
            print(extracted)
        #
        

        if 'spotify.com/album' in extracted[0]:
            if logging == 1:
                print("Album found, adding all tracks")

            
            extracted = album_to_tracks(extracted)
            #extracted = flatten_list(extracted)
            resulttrack = ''
            resultartist = ''
        else:
            resulttrack = spotify.track(extracted[0], market=None)
            resultartist = resulttrack['artists'][0]['name']
            resulttrack = resulttrack['name']
        
        if logging == 1:
            print('adding ',resulttrack,' by ',resultartist)

        spotify.user_playlist_add_tracks(username, bot.playlist_id, extracted )

        await channel_name.send('I have added song ' + resulttrack + ' by ' + resultartist + ' to the playlist ' + bot.playlist_name + ': ' + "<" + URIconverter("spotify:playlist:" + bot.playlist_id) + ">")
        #print(URIconverter("spotify:playlist:" + bot.playlist_id))
        #await channel_name.send('I have added song ' + resulttrack + ' by ' + resultartist + ' to the playlist ' + bot.playlist_name)



    await bot.process_commands(message)


@bot.command(brief='start watching specified channel')
async def watch_channel(ctx):
    if bot.watch == 0:
        bot.watch = 1
        await ctx.channel.send("I am now watching the text channel specified in code for spotify links")
    else:
        bot.watch = 0
        await ctx.channel.send("I am no longer watching a text channel")

@bot.command(brief='show playlist currently being added to')
async def get_playlist(ctx):
    convert="spotify:playlist:" + bot.playlist_id
    output_link=URIconverter(convert)
    await ctx.channel.send(" I am currently adding songs to this playlist: " + output_link)


@bot.command(brief='Choose the playlist to add to. Will create a new playlist if none exists or attach to an existing with the same name')
async def set_playlist(ctx , *, name):
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




if __name__ == '__main__':
    thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    thread.start()
    bot.run(TOKEN)


