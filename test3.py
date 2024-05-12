import sqlite3

connection = sqlite3.connect('my_database.db')
cursor = connection.cursor()

cursor.execute('UPDATE Messages SET active = 1 WHERE id = 3')
connection.commit()

# cursor.execute('''SELECT COUNT(*) FROM Messages WHERE coin = "SBTCSUSDT" AND deal_type = "SELL" AND active = 1''')

# cursor.execute("DROP Table Messages")
# cursor.execute("""CREATE TABLE IF NOT EXISTS Messages (
# id INTEGER PRIMARY KEY,
# id_message TEXT NOT NULL,
# datetime DATETIME,
# coin TEXT,
# hold_side TEXT,
# deal_type TEXT,
# orderId INTEGER,
# clientOid INTEGER,
# active INTEGER
# )""")
