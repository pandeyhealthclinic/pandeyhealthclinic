"""
Public lead-capture endpoint for the non-blocking "want a callback?"
popup. No login required — this is aimed at anonymous visitors who
are just browsing, so the clinic can follow up (cold outreach).
"""
import datetime
import logging
import re

from flask import Blueprint, request, jsonify

from app.firebase import get_db

logger = logging.getLogger(__name__)

leads_bp = Blueprint("leads", __name__, url_prefix="/leads")

PHONE_RE = re.compile(r"^[0-9+\-\s]{7,15}$")


@leads_bp.route("/capture", methods=["POST"])
def capture():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    page = (data.get("page") or "").strip()[:200]

    if not name or len(name) > 80:
        return jsonify({"error": "Please enter your name."}), 400
    if not phone or not PHONE_RE.match(phone):
        return jsonify({"error": "Please enter a valid phone number."}), 400

    db = get_db()
    if db is None:
        # Don't punish the visitor for the site being offline — just
        # log it so it's not silently lost, and tell the frontend it
        # "worked" from their point of view.
        logger.warning("Lead capture received but Firestore isn't configured — lost: %s / %s", name, phone)
        return jsonify({"status": "ok"})

    try:
        db.collection("leads").document().set(
            {
                "name": name,
                "phone": phone,
                "page": page,
                "status": "new",
                "created_at": datetime.datetime.utcnow().isoformat(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to save lead: %s", exc)
        return jsonify({"error": "Could not save right now — please try again."}), 500

    return jsonify({"status": "ok"})
