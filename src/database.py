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

    con.commit()
    con.close()


def get_connection() -> Connection:
    """
    Returns a connection to the database
    """
    con = sqlite3.connect(SQLITE_DB_PATH)
    return con
