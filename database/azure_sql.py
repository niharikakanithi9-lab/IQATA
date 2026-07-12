import pyodbc

from database.base_db import BaseDatabase


class AzureSQL(BaseDatabase):

    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None
        self.cursor = None

    def connect(self):
        if self.connection is None:
            self.connection = pyodbc.connect(self.connection_string)
            self.cursor = self.connection.cursor()

    def execute(self, query, params=()):
        self.connect()
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetchall(self, query, params=()):
        self.connect()
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetchone(self, query, params=()):
        self.connect()
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None