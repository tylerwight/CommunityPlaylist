import logging
from community_playlist.db.schema import GUILD_TABLE, GUILD_COLUMNS
from community_playlist.db.queries import select_one, update


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
