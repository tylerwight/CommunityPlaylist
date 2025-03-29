from community_playlist.db.session import get_connection

def select_one(query, params=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        cursor.close()
        return result

def select_all(query, params=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        cursor.close()
        return results

def update(query, params):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected
