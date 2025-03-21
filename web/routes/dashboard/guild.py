
import os
from dotenv import load_dotenv
from quart import Quart, Blueprint, render_template, request, session, redirect, url_for
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
import mysql.connector
import ast
from utils import is_invited, check_bot_exists, check_guild_admin, ipc_client, query_db
from config import ddiscord, app, sqluser, sqlpass, callbackurl, cid, secret, add_bot_url, spotify_scope

dashboard_guild_bp = Blueprint('dashboard_guild', __name__)

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
