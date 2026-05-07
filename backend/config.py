import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Local fallback for development
DB_PATH = os.path.join(BASE_DIR, "backend", "app.db")

# External database configuration for deployment
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DB_URL = DATABASE_URL
else:
    sqlite_path = DB_PATH.replace("\\", "/")
    DB_URL = f"sqlite:///{sqlite_path}"

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATASET_FOLDER = os.path.join(BASE_DIR, "datasets")
MODEL_FOLDER = os.path.join(BASE_DIR, "models")

SECRET_KEY = os.environ.get("APP_SECRET_KEY", "dev-secret-key")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-jwt-secret")
JWT_ALGO = "HS256"
