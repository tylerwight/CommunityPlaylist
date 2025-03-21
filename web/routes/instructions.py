from quart import Blueprint, render_template
from config import ddiscord

instructions_bp = Blueprint('instructions', __name__)

@instructions_bp.route("/instructions")
async def instructions():
    authorized = await ddiscord.authorized
        

    if authorized:
        user = await ddiscord.fetch_user()
        return await render_template("instructions.html", authorized = authorized, username = user.name)
    
    return await render_template("instructions.html", authorized = authorized, username = "none")