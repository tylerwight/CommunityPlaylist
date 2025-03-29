from quart import Blueprint, render_template
from community_playlist.web.config import ddiscord, app
from community_playlist.web.utils import is_invited

home_bp = Blueprint("home", __name__) 


@app.route("/")
async def home():
    authorized = await ddiscord.authorized

    if authorized:
        user = await ddiscord.fetch_user()
        if is_invited(user):
            return await render_template("index.html", authorized = authorized, username = user.name)

        return await render_template("not_invited.html", username=name, authorized=authorized)
        
    
    return await render_template("index.html", authorized = authorized, username = "none")