import sqlite3

from datetime import datetime as dt


class DBManager:
    def __init__(self):
        self.connection = sqlite3.connect('my_database.db')
        self.cursor = self.connection.cursor()

    def query(self, query):
        self.cursor.execute(query)
        self.connection.commit()

    def insert_message(self, id_message, coin, deal_type):
        now = dt.now()
        query = f'INSERT INTO Messages (id_message, datetime, coin, deal_type, active) VALUES ({id_message}, "{now}", "{coin}", "{deal_type}", 1)'
        self.query(query)

    def select_active_message(self, id_message):
        query = f'SELECT coin FROM Messages WHERE id_message = "{id_message}" AND active = 0'
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def select_active_hold(self, id_message):
        query = f'SELECT deal_type FROM Messages WHERE id_message = "{id_message}" AND active = 0'
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def close_deal(self, id_message):
        query = f'UPDATE Messages SET active = 0 WHERE id_message = "{id_message}"'
        self.query(query)

    def close(self):
        self.connection.close()
