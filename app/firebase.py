"""
Firebase Admin SDK bootstrap.

Design goal: the site must run with `python wsgi.py` even before a
Firebase service account key is supplied (Phase 1 = landing page only,
no writes needed yet). If credentials are missing or invalid, we fall
back to `None` clients and the content_service layer serves local seed
data instead of crashing the whole app.

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
_bucket = None
_firebase_ready = False


def init_firebase(app):
    """Initialize Firebase Admin (Firestore + Storage) using the app's config.

    Call once from the app factory. Safe to call multiple times.
    """
    global _firestore_client, _bucket, _firebase_ready

    if _firebase_ready:
        return

    bucket_name = app.config.get("FIREBASE_STORAGE_BUCKET")
    cred_json = app.config.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    cred_path = app.config.get("FIREBASE_SERVICE_ACCOUNT_PATH")

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage

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
            firebase_admin.initialize_app(
                cred, {"storageBucket": bucket_name} if bucket_name else None
            )

        _firestore_client = firestore.client()
        _bucket = _resolve_storage_bucket(storage, bucket_name) if bucket_name else None
        _firebase_ready = True
        logger.info("Firebase initialized successfully from %s.", source)
    except Exception as exc:  # noqa: BLE001 - we want the site to keep running
        logger.error("Firebase initialization failed, using seed data: %s", exc)
        _firestore_client = None
        _bucket = None


def _resolve_storage_bucket(storage, configured_name):
    """Return a Storage bucket handle that actually exists.

    Firebase has used two different bucket-naming conventions for the
    "default" bucket depending on when the project was created:
      - older projects:  <project-id>.appspot.com
      - newer projects:  <project-id>.firebasestorage.app

    The Firebase console shows one or the other, and it's easy to have
    FIREBASE_STORAGE_BUCKET set to a name that *looks* right but isn't
    the real underlying GCS bucket — every upload then fails with a
    404 "specified bucket does not exist". This checks the configured
    name and, if it doesn't actually exist, tries the other convention
    automatically so uploads work regardless of which one is set.
    """
    candidates = [configured_name]
    if configured_name.endswith(".firebasestorage.app"):
        candidates.append(configured_name.replace(".firebasestorage.app", ".appspot.com"))
    elif configured_name.endswith(".appspot.com"):
        candidates.append(configured_name.replace(".appspot.com", ".firebasestorage.app"))

    for name in candidates:
        try:
            bucket = storage.bucket(name)
            if bucket.exists():
                if name != configured_name:
                    logger.warning(
                        "FIREBASE_STORAGE_BUCKET is set to '%s' but that bucket doesn't "
                        "exist — using '%s' instead, which does. Update the env var to "
                        "'%s' to avoid this check on every restart.",
                        configured_name, name, name,
                    )
                else:
                    logger.info("Storage bucket '%s' confirmed.", name)
                return bucket
        except Exception as exc:  # noqa: BLE001
            logger.debug("Bucket candidate '%s' failed existence check: %s", name, exc)

    logger.error(
        "Could not find a working Storage bucket — tried %s. Uploads (gallery photos, "
        "patient reports) will fail until FIREBASE_STORAGE_BUCKET points at a bucket "
        "that actually exists (check the exact name under Firebase Console > Storage).",
        candidates,
    )
    # Fall back to the configured name anyway so the error surfaces clearly
    # in logs at upload time rather than masking the misconfiguration.
    return storage.bucket(configured_name)


def get_db():
    """Return the Firestore client, or None if Firebase isn't configured."""
    return _firestore_client


def get_bucket():
    """Return the Storage bucket, or None if Firebase isn't configured."""
    return _bucket


def is_firebase_ready():
    return _firebase_ready
