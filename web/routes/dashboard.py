
import os
from dotenv import load_dotenv
from quart import Quart, Blueprint, render_template, request, session, redirect, url_for
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
from config import ddiscord, app
import mysql.connector
import ast
from utils import is_invited, check_bot_exists, check_guild_admin, ipc_client, query_db

dashboard_bp = Blueprint('dashboard', __name__)

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path)

callbackurl = os.getenv('CALLBACK')
sqluser = os.getenv('MYSQL_USER')
sqlpass = os.getenv('MYSQL_PASS')
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
add_bot_url = os.getenv('DISCORD_URL')
add_bot_url = os.getenv('DISCORD_URL')
spotify_scope = 'playlist-modify-public'

@app.route("/dashboard")
async def dashboard():
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 
	if not is_invited((await ddiscord.fetch_user())):
		return await render_template("not_invited.html")
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