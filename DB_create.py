import sqlite3

conn = sqlite3.connect("pool.db")
cursor = conn.cursor()

# Созадём таблицы
cursor.execute("""CREATE TABLE users
                  (id integer PRIMARY KEY AUTOINCREMENT NOT NULL , telegram_id TEXT, name TEXT, balance DOUBLE, rate DOUBLE )""")

cursor.execute("""CREATE TABLE withdrawal
                  (id integer PRIMARY KEY AUTOINCREMENT NOT NULL , telegram_id TEXT, name TEXT, amount DOUBLE, date TEXT )""")
