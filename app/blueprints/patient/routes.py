from flask import Blueprint, render_template, g, redirect, url_for, jsonify, request, flash

from app.firebase import get_db
from app.utils.decorators import login_required
from app.utils import notifications as notif

patient_bp = Blueprint("patient", __name__, url_prefix="/dashboard")


@patient_bp.route("/")
@login_required
def dashboard():
    user = g.user
    upcoming_appointments, past_appointments, orders = _fetch_dashboard_data(user)

    return render_template(
        "patient/dashboard.html",
        user=user,
        upcoming_appointments=upcoming_appointments,
        past_appointments=past_appointments,
        orders=orders,
    )


@patient_bp.route("/refresh")
@login_required
def dashboard_refresh():
    upcoming_appointments, past_appointments, orders = _fetch_dashboard_data(g.user)
    return render_template(
        "patient/_dashboard_lists.html",
        upcoming_appointments=upcoming_appointments,
        past_appointments=past_appointments,
        orders=orders,
    )


def _fetch_dashboard_data(user):
    upcoming_appointments = []
    past_appointments = []
    orders = []

    db = get_db()
    if db is not None and user:
        appt_docs = (
            db.collection("appointments")
            .where("patient_uid", "==", user["uid"])
            .stream()
        )
        for doc in appt_docs:
            appt = doc.to_dict()
            appt["id"] = doc.id
            if appt.get("status") in ("completed", "cancelled"):
                past_appointments.append(appt)
            else:
                upcoming_appointments.append(appt)

        order_docs = db.collection("orders").where("patient_uid", "==", user["uid"]).stream()
        orders = [{**doc.to_dict(), "id": doc.id} for doc in order_docs]

    return upcoming_appointments, past_appointments, orders


@patient_bp.route("/profile")
@login_required
def profile():
    return render_template("patient/profile.html", user=g.user)


@patient_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    db = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()

        if db is None:
            flash("Firebase isn't configured yet — can't save your profile.", "error")
            return redirect(url_for("patient.profile"))

        db.collection("users").document(g.user["uid"]).set(
            {"name": name, "phone": phone}, merge=True
        )
        flash("Profile updated.", "info")
        return redirect(url_for("patient.profile"))

    return render_template("patient/profile_edit.html", user=g.user)


@patient_bp.route("/notifications")
@login_required
def notifications():
    items = notif.list_for_user(g.user["uid"])
    notif.mark_all_read(g.user["uid"])
    return render_template("patient/notifications.html", notifications=items)


@patient_bp.route("/notifications/unread-count")
@login_required
def notifications_unread_count():
    return jsonify({"count": notif.unread_count(g.user["uid"])})
