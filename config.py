
import os

# ==========================================
# Database Configuration
# ==========================================

# Choose: sqlite or azure
DATABASE_TYPE = "sqlite"

# SQLite Database
SQLITE_DB = "qa_platform.db"

# Azure SQL Database
AZURE_SQL_CONNECTION = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=your_server.database.windows.net;"
    "DATABASE=QAPlatform;"
    "UID=your_username;"
    "PWD=your_password;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)

# ==========================================
# Azure Blob Storage
# ==========================================

BLOB_CONNECTION_STRING = "your_blob_connection_string"

BLOB_CONTAINER = "screenshots"

# ==========================================
# Machine Learning
# ==========================================

MODEL_PATH = "ml/model.pkl"

# ==========================================
# Screenshot Folder
# ==========================================

SCREENSHOT_FOLDER = "screenshots"

# Create folder automatically
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

# ==========================================
# Reports
# ==========================================

REPORT_FOLDER = "reports"

os.makedirs(REPORT_FOLDER, exist_ok=True)