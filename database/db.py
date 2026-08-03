import mysql.connector

def get_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Musadiq@2004",
        database="helmet_violation_db"
    )

