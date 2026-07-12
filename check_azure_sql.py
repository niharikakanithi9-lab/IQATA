import pyodbc

server = "iqata-server.database.windows.net"
database = "iqata-db"
username = "iqata-admin"
password = "nihakanika-1028"

connection_string = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server=tcp:{server},1433;"
    f"Database={database};"
    f"Uid={username};"
    f"Pwd={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

try:
    conn = pyodbc.connect(connection_string)

    cursor = conn.cursor()
    cursor.execute("SELECT 1")

    result = cursor.fetchone()

    print("✅ Azure SQL Connection Successful")
    print("Result:", result)

    conn.close()

except Exception as e:
    print("❌ Connection Failed")
    print(e)