from pathlib import Path
from config.settings import BASE_PATH

DATABASE_PATH = BASE_PATH / "database"

DATABASE_PATH.mkdir(exist_ok=True)

DB_FILE = DATABASE_PATH / "gerencial.db"
