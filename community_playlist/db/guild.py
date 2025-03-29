import logging
from community_playlist.db.schema import GUILD_TABLE, GUILD_COLUMNS
from community_playlist.db.queries import select_one, update, select_all


def get_enabled_status(guild_id):
    query = f"SELECT {GUILD_COLUMNS['enabled']} FROM {GUILD_TABLE} WHERE {GUILD_COLUMNS['id']} = %s"
    try:
        result = select_one(query, (guild_id,))
        return result[0] if result else None
    except Exception as e:
        logging.error(f"DB error getting enabled status for guild {guild_id}: {e}")
        return None


def set_enabled_status(guild_id, status):
    query = f"UPDATE {GUILD_TABLE} SET {GUILD_COLUMNS['enabled']} = %s WHERE {GUILD_COLUMNS['id']} = %s"
    try:
        affected = update(query, (status, guild_id))
        return affected
    except Exception as e:
        logging.error(f"DB error updating enabled status for guild {guild_id}: {e}")
        return 0


def get_token(guild_id):
    query = f"SELECT {GUILD_COLUMNS['sp_token']} FROM {GUILD_TABLE} WHERE {GUILD_COLUMNS['id']} = %s"
    try:
        result = select_one(query, (guild_id,))
        return result[0] if result else None
    except Exception as e:
        logging.error(f"DB error getting token for guild {guild_id}: {e}")
        return None


def update_token(guild_id, token_data):
    query = f"UPDATE {GUILD_TABLE} SET {GUILD_COLUMNS['sp_token']} = %s WHERE {GUILD_COLUMNS['id']} = %s"
    try:
        affected = update(query, (token_data, guild_id))
        return affected
    except Exception as e:
        logging.error(f"DB error updating token for guild {guild_id}: {e}")
        return 0

def get_watch_channel(guild_id):
    query = f"SELECT {GUILD_COLUMNS['wch_channel']} FROM {GUILD_TABLE} WHERE {GUILD_COLUMNS['id']} = %s"
    try:
        result = select_one(query, (guild_id,))
        return result[0] if result else None
    except Exception as e:
        logging.error(f"DB error getting watch_channel for guild {guild_id}: {e}")
        return None


def set_watch_channel(guild_id, channel_id):
    query = f"UPDATE {GUILD_TABLE} SET {GUILD_COLUMNS['wch_channel']} = %s WHERE {GUILD_COLUMNS['id']} = %s"
    try:
        affected = update(query, (channel_id, guild_id))
        return affected
    except Exception as e:
        logging.error(f"DB error updating watch_channel for guild {guild_id}: {e}")
        return 0


def get_playlist(guild_id):
    query = f"SELECT {GUILD_COLUMNS['playlist_name']}, {GUILD_COLUMNS['playlist_id']} FROM {GUILD_TABLE} WHERE {GUILD_COLUMNS['id']} = %s"
    try:
        result = select_one(query, (guild_id,))
        if result:
            return {
                "name": result[0],
                "id": result[1]
            }
        return None
    except Exception as e:
        logging.error(f"DB error getting playlist info for guild {guild_id}: {e}")
        return None


def set_playlist(guild_id, playlist_name, playlist_id):
    query = f"UPDATE {GUILD_TABLE} SET {GUILD_COLUMNS['playlist_name']} = %s, {GUILD_COLUMNS['playlist_id']} = %s WHERE {GUILD_COLUMNS['id']} = %s"
    try:
        affected = update(query, (playlist_name, playlist_id, guild_id))
        return affected
    except Exception as e:
        logging.error(f"DB error updating playlist info for guild {guild_id}: {e}")
        return 0


def get_full_guild(guild_id):
    query = f"""
        SELECT 
            {GUILD_COLUMNS['id']},
            {GUILD_COLUMNS['name']},
            {GUILD_COLUMNS['sp_token']},
            {GUILD_COLUMNS['wch_channel']},
            {GUILD_COLUMNS['enabled']},
            {GUILD_COLUMNS['playlist_name']},
            {GUILD_COLUMNS['playlist_id']}
        FROM {GUILD_TABLE}
        WHERE {GUILD_COLUMNS['id']} = %s
    """
    try:
        result = select_one(query, (guild_id,))
        if not result:
            return None
        return {
            "guild_id":      result[0],
            "name":          result[1],
            "spotipy_token": result[2],
            "watch_channel": result[3],
            "enabled":       result[4],
            "playlist_name": result[5],
            "playlist_id":   result[6],
        }
    except Exception as e:
        logging.error(f"DB error getting full guild record for {guild_id}: {e}")
        return None


def update_guild_columns(guild_id, values: dict):
    if not values:
        logging.warning("update_guild_columns: No values provided.")
        return 0

    # Filter only valid columns
    valid_columns = {key: GUILD_COLUMNS[key] for key in values if key in GUILD_COLUMNS}
    if not valid_columns:
        logging.warning("update_guild_columns: No valid columns found in input.")
        return 0

    # Build SET clause and value list
    set_clause = ", ".join(f"{col} = %s" for col in valid_columns.values())
    sql_values = [values[key] for key in valid_columns.keys()]
    sql_values.append(str(guild_id))

    query = f"UPDATE {GUILD_TABLE} SET {set_clause} WHERE {GUILD_COLUMNS['id']} = %s"

    logging.info(f"update_guild_columns: executing {query}")
    logging.info(f"with values: {sql_values}")

    try:
        return update(query, sql_values)
    except Exception as e:
        logging.error(f"update_guild_columns: Error updating DB: {e}")
        return 0


def create_guild_if_not_exists(guild_id, name):
    check_query = f"SELECT 1 FROM {GUILD_TABLE} WHERE {GUILD_COLUMNS['id']} = %s"
    insert_query = f"""
        INSERT INTO {GUILD_TABLE} 
        ({GUILD_COLUMNS['id']}, {GUILD_COLUMNS['name']}, {GUILD_COLUMNS['enabled']}, {GUILD_COLUMNS['sp_token']})
        VALUES (%s, %s, %s, %s)
    """

    try:
        existing = select_one(check_query, (guild_id,))
        if existing:
            return False 

        inserted = update(insert_query, (guild_id, name, 0, "none"))
        return inserted > 0
    except Exception as e:
        logging.error(f"Error inserting new guild {guild_id}: {e}")
        return False


def get_all_guilds():
    query = f"""
        SELECT 
            {GUILD_COLUMNS['id']},
            {GUILD_COLUMNS['name']},
            {GUILD_COLUMNS['sp_token']},
            {GUILD_COLUMNS['wch_channel']},
            {GUILD_COLUMNS['enabled']},
            {GUILD_COLUMNS['playlist_name']},
            {GUILD_COLUMNS['playlist_id']}
        FROM {GUILD_TABLE}
    """
    try:
        return select_all(query)
    except Exception as e:
        logging.error(f"DB error fetching all guilds: {e}")
        return []
