from quart import Blueprint, render_template, redirect, url_for
import mysql.connector
import ast
import logging
from utils import check_guild_admin, ipc_client, query_db
from config import ddiscord, app, sqluser, sqlpass

dashboard_settings_bp = Blueprint('dashboard_settings', __name__)


@app.route("/dashboard/<int:guild_id>/channel")
async def dashboard_channel(guild_id):
	authorized = await ddiscord.authorized
	if not authorized:
		logging.info("Dashboard/{guild_id}/channel: not authorized, redirecting")
		return redirect(url_for("login")) 
	user_guilds = await ddiscord.fetch_guilds()
	admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)
	user = await ddiscord.fetch_user()

	logging.info(f'Dashboard/{guild_id}/channel: User admin status:{admin_okay}')
	if admin_okay != True:
		logging.info(f"Dashboard/{guild_id}/channel: User is NOT an admin of this server. Rejecting.")
		return ("Not Authorized")

	channel_names = await ipc_client.request("get_channels", guild_id = guild_id)
	logging.info(f"Dashboard/{guild_id}/channel: response from get_channels ipc: {channel_names}. Attempting to eval")
	if channel_names.response == None:
		channel_names = [[0, "None"]]
	else:
		channel_names = ast.literal_eval(channel_names.response)

	current_channel = (query_db(f"SELECT watch_channel from guilds where guild_id={final_guild.id}"))
	logging.info(f"Dashboard/{guild_id}/channel: current channel {current_channel}")
	if(current_channel == []):
		current_channel = "NONE"
	else:
		current_channel = current_channel[0][0]


	for target_channel in channel_names:
		logging.info(f"Dashboard/{guild_id}/channel: 0: {target_channel[0]} 1: {target_channel[1]} current_channel: {current_channel}")
		if str(target_channel[0]) == current_channel:
			current_channel = target_channel[1]
			break
	logging.info(f"Dashboard/{guild_id}/channel: loading dashboard_channel.html with: {user.name}, {final_guild}, {authorized}, {channel_names}, {current_channel}")
	return await render_template("dashboard_channel.html", username=user.name, guild = final_guild, authorized=authorized, channel_names=channel_names, current_channel=current_channel)




@app.route("/dashboard/<int:guild_id>/toggle")
async def dashboard_toggle(guild_id):
	authorized = await ddiscord.authorized
	if not authorized:
		logging.info("Dashboard/{guild_id}/toggle: not authorized, redirecting")
		return redirect(url_for("login")) 


	user_guilds = await ddiscord.fetch_guilds()
	admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)

	logging.info(f'Dashboard/{guild_id}/toggle: User admin status:{admin_okay}')
	if admin_okay != True:
		logging.info(f"Dashboard/{guild_id}/toggle: User is NOT an admin of this server. Rejecting.")
		return ("Not Authorized")
	
	bot_enabled = (query_db(f"SELECT enabled from guilds where guild_id={final_guild.id}"))
	
	if(bot_enabled == [] or bot_enabled == [(None,)]):
		bot_enabled = 1
	else:
		bot_enabled = bot_enabled[0][0]
	
	#swap the state
	if bot_enabled == 1:
		bot_enabled = 0
	else:
		bot_enabled = 1

	logging.info(f"Dashboard/{guild_id}/toggle: writing bot enabled to db: {bot_enabled}")
	mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
	cursor = mydb.cursor()
	sql = "UPDATE guilds set enabled = %s where guild_id = %s"
	val = (bot_enabled, guild_id)
	cursor.execute(sql, val)
	mydb.commit()
	cursor.close()
	mydb.close()   

	logging.info(f"Dashboard/{guild_id}/toggle: updating guild")
	await ipc_client.request("update_guild_ipc", guild_id = guild_id)

	return redirect(f"/dashboard/{guild_id}")



@app.route("/dashboard/<int:guild_id>/channel/<int:channel_id>")
async def dashboard_channel_set(guild_id, channel_id):
	authorized = await ddiscord.authorized
	if not authorized:
		logging.info("Dashboard/{guild_id}/channel/{channel_id}: not authorized, redirecting")
		return redirect(url_for("login")) 

	user_guilds = await ddiscord.fetch_guilds()
	admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)

	logging.info("Dashboard/{guild_id}/channel/{channel_id}: User admin status:{admin_okay}")
	if admin_okay != True:
		logging.info("Dashboard/{guild_id}/channel/{channel_id}: User is NOT an admin of this server. Rejecting.")
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