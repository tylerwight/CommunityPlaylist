import mysql.connector
import os
from community_playlist.db.config import sqluser, sqlpass

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=sqluser,
        password=sqlpass,
        database=os.getenv("MYSQL_DB", "discord")
    )
