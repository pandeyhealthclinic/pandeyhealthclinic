"""
Lightweight in-app notifications, stored per-user in Firestore
(`notifications` collection). Used for appointment confirmations,
status changes, and order updates. No-ops silently if Firebase isn't
configured, same pattern as the rest of the app.
"""
import datetime
import logging

from app.firebase import get_db

logger = logging.getLogger(__name__)


def notify(uid, message, link=None):
    db = get_db()
    if db is None or not uid:
        return
    try:
        db.collection("notifications").document().set(
            {
                "uid": uid,
                "message": message,
                "link": link,
                "read": False,
                "created_at": datetime.datetime.utcnow().isoformat(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to create notification: %s", exc)


def list_for_user(uid, limit=20):
    db = get_db()
    if db is None or not uid:
        return []
    try:
        docs = (
            db.collection("notifications")
            .where("uid", "==", uid)
            .stream()
        )
        items = [{**d.to_dict(), "id": d.id} for d in docs]
        items.sort(key=lambda n: n.get("created_at", ""), reverse=True)
        return items[:limit]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to list notifications: %s", exc)
        return []


def unread_count(uid):
    return sum(1 for n in list_for_user(uid, limit=50) if not n.get("read"))


def mark_read(uid, notification_id):
    db = get_db()
    if db is None:
        return
    doc_ref = db.collection("notifications").document(notification_id)
    doc = doc_ref.get()
    if doc.exists and doc.to_dict().get("uid") == uid:
        doc_ref.update({"read": True})


def mark_all_read(uid):
    db = get_db()
    if db is None or not uid:
        return
    for n in list_for_user(uid, limit=50):
        if not n.get("read"):
            db.collection("notifications").document(n["id"]).update({"read": True})
