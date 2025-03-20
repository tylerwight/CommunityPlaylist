
import os
import logging
from dotenv import load_dotenv
import discord
from quart import Quart, render_template, request, session, redirect, url_for
from quart_discord import DiscordOAuth2Session
from quart import Quart
from discord.ext.ipc.client import Client
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
import mysql.connector
import json
import ast
from config import ddiscord, app
from routes import register_routes


dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path)
logging.basicConfig(level=logging.INFO)

#Setup vars
callbackurl = os.getenv('CALLBACK')
#port = os.getenv('PORT')
sqluser = os.getenv('MYSQL_USER')
sqlpass = os.getenv('MYSQL_PASS')
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
TOKEN = os.getenv('DISCORD_TOKEN')
discord_cl_id = os.getenv('DISCORD_CLIENT_ID')
discord_cl_secret = os.getenv('DISCORD_CLIENT_SECRET')
discord_redirect_uri = os.getenv('DISCORD_CLIENT_REDIRECT_URL')
invited_users = json.loads(os.getenv('INVITED', '[]'))
add_bot_url = os.getenv('DISCORD_URL')
spotify_scope = 'playlist-modify-public'
intents = discord.Intents.all()



register_routes(app)






	
	




#uncomment if not launching from hypercorn directly
# if __name__ == "__main__":
#  	app.run(host='0.0.0.0', port=8080, ssl_context='adhoc', debug=True)
	

