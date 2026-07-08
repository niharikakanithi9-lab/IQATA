from database.sqlite_db import SQLiteDB

db = SQLiteDB()
db.connect()

print("Test Cases:", db.fetchone("SELECT COUNT(*) FROM test_cases")[0])
print("Test Runs :", db.fetchone("SELECT COUNT(*) FROM test_runs")[0])

db.close()