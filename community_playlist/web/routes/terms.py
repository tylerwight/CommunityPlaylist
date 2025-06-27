from quart import Blueprint, render_template
from community_playlist.web.config import ddiscord

terms_bp = Blueprint('terms', __name__)

@terms_bp.route("/terms")
async def terms():
    authorized = await ddiscord.authorized
        

    if authorized:
        user = await ddiscord.fetch_user()
        return await render_template("terms.html", authorized = authorized, username = user.name)
    
    return await render_template("terms.html", authorized = authorized, username = "none")