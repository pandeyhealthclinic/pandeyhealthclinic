"""
Auth decorators built on Firebase session cookies.

Flow this supports:
  1. Client signs in via Firebase JS SDK (email/password or Google).
  2. Client POSTs the resulting ID token to /auth/session.
  3. Backend verifies it and issues a long-lived HTTPOnly session
     cookie (this file's `SESSION_COOKIE_NAME`).
  4. Every protected route below reads + verifies that cookie via
     Firebase Admin, then loads the matching Firestore user profile
     (for role checks) into `flask.g.user`.

If Firebase isn't configured yet (no service account), these
decorators redirect to login with a clear flash message instead of
raising — so the rest of the site keeps working in seed-data mode.
"""
from functools import wraps
from flask import g, redirect, url_for, flash, request

from app.firebase import is_firebase_ready, get_db

SESSION_COOKIE_NAME = "clinic_session"


def _load_current_user():
    """Populate flask.g.user from the session cookie, if valid. Returns None if not logged in."""
    if hasattr(g, "user"):
        return g.user

    g.user = None
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie or not is_firebase_ready():
        return None

    try:
        from firebase_admin import auth as fb_auth

        decoded = fb_auth.verify_session_cookie(cookie, check_revoked=True)
        uid = decoded["uid"]

        profile = {"uid": uid, "email": decoded.get("email"), "role": "patient"}
        db = get_db()
        if db is not None:
            doc = db.collection("users").document(uid).get()
            if doc.exists:
                profile.update(doc.to_dict())

        g.user = profile
    except Exception:  # noqa: BLE001 - invalid/expired/revoked cookie
        g.user = None

    return g.user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _load_current_user()
        if not is_firebase_ready():
            flash("Patient accounts aren't set up yet — Firebase isn't configured.", "info")
            return redirect(url_for("main.home"))
        if user is None:
            flash("Please log in to continue.", "info")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _load_current_user()
        if not is_firebase_ready():
            flash("Admin accounts aren't set up yet — Firebase isn't configured.", "info")
            return redirect(url_for("main.home"))
        if user is None:
            return redirect(url_for("auth.login", next=request.path))
        if user.get("role") != "admin":
            flash("That area is restricted to clinic admins.", "error")
            return redirect(url_for("main.home"))
        return view(*args, **kwargs)

    return wrapped


def guest_only(view):
    """Redirect already-logged-in users away from login/register pages."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _load_current_user()
        if user is not None:
            return redirect(url_for("patient.dashboard"))
        return view(*args, **kwargs)

    return wrapped


def current_user():
    return _load_current_user()
