
import os
import logging
from dotenv import load_dotenv
import discord
from quart import Quart, render_template, request, session, redirect, url_for
from quart_discord import DiscordOAuth2Session
from quart import Quart
from discord.ext.ipc.client import Client
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
import mysql.connector
import json
import ast

load_dotenv()
logging.basicConfig(level=logging.INFO)

#Setup vars
callbackurl = os.getenv('CALLBACK')
#port = os.getenv('PORT')
sqluser = os.getenv('MYSQL_USER')
sqlpass = os.getenv('MYSQL_PASS')
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
TOKEN = os.getenv('DISCORD_TOKEN')
discord_cl_id = os.getenv('DISCORD_CLIENT_ID')
discord_cl_secret = os.getenv('DISCORD_CLIENT_SECRET')
discord_redirect_uri = os.getenv('DISCORD_CLIENT_REDIRECT_URL')
add_bot_url = os.getenv('DISCORD_URL')
spotify_scope = 'playlist-modify-public'
intents = discord.Intents.all()

#Setup Quart
app = Quart(__name__)
app.config["SECRET_KEY"] = "test123"
app.config["DISCORD_CLIENT_ID"] = discord_cl_id
app.config["DISCORD_CLIENT_SECRET"] = discord_cl_secret
app.config["DISCORD_REDIRECT_URI"] = discord_redirect_uri
ipc_client = Client(secret_key = "test")
ddiscord = DiscordOAuth2Session(app)



def convert_ipc_response(ipc_response):
	data = ipc_response.response
	elements = data.replace("[", "").replace("]", "").split(",")
	return [str(element) for element in elements]

def check_guild_admin(user_guilds, target_guild):
	for guild in user_guilds:
		if guild.permissions.administrator:
			print(f"you are an admin of this guild: {guild} with id {guild.id}, trying to see if you are admin of {target_guild}")
			if str(guild.id) == str(target_guild):
				return True, guild

	return False, None

async def check_bot_exists(guild_id):
	attempted_guild = await ipc_client.request("get_gld", guild_id = guild_id)
	if (attempted_guild.response == None) : 
		print("This guild does not have the bot running")
		return False
	else:
		print("This guild has the bot running")
		return True
	
def query_db(sql_string):
	if sql_string == None:
		print("empty string, no query")
		return None
	if not (sql_string.startswith("SELECT") or sql_string.startswith("select")):
		print("Didn't start with select")
		return None
	
	try:
		mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
		cursor = mydb.cursor()
	except Exception as e:
		logging.error(f'error connecting to Mysql DB error: {e}')

	cursor.execute(sql_string)
	out = cursor.fetchall()

	cursor.close()
	mydb.close()
	return out

def GetPlaylistID(username, playname, spotify_obj):
	playid = ''
	playlists = spotify_obj.user_playlists(username)
	for playlist in playlists['items']:  # iterate through playlists I follow
		if playlist['name'] == playname:  # filter for newly created playlist
			playid = playlist['id']
	return playid


#Quart endpoints

@app.route("/")
async def home():
	# resp = await ipc_client.request("get_guild_data")
	authorized = await ddiscord.authorized

	# print(query_db("SELECT * from guilds"))
	# print(resp)
	# print(str(resp.response))

	if authorized:
		return await render_template("index.html", authorized = await ddiscord.authorized, username = (await ddiscord.fetch_user()).name)
	
	return await render_template("index.html", authorized = await ddiscord.authorized, username = "none")

@app.route("/instructions")
async def instructions():
	authorized = await ddiscord.authorized

	if authorized:
		return await render_template("instructions.html", authorized = await ddiscord.authorized, username = (await ddiscord.fetch_user()).name)
	
	return await render_template("instructions.html", authorized = await ddiscord.authorized, username = "none")

@app.route("/login")
async def login():
	return await ddiscord.create_session()

@app.route("/logout")
async def logout():
	ddiscord.revoke()
	return redirect(url_for("home"))

@app.route("/callback_D")
async def callback_D():
    print("in callback")
    try:
        await ddiscord.callback()
    except Exception as e:
        print("error")
        print(e)
        pass
    print("trying to redir")
    print(url_for("dashboard"))
    return redirect(url_for("dashboard"))


@app.route("/callback")
async def callback():
	print("IM IN THE CALLBACK")
	print(f"we are acting on GUILD {session.get('acting_guild', 'none')}")
	cache_handler = spotipy.cache_handler.CacheFileHandler(username=session.get('acting_guild', 'none'))
	auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, open_browser=False, show_dialog=True,cache_handler=cache_handler)

	if not ('code' in request.args):
		print("couldn't find code")
		return redirect(url_for('home'))
	

	print("found the code")
	print(request.args.get("code"))

	auth_manager.get_access_token(request.args.get("code"))

	if not auth_manager.validate_token(cache_handler.get_cached_token()):
		print("NOT AUTHED.. REDIRECTING")
		return redirect(url_for('home'))
	
	print(" I think it worked!")
	try:
		sp = spotipy.Spotify(auth_manager=auth_manager)
		print(sp.me())
	except Exception as e:
		print("I made it through the full auth, but I still ran into an issue? It is this:")
		print(e)
		return redirect(url_for('home'))
	
	return redirect(f"/dashboard/{session.get('acting_guild', 'none')}")

	
	

@app.route("/dashboard")
async def dashboard():
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 
	authorized = await ddiscord.authorized
	name = (await ddiscord.fetch_user()).name
	user_guilds = await ddiscord.fetch_guilds()
	guild_count = len(user_guilds)

	guilds = []
	for guild in user_guilds:
		if guild.permissions.administrator:		
			guilds.append(guild)
	
	return await render_template("dashboard.html", guild_count = guild_count, guilds = guilds, username=name, authorized=authorized)


@app.route("/dashboard/<int:guild_id>")
async def dashboard_server(guild_id):
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 
	authorized = await ddiscord.authorized
	name = (await ddiscord.fetch_user()).name
	spot_auth = False
	installed = await check_bot_exists(guild_id)
	user_guilds = await ddiscord.fetch_guilds()
	admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)

	print(f'admin_okay: {admin_okay}')
	if admin_okay != True:
		print(f"Admin check didn't work! How did we get to this URL? The previous page should have listed only servers you're an admin of")
		return ("Not Authorized")

	try:
		cache_handler = spotipy.cache_handler.CacheFileHandler(username=guild_id)
		auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, cache_handler=cache_handler)

		if not cache_handler.get_cached_token() == None:
			print("Found cached token")
			sp = spotipy.Spotify(auth_manager=auth_manager)
			print(sp.me())
			spot_auth = True
		else:
			print("NO CACHED TOKEN!")
		
	except Exception as e:
		print("=========AUTH FAILED!=============")
		print(e)

	channel_names = await ipc_client.request("get_channels", guild_id = guild_id)
	print(f"response from get_channels ipc: {channel_names}. Attempting to eval")
	if channel_names.response == None:
		channel_names = [[0, "None"]]
	else:
		channel_names = ast.literal_eval(channel_names.response)
		

	current_channel_id = (query_db(f"SELECT watch_channel from guilds where guild_id={final_guild.id}"))
	if(current_channel_id == [] or current_channel_id == [(None,)]):
		current_channel_id = "NONE"
		has_channel = False
	else:
		current_channel_id = current_channel_id[0][0]
		has_channel = True

	current_playlist = (query_db(f"SELECT playlist_name from guilds where guild_id={final_guild.id}"))
	if(current_playlist == [] or current_playlist == [(None,)]):
		current_playlist = "NONE"
		has_playlist = False
	else:
		current_playlist = current_playlist[0][0]
		has_playlist = True

	bot_enabled = (query_db(f"SELECT enabled from guilds where guild_id={final_guild.id}"))
	print(f"this is what bot_enabled looks like before: {bot_enabled}")
	if(bot_enabled == [] or bot_enabled == [(None,)]):
		current_playlist = False
		print("Didn't get bot enabled status from DB. This should always exist as a 1 or 0")
	else:
		bot_enabled = bot_enabled[0][0]
	
	if bot_enabled == 1: bot_enabled = True
	else: bot_enabled = False
	

	print(f"this is what bot_enabled looks like: {bot_enabled}")
	
	#resolving channel id taken from DB to text (I should just store the text in the DB)
	print(f"printing current channel {current_channel_id}")
	for channel in channel_names:
		if str(channel[0]) == current_channel_id:
			current_channel_id = channel[1]
			break

	return await render_template("dashboard_specific.html", username=name, guild = final_guild,
	 installed = installed, spot_auth = spot_auth, add_bot_url = add_bot_url, authorized=authorized,
	 channel_names=channel_names, current_channel=current_channel_id, has_channel = has_channel,
	 current_playlist = current_playlist, has_playlist = has_playlist, bot_enabled = bot_enabled)

@app.route("/dashboard/<int:guild_id>/channel")
async def dashboard_channel(guild_id):
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 
	authorized = await ddiscord.authorized
	user_guilds = await ddiscord.fetch_guilds()
	admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)
	name = (await ddiscord.fetch_user()).name

	print(f'admin_okay: {admin_okay}')
	if admin_okay != True:
		print(f"Admin check didn't work! How did we get to this URL? The previous page should have listed only servers you're an admin of")
		return ("Not Authorized")

	channel_names = await ipc_client.request("get_channels", guild_id = guild_id)
	print(f"response from get_channels ipc: {channel_names}. Attempting to eval")
	if channel_names.response == None:
		channel_names = [[0, "None"]]
	else:
		channel_names = ast.literal_eval(channel_names.response)

	current_channel = (query_db(f"SELECT watch_channel from guilds where guild_id={final_guild.id}"))
	print(f"printing current channel {current_channel}")
	if(current_channel == []):
		current_channel = "NONE"
	else:
		current_channel = current_channel[0][0]


	for target_channel in channel_names:
		print(f"0: {target_channel[0]} 1: {target_channel[1]} current_channel: {current_channel}")
		if str(target_channel[0]) == current_channel:
			current_channel = target_channel[1]
			break

	return await render_template("dashboard_channel.html", username=name, guild = final_guild, authorized=authorized, channel_names=channel_names, current_channel=current_channel)


@app.route("/dashboard/<int:guild_id>/playlist", methods=['GET', 'POST'])
async def dashboard_playlist(guild_id):
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 
	authorized = await ddiscord.authorized
	user_guilds = await ddiscord.fetch_guilds()
	admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)
	name = (await ddiscord.fetch_user()).name

	print(f'admin_okay: {admin_okay}')
	if admin_okay != True:
		print(f"Admin check didn't work! How did we get to this URL? The previous page should have listed only servers you're an admin of")
		return ("Not Authorized")
	
	current_playlist = (query_db(f"SELECT playlist_name from guilds where guild_id={final_guild.id}"))
	if(current_playlist == [] or current_playlist == [(None,)]):
		current_playlist = "NONE"
		has_playlist = False
	else:
		current_playlist = current_playlist[0][0]
		has_playlist = True


	if request.method == 'POST':
		input_playlist = (await request.form).get('playlist_input')
		try:
			cache_handler = spotipy.cache_handler.CacheFileHandler(username=guild_id)
			auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, cache_handler=cache_handler)

			if not cache_handler.get_cached_token() == None:
				print("Found cached token")
				sp = spotipy.Spotify(auth_manager=auth_manager)
				print(sp.me())
			else:
				print("NO CACHED TOKEN!")
				return("Could not find your spotify data")
			
		except Exception as e:
			print("=========AUTH FAILED!=============")
			print(e)
			return(f"Found spotify data, but authentication failed for reason {e}")
		
		duplicate = 0
		username = sp.current_user()["id"]
		playlists = sp.user_playlists(username)
		while playlists:
			for i, playlist in enumerate(playlists['items']):
				if playlist['name'] == input_playlist:
					print("playlist already exists in Spotify, will add to it")
					duplicate = 1
					playlist_uri = playlist['uri']
					playlist_title = input_playlist
			if playlists['next']:
				playlists = sp.next(playlists)
			else:
				playlists = None

		if duplicate == 0:
			print("did NOT find playlist, making a new one")
			playlist_title = input_playlist
			username = sp.current_user()["id"]
			sp.user_playlist_create(username, name=playlist_title)
			playlist_uri = GetPlaylistID(username, playlist_title, sp)
		

		mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
		cursor = mydb.cursor()
		sql = "UPDATE guilds set playlist_name = %s, playlist_id = %s where guild_id = %s"
		val = (playlist_title, playlist_uri, guild_id)
		cursor.execute(sql, val)
		mydb.commit()
		cursor.close()
		mydb.close()  

		await ipc_client.request("update_guild_ipc", current_playlist = playlist_title, guild_id = guild_id)

		return await render_template("dashboard_playlistOK.html", username=name, guild = final_guild, authorized=authorized, current_playlist=current_playlist)


	return await render_template("dashboard_playlist.html", username=name, guild = final_guild, authorized=authorized, current_playlist=current_playlist)


# @app.route("/dashboard/<int:guild_id>/toggle")
# async def dashboard_toggle(guild_id):
# 	print("I AM IN HEREIHRIEHRIHERIEHRI")
# 	return ("reached")
@app.route("/dashboard/<int:guild_id>/toggle")
async def dashboard_toggle(guild_id):
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 
	print("I AM IN HEREIHRIEHRIHERIEHRI")
	user_guilds = await ddiscord.fetch_guilds()
	admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)

	print(f'admin_okay: {admin_okay}')
	if admin_okay != True:
		print(f"Admin check didn't work! How did we get to this URL? The previous page should have listed only servers you're an admin of")
		return ("Not Authorized")
	
	bot_enabled = (query_db(f"SELECT enabled from guilds where guild_id={final_guild.id}"))
	print(f"this is what bot_enabled looks like before: {bot_enabled}")
	if(bot_enabled == [] or bot_enabled == [(None,)]):
		bot_enabled = 1
		print("Didn't get bot enabled status from DB. This should always exist as a 1 or 0. Weird.")
	else:
		bot_enabled = bot_enabled[0][0]
	
	#swap the state
	if bot_enabled == 1:
		bot_enabled = 0
	else:
		bot_enabled = 1

	print(f"writing bot enabled to db: {bot_enabled}")
	mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
	cursor = mydb.cursor()
	sql = "UPDATE guilds set enabled = %s where guild_id = %s"
	val = (bot_enabled, guild_id)
	cursor.execute(sql, val)
	mydb.commit()
	cursor.close()
	mydb.close()   

	print("updating guild")
	await ipc_client.request("update_guild_ipc", guild_id = guild_id)

	return redirect(f"/dashboard/{guild_id}")

@app.route("/dashboard/<int:guild_id>/channel/<int:channel_id>")
async def dashboard_channel_set(guild_id, channel_id):
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 

	user_guilds = await ddiscord.fetch_guilds()
	admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)

	print(f'admin_okay: {admin_okay}')
	if admin_okay != True:
		print(f"Admin check didn't work! How did we get to this URL? The previous page should have listed only servers you're an admin of")
		return ("Not Authorized")
	
	mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
	cursor = mydb.cursor()
	sql = "UPDATE guilds set watch_channel = %s where guild_id = %s"
	val = (channel_id, guild_id)
	cursor.execute(sql, val)
	mydb.commit()
	cursor.close()
	mydb.close()   

	await ipc_client.request("update_guild_ipc", guild_id = guild_id)

	return redirect(f"/dashboard/{guild_id}")




@app.route("/dashboard/<int:guild_id>/spotauth")
async def dashboard_spotauth(guild_id):
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 

	user_guilds = await ddiscord.fetch_guilds()
	admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)

	print(f'admin_okay: {admin_okay}')
	if admin_okay != True:
		print(f"Admin check didn't work! How did we get to this URL? The previous page should have listed only servers you're an admin of")
		return ("Not Authorized")
	
	auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, open_browser=False, show_dialog=True)
	auth_url = auth_manager.get_authorize_url()
	session['acting_guild'] = guild_id
	return redirect(auth_url)



@app.route("/dashboard/<int:guild_id>/spotdc")
async def dashboard_spotdc(guild_id):
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 

	user_guilds = await ddiscord.fetch_guilds()
	admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)

	print(f'admin_okay: {admin_okay}')
	if admin_okay != True:
		print(f"Admin check didn't work! How did we get to this URL? The previous page should have listed only servers you're an admin of")
		return ("Not Authorized")
	
	cachefile = (f".cache-{guild_id}")
	try:
		os.remove(cachefile)
		print(f"{cachefile} successfully deleted Spotify data")
	except FileNotFoundError:
		print(f"{cachefile} not found.")
	except Exception as e:
		print(f"Error: {e}")

	return redirect(f"/dashboard/{guild_id}")


#uncomment if not launching from hypercorn directly
# if __name__ == "__main__":
#  	app.run(host='0.0.0.0', port=8080, ssl_context='adhoc', debug=True)
	

