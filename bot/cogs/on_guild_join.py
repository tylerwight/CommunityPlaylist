import logging
import mysql.connector
from discord.ext import commands

class on_guild_join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logging.info('===========================')
        logging.info(f'{guild} just added the discord bot!')
        logging.info('===========================')

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

        guild_id_str = str(guild.id)

        # Check if this guild already exists in the DB
        cursor.execute("SELECT * FROM guilds WHERE guild_id = %s", (guild_id_str,))
        record = cursor.fetchone()

        if record is None:
            logging.info("New Guild detected, adding to DB")

            # Insert a minimal row into the database
            sql = """INSERT INTO guilds (guild_id, name, enabled, spotipy_username)
                     VALUES (%s, %s, %s, %s)"""
            val = (guild_id_str, str(guild.name), 0, "none")
            cursor.execute(sql, val)
            mydb.commit()

            logging.info(f'Inserted {cursor.rowcount} rows for guild {guild_id_str} ({guild.name}).')

            # Add to guilds_state
            self.bot.guilds_state[guild_id_str] = {
                "guild_id":         guild_id_str,
                "name":             str(guild.name),
                "spotipy_username": "none",
                "watch_channel":    "",
                "enabled":          0,
                "playlist_name":    "",
                "playlist_id":      ""
            }

        else:
            logging.info(f"This newly joined guild already exists in the DB. Loading data for {guild_id_str}.")

            # record should match our  table schema

            self.bot.guilds_state[guild_id_str] = {
                "guild_id":         record[0],
                "name":             record[1],
                "spotipy_username": record[2],
                "watch_channel":    record[3],
                "enabled":          record[4],
                "playlist_name":    record[5],
                "playlist_id":      record[6]
            }
            
            logging.info(f"Data loaded: {self.bot.guilds_state[guild_id_str]}")

        cursor.close()
        mydb.close()
    



async def setup(bot):
    await bot.add_cog(on_guild_join(bot))