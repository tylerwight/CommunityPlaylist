import os
from dotenv import load_dotenv
from bot_core import CommunityPlaylistBot
from config import callbackurl, port, sqluser, sqlpass, cid, secret, TOKEN, spotify_scope
import api
import discord
import threading




if __name__ == '__main__':

    intents = discord.Intents.all()
    
    bot = CommunityPlaylistBot(command_prefix="!",intents=intents, callbackurl=callbackurl, flaskport=port, sqluser=sqluser, sqlpass=sqlpass, spotify_cid=cid, spotify_secret=secret)
    api.bot_instance = bot
    api_thread = threading.Thread(target=api.run_api, daemon=True)
    api_thread.start()
    bot.run(TOKEN)

    