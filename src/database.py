import sqlite3
import os
from sqlite3.dbapi2 import Connection
import config

SQLITE_DB_PATH = "db/einundzwanzig.db"


def setup_database():
    """
    Sets up the database and initialises all tables
    Must be called before any requests can be sent
    """

    # database path
    if not os.path.exists('db'):
        os.mkdir('db')

    # database setup
    con = sqlite3.connect(SQLITE_DB_PATH)
    cur = con.cursor()

    # setup tables

    # ATH PRICE TABLE
    cur.execute('CREATE TABLE IF NOT EXISTS price (price_usd REAL, last_message_id INTEGER)')

    first_entry = cur.execute('SELECT * FROM price').fetchone()

    if first_entry is None and config.FEATURE_ATH_MANUAL_LAST_ATH != 0:
        cur.execute('INSERT INTO price (price_usd, last_message_id) VALUES (?, 0)',
                    (config.FEATURE_ATH_MANUAL_LAST_ATH,))

    con.commit()
    con.close()


def get_connection() -> Connection:
    """
    Returns a connection to the database
    """
    con = sqlite3.connect(SQLITE_DB_PATH)
    return con
