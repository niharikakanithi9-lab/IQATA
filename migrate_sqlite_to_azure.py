from database.sqlite_db import SQLiteDB
from database.azure_sql import AzureSQL
from config import AZURE_SQL_CONNECTION
from datetime import datetime

# Connect databases
sqlite_db = SQLiteDB()
sqlite_db.connect()

azure_db = AzureSQL(AZURE_SQL_CONNECTION)
azure_db.connect()

# -----------------------------
# Migrate test_cases
# -----------------------------

print("Migrating test_cases...")

test_cases = sqlite_db.fetchall("""
SELECT id, name, module, browser, environment,
       priority, active, created_at
FROM test_cases
""")

# Mapping: old SQLite ID -> new Azure ID
id_map = {}

for row in test_cases:

    old_id = row[0]

    azure_db.cursor.execute("""
    INSERT INTO test_cases
    (name, module, browser, environment,
     priority, active, created_at)
    OUTPUT INSERTED.id
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    row[1:])

    new_id = azure_db.cursor.fetchone()[0]
    azure_db.connection.commit()

    id_map[old_id] = new_id

print(f"✅ Migrated {len(test_cases)} test cases")

# -----------------------------
# Migrate test_runs
# -----------------------------

print("Migrating test_runs...")

test_runs = sqlite_db.fetchall("""
SELECT
test_case_id,
status,
execution_time,
started_at,
ended_at,
failure_reason,
suggested_root_cause,
screenshot_url,
log_url
FROM test_runs
""")

count = 0

for row in test_runs:
    try:
        new_test_case_id = id_map[row[0]]
        started_at = datetime.fromisoformat(row[3]) if row[3] else None
        ended_at = datetime.fromisoformat(row[4]) if row[4] else None
        azure_db.execute("""
        INSERT INTO test_runs
        (
            test_case_id,
            status,
            execution_time,
            started_at,
            ended_at,
            failure_reason,
            suggested_root_cause,
            screenshot_url,
            log_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
    new_test_case_id,
    row[1],
    row[2],
    started_at,
    ended_at,
    row[5],
    row[6],
    row[7],
    row[8]
    ))

        count += 1

    except Exception as e:
        print("\n❌ Failed row:")
        print(row)
        print("\nError:")
        print(e)
        break

print(f"✅ Migrated {count} test runs")

sqlite_db.close()
azure_db.close()

print("\n🎉 Migration completed successfully!")