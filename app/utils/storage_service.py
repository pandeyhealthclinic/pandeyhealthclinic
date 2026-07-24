"""
Firebase Storage helper for patient-uploaded files (previous reports,
prescriptions, etc.). Returns None instead of raising when Storage
isn't configured, so appointment booking still works without a file
attached.
"""
import logging
import uuid

from app.firebase import get_bucket

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp"}
MAX_REPORT_BYTES = 8 * 1024 * 1024  # 8 MB


def _extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def upload_patient_report(file_storage, patient_uid, subfolder="reports"):
    """Upload a werkzeug FileStorage to Storage under reports/{uid}/{uuid}.ext.

    Returns the public download URL, or None if:
      - no file was provided
      - Storage isn't configured (offline mode)
      - the file fails validation (extension/size)
    """
    if file_storage is None or not file_storage.filename:
        return None

    ext = _extension(file_storage.filename)
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning("Rejected report upload with disallowed extension: %s", ext)
        return None

    bucket = get_bucket()
    if bucket is None:
        logger.warning("Storage not configured — skipping report upload (offline mode).")
        return None

    try:
        blob_path = f"{subfolder}/{patient_uid}/{uuid.uuid4().hex}.{ext}"
        blob = bucket.blob(blob_path)
        blob.upload_from_file(file_storage.stream, content_type=file_storage.mimetype)
        blob.make_public()
        return blob.public_url
    except Exception as exc:  # noqa: BLE001
        logger.error("Report upload failed: %s", exc)
        return None
