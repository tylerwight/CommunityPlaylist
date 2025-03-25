# CommunityPlaylist
A Python Discord bot that monitors your Discord server for Spotify links and creates a running playlist of the music.

At a glance:
- Uses discord.py and spotipy to interface with Discord and Spotify
- Web frontend (flask/quart) for users to manage bot status, configuration, and Spotify authentication.
- Frontend and bot communicate with FastAPI api calls
- Users quart_discord for website's "login with Discord" functionality
- Full multi user support with the intention on it being a public application
- At the moment the offical website is invite only as I am working toward getting the Spotify app approved.

https://communityplaylist.org

![web](image.png)


Bot commands:
- !get_playlist
- all other management and configuration of the bot is done on the web interface.

## How To Build:
Steps to setup and run this code

- use setup.sh to create a mysql server with database named "discord" and correct schema
- use pipsetup.sh to ensure you have all the correct python libraries
- create a .env file in the root of this repo with the below data (both the web and bot look at the same .env file in root)
```
DISCORD_TOKEN=
DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
MYSQL_USER=discord
MYSQL_PASS=
SPOTIPY_CLIENT_ID=
SPOTIPY_CLIENT_SECRET=
DISCORD_URL= "<url to add bot to discord server>"
DISCORD_CLIENT_REDIRECT_URL="<url>/callback_D"
CALLBACK="<url>/callback"
PORT = "8080"
INVITED = '["<discord_user_id>", "<discord_user_id>"]'
```
- run `cd web; bash ./start_webserver.sh` to start website
- run `cd bot; python3 CommunityPlaylistbot.py` to start the bot
- navigate to the web interface to add your bot to a server and test

## TODO:
- [x] Add web frontent to manage authentication
- [x] Use discord.py's Cogs for commands
- [x] sql connection
- [x] clean up sql code and architecture
- [x] streamline spotify authentication (using web frontend)
- [x] add ability to see login info on web frontend, and in turn, confirm your authentication data is removed
- [ ] update to discords built in command prefix stuff
- [x] Update readme with new howto info
- [ ] Store Spotify keys in a better place
- [ ] Make better setup script
- [ ] redesign database schema
- [ ] add testing
- [ ] add automated deploying/updating
- [ ] add automated testing
- [ ] update pictures on website



