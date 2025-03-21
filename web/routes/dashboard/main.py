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



dashboard_main_bp = Blueprint('dashboard_main', __name__)


@app.route("/dashboard")
async def dashboard():
	if not await ddiscord.authorized:
		return redirect(url_for("login")) 

	authorized = await ddiscord.authorized
	name = (await ddiscord.fetch_user()).name
	if not is_invited((await ddiscord.fetch_user())):
		return await render_template("not_invited.html", username=name, authorized=authorized)

	user_guilds = await ddiscord.fetch_guilds()
	guild_count = len(user_guilds)

	guilds = []
	for guild in user_guilds:
		if guild.permissions.administrator:		
			guilds.append(guild)
	
	return await render_template("dashboard.html", guild_count = guild_count, guilds = guilds, username=name, authorized=authorized)