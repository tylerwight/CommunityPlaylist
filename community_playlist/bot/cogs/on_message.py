import discord
from discord.ext import commands
import logging
import mysql.connector
import spotipy
import spotipy.util as util
import re
from spotipy.oauth2 import SpotifyOAuth
from community_playlist.bot.utils import album_to_tracks
from community_playlist.db.spotipy_handler import CacheSQLHandler
from community_playlist.bot.config import sqluser, sqlpass, enkey


class on_message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        guild_id_str = str(message.guild.id)
        current_guild = self.bot.guilds_state.get(guild_id_str)

        if not current_guild:
            logging.error(f"ON_MESSAGE: No guild data found for guild {guild_id_str}, skipping message.")
            return

        logging.info(f"ON_MESSAGE: Message detected in guild {guild_id_str} => {current_guild}")
        username = current_guild["spotipy_token"]

        channel_id_str = str(message.channel.id)
        channel_obj = message.channel

        if current_guild["enabled"] != 1:
            logging.info("ON_MESSAGE: Guild has bot disabled, skipping...")
            return

        if channel_id_str != current_guild["watch_channel"]:
            logging.info("ON_MESSAGE: Not the monitored channel for this guild, skipping...")
            return

        text_track = "spotify.com/track"
        text_album = "spotify.com/album"
        if (text_track in message.content) or (text_album in message.content):
            match = re.search(r"(?P<url>https?://[^\s]+)", message.content)
            if not match:
                logging.error(f"ON_MESSAGE: Found spotify.com link but couldn't extract a valid album/track URL")
                channel_obj.send(f"Found spotify.com link but couldn't extract a valid album/track URL")
                return

            found_link = match.group("url")
            logging.info(f"ON_MESSAGE: Found a Spotify link: {found_link}")
            logging.info(f"ON_MESSAGE: Creating Spotify auth manager for guild: {current_guild['guild_id']}")

            # Spotify Auth
            try:
                cache_handler = CacheSQLHandler(cache_where=f"guild_id={current_guild['guild_id']}",
                                                sqluser=sqluser,
                                                sqlpass=sqlpass,
                                                encrypt=True,
                                                key=enkey)
                auth_manager = SpotifyOAuth(
                    client_id=self.bot.spotify_cid,
                    client_secret=self.bot.spotify_secret,
                    redirect_uri=self.bot.callbackurl,
                    scope=self.bot.spotify_scope,
                    cache_handler=cache_handler
                )

                if cache_handler.get_cached_token() is not None:
                    logging.info("ON_MESSAGE: Found cached token")
                    spotify = spotipy.Spotify(auth_manager=auth_manager)
                    logging.info(f"ON_MESSAGE: Spotify user: {spotify.me()}")
                else:
                    logging.warning("ON_MESSAGE: No cached token found.")
                    await channel_obj.send(
                        "Found a spotify link, but failed Spotify authentication. "
                        "Please login to the website and check your Spotify authentication."
                    )
                    return

                logging.info("ON_MESSAGE: Authenticated to Spotify. Attempting to add track...")

            except Exception as e:
                logging.error(f"ON_MESSAGE: Could not authenticate to Spotify: {e}")
                await channel_obj.send(
                    "Found a spotify link, but failed Spotify authentication. "
                    "Please login to the website and check your Spotify authentication."
                )
                return

            # If it's an album link, expand to all tracks
            extracted_tracks = []
            if "spotify.com/album" in found_link:
                logging.info("ON_MESSAGE: Album link detected, adding all tracks from album.")
                extracted_tracks = album_to_tracks([found_link], spotify)
                track_name = "AlbumTracks"
                resultartist_name = "Various"
            else:
                # Single track
                try:
                    track_data = spotify.track(found_link)
                    track_name = track_data['name']
                    resultartist_name = track_data['artists'][0]['name']
                    extracted_tracks = [found_link]  # the track's URL/URI
                except Exception as e:
                    logging.error(f"ON_MESSAGE: error getting spotify track: {e}")
                    await channel_obj.send("I couldn't find this song in Spotify, is the link correct?")


            logging.info(f'ON_MESSAGE: Adding "{track_name}" by {resultartist_name} to playlist.')
            playlist_id = current_guild["playlist_id"]
            spotify.user_playlist_add_tracks(username, playlist_id, extracted_tracks)


            playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"

            if "spotify.com/album" in found_link:
                await channel_obj.send(
                    f"I have added the album '{track_name}' by {resultartist_name} "
                    f"to playlist {current_guild['playlist_name']}: <{playlist_url}>"
                )
            else:
                await channel_obj.send(
                    f"I have added the song '{track_name}' by {resultartist_name} "
                    f"to playlist {current_guild['playlist_name']}: <{playlist_url}>"
                )





async def setup(bot):
    await bot.add_cog(on_message(bot))