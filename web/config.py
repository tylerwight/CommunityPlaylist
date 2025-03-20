import os
from quart import Quart
from quart_discord import DiscordOAuth2Session
from dotenv import load_dotenv
import logging

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path)

logging.basicConfig(level=logging.INFO)

# Setup Quart app
app = Quart(__name__)
app.config["SECRET_KEY"] = "test123"
app.config["DISCORD_CLIENT_ID"] = os.getenv("DISCORD_CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("DISCORD_CLIENT_SECRET")
app.config["DISCORD_REDIRECT_URI"] = os.getenv("DISCORD_CLIENT_REDIRECT_URL")

# Initialize Discord OAuth2 session
ddiscord = DiscordOAuth2Session(app)

