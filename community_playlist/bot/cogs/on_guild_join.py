import logging
import mysql.connector
from discord.ext import commands
import community_playlist.db as db

class on_guild_join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logging.info('===========================')
        logging.info(f'{guild} just added the Discord bot!')
        logging.info('===========================')

        guild_id_str = str(guild.id)
        guild_name = str(guild.name)

        # Try to insert new guild if it doesn't exist
        created = db.guild.create_guild_if_not_exists(guild_id_str, guild_name)

        if created:
            logging.info("New Guild detected, added to DB.")
            # Set default state in memory
            self.bot.guilds_state[guild_id_str] = {
                "guild_id":      guild_id_str,
                "name":          guild_name,
                "spotipy_token": "NULL",
                "watch_channel": "",
                "enabled":       0,
                "playlist_name": "",
                "playlist_id":   ""
            }
        else:
            logging.info(f"This newly joined guild already exists in the DB. Loading data for {guild_id_str}.")
            full_data = db.guild.get_full_guild(guild_id_str)
            if full_data:
                self.bot.guilds_state[guild_id_str] = full_data
                logging.info(f"Data loaded: {full_data}")
            else:
                logging.warning(f"Could not load existing guild data for {guild_id_str}")
    



async def setup(bot):
    await bot.add_cog(on_guild_join(bot))