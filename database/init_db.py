from database.sqlite_db import SQLiteDB

db = SQLiteDB()
db.connect()

with open("database/schema.sql", "r") as file:
    schema = file.read()

db.connection.executescript(schema)

print("Database initialized successfully!")

db.close()