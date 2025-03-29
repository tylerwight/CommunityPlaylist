import os
from dotenv import load_dotenv
import discord
import logging
import colorlog
from logging.handlers import TimedRotatingFileHandler
import base64

#App variables config

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", ".env"))
load_dotenv(dotenv_path)

callbackurl = os.getenv('CALLBACK')
port = os.getenv('PORT')
sqluser = os.getenv('MYSQL_USER')
sqlpass = os.getenv('MYSQL_PASS')
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
spotify_scope = 'playlist-modify-public'
TOKEN = os.getenv('DISCORD_TOKEN')
enkey = base64.b64decode(os.getenv('ENKEY'))


## logging config

os.makedirs("../logs", exist_ok=True)


console_handler = colorlog.StreamHandler()
console_handler.setFormatter(colorlog.ColoredFormatter(
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



file_handler = TimedRotatingFileHandler(
    "../logs/CommunityPlaylistBot.log",
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)

file_formatter = logging.Formatter(
    fmt='[%(asctime)s] [ComPlayBOT] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S' 
)

file_handler.setFormatter(file_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)


api_logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [api] [%(levelname)s] %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
        },
        "file": {
            "formatter": "default",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "../logs/CommunityPlaylistBot.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["default", "file"],
            "level": "INFO",
        },
        "uvicorn.error": {
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}