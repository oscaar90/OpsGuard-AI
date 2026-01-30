import sqlite3

def get_user(username):
    # SQL Injection clara para que la IA se luzca
    query = f"SELECT * FROM users WHERE name = '{username}'" 
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.execute(query)
    return cursor.fetchone()