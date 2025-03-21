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

dashboard_settings_bp = Blueprint('dashboard_settings', __name__)


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