import os
import mysql.connector


class BaseRepository:

    def get_connection(self):
        return mysql.connector.connect(
            host=os.getenv("MYSQLHOST"),
            user=os.getenv("MYSQLUSER"),
            password=os.getenv("MYSQLPASSWORD"),
            database=os.getenv("MYSQLDATABASE"),
            port=int(os.getenv("MYSQLPORT", 3306)),
            autocommit=True
        )

    def get_cursor(self, dictionary=False):
        conn = self.get_connection()
        cursor = conn.cursor(
            dictionary=dictionary,
            buffered=True
        )
        return cursor, conn