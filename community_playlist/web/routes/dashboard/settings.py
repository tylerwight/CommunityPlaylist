from quart import Blueprint, render_template, redirect, url_for
import mysql.connector
import logging
from community_playlist.web.utils import bot_api_call, require_admin
from community_playlist.web.config import ddiscord, app, sqluser, sqlpass, bot_api_url
import community_playlist.db as db

dashboard_settings_bp = Blueprint('dashboard_settings', __name__)


@app.route("/dashboard/<int:guild_id>/channel")
@require_admin()
async def dashboard_channel(guild_id, final_guild):

	user = await ddiscord.fetch_user()
	channel_names = [[0, "None"]]

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

	logging.info(f"Dashboard/{guild_id}/channel: response from get_channels: {channel_names}.")


	current_channel = db.guild.get_watch_channel(final_guild.id)
	if not current_channel:
		current_channel = "NONE"


	logging.info(f"Dashboard/{guild_id}/channel: current channel {current_channel}")



	for target_channel in channel_names:
		if str(target_channel[0]) == current_channel:
			current_channel = target_channel[1]
			break
	
	logging.info(f"Dashboard/{guild_id}/channel: loading dashboard_channel.html with: {user.name}, {final_guild}, {True}, {channel_names}, {current_channel}")
	return await render_template("dashboard_channel.html", username=user.name, guild = final_guild, authorized=True, channel_names=channel_names, current_channel=current_channel)




@app.route("/dashboard/<int:guild_id>/toggle")
@require_admin() #injects final_guild
async def dashboard_toggle(guild_id, final_guild):

	bot_enabled = db.guild.get_enabled_status(final_guild.id)
	if bot_enabled is None:
		bot_enabled = False 
		logging.info(f"Dashboard/{guild_id}: Didn't get bot enabled status from DB. This should always exist as a 1 or 0")


	
	#swap the state
	if bot_enabled == 1:
		bot_enabled = 0
	else:
		bot_enabled = 1

	logging.info(f"Dashboard/{guild_id}/toggle: writing bot enabled to db: {bot_enabled}")

	db.guild.set_enabled_status(guild_id, bot_enabled)

	logging.info(f"Dashboard/{guild_id}/toggle: Changed DB, asking bot to read from DB and update")

	response = bot_api_call(endpoint="update_guild", payload={"guild_id": guild_id}, method="POST")
	if response:
		logging.info(f"API call to bot response: {response.json()}")


	return redirect(f"/dashboard/{guild_id}")



@app.route("/dashboard/<int:guild_id>/channel/<int:channel_id>")
@require_admin() #injects final_guild
async def dashboard_channel_set(guild_id, channel_id, final_guild):

	db.guild.set_watch_channel(guild_id, channel_id)

	logging.info(f"Dashboard/{guild_id}/channel/{channel_id}: Changed DB, asking bot to read from DB and update")
	response = bot_api_call(endpoint="update_guild", payload={"guild_id": guild_id}, method="POST")
	if response:
		logging.info(f"API call to bot response: {response.json()}")

	return redirect(f"/dashboard/{guild_id}")