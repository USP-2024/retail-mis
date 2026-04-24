import os

DATA_PATH = "data/retail.csv"
CACHE_ENABLED = True
SECRET_KEY = "retail-mis-secret-2024"
DATABASE_PATH = "database/db.sqlite3"
CHARTS_DIR = "static/charts"
REPORTS_DIR = "static/reports"
UPLOAD_FOLDER = "uploads"

USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin"
    },
    "manager": {
        "password": "manager123",
        "role": "manager"
    }
}

os.makedirs("database", exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)