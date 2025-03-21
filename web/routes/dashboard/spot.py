import os
from quart import Blueprint, render_template, request, session, redirect, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import mysql.connector
import logging
from utils import check_guild_admin, ipc_client, query_db, GetPlaylistID
from config import ddiscord, app, sqluser, sqlpass, callbackurl, cid, secret, spotify_scope

dashboard_spot_bp = Blueprint('dashboard_spot', __name__)


@app.route("/dashboard/<int:guild_id>/playlist", methods=['GET', 'POST'])
async def dashboard_playlist(guild_id):
    authorized = await ddiscord.authorized
    if not authorized:
        logging.info(f"Dashboard/{guild_id}/playlist: not authorized, redirecting")
        return redirect(url_for("login")) 

    user_guilds = await ddiscord.fetch_guilds()
    admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)
    
    user = await ddiscord.fetch_user()

    logging.info(f"Dashboard/{guild_id}/playlist: User admin status:{admin_okay}")
    if admin_okay != True:
        logging.info(f"Dashboard/{guild_id}/playlist: User is NOT an admin of this server. Rejecting.")
        return ("Not Authorized")
    
    current_playlist = (query_db(f"SELECT playlist_name from guilds where guild_id={final_guild.id}"))
    if(current_playlist == [] or current_playlist == [(None,)]):
        current_playlist = "NONE"
        has_playlist = False
    else:
        current_playlist = current_playlist[0][0]
        has_playlist = True

    if request.method == 'GET':
        logging.info(f"Dashboard/{guild_id}/playlist: GET request, returning {user.name}, {final_guild}, {authorized}, {current_playlist}")
        return await render_template("dashboard_playlist.html", username=user.name, guild = final_guild, authorized=authorized, current_playlist=current_playlist)

    if request.method != 'POST':
        return (f"error, not POST or GET?")

    input_playlist = (await request.form).get('playlist_input')
    try:
        #cache_handler = spotipy.cache_handler.CacheFileHandler(username=guild_id)
        cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path = f"../bot/.cache-{guild_id}")
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
    

    mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
    cursor = mydb.cursor()
    sql = "UPDATE guilds set playlist_name = %s, playlist_id = %s where guild_id = %s"
    val = (playlist_title, playlist_uri, guild_id)
    cursor.execute(sql, val)
    mydb.commit()
    cursor.close()
    mydb.close()  

    await ipc_client.request("update_guild_ipc", current_playlist = playlist_title, guild_id = guild_id)
    current_playlist = playlist_title
    logging.info(f"Dashboard/{guild_id}/playlist: Rendering dashboard_playlistOK.html with: {user.name}, {final_guild}, {authorized}, {current_playlist}")
    return await render_template("dashboard_playlistOK.html", username= user.name, guild = final_guild, authorized=authorized, current_playlist=current_playlist)


    




@app.route("/dashboard/<int:guild_id>/spotauth")
async def dashboard_spotauth(guild_id):
    authorized = await ddiscord.authorized
    if not authorized:
        return redirect(url_for("login")) 

    user_guilds = await ddiscord.fetch_guilds()
    admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)

    logging.info(f"Dashboard/{guild_id}/spotauth: User admin status:{admin_okay}")
    if admin_okay != True:
        logging.info(f"Dashboard/{guild_id}/spotauth: User is NOT an admin of this server. Rejecting.")
        return ("Not Authorized")
    
    auth_manager=SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=callbackurl, scope=spotify_scope, open_browser=False, show_dialog=True)
    auth_url = auth_manager.get_authorize_url()
    session['acting_guild'] = guild_id
    return redirect(auth_url)



@app.route("/dashboard/<int:guild_id>/spotdc")
async def dashboard_spotdc(guild_id):
    authorized = await ddiscord.authorized
    if not authorized:
        return redirect(url_for("login")) 

    user_guilds = await ddiscord.fetch_guilds()
    admin_okay, final_guild = check_guild_admin(user_guilds, guild_id)

    logging.info(f"Dashboard/{guild_id}/spotdc: User admin status:{admin_okay}")
    if admin_okay != True:
        logging.info(f"Dashboard/{guild_id}/spotdc: User is NOT an admin of this server. Rejecting.")
        return ("Not Authorized")
    
    cachefile = (f".cache-{guild_id}")
    try:
        os.remove(cachefile)
        logging.info(f"Dashboard/{guild_id}/spotdc: {cachefile} successfully deleted Spotify data")
    except FileNotFoundError:
        logging.info(f"Dashboard/{guild_id}/spotdc:{cachefile} not found.")
        return ("Could not find your Spotify data, is it already deleted?")
    except Exception as e:
        logging.info(f"Dashboard/{guild_id}/spotdc: Error removing cache file: {e}")
        return ("Could not find your Spotify data, is it already deleted?")

    return redirect(f"/dashboard/{guild_id}")

