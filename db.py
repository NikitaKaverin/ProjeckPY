import sqlite3

from datetime import datetime as dt


class DBManager:
    def __init__(self):
        self.connection = sqlite3.connect('my_database.db')
        self.cursor = self.connection.cursor()

    def query(self, query):
        self.cursor.execute(query)
        self.connection.commit()

    def insert_message(self, id_message, coin, deal_type, orderId, clientOid):
        now = dt.now()
        query = f'INSERT INTO Messages (id_message, datetime, coin, deal_type, orderId, clientOid, active) VALUES ({id_message}, "{now}", "{coin}", "{deal_type}", {orderId}, {clientOid}, 1)'
        self.query(query)

    def select_active_message(self, id_message):
        query = f'SELECT coin, deal_type, orderId, clientOid FROM Messages WHERE id_message = "{id_message}" AND active = 1'
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def close_deal(self, id_message):
        query = f'UPDATE Messages SET active = 0 WHERE id_message = "{id_message}"'
        self.query(query)

    def add_coin(self, name, maxLever):
        query = f'INSERT INTO Coins(name, maxLever) VALUES ("{name}", {maxLever})'
        self.query(query)

    def select_coin(self, name):
        query = f'SELECT name, maxLever FROM Coins WHERE name LIKE "{name}"'
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def initDB(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS Messages (
        id INTEGER PRIMARY KEY,
        id_message TEXT NOT NULL,
        datetime DATETIME,
        coin TEXT,
        deal_type TEXT,
        orderId INTEGER,
        clientOid INTEGER,
        active INTEGER
        )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS Coins(
        name TEXT,
        maxLever INTEGER
        )""")

    def close(self):
        self.connection.close()


if __name__ == '__main__':
    db = DBManager()
    db.query("""DROP TABLE Messages""")
    db.initDB()
