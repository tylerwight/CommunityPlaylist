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
from flask import Flask, render_template, request, redirect, session
from flask_session import Session
import threading
from random import randint
import mysql.connector

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
#MYSQL setup
#=============
sqluser = os.getenv('MYSQL_USER')
sqlpass = os.getenv('MYSQL_PASS')
mydb = mysql.connector.connect(
        host = "localhost",
        user = sqluser,
        password = sqlpass,
        database = "discord"
)
cursor = mydb.cursor()

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

guild_data = []

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

    duplicate = 0
    cursor.execute("SELECT guild_id FROM guilds")
    existing_guilds = cursor.fetchall()

    #For every guild (server) the bot is connected to, check if it exists in the database. If it doesn't, add it.
    for guild in bot.guilds:
        print(f'{guild}')
        
        for x in existing_guilds:
            for y in x:
                if str(guild.id) in y:
                    print("duplicate guild id found!")
                    duplicate = duplicate + 1
                    print("Guild already exists, loading it's information")
                    cursor.execute("SELECT * FROM guilds where guild_id=%s",([y]))
                    records = cursor.fetchall()

                    listed_records = [list(row) for row in records]
                    print(f"records is {records}")
                    print(f"listed_records is {listed_records}")
                    guild_data.append(listed_records[0])


                    #print(row)

        if (duplicate == 0):
            print("New Guild detected, adding to DB")
            sql = "INSERT INTO guilds (guild_id,name,enabled) VALUES (%s, %s, %s)"
            val = (str(guild.id),str(guild), 0)
            cursor.execute(sql, val)
            mydb.commit()
            print(f'I inserted {cursor.rowcount} rows using {guild.id} and {guild}')
            print("adding to guild_data")
            item = [str(guild.id), str(guild), None, None, 0, None, None]
            guild_data.append(item)
        
        if (duplicate > 1):
            print("more than one duplicate!? something weird is going on.")

    print("")
    print(f"guild_data is {guild_data}")
    print(f"guild_data is type: {type(guild_data)}")
    for item in guild_data:
        print(f"guild data item: {item}")
        print(f"item type: {type(item)}")
            




@bot.event
async def on_message(message):
    #ignore messages from the bot
    if str(message.author.id) == str(bot.user.id):
        return
    
    id = message.guild.id
    for i in guild_data:
        if (int(i[0]) == id):
            current_guild = i

    print(f"printing current_guild : {current_guild}")
    

    channel = str(message.channel.id)
    channel_name = bot.get_channel(message.channel.id)
    textSearch = "spotify.com/track"
    textSearch2 = "spotify.com/album"

    if current_guild[4] != 1:
        print("Guild has not eanbled bot, skipping...")
        await bot.process_commands(message)
        return


    if channel != current_guild[3]:
        if logging == 1:
            print("Not an enabled channel for this guild, skipping...")
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
async def enable(ctx):
    id = ctx.message.guild.id
    for index,i in enumerate(guild_data):
        if (int(i[0]) == id):
            current_guild = i
            guild_index = index


    if (guild_data[guild_index][4] == 0):
        guild_data[guild_index][4] = 1
        await ctx.channel.send(f"Enabled and monitoring for guild {guild_data[guild_index][1]}")
    else:
        await ctx.channel.send(f"Disabled and not monitoring for guild {guild_data[guild_index][1]}")
        guild_data[guild_index][4] = 0

    sql = "UPDATE guilds set enabled = %s where guild_id = %s"
    val = (guild_data[guild_index][4], guild_data[guild_index][0])
    cursor.execute(sql, val)
    mydb.commit()


@bot.command(brief='show playlist currently being added to')
async def get_playlist(ctx):
    convert="spotify:playlist:" + bot.playlist_id
    output_link=URIconverter(convert)
    await ctx.channel.send(" I am currently adding songs to this playlist: " + output_link)


@bot.command(brief='Set which text channel to watch for spotify links')
async def set_channel(ctx, *, channel_id):
    id = ctx.message.guild.id
    for index,i in enumerate(guild_data):
        if (int(i[0]) == id):
            current_guild = i
            guild_index = index
    
    print(f"trying to set guild: {current_guild} channel id to {channel_id}")
    guild_data[guild_index][3] = channel_id
    sql = "UPDATE guilds set watch_channel = %s where guild_id = %s"
    val = (channel_id, current_guild[0])
    cursor.execute(sql, val)
    mydb.commit()



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
    #thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    #thread.start()
    bot.run(TOKEN)


