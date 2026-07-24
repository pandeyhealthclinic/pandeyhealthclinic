"""
Content service — the single source of truth every route uses to
fetch site content.

Read path: Firestore collection (if Firebase is configured and the
collection has documents) -> otherwise the local seed_content module.
This lets the admin CMS (Phase 5) take over content live, without any
template or route code needing to change.
"""
import logging
from app.firebase import get_db
from app.utils import seed_content

logger = logging.getLogger(__name__)


def _collection_or_seed(collection_name, seed_value):
    db = get_db()
    if db is None:
        return seed_value
    try:
        docs = list(db.collection(collection_name).stream())
        if not docs:
            return seed_value
        return [doc.to_dict() for doc in docs]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed reading collection '%s', using seed data: %s", collection_name, exc)
        return seed_value


def _document_or_seed(collection_name, doc_id, seed_value):
    db = get_db()
    if db is None:
        return seed_value
    try:
        doc = db.collection(collection_name).document(doc_id).get()
        if not doc.exists:
            return seed_value
        return doc.to_dict()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed reading doc '%s/%s', using seed data: %s", collection_name, doc_id, exc)
        return seed_value


def get_hero():
    return _document_or_seed("site_content", "hero", seed_content.HERO)


def get_about():
    return _document_or_seed("site_content", "about", seed_content.ABOUT)


def get_vision():
    return _document_or_seed("site_content", "vision", seed_content.VISION)


def get_why_choose_us():
    return _collection_or_seed("why_choose_us", seed_content.WHY_CHOOSE_US)


def get_services():
    return _collection_or_seed("services", seed_content.SERVICES)


def get_doctor():
    return _document_or_seed("site_content", "doctor", seed_content.DOCTOR)


def get_testimonials():
    all_testimonials = _collection_or_seed("testimonials", seed_content.TESTIMONIALS)
    return [t for t in all_testimonials if t.get("approved", True)]


def get_gallery():
    return _collection_or_seed("gallery", seed_content.GALLERY)


def get_contact():
    return _document_or_seed("site_content", "contact", seed_content.CONTACT)


def get_nav_links():
    return seed_content.NAV_LINKS


def get_medicines():
    return _collection_or_seed("medicines", seed_content.MEDICINES)


def get_medicine(medicine_id):
    medicines = get_medicines()
    return next((m for m in medicines if m.get("id") == medicine_id), None)


def get_medicine_categories():
    return seed_content.MEDICINE_CATEGORIES
