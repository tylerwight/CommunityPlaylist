import os
from quart import Blueprint, render_template, request, session, redirect, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import mysql.connector
import logging
from community_playlist.web.utils import GetPlaylistID, bot_api_call, require_admin
from community_playlist.db.spotipy_handler import CacheSQLHandler
from community_playlist.web.config import ddiscord, app, sqluser, sqlpass, callbackurl, cid, secret, spotify_scope, enkey
import community_playlist.db as db

dashboard_spot_bp = Blueprint('dashboard_spot', __name__)


@app.route("/dashboard/<int:guild_id>/playlist", methods=['GET', 'POST'])
@require_admin()
async def dashboard_playlist(guild_id, final_guild):    
    user = await ddiscord.fetch_user()

    playlist_info = db.guild.get_playlist(final_guild.id)
    if not playlist_info or not playlist_info["name"]:
        current_playlist = "NONE"
        has_playlist = False
    else:
        current_playlist = playlist_info["name"]
        has_playlist = True


    if request.method == 'GET':
        logging.info(f"Dashboard/{guild_id}/playlist: GET request, returning {user.name}, {final_guild}, {True}, {current_playlist}")
        return await render_template("dashboard_playlist.html", username=user.name, guild = final_guild, authorized=True, current_playlist=current_playlist)

    if request.method != 'POST':
        return (f"error, not POST or GET?")

    input_playlist = (await request.form).get('playlist_input')
    try:
        cache_handler = CacheSQLHandler(cache_where=f"guild_id={guild_id}",
                                        sqluser=sqluser,
                                        sqlpass=sqlpass,
                                        encrypt=True,
                                        key=enkey)
        auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, cache_handler=cache_handler)

        if not cache_handler.get_cached_token() == None:
            logging.info(f"Dashboard/{guild_id}/playlist: Found cached token")
            sp = spotipy.Spotify(auth_manager=auth_manager)
            logging.info(f"Dashboard/{guild_id}/playlist: user: {sp.me()}")
        else:
            logging.error(f"Dashboard/{guild_id}/playlist: NO CACHED TOKEN!")
            return("ERROR: Could not find your spotify data")
        
    except Exception as e:
        logging.error(f"Dashboard/{guild_id}: Spotify auth failed with error: {e}")
        return(f"Found spotify data, but authentication failed with error: {e}")
    
    duplicate = 0
    username = sp.current_user()["id"]
    playlists = sp.user_playlists(username)

    while playlists:
        for i, playlist in enumerate(playlists['items']):
            if playlist['name'] == input_playlist:
                logging.info(f"Dashboard/{guild_id}/playlist: playlist already exists in Spotify, adding to existing playlist")
                duplicate = 1
                playlist_uri = playlist['uri']
                playlist_title = input_playlist
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None

    if duplicate == 0:
        logging.info(f"Dashboard/{guild_id}/playlist: did NOT find playlist, making a new one")
        playlist_title = input_playlist
        username = sp.current_user()["id"]
        sp.user_playlist_create(username, name=playlist_title)
        playlist_uri = GetPlaylistID(username, playlist_title, sp)
    
    db.guild.set_playlist(guild_id, playlist_title, playlist_uri)


    response = bot_api_call(endpoint="update_guild", payload={"guild_id": guild_id}, method="POST")
    if response:
        logging.info(f"API call to bot response: {response.json()}")

    current_playlist = playlist_title
    logging.info(f"Dashboard/{guild_id}/playlist: Rendering dashboard_playlistOK.html with: {user.name}, {final_guild}, {True}, {current_playlist}")
    return await render_template("dashboard_playlistOK.html", username= user.name, guild = final_guild, authorized=True, current_playlist=current_playlist)


    




@app.route("/dashboard/<int:guild_id>/spotauth")
@require_admin()
async def dashboard_spotauth(guild_id, final_guild):

    auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, open_browser=False, show_dialog=True)
    auth_url = auth_manager.get_authorize_url()
    session['acting_guild'] = guild_id

    return redirect(auth_url)



@app.route("/dashboard/<int:guild_id>/spotdc")
@require_admin()
async def dashboard_spotdc(guild_id, final_guild):

    db.guild.update_token(guild_id, "NULL")

    return redirect(f"/dashboard/{guild_id}")

