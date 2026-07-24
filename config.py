"""
Central configuration for the Pandey Health Clinic application.

All secrets are read from environment variables (see .env.example).
Never hardcode Firebase keys or credentials here.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB upload cap (reports/images)

    # --- Firebase (Client SDK — used by frontend JS for Auth) ---
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
    FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "")
    FIREBASE_MESSAGING_SENDER_ID = os.getenv("FIREBASE_MESSAGING_SENDER_ID", "")
    FIREBASE_APP_ID = os.getenv("FIREBASE_APP_ID", "")

    # --- Firebase Admin (Server SDK — used by Flask backend) ---
    # Local dev: point this at a JSON file on disk.
    FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH", "firebase-service-account.json"
    )
    # Render (or any host without file uploads): paste the *entire*
    # service account JSON file contents into this env var instead.
    # Checked first if present — see app/firebase.py.
    FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")

    # --- Clinic identity (also editable later via Admin CMS) ---
    CLINIC_NAME = "Pandey Health Clinic"
    DOCTOR_NAME = "Dr. Ved Prakash Pandey"
    DOCTOR_QUALIFICATION = "B.Sc (MU), B.E.MS, M.D. Kolkata (WB)"
    CLINIC_TAGLINE = "Lord's Cares Better"
    CLINIC_PHONE = "8083250208"
    CLINIC_CITY = "Gaya, Bihar"


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
