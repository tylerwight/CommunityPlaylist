
import os
from dotenv import load_dotenv
from quart import Quart, Blueprint, render_template, request, session, redirect, url_for
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
import mysql.connector
import ast

from utils import is_invited, check_bot_exists, check_guild_admin, ipc_client, query_db
from config import ddiscord, app, sqluser, sqlpass, callbackurl, cid, secret, add_bot_url, spotify_scope
















