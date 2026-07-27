"""
Firebase Storage helper for patient-uploaded files (previous reports,
prescriptions, gallery photos, etc.). Returns None instead of raising
when Storage isn't configured, so the calling route can degrade
gracefully rather than 500.
"""
import datetime
import logging
import uuid

from app.firebase import get_bucket

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp"}
MAX_REPORT_BYTES = 8 * 1024 * 1024  # 8 MB


def _extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def upload_patient_report(file_storage, patient_uid, subfolder="reports"):
    """Upload a werkzeug FileStorage to Storage under {subfolder}/{uid}/{uuid}.ext.

    Returns a URL the browser can load directly, or None if:
      - no file was provided
      - Storage isn't configured (offline mode)
      - the file fails validation (extension/size)
      - the upload itself fails
    """
    if file_storage is None or not file_storage.filename:
        return None

    ext = _extension(file_storage.filename)
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning("Rejected upload with disallowed extension: %s", ext)
        return None

    # Enforce the size cap (previously defined but never actually checked).
    file_storage.stream.seek(0, 2)  # seek to end
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_REPORT_BYTES:
        logger.warning("Rejected upload — %d bytes exceeds %d byte limit.", size, MAX_REPORT_BYTES)
        return None

    bucket = get_bucket()
    if bucket is None:
        logger.warning("Storage not configured — skipping upload (offline mode).")
        return None

    try:
        blob_path = f"{subfolder}/{patient_uid}/{uuid.uuid4().hex}.{ext}"
        blob = bucket.blob(blob_path)
        blob.upload_from_file(file_storage.stream, content_type=file_storage.mimetype)
    except Exception as exc:  # noqa: BLE001
        logger.error("Upload to Storage failed: %s", exc)
        return None

    # Try to make the object publicly readable via legacy ACLs. Most new
    # Firebase Storage buckets have "Uniform Bucket-Level Access" enabled
    # by default, which makes make_public() raise — every single upload
    # was silently failing here before. Fall back to a long-lived signed
    # URL, which works regardless of the bucket's ACL/UBLA setting.
    try:
        blob.make_public()
        return blob.public_url
    except Exception as exc:  # noqa: BLE001
        logger.info("make_public() unavailable (likely Uniform Bucket-Level Access) — using a signed URL instead: %s", exc)

    try:
        return blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(days=3650),
            method="GET",
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Could not generate a signed URL either — the upload succeeded but no browsable "
            "link could be created. Grant the Firebase service account the 'Service Account "
            "Token Creator' IAM role in Google Cloud Console to fix this. Error: %s", exc
        )
        return None
        
