from quart import Blueprint, render_template, redirect, url_for
from config import ddiscord, app
from utils import is_invited
import logging



dashboard_main_bp = Blueprint('dashboard_main', __name__)


@app.route("/dashboard")
async def dashboard():
	authorized = await ddiscord.authorized

	if not authorized:
		logging.info("Dashboard: Not authorized, redirecting")
		return redirect(url_for("login")) 

	user = await ddiscord.fetch_user()

	if not is_invited(user):
		logging.info("Dashboard: User is not invited")
		return await render_template("not_invited.html", username=user.name, authorized=authorized)

	user_guilds = await ddiscord.fetch_guilds()
	guild_count = len(user_guilds)

	admin_guilds = []
	for guild in user_guilds:
		if guild.permissions.administrator:		
			admin_guilds.append(guild)
	
	return await render_template("dashboard.html", guild_count = guild_count, guilds = admin_guilds, username=user.name, authorized=authorized)