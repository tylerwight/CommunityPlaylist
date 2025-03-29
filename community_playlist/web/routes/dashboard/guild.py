
from quart import Blueprint, render_template, redirect, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
from community_playlist.web.utils import is_invited, check_bot_exists, bot_api_call, require_admin
from community_playlist.db.spotipy_handler import CacheSQLHandler
from community_playlist.web.config import ddiscord, app, callbackurl, cid, secret, add_bot_url, spotify_scope, sqluser, sqlpass, enkey
import community_playlist.db as db

dashboard_guild_bp = Blueprint('dashboard_guild', __name__)

@app.route("/dashboard/<int:guild_id>")
@require_admin()
async def dashboard_server(guild_id, final_guild):
    user = await ddiscord.fetch_user()
    spot_auth = False
    installed = await check_bot_exists(guild_id)

    try:
        cache_handler = CacheSQLHandler(
            cache_where=f"guild_id={guild_id}",
            sqluser=sqluser,
            sqlpass=sqlpass,
            encrypt=True,
            key=enkey
        )

        auth_manager = SpotifyOAuth(
            client_id=cid,
            client_secret=secret,
            redirect_uri=callbackurl,
            scope=spotify_scope,
            cache_handler=cache_handler
        )

        if cache_handler.get_cached_token():
            logging.info(f"Dashboard/{guild_id}: Found cached Spotify token")
            sp = spotipy.Spotify(auth_manager=auth_manager)
            logging.info(f"Dashboard/{guild_id}: Spotify user: {sp.me()}")
            spot_auth = True
        else:
            logging.info(f"Dashboard/{guild_id}: No cached Spotify token")
    except Exception as e:
        logging.error(f"Dashboard/{guild_id}: Spotify auth failed with error: {e}")
        return f"Found Spotify data, but authentication failed with error: {e}"


	#get channel names from bot
    response = bot_api_call(endpoint="channels", payload={"guild_id": guild_id}, method="POST")
    channel_names = []
    if response:
        try:
            channel_names = response.json()
            logging.info(f"API call to bot response: {channel_names}")
        except Exception as e:
            logging.error(f"Failed to parse channel data: {e}")
    else:
        logging.warning("No response from bot API")

    # Get current watch channel
    current_channel_id = db.guild.get_watch_channel(final_guild.id)
    has_channel = bool(current_channel_id)
    if not current_channel_id:
        current_channel_id = "NONE"

    # Get current playlist
    playlist_info = db.guild.get_playlist(final_guild.id)
    has_playlist = bool(playlist_info and playlist_info["name"])
    current_playlist = playlist_info["name"] if has_playlist else "NONE"

    # Get enabled status
    bot_enabled = db.guild.get_enabled_status(final_guild.id)
    if bot_enabled is None:
        bot_enabled = False
        logging.info(f"Dashboard/{guild_id}: Didn't get bot enabled status from DB. Should always exist.")
    else:
        bot_enabled = bool(bot_enabled)

    # Resolve channel ID to name
    logging.info(f"Dashboard/{guild_id}: printing current channel {current_channel_id}")
    for channel in channel_names:
        if str(channel[0]) == current_channel_id:
            current_channel_id = channel[1]
            break

    logging.info(
        f"Dashboard/{guild_id}: Rendering dashboard_specific.html with:\n"
        f"\tusername: {user.name} guild: {final_guild}\n"
        f"\tinstalled: {installed} add_bot_url: {add_bot_url}\n"
        f"\tchannel_names: {channel_names} current_channel_id: {current_channel_id}\n"
        f"\thas_channel: {has_channel} current_playlist: {current_playlist}\n"
        f"\thas_playlist: {has_playlist} bot_enabled: {bot_enabled}"
    )

    return await render_template("dashboard_specific.html",
        username=user.name,
        guild=final_guild,
        installed=installed,
        spot_auth=spot_auth,
        add_bot_url=add_bot_url,
        authorized=True,
        channel_names=channel_names,
        current_channel=current_channel_id,
        has_channel=has_channel,
        current_playlist=current_playlist,
        has_playlist=has_playlist,
        bot_enabled=bot_enabled
    )
