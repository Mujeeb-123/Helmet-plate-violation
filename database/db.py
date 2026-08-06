import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Musadiq@2004",
            database="helmet_violation_db"
        )

        return conn

    except Error as e:
        print(f"MySQL Connection Error: {e}")
        return None
