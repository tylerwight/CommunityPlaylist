from spotipy import CacheHandler 
import mysql.connector
from nacl import secret, utils
from nacl.encoding import Base64Encoder
import json
import logging


"""
Class that is a Cache Handler for Spotipy that allows you to encrypt and then store Spotify API tokens in SQL
"""
class CacheSQLHandler(CacheHandler):
    def __init__(self,
                 cache_sql_host = "localhost",
                 cache_database = "discord",
                 cache_table = "guilds",
                 cache_column="spotipy_token",
                 cache_where = None,
                 sqluser = None,
                 sqlpass = None,
                 encrypt=False,
                 key = None):
        
        self.cache_sql_host = cache_sql_host
        self.cache_database = cache_database
        self.cache_table = cache_table
        self.cache_column = cache_column
        self.cache_where = cache_where
        self.sqluser = sqluser
        self.sqlpass = sqlpass
        self.encrypt = encrypt
        self.box = None

        if encrypt == True and key == None:
            raise ValueError("CacheSQLHandler: Encrypt = True but no key given")
        if encrypt == True and key != None:
            self.box = secret.SecretBox(key)

    def get_cached_token(self):
        token_info = None

        try:
            mydb = mysql.connector.connect(
                host=self.cache_sql_host,
                user=self.sqluser,
                password=self.sqlpass,
                database=self.cache_database
            )
            cursor = mydb.cursor()
        except Exception as e:
            logging.error(f"CacheSQLHandler: Error connecting to MySQL DB: {e}")
            return None

        try:
            query = f"SELECT {self.cache_column} FROM {self.cache_table} WHERE {self.cache_where}"
            cursor.execute(query)
            record = cursor.fetchone()
            if not record:
                logging.error(f"CacheSQLHandler: No DB record found for {query}")
                return None
            
            if record[0] is None:
                logging.info(f"CacheSQLHandler: DB returned NULL, This account has no Spotify token")
                return None

            #set token_info
            if self.encrypt:
                logging.debug(f"CacheSQLHandler(DECRYPTION): Got this out of the DB: {record[0]}")
                decrypted = self.box.decrypt(record[0].encode(), encoder=Base64Encoder)
                token_info = json.loads(decrypted)
            else:
                token_info = json.loads(record[0])

            logging.debug(f"CacheSQLHandler: Got this out of the DB: {token_info}")

        except Exception as e:
            logging.error(f"Error during SELECT: {e}")
        finally:
            cursor.close()
            mydb.close()



        return token_info

    def save_token_to_cache(self, token_info):
        token_write = None
        try:
            mydb = mysql.connector.connect(
                host=self.cache_sql_host,
                user=self.sqluser,
                password=self.sqlpass,
                database=self.cache_database
            )
            cursor = mydb.cursor()
        except Exception as e:
            logging.error(f"CacheSQLHandler: Error connecting to MySQL DB: {e}")
            return None


        try:
            if self.encrypt:
                logging.debug(f"CacheSQLHandler(ENCRYPTED): Putting this in DB : {json.dumps(token_info)}")
                data = json.dumps(token_info).encode("utf-8")
                logging.debug(f"CacheSQLHandler(ENCRYPTED): Encoded: {data}")
                token_write = self.box.encrypt(data, encoder=Base64Encoder)
            else:
                token_write = json.dumps(token_info)

            logging.debug(f"CacheSQLHandler: Putting this in DB : {token_write}")
            update_query = f"UPDATE {self.cache_table} SET {self.cache_column} = %s WHERE {self.cache_where}"
            cursor.execute(update_query, (token_write.decode() if self.encrypt else token_write,))

            if cursor.rowcount == 0:
                logging.warning(f"CacheSQLHandler: Could not write to DB with: {update_query}")
                return None
            mydb.commit()


        except Exception as e:
            logging.error(f"Error during DB update: {e}")
        finally:
            cursor.close()
            mydb.close()