import sqlite3

conn = sqlite3.connect("qa_platform.db")
cursor = conn.cursor()

cursor.execute("""
SELECT started_at, ended_at
FROM test_runs
LIMIT 10
""")

for row in cursor.fetchall():
    print(row)

conn.close()