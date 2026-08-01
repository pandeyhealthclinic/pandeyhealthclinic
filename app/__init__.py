"""
Application factory for Pandey Health Clinic.

Phase 1 registers only the `main` blueprint (public landing page).
Later phases will add: auth, patient, appointments, medicines, admin.
"""
import logging
from flask import Flask

from config import config_map
from app.firebase import init_firebase


def create_app(env="development"):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_map.get(env, config_map["development"]))

    logging.basicConfig(level=logging.INFO)

    init_firebase(app)

    register_blueprints(app)
    register_context_processors(app)
    register_error_handlers(app)
    register_template_globals(app)

    return app


def register_template_globals(app):
    @app.template_global()
    def image_url(value, default=""):
        """Resolve an image field that may be a bare filename (served from
        /static/images/), a full URL, or a base64 data: URI (images are
        now stored directly in Firestore documents, not Cloud Storage,
        since Storage requires a paid Firebase plan)."""
        from flask import url_for

        if not value:
            return default
        if value.startswith("http://") or value.startswith("https://") or value.startswith("data:"):
            return value
        return url_for("static", filename=f"images/{value}")


def register_blueprints(app):
    from app.blueprints.main.routes import main_bp
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.patient.routes import patient_bp
    from app.blueprints.appointments.routes import appointments_bp
    from app.blueprints.medicines.routes import medicines_bp
    from app.blueprints.admin.routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(medicines_bp)
    app.register_blueprint(admin_bp)


def register_context_processors(app):
    """Make clinic identity constants available in every template."""

    @app.context_processor
    def inject_clinic_globals():
        from app.utils.decorators import current_user
        from app.firebase import is_firebase_ready
        from app.utils import notifications as notif

        user = current_user()
        unread = notif.unread_count(user["uid"]) if user else 0

        return {
            "CLINIC_NAME": app.config["CLINIC_NAME"],
            "DOCTOR_NAME": app.config["DOCTOR_NAME"],
            "CLINIC_PHONE": app.config["CLINIC_PHONE"],
            "CLINIC_TAGLINE": app.config["CLINIC_TAGLINE"],
            "FIREBASE_CLIENT_CONFIG": {
                "apiKey": app.config["FIREBASE_API_KEY"],
                "authDomain": app.config["FIREBASE_AUTH_DOMAIN"],
                "projectId": app.config["FIREBASE_PROJECT_ID"],
                "storageBucket": app.config["FIREBASE_STORAGE_BUCKET"],
                "messagingSenderId": app.config["FIREBASE_MESSAGING_SENDER_ID"],
                "appId": app.config["FIREBASE_APP_ID"],
            },
            "FIREBASE_READY": is_firebase_ready(),
            "current_user": user,
            "unread_notifications": unread,
        }


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("500.html"), 500
