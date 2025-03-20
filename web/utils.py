import mysql.connector
import logging
from discord.ext.ipc.client import Client
from config import ddiscord, invited_users, sqluser, sqlpass

ipc_client = Client(secret_key = "test")

def convert_ipc_response(ipc_response):
	data = ipc_response.response
	elements = data.replace("[", "").replace("]", "").split(",")
	return [str(element) for element in elements]

def check_guild_admin(user_guilds, target_guild):
	for guild in user_guilds:
		if guild.permissions.administrator:
			print(f"you are an admin of this guild: {guild} with id {guild.id}, trying to see if you are admin of {target_guild}")
			if str(guild.id) == str(target_guild):
				return True, guild

	return False, None

async def check_bot_exists(guild_id):
	attempted_guild = await ipc_client.request("get_gld", guild_id = guild_id)
	if (attempted_guild.response == None) : 
		print("This guild does not have the bot running")
		return False
	else:
		print("This guild has the bot running")
		return True
	
def query_db(sql_string):
	if sql_string == None:
		print("empty string, no query")
		return None
	if not (sql_string.startswith("SELECT") or sql_string.startswith("select")):
		print("Didn't start with select")
		return None
	
	try:
		mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
		cursor = mydb.cursor()
	except Exception as e:
		logging.error(f'error connecting to Mysql DB error: {e}')

	cursor.execute(sql_string)
	out = cursor.fetchall()

	cursor.close()
	mydb.close()
	return out

def GetPlaylistID(username, playname, spotify_obj):
	playid = ''
	playlists = spotify_obj.user_playlists(username)
	for playlist in playlists['items']:  # iterate through playlists I follow
		if playlist['name'] == playname:  # filter for newly created playlist
			playid = playlist['id']
	return playid


def is_invited(user):
	id = str(user.id)
	if id in invited_users:
		return True
	return False