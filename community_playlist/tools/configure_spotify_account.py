from quart import Quart, request, redirect, url_for
import spotipy
import logging
from spotipy.oauth2 import SpotifyOAuth
from community_playlist.db.spotipy_handler import CacheSQLHandler
from community_playlist.db.guild import create_guild_if_not_exists
from community_playlist.web.config import ddiscord, app, callbackurl, cid, secret, spotify_scope, sqluser, sqlpass, enkey



@app.route('/')
async def index():
    create_guild_if_not_exists(0, 'default')
    auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, open_browser=False, show_dialog=True)
    auth_url = auth_manager.get_authorize_url()

    html = f"""
    <html>
        <head><title>Spotify Auth</title></head>
        <body>
            <h1>Authorize Spotify</h1>
            <p><a href="{auth_url}">Click here to log in with Spotify</a></p>
        </body>
    </html>
    """
    return html


@app.route("/callback")
async def callback():
	logging.info("Callback: Spotify callback initiated")
	logging.info(f"Callback: We are working on 000")
	
	cache_handler = CacheSQLHandler(cache_where=f"guild_id=0",
									sqluser=sqluser,
									sqlpass=sqlpass,
									encrypt=True,
									key=enkey)
	
	auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, open_browser=False, show_dialog=True, cache_handler=cache_handler)

	if not ('code' in request.args):
		logging.error("Callback: Couldn't find Spotify authcode in callback request")
		return redirect(f"/failure")
	

	logging.info("Callback: Found Spotify authcode")

	auth_manager.get_access_token(request.args.get("code"))

	if not auth_manager.validate_token(cache_handler.get_cached_token()):
		logging.info("Callback: Spotify auth code rejected, redirecting")
		return redirect(f"/failure")
	
	logging.info("Callback: Spotify auth code accepted")
	try:
		sp = spotipy.Spotify(auth_manager=auth_manager)
		logging.info(f"Callback: logged in Spotify with user: {sp.me()}")
	except Exception as e:
		logging.error(f"Callback: I made it through the full auth, but I still ran into an issue? Error: {e}")
		return redirect(f"/failure")
	
	return redirect(f"/success")


@app.route('/success')
async def success():
    return "Success!"


@app.route('/failure')
async def failure():
    return "Failure!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, ssl_context='adhoc')