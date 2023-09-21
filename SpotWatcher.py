#SpotWatcher.py
#Tyler Wight
#Waits for an event (discord message in this case) and if it has a spotify link it in, it adds it to a given playlist
#Keeps guild data/settings in a mysql database and supports multiple discord servers
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
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)
load_dotenv()

#=============
#Functions
#=============

#convert URI to full spotify link
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

#take an album id and convert it to multiple track uris
def album_to_tracks(album_ids, spotify_obj):
    result1 = []
    final_result = []
    #print(album_ids)
    for ids in album_ids:
        result1.append(spotify_obj.album_tracks(f'{ids}'))
    for item in result1:
        for x in item['items']:
            final_result.append(x['uri'])
    return final_result


def GetPlaylistID(username, playname, spotify_obj):
    playid = ''
    playlists = spotify_obj.user_playlists(username)
    for playlist in playlists['items']:  # iterate through playlists I follow
        if playlist['name'] == playname:  # filter for newly created playlist
            playid = playlist['id']
    return playid

#=============
#DISCORD auth
#=============
intents = discord.Intents.all()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix="_",intents=intents)

#=============
#Spotify auth
#=============
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
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
#Basic Vars and setup
#=============
guild_data = []
logging = 1




#=============
#Flask Functions -- these are unused right
#=============



@app.route('/')
def home():

#    if not auth_manager.validate_token():
#        print("no token")
#    else:
#        print("there is token")
#        #spotify = spotipy.Spotify(auth_manager=auth_manager)
 #       #playlists = spotify.user_playlists(username)
#        print(cache_handler.get_cached_token())



    
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/authed')
def authed():
    return render_template("alreadyauthed.html")

@app.route('/contact')
def contact():


    return "Contact test"

@app.route("/callback")
def callback():
    token_info = auth_manager.get_access_token(request.args["code"])
    new_auth = SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri="http://10.100.1.90:8080/callback", scope=scope, open_browser=True, show_dialog=True, token_info=token_info)
    user_id = "corl45"
    print("printing token info fur shure")
    print(type(token_info))
    print (token_info)
    print(token_info['access_token'])
    print(type(token_info['access_token']))
    spotify = spotipy.Spotify(auth_manager=new_auth)
    print(spotify.current_user())
    
    return redirect('/')

@app.route('/open')
def open():
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)



#=============
#Discord Bot Functions
#=============


#=============
#On Ready
#=============
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    duplicate = 0
    cursor.execute("SELECT guild_id FROM guilds")
    existing_guilds = cursor.fetchall()

    #For every guild (server) the bot is connected to, check if it exists in the database. If it doesn't, add it.
    for guild in bot.guilds:
        print(f'{guild}')
        duplicate = 0

        #Check the database (existing_guilds) and compare to guilds the bot is connected to. If it doesn't exist
        for x in existing_guilds:
            for y in x:
                if str(guild.id) in y:
                    duplicate = duplicate + 1
                    if logging == 1:
                        print("duplicate guild id found!")
                        print("Guild already exists, loading it's information from DB")
                        
                    #get data from DB for existing guild
                    cursor.execute("SELECT * FROM guilds where guild_id=%s",([y]))
                    records = cursor.fetchall()
                    #convert to list because it's a list of tuples by default
                    listed_records = [list(row) for row in records]
                    if logging == 1:
                        print(f"data loaded for guild: {listed_records[0]}")

                    guild_data.append(listed_records[0])

        #Guild does not exist in DB, create it in the DB
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

    print(f"guild_data loaded is {guild_data}")

@bot.event
async def on_guild_join(guild):
    print("===========================")
    print(f'{guild} has  just added the discord bot!!')
    print("===========================")


    duplicate = 0
    cursor.execute("SELECT guild_id FROM guilds")
    existing_guilds = cursor.fetchall()


    for x in existing_guilds:
        for y in x:
            if str(guild.id) in y:
                duplicate = duplicate + 1
                if logging == 1:
                    print("duplicate guild id found!")
                    print("Guild already exists, loading it's information from DB")
                    
                #get data from DB for existing guild
                cursor.execute("SELECT * FROM guilds where guild_id=%s",([y]))
                records = cursor.fetchall()
                #convert to list because it's a list of tuples by default
                listed_records = [list(row) for row in records]
                if logging == 1:
                    print(f"data loaded for guild: {listed_records[0]}")

                guild_data.append(listed_records[0])

    #Guild does not exist in DB, create it in the DB
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


    print("===========================")
    print("===========================")


#=============
#On message
#=============
@bot.event
async def on_message(message):
    #ignore messages from the bot
    if str(message.author.id) == str(bot.user.id):
        return
    
    #get information about the guild this message applies to
    id = message.guild.id
    for i in guild_data:
        if (int(i[0]) == id):
            current_guild = i


    #set Spotify username for auth from guild info/db
    username=current_guild[2]

    if logging==1:
        print(f"Message detected, printing current_guild : {current_guild}")
    
    #vairable setup to search for spotify links
    channel = str(message.channel.id)
    channel_name = bot.get_channel(message.channel.id)
    textSearch = "spotify.com/track"
    textSearch2 = "spotify.com/album"

    #Check if monitoring is enabled for this guild.
    if current_guild[4] != 1:
        print("Guild has bot disabled, skipping...")
        await bot.process_commands(message)
        return

    #Check if the message came from the channel we want to monitor
    if channel != current_guild[3]:
        if logging == 1:
            print("Not the monitored channel for this guild, skipping...")
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


        if logging == 1:
            print("Found this link: ")
            print(extracted)
            print(f"creating auth manager with username {username}")
        
        #try to auth to spotify
        try:
            auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri="http://localhost:8080", scope=scope, open_browser=True, show_dialog=True, username=username)
            spotify = spotipy.Spotify(auth_manager=auth_manager)
            print(spotify.current_user())
        except:
            await channel_name.send(' Found a spotify link, but failed spotify authentication. Did you use auth_me command?')
            return

        if 'spotify.com/album' in extracted[0]:
            if logging == 1:
                print("Album found, adding all tracks")

            
            extracted = album_to_tracks(extracted, spotify)
            resulttrack = ''
            resultartist = ''
        else:
            resulttrack = spotify.track(extracted[0], market=None)
            resultartist = resulttrack['artists'][0]['name']
            resulttrack = resulttrack['name']
        
        if logging == 1:
            print('adding ',resulttrack,' by ',resultartist)

        print(f"attempting to add song to playlist id {current_guild[6]}")
        spotify.user_playlist_add_tracks(username, current_guild[6], extracted )

        await channel_name.send('I have added song ' + resulttrack + ' by ' + resultartist + ' to the playlist ' + current_guild[6] + ': ' + "<" + URIconverter("spotify:playlist:" + current_guild[6]) + ">")



    await bot.process_commands(message)


#=============
#enable command
#=============

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

#=============
#get_playlist command
#=============
@bot.command(brief='show playlist currently being added to')
async def get_playlist(ctx):
    id = ctx.message.guild.id
    for i in guild_data:
        if (int(i[0]) == id):
            current_guild = i

    if current_guild[6] == None:
        await ctx.channel.send("No playlist setup to watch, please use the set_playlist command")
        return

    convert="spotify:playlist:" + current_guild[6]
    output_link=URIconverter(convert)
    await ctx.channel.send("I am currently adding songs to this playlist: " + output_link)


#=============
#set_channel command
#=============

@bot.command(brief='Set which text channel to watch for spotify links')
async def set_channel(ctx, *, channel_id):
    id = ctx.message.guild.id
    for index,i in enumerate(guild_data):
        if (int(i[0]) == id):
            current_guild = i
            guild_index = index
    
    if logging == 1:
        print(f"trying to set guild: {current_guild} channel id to {channel_id}")

    guild_data[guild_index][3] = channel_id
    sql = "UPDATE guilds set watch_channel = %s where guild_id = %s"
    val = (channel_id, current_guild[0])
    cursor.execute(sql, val)
    mydb.commit()


#=============
#auth_me command
#=============
@bot.command(brief='Authenticate your Spotify Account to allow it to create/add to playlists')
async def auth_me(ctx, *, name):
    id = ctx.message.guild.id
    for index,i in enumerate(guild_data):
        if (int(i[0]) == id):
            current_guild = i
            guild_index = index
    
    if logging == 1:
        print(f"trying to auth to spotify with username {name}")

    try:
        auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri="http://localhost:8080", scope=scope, open_browser=True, show_dialog=True, username=name)
    except:
        ctx.channel.send(f" Tried to auth to spotify with user {name} but it failed. Not sure why")
        return

    
    auth_url = auth_manager.get_authorize_url()
    if logging == 1:
        print(f"telling user to go here: {auth_url}")
    await ctx.channel.send(f"You are attempting to authenticate user {name}. Please visit this URL while logged into that account:\n {auth_url} \n Once you click authorize, paste the code below.")
    
    def check(m):
        return m.channel == ctx.message.channel
    
    code = await bot.wait_for('message', check=check)
    if logging == 1:
        print(f"got code return printing content:{code.content}")


    try:
        auth_manager.get_access_token(code.content)
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        current_user = spotify.current_user()
        print(current_user)
    except:
        await ctx.channel.send(f"Failed to authenticate with your access token. Did you grab the right data/code?")
        return

    await ctx.channel.send(f"It worked! I am authenticated with user: {current_user}")
    guild_data[guild_index][2] = name
    sql = "UPDATE guilds set spotipy_username = %s where guild_id = %s"
    val = (name, current_guild[0])
    cursor.execute(sql, val)
    mydb.commit()


#=============
#set_playlist command
#=============
@bot.command(brief='Choose the playlist to add to. Will create a new playlist if none exists or attach to an existing with the same name')
async def set_playlist(ctx , *, name):
    id = ctx.message.guild.id
    for index,i in enumerate(guild_data):
        if (int(i[0]) == id):
            current_guild = i
            guild_index = index   
    
    duplicate = 0

    if current_guild[2] == None:
        await ctx.channel.send(" No spotify user set, did you use auth_me?")
        return

    try:
        username = current_guild[2]
        auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri="http://localhost:8080", scope=scope, open_browser=True, show_dialog=True, username=username)
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        print(spotify.current_user())
    except:
        await ctx.channel.send("failed to auth to Spotify. Did you use auth_me?")
        return


    playlists = spotify.user_playlists(username)
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            if playlist['name'] == name:
                print("playlist name already exists, will add to it")
                duplicate = 1
                guild_data[guild_index][6] = playlist['uri']
                guild_data[guild_index][5] = name
        if playlists['next']:
            playlists = spotify.next(playlists)
        else:
            playlists = None
    
    if duplicate == 0:
        guild_data[guild_index][5] = name
        spotify.user_playlist_create(username, name=guild_data[guild_index][5])
        guild_data[guild_index][6] = GetPlaylistID(username, guild_data[guild_index][5], spotify)
    await ctx.channel.send("Found or created a playlist named: " + str(guild_data[guild_index][5]) + " with id: " + str(guild_data[guild_index][6]))

    guild_data[guild_index][5] = name
    sql = "UPDATE guilds set playlist_name = %s, playlist_id = %s where guild_id = %s"
    val = (name, guild_data[guild_index][6], current_guild[0])
    cursor.execute(sql, val)
    mydb.commit()





if __name__ == '__main__':
    #thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    #thread.start()
    bot.run(TOKEN)


