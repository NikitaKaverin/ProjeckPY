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

    def query_with_commit(self, query):
        self.cursor.execute(query)
        self.connection.commit()

    def select_coin(self, name):
        query = f'SELECT * FROM Coins WHERE name LIKE "{name}"'
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def check_active_deal(self, coin, deal_type):
        query = f'SELECT COUNT(*) AS flag FROM Messages WHERE coin = "{coin}" AND deal_type = "{deal_type}" AND active = 1'
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def get_active_deal(self, coin, deal_type):
        query = f'SELECT * from Messages WHERE coin = "{coin}" AND deal_type = "{deal_type}" AND active = 1'
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def save_deal(self, id_message, coin, deal_type, hold_side, order_id, client_oid):
        now = dt.now()
        query = (f'INSERT INTO Messages '
                 f'(id_message, datetime, coin, deal_type, hold_side, orderId, clientOid, active) '
                 f'VALUES '
                 f'({id_message}, "{now}", "{coin}", "{deal_type}", "{hold_side}", {order_id}, {client_oid}, 1)')
        self.query_with_commit(query)

    def update_deal_status(self, deal_id, status):
        query = f'UPDATE Messages SET active = {status} WHERE id = {deal_id}'
        self.query_with_commit(query)

    def get_deal_by_msg_id(self, msg_id):
        query = f'SELECT * FROM Messages WHERE id_message = {msg_id}'
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def initDB(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS Messages (
        id INTEGER PRIMARY KEY,
        id_message TEXT NOT NULL,
        datetime DATETIME,
        coin TEXT,
        hold_side TEXT,
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
