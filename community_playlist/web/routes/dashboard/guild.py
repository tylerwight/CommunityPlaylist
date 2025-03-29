
from quart import Blueprint, render_template, redirect, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
from community_playlist.web.utils import is_invited, check_bot_exists, check_guild_admin, query_db, bot_api_call
from community_playlist.db.spotipy_handler import CacheSQLHandler
from community_playlist.web.config import ddiscord, app, callbackurl, cid, secret, add_bot_url, spotify_scope, sqluser, sqlpass, enkey

dashboard_guild_bp = Blueprint('dashboard_guild', __name__)

@app.route("/dashboard/<int:guild_id>")
async def dashboard_server(guild_id):
	authorized  = await ddiscord.authorized
	if not authorized:
		logging.info(f'Dashboard/{guild_id}: {admin_okay}')
		return redirect(url_for("login")) 

	user = await ddiscord.fetch_user()
	spot_auth = False
	installed = await check_bot_exists(guild_id)
	user_guilds = await ddiscord.fetch_guilds()
	admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)

	logging.info(f"Dashboard/{guild_id}: User admin status:{admin_okay}")
	if admin_okay != True:
		logging.info(f"Dashboard/{guild_id}: User is NOT an admin of this server. Rejecting.")
		return ("Not Authorized")

	try:
		cache_handler = CacheSQLHandler(cache_where=f"guild_id={guild_id}",
										sqluser=sqluser,
										sqlpass=sqlpass,
										encrypt=True,
										key=enkey)
										
		auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, cache_handler=cache_handler)

		if not cache_handler.get_cached_token() == None:
			logging.info(f"Dashboard/{guild_id}: Found cached Spotify token")
			sp = spotipy.Spotify(auth_manager=auth_manager)
			logging.info(f"Dashboard/{guild_id}: Spotify user: {sp.me()}")
			spot_auth = True
		else:
			logging.info(f"Dashboard/{guild_id}: No cached Spotify token")
		
	except Exception as e:
		logging.error(f"Dashboard/{guild_id}: Spotify auth failed with error: {e}")
		return(f"Found spotify data, but authentication failed with error: {e}")



	response = bot_api_call(endpoint="channels", payload={"guild_id": guild_id}, method="POST")
	if response:
		try:
			data = response.json()
			logging.info(f"API call to bot response: {data}")
			if data:
				channel_names = data
		except Exception as e:
			logging.error(f"Failed to parse channel data: {e}")
	else:
		logging.warning("No response from bot API")

	logging.info(f"Dashboard/{guild_id}: response from get_channels: {channel_names}.")
		

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

	if(bot_enabled == [] or bot_enabled == [(None,)]):
		current_playlist = False
		logging.info(f"Dashboard/{guild_id}:Didn't get bot enabled status from DB. This should always exist as a 1 or 0")
	else:
		bot_enabled = bot_enabled[0][0]
	
	if bot_enabled == 1: 
		bot_enabled = True
	else: 
		bot_enabled = False
	


	
	#resolving channel id taken from DB to text (I should just store the text in the DB)
	logging.info(f"Dashboard/{guild_id}: printing current channel {current_channel_id}")
	for channel in channel_names:
		if str(channel[0]) == current_channel_id:
			current_channel_id = channel[1]
			break

	logging.info(
	f"Dashboard/{guild_id}: Rendering dashboard_specific.html with:\n"
	f"\tusername: {user.name} guild: {final_guild}\n"
	f"\tinstalled: {installed} add_bot_url: {add_bot_url}\n"
	f"\tchannel_names: {channel_names} current_channel_id: {current_channel_id}\n"
	f"\thas_channel: {has_channel} current_playlist: {current_playlist}\n"
	f"\thas_playlist: {has_playlist} bot_enabled: {bot_enabled}"
	)

	return await render_template("dashboard_specific.html", username=user.name, guild = final_guild,
	 installed = installed, spot_auth = spot_auth, add_bot_url = add_bot_url, authorized=authorized,
	 channel_names=channel_names, current_channel=current_channel_id, has_channel = has_channel,
	 current_playlist = current_playlist, has_playlist = has_playlist, bot_enabled = bot_enabled)
