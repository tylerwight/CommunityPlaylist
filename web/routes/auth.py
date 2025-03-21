from quart import Blueprint, request, session, redirect, url_for
import spotipy
import logging
from spotipy.oauth2 import SpotifyOAuth
from config import ddiscord, app


auth_bp = Blueprint('auth', __name__)


@app.route("/login")
async def login():
	logging.INFO("Attempting discord login")
	return await ddiscord.create_session()


@app.route("/logout")
async def logout():
	logging.INFO("Attempting discord logout")
	ddiscord.revoke()
	return redirect(url_for("home"))


#Discord callback
@app.route("/callback_D")
async def callback_D():
    logging.INFO("Discord callback initiated")
    try:
        await ddiscord.callback()
    except Exception as e:
        logging.error(f"Error attempting discord callback: {e}")
        pass
    return redirect(url_for("dashboard"))

#Spotify Callback
@app.route("/callback")
async def callback():
	logging.INFO("Spotify callback initiated")
	logging.INFO(f"We are working on {session.get('acting_guild', 'none')}")
	cache_handler = spotipy.cache_handler.CacheFileHandler(username=session.get('acting_guild', 'none'))
	auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, open_browser=False, show_dialog=True, cache_handler=cache_handler)

	if not ('code' in request.args):
		logging.error("Couldn't find Spotify authcode in callback request")
		return redirect(url_for('home'))
	

	logging.INFO("Found Spotify authcode")

	auth_manager.get_access_token(request.args.get("code"))

	if not auth_manager.validate_token(cache_handler.get_cached_token()):
		logging.INFO("Spotify auth code rejected, redirecting")
		return redirect(url_for('home'))
	
	logging.INFO("Spotify auth code accepted")
	try:
		sp = spotipy.Spotify(auth_manager=auth_manager)
		logging.INFO(f"logged in Spotify with user: {sp.me()}"
	except Exception as e:
		logging.error(f"I made it through the full auth, but I still ran into an issue? Error: {e}")
		return redirect(url_for('home'))
	
	return redirect(f"/dashboard/{session.get('acting_guild', 'none')}")