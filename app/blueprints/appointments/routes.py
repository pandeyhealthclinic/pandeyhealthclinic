import datetime
import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash, g

from app.firebase import get_db
from app.utils import content_service as content
from app.utils.decorators import login_required
from app.utils.storage_service import upload_patient_report

logger = logging.getLogger(__name__)

appointments_bp = Blueprint("appointments", __name__, url_prefix="/appointments")

TIME_SLOTS = [
    f"{h:02d}:{m:02d}"
    for h in list(range(9, 21))
    for m in (0, 30)
]


def _today_str():
    return datetime.date.today().isoformat()


@appointments_bp.route("/book", methods=["GET"])
@login_required
def book_form():
    services = content.get_services()
    preselected = request.args.get("service", "")
    preselected_type = request.args.get("consultation_type", "offline")
    return render_template(
        "appointments/book.html",
        services=services,
        preselected=preselected,
        preselected_type=preselected_type,
        time_slots=TIME_SLOTS,
        min_date=_today_str(),
    )


@appointments_bp.route("/book", methods=["POST"])
@login_required
def book_submit():
    services = {s["id"]: s for s in content.get_services()}
    service_id = request.form.get("service_id")
    date = request.form.get("date")
    time = request.form.get("time")
    consultation_type = request.form.get("consultation_type", "offline")
    symptoms = request.form.get("symptoms", "").strip()
    report_file = request.files.get("report")

    service = services.get(service_id)
    if not service or not date or not time:
        flash("Please choose a valid service, date, and time.", "error")
        return redirect(url_for("appointments.book_form", service=service_id))

    if date < _today_str():
        flash("Please choose a date from today onward.", "error")
        return redirect(url_for("appointments.book_form", service=service_id))

    db = get_db()
    user = g.user

    if db is None:
        flash(
            "Booking isn't connected to the clinic system yet (Firebase not configured). "
            "Please call the clinic directly to confirm your appointment.",
            "info",
        )
        return redirect(url_for("main.home"))

    # Prevent double-booking the exact same slot.
    try:
        existing = (
            db.collection("appointments")
            .where("date", "==", date)
            .where("time", "==", time)
            .where("status", "in", ["pending", "confirmed"])
            .limit(1)
            .stream()
        )
        if any(True for _ in existing):
            flash("That time slot was just taken. Please pick another.", "error")
            return redirect(url_for("appointments.book_form", service=service_id))
    except Exception as exc:  # noqa: BLE001 - e.g. missing Firestore composite index
        logger.warning("Slot-conflict check skipped (%s) — see README for the required Firestore index.", exc)

    report_url = upload_patient_report(report_file, user["uid"]) if report_file else None

    appt_ref = db.collection("appointments").document()
    appt_ref.set(
        {
            "patient_uid": user["uid"],
            "patient_name": user.get("name", ""),
            "patient_email": user.get("email", ""),
            "patient_phone": user.get("phone", ""),
            "service_id": service_id,
            "service_name": service["name"],
            "price": service["price"],
            "date": date,
            "time": time,
            "consultation_type": consultation_type,
            "symptoms": symptoms,
            "report_url": report_url,
            "status": "pending",
            "created_at": datetime.datetime.utcnow().isoformat(),
        }
    )

    flash("Appointment requested! We'll confirm it shortly.", "info")
    return redirect(url_for("appointments.confirmation", appointment_id=appt_ref.id))


@appointments_bp.route("/confirmation/<appointment_id>")
@login_required
def confirmation(appointment_id):
    db = get_db()
    appointment = None
    if db is not None:
        doc = db.collection("appointments").document(appointment_id).get()
        if doc.exists:
            appointment = {**doc.to_dict(), "id": doc.id}
    return render_template("appointments/confirmation.html", appointment=appointment)


@appointments_bp.route("/<appointment_id>/cancel", methods=["POST"])
@login_required
def cancel(appointment_id):
    db = get_db()
    if db is None:
        flash("Booking system isn't connected yet.", "info")
        return redirect(url_for("patient.dashboard"))

    doc_ref = db.collection("appointments").document(appointment_id)
    doc = doc_ref.get()
    if not doc.exists or doc.to_dict().get("patient_uid") != g.user["uid"]:
        flash("Appointment not found.", "error")
        return redirect(url_for("patient.dashboard"))

    doc_ref.update({"status": "cancelled"})
    flash("Appointment cancelled.", "info")
    return redirect(url_for("patient.dashboard"))


@appointments_bp.route("/<appointment_id>/consult", methods=["GET"])
@login_required
def consult(appointment_id):
    db = get_db()
    if db is None:
        flash("Booking system isn't connected yet.", "info")
        return redirect(url_for("patient.dashboard"))

    doc = db.collection("appointments").document(appointment_id).get()
    if not doc.exists:
        flash("Appointment not found.", "error")
        return redirect(url_for("patient.dashboard"))

    appointment = {**doc.to_dict(), "id": doc.id}
    user = g.user
    if appointment.get("patient_uid") != user["uid"] and user.get("role") != "admin":
        flash("You don't have access to this consultation.", "error")
        return redirect(url_for("patient.dashboard"))

    messages = [
        {**m.to_dict(), "id": m.id}
        for m in db.collection("appointments").document(appointment_id).collection("messages").stream()
    ]
    messages.sort(key=lambda m: m.get("created_at", ""))

    return render_template("appointments/consult.html", appointment=appointment, messages=messages)


@appointments_bp.route("/<appointment_id>/consult/messages", methods=["GET"])
@login_required
def consult_messages_fragment(appointment_id):
    db = get_db()
    if db is None:
        return "", 204

    doc = db.collection("appointments").document(appointment_id).get()
    if not doc.exists:
        return "", 404

    appointment = doc.to_dict()
    user = g.user
    if appointment.get("patient_uid") != user["uid"] and user.get("role") != "admin":
        return "", 403

    messages = [
        {**m.to_dict(), "id": m.id}
        for m in db.collection("appointments").document(appointment_id).collection("messages").stream()
    ]
    messages.sort(key=lambda m: m.get("created_at", ""))

    return render_template("appointments/_chat_messages.html", messages=messages)


@appointments_bp.route("/<appointment_id>/consult/message", methods=["POST"])
@login_required
def consult_message(appointment_id):
    db = get_db()
    if db is None:
        return redirect(url_for("patient.dashboard"))

    doc_ref = db.collection("appointments").document(appointment_id)
    doc = doc_ref.get()
    if not doc.exists:
        flash("Appointment not found.", "error")
        return redirect(url_for("patient.dashboard"))

    appointment = doc.to_dict()
    user = g.user
    if appointment.get("patient_uid") != user["uid"] and user.get("role") != "admin":
        flash("You don't have access to this consultation.", "error")
        return redirect(url_for("patient.dashboard"))

    text = request.form.get("text", "").strip()
    if text:
        doc_ref.collection("messages").document().set(
            {
                "sender_uid": user["uid"],
                "sender_name": user.get("name") or ("Clinic Staff" if user.get("role") == "admin" else "Patient"),
                "sender_role": user.get("role", "patient"),
                "text": text,
                "read_by_admin": user.get("role") == "admin",
                "created_at": datetime.datetime.utcnow().isoformat(),
            }
        )

    return redirect(url_for("appointments.consult", appointment_id=appointment_id))


@appointments_bp.route("/<appointment_id>/reschedule", methods=["GET", "POST"])
@login_required
def reschedule(appointment_id):
    db = get_db()
    if db is None:
        flash("Booking system isn't connected yet.", "info")
        return redirect(url_for("patient.dashboard"))

    doc_ref = db.collection("appointments").document(appointment_id)
    doc = doc_ref.get()
    if not doc.exists or doc.to_dict().get("patient_uid") != g.user["uid"]:
        flash("Appointment not found.", "error")
        return redirect(url_for("patient.dashboard"))

    appointment = {**doc.to_dict(), "id": doc.id}

    if request.method == "POST":
        date = request.form.get("date")
        time = request.form.get("time")
        if not date or not time or date < _today_str():
            flash("Please choose a valid future date and time.", "error")
            return redirect(url_for("appointments.reschedule", appointment_id=appointment_id))

        doc_ref.update({"date": date, "time": time, "status": "pending"})
        flash("Appointment rescheduled — awaiting confirmation.", "info")
        return redirect(url_for("patient.dashboard"))

    return render_template(
        "appointments/reschedule.html",
        appointment=appointment,
        time_slots=TIME_SLOTS,
        min_date=_today_str(),
    )
