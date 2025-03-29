from quart import Blueprint, request, session, redirect, url_for
import spotipy
import logging
from spotipy.oauth2 import SpotifyOAuth
from community_playlist.db.spotipy_handler import CacheSQLHandler
from community_playlist.web.config import ddiscord, app, callbackurl, cid, secret, spotify_scope, sqluser, sqlpass, enkey


auth_bp = Blueprint('auth', __name__)


@app.route("/login")
async def login():
	logging.info("Login: Attempting discord login")
	return await ddiscord.create_session()


@app.route("/logout")
async def logout():
	logging.info("Logout: Attempting discord logout")
	ddiscord.revoke()
	return redirect(url_for("home"))


#Discord callback
@app.route("/callback_D")
async def callback_D():
    logging.info("Callback_D: Discord callback initiated")
    try:
        await ddiscord.callback()
    except Exception as e:
        logging.error(f"Callback_D: Error attempting discord callback: {e}")
        pass
    return redirect(url_for("dashboard"))

#Spotify Callback
@app.route("/callback")
async def callback():
	acting_guild = session.get('acting_guild', 'none')
	logging.info("Callback: Spotify callback initiated")
	logging.info(f"Callback: We are working on {acting_guild}")
	
	cache_handler = CacheSQLHandler(cache_where=f"guild_id={acting_guild}",
									sqluser=sqluser,
									sqlpass=sqlpass,
									encrypt=True,
									key=enkey)
	
	auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, open_browser=False, show_dialog=True, cache_handler=cache_handler)

	if not ('code' in request.args):
		logging.error("Callback: Couldn't find Spotify authcode in callback request")
		return redirect(url_for('home'))
	

	logging.info("Callback: Found Spotify authcode")

	auth_manager.get_access_token(request.args.get("code"))

	if not auth_manager.validate_token(cache_handler.get_cached_token()):
		logging.info("Callback: Spotify auth code rejected, redirecting")
		return redirect(url_for('home'))
	
	logging.info("Callback: Spotify auth code accepted")
	try:
		sp = spotipy.Spotify(auth_manager=auth_manager)
		logging.info(f"Callback: logged in Spotify with user: {sp.me()}")
	except Exception as e:
		logging.error(f"Callback: I made it through the full auth, but I still ran into an issue? Error: {e}")
		return redirect(url_for('home'))
	
	return redirect(f"/dashboard/{session.get('acting_guild', 'none')}")