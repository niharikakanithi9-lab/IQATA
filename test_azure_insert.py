from database.azure_sql import AzureSQL
from config import AZURE_SQL_CONNECTION

db = AzureSQL(AZURE_SQL_CONNECTION)

db.connect()

db.execute("""
INSERT INTO test_cases
(name, module, browser, environment, priority)
VALUES
(
    'Login Test',
    'Authentication',
    'Chrome',
    'Production',
    0.9
)
""")

print("✅ Insert successful")

rows = db.fetchall("SELECT * FROM test_cases")

for row in rows:
    print(row)

db.close()