"""
One-off helper: promote an existing registered user to the 'admin' role.

Usage (from the project root, with .env / service account already configured):

    python -m app.utils.promote_admin someone@example.com

This looks the user up by email in Firebase Auth, then sets
role='admin' on their Firestore users/{uid} document. Run this once
per admin account you need — there is no UI for it yet (that's the
Admin Panel, coming in Phase 5).
"""
import sys
from app import create_app
from app.firebase import get_db


def promote(email):
    app = create_app("development")
    with app.app_context():
        from firebase_admin import auth as fb_auth

        try:
            user_record = fb_auth.get_user_by_email(email)
        except Exception as exc:  # noqa: BLE001
            print(f"Could not find a Firebase user with email {email}: {exc}")
            return

        db = get_db()
        if db is None:
            print("Firestore is not configured — check your .env and service account file.")
            return

        db.collection("users").document(user_record.uid).set(
            {"uid": user_record.uid, "email": email, "role": "admin"}, merge=True
        )
        print(f"{email} is now an admin.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m app.utils.promote_admin <email>")
        sys.exit(1)
    promote(sys.argv[1])
