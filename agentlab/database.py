"""SQLite durability settings shared by business state and policy checkpoints."""
import sqlite3


def connect(database):
    connection = sqlite3.connect(database)
    try:
        connection.execute('PRAGMA journal_mode = WAL')
        connection.execute('PRAGMA synchronous = FULL')
        connection.execute('PRAGMA foreign_keys = ON')
    except BaseException:
        connection.close()
        raise
    return connection
