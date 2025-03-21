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

dashboard_spot_bp = Blueprint('dashboard_spot', __name__)


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

