import sqlite3

from datetime import datetime as dt


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DBManager:
    def __init__(self):
        self.connection = sqlite3.connect('my_database.db')
        self.connection.row_factory = dict_factory
        self.cursor = self.connection.cursor()

    def query(self, query):
        self.cursor.execute(query)
        self.connection.commit()

    def insert_message(self, id_message, coin, deal_type, orderId, clientOid, fee):
        now = dt.now()
        query = (f'INSERT INTO Messages '
                 f'(id_message, datetime, coin, deal_type, orderId, clientOid, fee, pnl, active) '
                 f'VALUES '
                 f'({id_message}, "{now}", "{coin}", "{deal_type}", {orderId}, {clientOid}, {fee}, 0, 1)')
        self.query(query)

    def update_message(self, id, id_message_new, orderId, clienOid, fee):
        query = f'UPDATE Messages SET orderId = {orderId}, clientOid = {clienOid}, fee = {fee}, id_message = {id_message_new} WHERE id = {id}'
        self.query(query)

    def select_message(self, coin):
        query = f'SELECT * FROM Messages WHERE coin = "{coin}" AND active = 1'
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def select_active_message(self, id_message):
        query = f'SELECT id, coin, deal_type, orderId, clientOid, fee FROM Messages WHERE id_message = "{id_message}"'
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def close_deal(self, id_message, pnl, fee):
        query = f'UPDATE Messages SET active = 0, pnl = {pnl}, fee = {fee} WHERE id_message = "{id_message}"'
        self.query(query)

    def manual_close_deal(self, id, totalProfits, fee):
        query = f'UPDATE Messages SET active = 2, pnl = {totalProfits}, fee = fee + {fee} WHERE id = {id} AND active = 1'
        self.query(query)

    def add_coin(self, name, maxLever):
        query = f'INSERT INTO Coins(name, maxLever) VALUES ("{name}", {maxLever})'
        self.query(query)

    def select_coin(self, name):
        query = f'SELECT name, maxLever FROM Coins WHERE name LIKE "{name}"'
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def update_coin(self, name, maxLever):
        query = f'UPDATE Coins SET maxLever = {maxLever} WHERE name = {name}'
        self.query(query)

    def initDB(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS Messages (
        id INTEGER PRIMARY KEY,
        id_message TEXT NOT NULL,
        datetime DATETIME,
        coin TEXT,
        deal_type TEXT,
        orderId INTEGER,
        clientOid INTEGER,
        fee FLOAT,
        pnl FLOAT,
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
