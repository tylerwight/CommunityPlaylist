# SpotWatcher
A discord bot that will watch a specified discord channel for new spotify links when posted, and add them to a playlist on the fly. This bot supports having multiple separate discord servers. Keeps track of it's state in a mysql database and picks up where it left off on startup.



## How to Install:


* Run setup.sh to prep the environment. This will install python, all pip packages, mysql, and prep mysql for use with SpotWatcher. Be sure to change your mysql password and note the username/password
* Create a bot in the Discord developer Portal and auth it to your discord server. Be sure to note the bot token
* Create a spotify app on the spotify developer portal. Be sure to note the spotify client id and secret.
* Create a file in the same directory as the script named exactly ".env". This is a file to hold secrets.
* This .env file will house all our secrets for both spotify and discord. Here is how the file should look:

```
DISCORD_TOKEN='<Token>'
MYSQL_USER='discord'
MYSQL_PASS='<mysql password>'
SPOTIPY_CLIENT_ID='<spotify_client_id>'
SPOTIPY_CLIENT_SECRET='<spotify_client_secret>'
CALLBACK="<URL for Spotify Callback>" (http://localhost:8080/callback for testing locally)
PORT = "8080"
```

Once everything has been been setup, start the bot like this:
```
python3 SpotWatcher.py
```



## How to Use:

note: default command prefix is "_" so be defualt to run the auth_me command will be "_auth_me"

1. Use the "auth_me <spotify username>" command to authenticate to spotify.
    - Get the username by logging into spotify on a web browser and going to account section, it could be a random bunch of numbers/letters
    - Click the link the bot posts to open spotify in a browser where you are logged into your account you want to share
    - Click authroize, it will redirect to a url that will fail, it may take a few seconds to timeout.
    - Read the URL in the address bar.In the url there is a section "code=xxxxyyyyxxxxyy". Copy the entire code, only the data after "code="
    - Paste it in the chat channel with the bot where it asked

2. Use "set_playlist <name>" to choose a spotify playlist to put stuff in. If it exists in your account already it will add to it, if it doesn't it will create it.

3. Use "set_channel <channel_id>" to choose which channel it watches for spotify links. You can get the text channel id by right clicking -> copy link. Paste the link somewhere to look at it. The channel ID is the final (right-most) number.

4. Use the "enable" command to turn on (or off) monitoring of the channel for spotify links. "_enable"

5. Paste a spotify link in the channel you set. If all is well, it should be automatically added to the playlist you setup, using the account you authenticated with.


## Commands:

- auth_me <spotify username>    - The authentication process for a spotify user to allow the bot to post
- enable                        - Enables or disable the bot actively monitoring and adding songs.
- get_playlist                  - Displays the spotify playlist currently in use for adding songs.
- set_channel <channel ID>      - Set/change the channel ID of the channel you want the bot to monitor
- set_playlist <playlist_name>  - Set/change the spotify playlist to use for adding songs. If it finds an existing playlist it will add to it, otherwise it will create a new one.


## TODO:
- add web frontend (half way done)
- steamline spotify authentication (using web frontend)
- add ability to see login info on web frontend, and in turn, confirm your authentication data is removed
- update to discords build in command prefix stuff