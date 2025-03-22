import os
from quart import Quart
from quart_discord import DiscordOAuth2Session
from dotenv import load_dotenv
import json
import logging
import colorlog

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path)

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    fmt='[%(asctime)s] [ComPlayWEB] [%(log_color)s%(levelname)s%(reset)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    }
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)

# Setup Quart app
app = Quart(__name__)
app.config["SECRET_KEY"] = "test123"
app.config["DISCORD_CLIENT_ID"] = os.getenv("DISCORD_CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("DISCORD_CLIENT_SECRET")
app.config["DISCORD_REDIRECT_URI"] = os.getenv("DISCORD_CLIENT_REDIRECT_URL")


invited_users = json.loads(os.getenv('INVITED', '[]'))
sqluser = os.getenv('MYSQL_USER')
sqlpass = os.getenv('MYSQL_PASS')
callbackurl = os.getenv('CALLBACK')
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
add_bot_url = os.getenv('DISCORD_URL')
spotify_scope = 'playlist-modify-public'
bot_api_url = "http://localhost:8090/"


# Initialize Discord OAuth2 session
ddiscord = DiscordOAuth2Session(app)

