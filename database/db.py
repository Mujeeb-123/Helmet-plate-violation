import os
import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQLHOST", "localhost"),
            port=int(os.getenv("MYSQLPORT", "3306")),
            user=os.getenv("MYSQLUSER", "root"),
            password=os.getenv("MYSQLPASSWORD", ""),
            database=os.getenv("MYSQLDATABASE", "helmet_violation_db")
        )

        return conn

    except Error as e:
        print(f"MySQL Connection Error: {e}")
        return None