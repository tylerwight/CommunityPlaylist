import os
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
import time
import asyncio
from flask import Flask, render_template, request, redirect, session
#from flask_session import Session
import threading
from random import randint
import mysql.connector
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class SpotWatcher(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callbackurl = kwargs.pop('callbackurl', 'http://localhost:8080/')
        self.guild_data = []
        self.flaskport = kwargs.pop('flaskport', '8080')

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        for guild in self.guilds:
            print(f'{guild}')

        print(f'my callback url and port are: {self.callbackurl} - {self.flaskport}')



if __name__ == '__main__':
    load_dotenv()
    intents = discord.Intents.all()
    callbackurl = os.getenv('CALLBACK')
    port = os.getenv('PORT')

    bot = SpotWatcher(command_prefix="!",intents=intents, callbackurl=callbackurl, flaskport=port)

    TOKEN = os.getenv('DISCORD_TOKEN')
    bot.run(TOKEN)