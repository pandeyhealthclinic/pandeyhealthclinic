"""
Image/file "upload" helper — stores files as base64 data URIs directly
inside Firestore documents instead of using Firebase Cloud Storage.

Why: Cloud Storage requires the Blaze (pay-as-you-go) Firebase plan.
Firestore and Realtime Database both work on the free Spark plan, so
this avoids Storage entirely — no bucket, no billing account needed.

Trade-off: Firestore caps each document at 1 MiB, and base64 encoding
adds ~33% overhead. MAX_REPORT_BYTES is set well under that ceiling so
a document still has room left for its other fields (patient name,
items, status, etc). This is fine for gallery photos and prescription
snapshots; it is NOT meant for large/high-res files — encourage users
to upload a reasonably sized image (a phone photo often needs
resizing first).
"""
import base64
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp"}
MIME_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}
MAX_REPORT_BYTES = 500 * 1024  # 500 KB raw (~667 KB once base64-encoded)


def _extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def upload_patient_report(file_storage, patient_uid, subfolder="reports"):
    """Encode an uploaded file as a base64 data: URI.

    `patient_uid` and `subfolder` are no longer used for a storage path
    (kept in the signature so every existing call site — appointment
    report uploads, admin gallery uploads — needs no changes) but are
    accepted for future use (e.g. if a real object store is added back
    later).

    Returns a "data:<mime>;base64,<...>" string ready to drop straight
    into an <img src> or <a href>, or None if:
      - no file was provided
      - the extension isn't allowed
      - the file is too large for a Firestore document
    """
    if file_storage is None or not file_storage.filename:
        return None

    ext = _extension(file_storage.filename)
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning("Rejected upload with disallowed extension: %s", ext)
        return None

    file_storage.stream.seek(0, 2)  # seek to end
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_REPORT_BYTES:
        logger.warning(
            "Rejected upload — %d bytes exceeds the %d byte limit for inline Firestore "
            "storage. Ask the user to upload a smaller/compressed file.",
            size, MAX_REPORT_BYTES,
        )
        return None

    try:
        raw = file_storage.stream.read()
        encoded = base64.b64encode(raw).decode("ascii")
        mime = MIME_TYPES.get(ext, file_storage.mimetype or "application/octet-stream")
        return f"data:{mime};base64,{encoded}"
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to encode upload as base64: %s", exc)
        return None
