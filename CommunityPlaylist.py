
import os
from CommunityPlaylistBot import CommunityPlaylistBot
import logging
from dotenv import load_dotenv
import discord
from quart import Quart, render_template, request, session, redirect, url_for
from quart_discord import DiscordOAuth2Session
from quart import Quart
from discord.ext.ipc.client import Client

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
logging.basicConfig(level=logging.INFO)


app = Quart(__name__)
app.config["SECRET_KEY"] = "test123"
app.config["DISCORD_CLIENT_ID"] = discord_cl_id
app.config["DISCORD_CLIENT_SECRET"] = discord_cl_secret
app.config["DISCORD_REDIRECT_URI"] = discord_redirect_uri
ipc_client = Client(secret_key = "test")
ddiscord = DiscordOAuth2Session(app)


@app.route("/")
async def home():
	resp = await ipc_client.request("get_guild_data")
	print(resp)
	print(str(resp.response))
	return await render_template("index.html", authorized = await ddiscord.authorized)

@app.route("/login")
async def login():
	return await ddiscord.create_session()

@app.route("/callback")
async def callback():
	try:
		await ddiscord.callback()
	except Exception:
		pass

	return redirect(url_for("dashboard"))

@app.route("/dashboard")
async def dashboard():
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 

	guild_count = await ipc_client.request("get_guild_count")
	guild_ids = await ipc_client.request("get_guild_ids")

	user_guilds = await ddiscord.fetch_guilds()

	guilds = []

	for guild in user_guilds:
		if guild.permissions.administrator:			
			guild.class_color = "green-border" if guild.id in guild_ids else "red-border"
			guilds.append(guild)

	guilds.sort(key = lambda x: x.class_color == "red-border")
	name = (await ddiscord.fetch_user()).name
	return await render_template("dashboard.html", guild_count = guild_count, guilds = guilds, username=name)

@app.route("/dashboard/<int:guild_id>")
async def dashboard_server(guild_id):
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 

	guild = await ipc_client.request("get_guild", guild_id = guild_id)
	if guild is None:
		return redirect(f'https://discord.com/oauth2/authorize?&client_id={app.config["DISCORD_CLIENT_ID"]}&scope=bot&permissions=8&guild_id={guild_id}&response_type=code&redirect_uri={app.config["DISCORD_REDIRECT_URI"]}')
	return guild["name"]




intents = discord.Intents.all()
#bot = CommunityPlaylistBot(command_prefix="!",intents=intents, callbackurl=callbackurl, flaskport=port, sqluser=sqluser, sqlpass=sqlpass, spotify_cid=cid, spotify_secret=secret)
#bot.run(TOKEN)

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=8080)
	

