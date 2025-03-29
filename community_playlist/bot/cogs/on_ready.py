import discord
from discord.ext import commands
import mysql.connector
import logging
import community_playlist.db as db


class on_ready(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f'{self.bot.user} has connected to Discord!')

        existing_guilds = db.guild.get_all_guilds()
        db_guild_ids = {record[0] for record in existing_guilds}
        logging.debug(f"Existing guilds in DB: {db_guild_ids}")

        for connected_guild in self.bot.guilds:
            guild_id_str = str(connected_guild.id)

            if guild_id_str in db_guild_ids:
                logging.info(f"Found connected guild in DB: {guild_id_str}, loading data...")
                full_data = db.guild.get_full_guild(guild_id_str)
                if full_data:
                    self.bot.guilds_state[guild_id_str] = full_data
            else:
                logging.info(f"Guild {guild_id_str} not found in DB, inserting.")

                db.guild.create_guild_if_not_exists(guild_id_str, connected_guild.name)

                self.bot.guilds_state[guild_id_str] = {
                    "guild_id":      guild_id_str,
                    "name":          connected_guild.name,
                    "spotipy_token": "NULL",
                    "watch_channel": "",
                    "enabled":       0,
                    "playlist_name": "",
                    "playlist_id":   ""
                }


        logging.info("Guild Data after on_ready:")
        for data in self.bot.guilds_state.values():
            logging.info(f"\n{data}")
 



async def setup(bot):
    await bot.add_cog(on_ready(bot))