import os
import sqlite3
import json
import config

db_path = os.path.join(config.STATE_DIR, "offerbot.sqlite3")

def init_db():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS allowed_users (user_id INTEGER PRIMARY KEY)")
        # Added 'caption' column here
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_offers (
                offer_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_id INTEGER, 
                file_data TEXT, 
                caption TEXT
            )
        """)
        conn.commit()

def add_user(user_id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO allowed_users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def remove_user(user_id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM allowed_users WHERE user_id = ?", (user_id,))
        conn.commit()

def is_allowed(user_id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM allowed_users WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None

def save_pending_offer(user_id, media_list, caption):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pending_offers (user_id, file_data, caption) VALUES (?, ?, ?)", 
                       (user_id, json.dumps(media_list), caption))
        conn.commit()
        return cursor.lastrowid

def get_pending_offer(offer_id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, file_data, caption FROM pending_offers WHERE offer_id = ?", (offer_id,))
        row = cursor.fetchone()
        if row:
            return {"user_id": row[0], "media": json.loads(row[1]), "caption": row[2]}
        return None

def delete_pending_offer(offer_id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pending_offers WHERE offer_id = ?", (offer_id,))
        conn.commit()
