"""
Firebase Admin SDK bootstrap — Firestore only.

Design goal: the site must run with `python wsgi.py` even before a
Firebase service account key is supplied. If credentials are missing
or invalid, we fall back to `None` and the content_service layer
serves local seed data instead of crashing the whole app.

Cloud Storage is intentionally NOT used here — it requires the paid
Blaze plan. Uploaded files (gallery photos, prescription reports) are
instead base64-encoded and stored directly as Firestore document
fields; see app/utils/storage_service.py.

Two ways to supply the service account, checked in this order:
  1. FIREBASE_SERVICE_ACCOUNT_JSON — the *entire contents* of the
     service account JSON file, pasted as a single environment
     variable value. This is the one to use on Render (or any host
     where you can't commit a JSON file to the repo) — paste the
     whole file's contents into this env var in the dashboard.
  2. FIREBASE_SERVICE_ACCOUNT_PATH — a path to a local JSON file.
     This is the one used for local development (see .env.example).
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

_firestore_client = None
_firebase_ready = False


def init_firebase(app):
    """Initialize Firebase Admin (Firestore only) using the app's config.

    Call once from the app factory. Safe to call multiple times.
    """
    global _firestore_client, _firebase_ready

    if _firebase_ready:
        return

    cred_json = app.config.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    cred_path = app.config.get("FIREBASE_SERVICE_ACCOUNT_PATH")

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if cred_json:
            cred = credentials.Certificate(json.loads(cred_json))
            source = "FIREBASE_SERVICE_ACCOUNT_JSON env var"
        elif cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            source = f"file '{cred_path}'"
        else:
            logger.warning(
                "No Firebase credentials found (checked FIREBASE_SERVICE_ACCOUNT_JSON "
                "env var and FIREBASE_SERVICE_ACCOUNT_PATH file '%s'). Running in "
                "OFFLINE/SEED-DATA mode — Firestore reads/writes will use local "
                "fallback content until credentials are added.",
                cred_path,
            )
            return

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        _firestore_client = firestore.client()
        _firebase_ready = True
        logger.info("Firebase (Firestore) initialized successfully from %s.", source)
    except Exception as exc:  # noqa: BLE001 - we want the site to keep running
        logger.error("Firebase initialization failed, using seed data: %s", exc)
        _firestore_client = None


def get_db():
    """Return the Firestore client, or None if Firebase isn't configured."""
    return _firestore_client


def is_firebase_ready():
    return _firebase_ready
