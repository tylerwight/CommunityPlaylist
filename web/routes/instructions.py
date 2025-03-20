from quart import Blueprint, render_template
from config import ddiscord

instructions_bp = Blueprint('instructions', __name__)

@instructions_bp.route("/instructions")
async def instructions():
	authorized = await ddiscord.authorized

	if authorized:
		return await render_template("instructions.html", authorized = await ddiscord.authorized, username = (await ddiscord.fetch_user()).name)
	
	return await render_template("instructions.html", authorized = await ddiscord.authorized, username = "none")