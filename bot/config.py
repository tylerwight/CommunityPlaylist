import os
from dotenv import load_dotenv
import discord
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    fmt='[%(asctime)s] [ComPlayBOT] [%(log_color)s%(levelname)s%(reset)s] %(message)s',
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


dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path)

callbackurl = os.getenv('CALLBACK')
port = os.getenv('PORT')
sqluser = os.getenv('MYSQL_USER')
sqlpass = os.getenv('MYSQL_PASS')
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
spotify_scope = 'playlist-modify-public'
TOKEN = os.getenv('DISCORD_TOKEN')