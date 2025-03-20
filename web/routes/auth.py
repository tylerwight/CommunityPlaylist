from quart import Quart, Blueprint, render_template, request, session, redirect, url_for
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
from config import ddiscord, app

auth_bp = Blueprint('auth', __name__)


@app.route("/login")
async def login():
	return await ddiscord.create_session()

@app.route("/logout")
async def logout():
	ddiscord.revoke()
	return redirect(url_for("home"))

@app.route("/callback_D")
async def callback_D():
    print("in callback")
    try:
        await ddiscord.callback()
    except Exception as e:
        print("error")
        print(e)
        pass
    print("trying to redir")
    print(url_for("dashboard"))
    return redirect(url_for("dashboard"))


@app.route("/callback")
async def callback():
	print("IM IN THE CALLBACK")
	print(f"we are acting on GUILD {session.get('acting_guild', 'none')}")
	cache_handler = spotipy.cache_handler.CacheFileHandler(username=session.get('acting_guild', 'none'))
	auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, open_browser=False, show_dialog=True,cache_handler=cache_handler)

	if not ('code' in request.args):
		print("couldn't find code")
		return redirect(url_for('home'))
	

	print("found the code")
	print(request.args.get("code"))

	auth_manager.get_access_token(request.args.get("code"))

	if not auth_manager.validate_token(cache_handler.get_cached_token()):
		print("NOT AUTHED.. REDIRECTING")
		return redirect(url_for('home'))
	
	print(" I think it worked!")
	try:
		sp = spotipy.Spotify(auth_manager=auth_manager)
		print(sp.me())
	except Exception as e:
		print("I made it through the full auth, but I still ran into an issue? It is this:")
		print(e)
		return redirect(url_for('home'))
	
	return redirect(f"/dashboard/{session.get('acting_guild', 'none')}")