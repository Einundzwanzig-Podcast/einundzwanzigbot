import sqlite3
import os
from sqlite3.dbapi2 import Connection

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
    cur.execute('CREATE TABLE IF NOT EXISTS price (price_usd real)')

    con.commit()

def get_connection() -> Connection:
    con = sqlite3.connect(SQLITE_DB_PATH)
    return con