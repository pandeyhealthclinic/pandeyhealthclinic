"""
Image/file "upload" helper — stores files as base64 data URIs directly
inside Firestore documents instead of using Firebase Cloud Storage.

Why: Cloud Storage requires the Blaze (pay-as-you-go) Firebase plan.
Firestore and Realtime Database both work on the free Spark plan, so
this avoids Storage entirely — no bucket, no billing account needed.

Trade-off: Firestore caps each document at 1 MiB, and base64 encoding
adds ~33% overhead. MAX_REPORT_BYTES is set well under that ceiling so
a document still has room left for its other fields (patient name,
items, status, etc). To make that limit invisible to a normal user,
any image over the limit is automatically resized/re-compressed with
Pillow until it fits — a real phone photo (often 3-8 MB) just works
without anyone needing to manually shrink it first. Only a PDF, or an
image that still can't be squeezed under the limit even at low
quality, gets rejected.
"""
import base64
import io
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MIME_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}
MAX_REPORT_BYTES = 500 * 1024  # 500 KB raw (~667 KB once base64-encoded)

# Compression ladder tried in order until the result fits under
# MAX_REPORT_BYTES: (max longest-edge in pixels, JPEG quality).
_COMPRESSION_STEPS = [
    (1600, 85),
    (1600, 70),
    (1200, 60),
    (1000, 50),
    (800, 45),
    (640, 40),
]


def _extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _compress_image(raw_bytes):
    """Try progressively smaller/lower-quality re-encodes until the
    result fits under MAX_REPORT_BYTES. Returns (bytes, mime) on
    success, or (None, None) if even the smallest step is still over
    the limit (e.g. a very busy/high-detail image)."""
    try:
        from PIL import Image
    except ImportError:
        logger.error("Pillow isn't installed — can't auto-compress oversized images. Add 'Pillow' to requirements.txt.")
        return None, None

    try:
        image = Image.open(io.BytesIO(raw_bytes))
        image = image.convert("RGB")  # normalize (drops alpha; fine for photos)
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not open upload as an image for compression: %s", exc)
        return None, None

    for max_edge, quality in _COMPRESSION_STEPS:
        resized = image.copy()
        resized.thumbnail((max_edge, max_edge))
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=quality, optimize=True)
        data = buffer.getvalue()
        if len(data) <= MAX_REPORT_BYTES:
            return data, "image/jpeg"

    return None, None


def upload_patient_report(file_storage, patient_uid, subfolder="reports"):
    """Encode an uploaded file as a base64 data: URI.

    `patient_uid` and `subfolder` are no longer used for a storage path
    (kept in the signature so every existing call site — appointment
    report uploads, admin gallery uploads — needs no changes) but are
    accepted for future use.

    Returns a "data:<mime>;base64,<...>" string ready to drop straight
    into an <img src> or <a href>, or None if:
      - no file was provided
      - the extension isn't allowed
      - it's a PDF over the size limit (PDFs aren't compressed)
      - it's an image that's still too large even after compression
    """
    if file_storage is None or not file_storage.filename:
        return None

    ext = _extension(file_storage.filename)
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning("Rejected upload with disallowed extension: %s", ext)
        return None

    raw = file_storage.stream.read()
    size = len(raw)

    if size <= MAX_REPORT_BYTES:
        mime = MIME_TYPES.get(ext, file_storage.mimetype or "application/octet-stream")
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    if ext not in IMAGE_EXTENSIONS:
        logger.warning(
            "Rejected upload — %d bytes exceeds the %d byte limit and .%s files can't be "
            "auto-compressed (only images can). Ask the user for a smaller PDF.",
            size, MAX_REPORT_BYTES, ext,
        )
        return None

    logger.info("Upload is %d bytes (over the %d byte limit) — auto-compressing...", size, MAX_REPORT_BYTES)
    compressed, mime = _compress_image(raw)
    if compressed is None:
        logger.warning(
            "Rejected upload — %d bytes, and it still didn't fit under the %d byte limit "
            "even after compression. Ask the user for a smaller/simpler image.",
            size, MAX_REPORT_BYTES,
        )
        return None

    logger.info("Compressed upload from %d to %d bytes.", size, len(compressed))
    encoded = base64.b64encode(compressed).decode("ascii")
    return f"data:{mime};base64,{encoded}"
