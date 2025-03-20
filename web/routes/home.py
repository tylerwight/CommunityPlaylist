import os
from dotenv import load_dotenv
import json
from quart import Blueprint, render_template
from config import ddiscord, app

home_bp = Blueprint("home", __name__) 

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path)

invited_users = json.loads(os.getenv('INVITED', '[]'))

@app.route("/")
async def home():
	# resp = await ipc_client.request("get_guild_data")
	authorized = await ddiscord.authorized
	print(invited_users)


	if authorized:
		if is_invited((await ddiscord.fetch_user())):
			return await render_template("index.html", authorized = await ddiscord.authorized, username = (await ddiscord.fetch_user()).name)
		return await render_template("not_invited.html")
		
	
	return await render_template("index.html", authorized = await ddiscord.authorized, username = "none")