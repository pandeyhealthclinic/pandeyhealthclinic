import datetime
import logging

from flask import Blueprint, render_template, request, jsonify, make_response, redirect, url_for, flash

from app.firebase import is_firebase_ready, get_db
from app.utils.decorators import SESSION_COOKIE_NAME, guest_only, current_user

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

SESSION_EXPIRY = datetime.timedelta(days=5)


@auth_bp.route("/login", methods=["GET", "POST"])
@guest_only
def login():
    if request.method == "POST":
        flash(
            "Your browser submitted the form before the page finished loading "
            "the sign-in script. This can happen on a slow connection or if a "
            "browser extension blocked Google's Firebase scripts. Please "
            "refresh the page, wait a second for it to fully load, and try "
            "again.",
            "error",
        )
        return redirect(url_for("auth.login"))
    return render_template("auth/login.html", next_url=request.args.get("next", ""))


@auth_bp.route("/register", methods=["GET", "POST"])
@guest_only
def register():
    if request.method == "POST":
        flash(
            "Your browser submitted the form before the page finished loading "
            "the sign-up script. Please refresh the page, wait a second for "
            "it to fully load, and try again.",
            "error",
        )
        return redirect(url_for("auth.register"))
    return render_template("auth/register.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@guest_only
def forgot_password():
    if request.method == "POST":
        flash(
            "Your browser submitted the form before the page finished loading. "
            "Please refresh the page, wait a second for it to fully load, and "
            "try again.",
            "error",
        )
        return redirect(url_for("auth.forgot_password"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/session", methods=["POST"])
def create_session():
    """Exchange a Firebase ID token (from the client SDK) for a secure session cookie."""
    if not is_firebase_ready():
        return jsonify({"error": "Firebase is not configured on this server yet."}), 503

    data = request.get_json(silent=True) or {}
    id_token = data.get("idToken")
    if not id_token:
        return jsonify({"error": "Missing idToken."}), 400

    try:
        from firebase_admin import auth as fb_auth

        # Verify the token is fresh before minting a long-lived session cookie.
        decoded = fb_auth.verify_id_token(id_token)
        uid = decoded["uid"]

        session_cookie = fb_auth.create_session_cookie(id_token, expires_in=SESSION_EXPIRY)

        _ensure_user_profile(uid, decoded)

        resp = make_response(jsonify({"status": "ok"}))
        resp.set_cookie(
            SESSION_COOKIE_NAME,
            session_cookie,
            max_age=int(SESSION_EXPIRY.total_seconds()),
            httponly=True,
            secure=request.is_secure,
            samesite="Lax",
            path="/",
        )
        return resp
    except Exception as exc:  # noqa: BLE001
        logger.warning("Session creation failed: %s", exc)
        return jsonify({"error": "Could not verify credentials. Please try logging in again."}), 401


@auth_bp.route("/register-profile", methods=["POST"])
def register_profile():
    """Create/update the Firestore profile doc right after client-side sign-up."""
    if not is_firebase_ready():
        return jsonify({"error": "Firebase is not configured on this server yet."}), 503

    data = request.get_json(silent=True) or {}
    id_token = data.get("idToken")
    if not id_token:
        return jsonify({"error": "Missing idToken."}), 400

    try:
        from firebase_admin import auth as fb_auth

        decoded = fb_auth.verify_id_token(id_token)
        uid = decoded["uid"]

        db = get_db()
        if db is not None:
            db.collection("users").document(uid).set(
                {
                    "uid": uid,
                    "email": decoded.get("email"),
                    "name": data.get("name", ""),
                    "phone": data.get("phone", ""),
                    "role": "patient",
                    "created_at": datetime.datetime.utcnow().isoformat(),
                },
                merge=True,
            )
        return jsonify({"status": "ok"})
    except Exception as exc:  # noqa: BLE001
        logger.warning("Profile creation failed: %s", exc)
        return jsonify({"error": "Could not save your profile. Please try again."}), 400


def _ensure_user_profile(uid, decoded_token):
    """Make sure every authenticated user (incl. Google sign-in) has a Firestore profile doc."""
    db = get_db()
    if db is None:
        return
    doc_ref = db.collection("users").document(uid)
    if not doc_ref.get().exists:
        doc_ref.set(
            {
                "uid": uid,
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name", ""),
                "role": "patient",
                "created_at": datetime.datetime.utcnow().isoformat(),
            }
        )


@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    resp = make_response(redirect(url_for("main.home")))
    resp.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return resp
