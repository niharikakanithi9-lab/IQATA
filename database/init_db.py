from config import DATABASE_TYPE, SQLITE_DB, AZURE_SQL_CONNECTION
from database.sqlite_db import SQLiteDB
from database.azure_sql import AzureSQL

if DATABASE_TYPE == "azure":
    db = AzureSQL(AZURE_SQL_CONNECTION)
else:
    db = SQLiteDB(SQLITE_DB)

db.connect()

with open("database/schema.sql", "r") as file:
    schema = file.read()

if DATABASE_TYPE == "sqlite":
    db.connection.executescript(schema)
else:
    for statement in schema.split(";"):
        statement = statement.strip()
        if statement:
            try:
                db.execute(statement)
            except Exception:
                pass

print("Database initialized successfully!")

db.close()