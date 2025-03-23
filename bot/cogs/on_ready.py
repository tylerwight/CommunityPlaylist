import discord
from discord.ext import commands
import mysql.connector
import logging

class on_ready(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f'{self.bot.user} has connected to Discord!')

        try:
            mydb = mysql.connector.connect(
                host="localhost",
                user=self.bot.sqluser,
                password=self.bot.sqlpass,
                database="discord"
            )
            cursor = mydb.cursor()
        except Exception as e:
            logging.error(f'Error connecting to MySQL DB: {e}')
            return

        cursor.execute("SELECT * FROM guilds")
        existing_guilds = cursor.fetchall()
        logging.debug(f"Existing guilds in DB: {existing_guilds}")

        #look through guilds that the bot is connected to, and compare them to guilds we have in the DB to match them up
        for connected_guild in self.bot.guilds:
            found = False
            for existing_guild in existing_guilds:
                if str(connected_guild.id) == existing_guild[0]:
                    logging.info(f"found connected guild: {connected_guild.id} in DB:{existing_guild[0]}, Loading data")
                    self.bot.guilds_state[existing_guild[0]] = {
                        "guild_id":         existing_guild[0],
                        "name":             existing_guild[1],
                        "spotipy_username": existing_guild[2],
                        "watch_channel":    existing_guild[3],
                        "enabled":          existing_guild[4],
                        "playlist_name":    existing_guild[5],
                        "playlist_id":      existing_guild[6],
                    }
                    found = True
                    break

            if not found:
                logging.info(f"Guild {connected_guild.id} not in DB, adding to DB.")
                self.bot.guilds_state[str(connected_guild.id)] = {
                    "guild_id":         str(connected_guild.id),
                    "name":             connected_guild.name,
                    "spotipy_username": "none",
                    "watch_channel":    "",
                    "enabled":          "0",
                    "playlist_name":    "",
                    "playlist_id":      "",
                }
                sql = "INSERT INTO guilds (guild_id,name,enabled, spotipy_username) VALUES (%s, %s, %s, %s)"
                val = (self.bot.guilds_state[str(connected_guild.id)]["guild_id"],
                       self.bot.guilds_state[str(connected_guild.id)]["name"],
                       0, "tmp"
                      )
                cursor.execute(sql, val)
                mydb.commit()

        logging.info("Guild Data after on_ready:")
        for data in self.bot.guilds_state.values():
            logging.info(f"\n{data}")




        cursor.close()
        mydb.close()
 



async def setup(bot):
    await bot.add_cog(on_ready(bot))