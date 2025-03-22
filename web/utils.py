import mysql.connector
import logging
import requests
from config import invited_users, sqluser, sqlpass, bot_api_url



def check_guild_admin(user_guilds, target_guild):
    logging.info(f"Checking if user is an admin of guild {target_guild}")
    for guild in user_guilds:
        if guild.permissions.administrator:
            if str(guild.id) == str(target_guild):
                logging.info(f"User is an admin of guild {target_guild}")
                return True, guild

    return False, None

async def check_bot_exists(guild_id):
    response = bot_api_call(endpoint="guild", payload={"guild_id": guild_id}, method="POST")
    if not response:
        logging.warning(f"No response received from bot API for guild {guild_id}")
        return False
    
    data = response.json()
    logging.info(f"API call to bot response: {data}")
    
    if 'error' in data: 
        logging.info(f"Guild {guild_id} does not have the bot running: {data['error']}")
        return False
    else:
        logging.info(f"Guild {guild_id} has the bot running: {data}")
        return True
    
def query_db(sql_string):
    if sql_string == None:
        logging.error("Empty DB query")
        return None
    if not (sql_string.startswith("SELECT") or sql_string.startswith("select")):
        logging.error("DB Query malformed")
        return None
    
    try:
        mydb = mysql.connector.connect(host = "localhost", user = sqluser, password = sqlpass, database = "discord")
        cursor = mydb.cursor()
    except Exception as e:
        logging.error(f'Error connecting to Mysql DB error: {e}')

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

def bot_api_call(endpoint, payload = None, method = 'GET'):
    url = f"{bot_api_url}{endpoint}"
    logging.info(f"making API call to URL: {url}")

    try:
        if method == 'POST':
            response = requests.post(url, json=payload)
        elif method == 'GET':
            response = requests.get(url)
        else:
            logging.error(f"Bot api call has malformed method (not POST or GET)")
            return None

        response.raise_for_status()
        return response


    except requests.RequestException as e:
        logging.error(f"Error during bot API call to {url}: {e}")
    
        return None