import sqlite3
from core.database import DB_FILE

class SQLiteManager:
    def __init__(self):

        self.conn = sqlite3.connect(
            DB_FILE,
            timeout=30,
            check_same_thread=False
        )

        self.conn.row_factory = sqlite3.Row

        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self.conn.execute("PRAGMA busy_timeout=10000;")

    def execute(self, sql, params=()):
        cursor = self.conn.cursor()
        cursor.execute(sql, params)

        self.conn.commit()

        return cursor

    def query(self, sql, params=()):
        cursor = self.conn.cursor()
        cursor.execute(sql, params)

        return cursor.fetchall()

    def close(self):
        self.conn.close()
        