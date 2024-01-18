
import os
from CommunityPlaylistBot import CommunityPlaylistBot
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
import json

class SQLCacheHandler(spotipy.CacheHandler):
	"""
	A cache handler that stores the token info in SQL.
	"""

	def __init__(self, sql, key=None):
		"""
		Parameters:
			* sql: sql object
			* key: May be supplied, will otherwise be generated
					(takes precedence over `token_info`)
		"""
		self.sql = sql
		self.key = key if key else 'token_info'

	def get_cached_token(self):
		token_info = None
		try:
			#token_info = self.redis.get(self.key)
			#if token_info:
				#return json.loads(token_info)
			print("attempting to get")

		except Exception as e:
			print('Error getting token from cache: ' + str(e))

		return token_info

	def save_token_to_cache(self, token_info):
		try:
			#self.redis.set(self.key, json.dumps(token_info))
			print("I AM IN CACHE HANLDER, PRINTING")
			print(self.key)
			print(json.dumps(token_info))

		except Exception as e:
			print('Error saving token to cache: ' + str(e))


load_dotenv()

callbackurl = os.getenv('CALLBACK')
port = os.getenv('PORT')
sqluser = os.getenv('MYSQL_USER')
sqlpass = os.getenv('MYSQL_PASS')
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
TOKEN = os.getenv('DISCORD_TOKEN')
discord_cl_id = os.getenv('DISCORD_CLIENT_ID')
discord_cl_secret = os.getenv('DISCORD_CLIENT_SECRET')
discord_redirect_uri = os.getenv('DISCORD_CLIENT_REDIRECT_URL')
add_bot_url = os.getenv('DISCORD_URL')
logging.basicConfig(level=logging.INFO)


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

@app.route("/")
async def home():
	resp = await ipc_client.request("get_guild_data")
	authorized = await ddiscord.authorized

	print(resp)
	print(str(resp.response))

	if authorized:
		return await render_template("index.html", authorized = await ddiscord.authorized, username = (await ddiscord.fetch_user()).name)
	
	return await render_template("index.html", authorized = await ddiscord.authorized, username = "none")

@app.route("/login")
async def login():
	return await ddiscord.create_session()

@app.route("/logout")
async def logout():
	ddiscord.revoke()
	return redirect(url_for("home"))

@app.route("/callback_D")
async def callback_D():
	try:
		await ddiscord.callback()
	except Exception:
		pass

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
	sp = spotipy.Spotify(auth_manager=auth_manager)
	print(sp.me())
	return redirect(url_for('home'))

	
	

@app.route("/dashboard")
async def dashboard():
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 
	#guild_count = await ipc_client.request("get_guild_count")
	guild_ids = await ipc_client.request("get_guild_data")
	guild_ids = guild_ids.response
	elements = guild_ids.replace("[", "").replace("]", "").split(",")
	guild_ids = [str(element) for element in elements]
	guild_count = len(guild_ids)

	user_guilds = await ddiscord.fetch_guilds()

	guilds = []

	for guild in user_guilds:
		if guild.permissions.administrator:		
			guild.class_color = "green-border" if str(guild.id) in guild_ids else "red-border"
			guilds.append(guild)

	guilds.sort(key = lambda x: x.class_color == "red-border")
	name = (await ddiscord.fetch_user()).name
	return await render_template("dashboard.html", guild_count = guild_count, guilds = guilds, username=name)



@app.route("/dashboard/<int:guild_id>")
async def dashboard_server(guild_id):
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 
	
	name = (await ddiscord.fetch_user()).name
	admin_okay = False
	spot_auth = False
	attempted_guild = await ipc_client.request("get_gld", guild_id = guild_id)

	if (attempted_guild.response == None) : 
		installed = False
	else:
		installed = True
		attempted_guild = json.loads(attempted_guild.response)	
	
	user_guilds = await ddiscord.fetch_guilds()

	for guild in user_guilds:
		if guild.permissions.administrator:
			print(f"you are an admin of this guilde: {guild} with id {guild.id}")
			print(f"the guild_id at this URL is: {guild_id}")
			if str(guild.id) == str(guild_id):
				admin_okay = True
				final_guild = guild

	print(f'admin_okay - {admin_okay}')
	if admin_okay != True:
		print(f"Admin check didn't work! How did we get to this URL? The previous page should have listed only servers you're an admin of")
		return redirect(url_for('home'))
	


	try:
		cache_handler = spotipy.cache_handler.CacheFileHandler(username=guild_id)
		print(cache_handler.get_cached_token())
		auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, cache_handler=cache_handler)

		if not cache_handler.get_cached_token() == None:
			print("Found cached token")
			sp = spotipy.Spotify(auth_manager=auth_manager)
			print(sp.me())
			spot_auth = True
		else:
			print("NO CACHED TOKEN!")
			spot_auth = False
		
	except:
		print("=========AUTH FAILED!=============")
		spot_auth = False
	
	
	return await render_template("dashboard_specific.html", username=name, guild = final_guild, installed = installed, spot_auth = spot_auth, add_bot_url = add_bot_url)

@app.route("/dashboard/<int:guild_id>/spotauth")
async def dashboard_spotauth(guild_id):
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 
	
	name = (await ddiscord.fetch_user()).name
	admin_okay = False
	attempted_guild = await ipc_client.request("get_gld", guild_id = guild_id)

	if (attempted_guild.response == None) : 
		installed = False
	else:
		installed = True
		attempted_guild = json.loads(attempted_guild.response)	
	
	user_guilds = await ddiscord.fetch_guilds()

	for guild in user_guilds:
		if guild.permissions.administrator:
			print(f"you are an admin of this guilde: {guild} with id {guild.id}")
			print(f"the guild_id at this URL is: {guild_id}")
			if str(guild.id) == str(guild_id):
				admin_okay = True
				final_guild = guild

	print(f'admin_okay - {admin_okay}')
	if admin_okay != True:
		print(f"Admin check didn't work! How did we get to this URL? The previous page should have listed only servers you're an admin of")
		return redirect(url_for('home'))
	auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, open_browser=False, show_dialog=True, username=username)
	auth_url = auth_manager.get_authorize_url()
	session['acting_guild'] = guild_id
	#return await render_template("dashboard_specific.html", username=name, guild = final_guild, installed = installed, spot_auth = False, add_bot_url = add_bot_url)
	return redirect(auth_url)


#auth_manager=SpotifyOAuth(client_id=self.spotify_cid, client_secret=self.spotify_secret, redirect_uri=self.callbackurl, scope=self.spotify_scope, open_browser=True, show_dialog=True, username=name)

intents = discord.Intents.all()
#bot = CommunityPlaylistBot(command_prefix="!",intents=intents, callbackurl=callbackurl, flaskport=port, sqluser=sqluser, sqlpass=sqlpass, spotify_cid=cid, spotify_secret=secret)
#bot.run(TOKEN)

if __name__ == "__main__":

	callbackurl = os.getenv('CALLBACK')
	port = os.getenv('PORT')
	sqluser = os.getenv('MYSQL_USER')
	sqlpass = os.getenv('MYSQL_PASS')
	cid = os.getenv('SPOTIPY_CLIENT_ID')
	secret = os.getenv('SPOTIPY_CLIENT_SECRET')
	TOKEN = os.getenv('DISCORD_TOKEN')
	spotify_scope = 'playlist-modify-public'
	username = 'test'

	app.run(host='0.0.0.0', port=8080)
	

