import os
from dotenv import load_dotenv
import json
from quart import Blueprint, render_template
from config import ddiscord, app
from utils import is_invited

home_bp = Blueprint("home", __name__) 

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path)

invited_users = json.loads(os.getenv('INVITED', '[]'))

@app.route("/")
async def home():
    authorized = await ddiscord.authorized

    
    if authorized:
        user = await ddiscord.fetch_user()
        if is_invited(user):
            return await render_template("index.html", authorized = authorized, username = user.name)

        return await render_template("not_invited.html", username=name, authorized=authorized)
        
    
    return await render_template("index.html", authorized = authorized, username = "none")