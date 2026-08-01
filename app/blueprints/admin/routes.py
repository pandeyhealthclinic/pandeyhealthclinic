import datetime
import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app.firebase import get_db
from app.utils.decorators import admin_required
from app.utils.slug import slugify
from app.utils.storage_service import upload_patient_report
from app.utils import content_service as content

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.context_processor
def inject_admin_sidebar_badges():
    db = get_db()
    unread = 0
    if db is not None:
        try:
            appts = db.collection("appointments").where("consultation_type", "==", "online").stream()
            for a in appts:
                msgs = a.reference.collection("messages").stream()
                unread += sum(
                    1 for m in msgs
                    if m.to_dict().get("sender_role") != "admin" and not m.to_dict().get("read_by_admin", False)
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Sidebar unread badge unavailable: %s", exc)
    return {"admin_unread_consultations": unread}


def _require_db():
    """Return the Firestore client or None. Every write route should bail
    out with a clear flash if Firebase isn't configured yet."""
    return get_db()


# ---------------------------------------------------------------- Dashboard

@admin_bp.route("/")
@admin_required
def dashboard():
    db = _require_db()
    stats = {
        "total_patients": 0,
        "pending_appointments": 0,
        "total_appointments": 0,
        "total_orders": 0,
        "total_revenue": 0,
        "low_stock_medicines": 0,
        "pending_testimonials": 0,
    }
    recent_appointments = []
    recent_orders = []

    if db is not None:
        try:
            users = list(db.collection("users").where("role", "==", "patient").stream())
            stats["total_patients"] = len(users)

            appts = list(db.collection("appointments").stream())
            stats["total_appointments"] = len(appts)
            stats["pending_appointments"] = sum(1 for a in appts if a.to_dict().get("status") == "pending")
            recent_appointments = sorted(
                [{**a.to_dict(), "id": a.id} for a in appts],
                key=lambda a: a.get("created_at", ""),
                reverse=True,
            )[:6]

            orders = list(db.collection("orders").stream())
            stats["total_orders"] = len(orders)
            stats["total_revenue"] = sum(o.to_dict().get("total", 0) for o in orders if o.to_dict().get("status") != "cancelled")
            recent_orders = sorted(
                [{**o.to_dict(), "id": o.id} for o in orders],
                key=lambda o: o.get("created_at", ""),
                reverse=True,
            )[:6]

            medicines = content.get_medicines()
            stats["low_stock_medicines"] = sum(1 for m in medicines if 0 < m.get("stock", 0) <= 10)

            testimonials = list(db.collection("testimonials").stream())
            stats["pending_testimonials"] = sum(1 for t in testimonials if not t.to_dict().get("approved", True))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Dashboard stats partially unavailable: %s", exc)

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_appointments=recent_appointments,
        recent_orders=recent_orders,
        firebase_ready=db is not None,
    )


# ---------------------------------------------------------------- Services

@admin_bp.route("/services")
@admin_required
def services_list():
    return render_template("admin/services.html", services=content.get_services())


@admin_bp.route("/services/new", methods=["GET", "POST"])
@admin_required
def service_new():
    if request.method == "POST":
        db = _require_db()
        if db is None:
            flash("Firebase isn't configured — can't save yet.", "error")
            return redirect(url_for("admin.services_list"))

        name = request.form.get("name", "").strip()
        service_id = slugify(name)
        db.collection("services").document(service_id).set(
            {
                "id": service_id,
                "name": name,
                "description": request.form.get("description", "").strip(),
                "price": request.form.get("price", 0, type=int),
                "duration": request.form.get("duration", "").strip(),
                "image": request.form.get("image", "").strip() or "service-general.jpg",
            }
        )
        flash(f"Service '{name}' added.", "info")
        return redirect(url_for("admin.services_list"))

    return render_template("admin/service_form.html", service=None)


@admin_bp.route("/services/<service_id>/edit", methods=["GET", "POST"])
@admin_required
def service_edit(service_id):
    service = next((s for s in content.get_services() if s["id"] == service_id), None)
    if not service:
        flash("Service not found.", "error")
        return redirect(url_for("admin.services_list"))

    if request.method == "POST":
        db = _require_db()
        if db is None:
            flash("Firebase isn't configured — can't save yet.", "error")
            return redirect(url_for("admin.services_list"))

        db.collection("services").document(service_id).set(
            {
                "id": service_id,
                "name": request.form.get("name", "").strip(),
                "description": request.form.get("description", "").strip(),
                "price": request.form.get("price", 0, type=int),
                "duration": request.form.get("duration", "").strip(),
                "image": request.form.get("image", "").strip() or service.get("image", ""),
            }
        )
        flash("Service updated.", "info")
        return redirect(url_for("admin.services_list"))

    return render_template("admin/service_form.html", service=service)


@admin_bp.route("/services/<service_id>/delete", methods=["POST"])
@admin_required
def service_delete(service_id):
    db = _require_db()
    if db is not None:
        db.collection("services").document(service_id).delete()
        flash("Service deleted.", "info")
    return redirect(url_for("admin.services_list"))


# ---------------------------------------------------------------- Medicines

@admin_bp.route("/medicines")
@admin_required
def medicines_list():
    return render_template("admin/medicines.html", medicines=content.get_medicines())


@admin_bp.route("/medicines/new", methods=["GET", "POST"])
@admin_required
def medicine_new():
    if request.method == "POST":
        db = _require_db()
        if db is None:
            flash("Firebase isn't configured — can't save yet.", "error")
            return redirect(url_for("admin.medicines_list"))

        name = request.form.get("name", "").strip()
        medicine_id = slugify(name)
        db.collection("medicines").document(medicine_id).set(_medicine_payload(medicine_id, request.form))
        flash(f"Medicine '{name}' added.", "info")
        return redirect(url_for("admin.medicines_list"))

    return render_template("admin/medicine_form.html", medicine=None, categories=content.get_medicine_categories())


@admin_bp.route("/medicines/<medicine_id>/edit", methods=["GET", "POST"])
@admin_required
def medicine_edit(medicine_id):
    medicine = content.get_medicine(medicine_id)
    if not medicine:
        flash("Medicine not found.", "error")
        return redirect(url_for("admin.medicines_list"))

    if request.method == "POST":
        db = _require_db()
        if db is None:
            flash("Firebase isn't configured — can't save yet.", "error")
            return redirect(url_for("admin.medicines_list"))

        db.collection("medicines").document(medicine_id).set(_medicine_payload(medicine_id, request.form, medicine))
        flash("Medicine updated.", "info")
        return redirect(url_for("admin.medicines_list"))

    return render_template("admin/medicine_form.html", medicine=medicine, categories=content.get_medicine_categories())


def _medicine_payload(medicine_id, form, existing=None):
    existing = existing or {}
    return {
        "id": medicine_id,
        "name": form.get("name", "").strip(),
        "category": form.get("category", "").strip(),
        "description": form.get("description", "").strip(),
        "mrp": form.get("mrp", 0, type=int),
        "offer_price": form.get("offer_price", 0, type=int),
        "stock": form.get("stock", 0, type=int),
        "prescription_required": form.get("prescription_required") == "on",
        "rating": existing.get("rating", 4.5),
        "review_count": existing.get("review_count", 0),
        "image": form.get("image", "").strip() or existing.get("image", "med-paracetamol.jpg"),
    }


@admin_bp.route("/medicines/<medicine_id>/delete", methods=["POST"])
@admin_required
def medicine_delete(medicine_id):
    db = _require_db()
    if db is not None:
        db.collection("medicines").document(medicine_id).delete()
        flash("Medicine deleted.", "info")
    return redirect(url_for("admin.medicines_list"))


# ---------------------------------------------------------------- Appointments

@admin_bp.route("/appointments")
@admin_required
def appointments_list():
    status_filter = request.args.get("status", "")
    appointments = _fetch_appointments(status_filter)
    return render_template("admin/appointments.html", appointments=appointments, status_filter=status_filter)


@admin_bp.route("/appointments/table")
@admin_required
def appointments_table_fragment():
    status_filter = request.args.get("status", "")
    appointments = _fetch_appointments(status_filter)
    return render_template("admin/_appointments_table.html", appointments=appointments)


def _fetch_appointments(status_filter=""):
    db = _require_db()
    appointments = []
    if db is not None:
        docs = db.collection("appointments").stream()
        appointments = [{**d.to_dict(), "id": d.id} for d in docs]
        if status_filter:
            appointments = [a for a in appointments if a.get("status") == status_filter]
        appointments.sort(key=lambda a: (a.get("date", ""), a.get("time", "")))
    return appointments


@admin_bp.route("/appointments/<appointment_id>/status", methods=["POST"])
@admin_required
def appointment_status(appointment_id):
    db = _require_db()
    new_status = request.form.get("status")
    if db is not None and new_status in ("confirmed", "cancelled", "completed", "pending"):
        doc_ref = db.collection("appointments").document(appointment_id)
        doc = doc_ref.get()
        appt = doc.to_dict() if doc.exists else {}

        update = {"status": new_status}
        # Generate a video-call link the first time an online appointment is confirmed.
        if new_status == "confirmed" and appt.get("consultation_type") == "online" and not appt.get("meeting_link"):
            update["meeting_link"] = f"https://meet.jit.si/PandeyHealthClinic-{appointment_id}"

        doc_ref.update(update)

        if appt.get("patient_uid"):
            from app.utils.notifications import notify

            messages = {
                "confirmed": f"Your appointment for {appt.get('service_name', 'your service')} on {appt.get('date', '')} is confirmed.",
                "cancelled": f"Your appointment for {appt.get('service_name', 'your service')} was cancelled by the clinic.",
                "completed": f"Your appointment for {appt.get('service_name', 'your service')} is marked complete.",
                "pending": f"Your appointment for {appt.get('service_name', 'your service')} is pending review again.",
            }
            notify(appt["patient_uid"], messages.get(new_status, "Your appointment status changed."), link="/dashboard/")

        flash(f"Appointment marked as {new_status}.", "info")
    return redirect(url_for("admin.appointments_list"))


# ---------------------------------------------------------------- Orders

@admin_bp.route("/orders")
@admin_required
def orders_list():
    status_filter = request.args.get("status", "")
    orders = _fetch_orders(status_filter)
    return render_template("admin/orders.html", orders=orders, status_filter=status_filter)


@admin_bp.route("/orders/table")
@admin_required
def orders_table_fragment():
    status_filter = request.args.get("status", "")
    orders = _fetch_orders(status_filter)
    return render_template("admin/_orders_table.html", orders=orders)


def _fetch_orders(status_filter=""):
    db = _require_db()
    orders = []
    if db is not None:
        docs = db.collection("orders").stream()
        orders = [{**d.to_dict(), "id": d.id} for d in docs]
        if status_filter:
            orders = [o for o in orders if o.get("status") == status_filter]
        orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
    return orders


@admin_bp.route("/orders/<order_id>/status", methods=["POST"])
@admin_required
def order_status(order_id):
    db = _require_db()
    new_status = request.form.get("status")
    valid = ("pending", "confirmed", "packed", "dispatched", "delivered", "cancelled", "refunded")
    if db is not None and new_status in valid:
        doc_ref = db.collection("orders").document(order_id)
        doc = doc_ref.get()
        order = doc.to_dict() if doc.exists else {}

        doc_ref.update({"status": new_status})

        if order.get("patient_uid"):
            from app.utils.notifications import notify

            notify(order["patient_uid"], f"Your order is now {new_status}.", link="/dashboard/")

        flash(f"Order marked as {new_status}.", "info")
    return redirect(url_for("admin.orders_list"))


@admin_bp.route("/orders/<order_id>/return-status", methods=["POST"])
@admin_required
def order_return_status(order_id):
    db = _require_db()
    decision = request.form.get("decision")
    if db is not None and decision in ("approved", "rejected"):
        doc_ref = db.collection("orders").document(order_id)
        doc = doc_ref.get()
        order = doc.to_dict() if doc.exists else {}
        return_request = order.get("return_request")

        if return_request:
            return_request["status"] = decision
            doc_ref.update({"return_request": return_request})

            if order.get("patient_uid"):
                from app.utils.notifications import notify

                request_type = return_request.get("type", "return")
                notify(
                    order["patient_uid"],
                    f"Your {request_type} request was {decision}.",
                    link="/dashboard/",
                )

            flash(f"Return/exchange request {decision}.", "info")
        else:
            flash("No return/exchange request found on this order.", "error")
    return redirect(url_for("admin.orders_list"))


# ---------------------------------------------------------------- Testimonials

@admin_bp.route("/testimonials")
@admin_required
def testimonials_list():
    db = _require_db()
    testimonials = []
    if db is not None:
        docs = db.collection("testimonials").stream()
        testimonials = [{**d.to_dict(), "id": d.id} for d in docs]
    else:
        testimonials = content.get_testimonials()
    return render_template("admin/testimonials.html", testimonials=testimonials)


@admin_bp.route("/testimonials/<testimonial_id>/approve", methods=["POST"])
@admin_required
def testimonial_approve(testimonial_id):
    db = _require_db()
    if db is not None:
        db.collection("testimonials").document(testimonial_id).update({"approved": True})
        flash("Testimonial approved.", "info")
    return redirect(url_for("admin.testimonials_list"))


@admin_bp.route("/testimonials/<testimonial_id>/reject", methods=["POST"])
@admin_required
def testimonial_reject(testimonial_id):
    db = _require_db()
    if db is not None:
        db.collection("testimonials").document(testimonial_id).update({"approved": False})
        flash("Testimonial hidden from the site.", "info")
    return redirect(url_for("admin.testimonials_list"))


@admin_bp.route("/testimonials/<testimonial_id>/delete", methods=["POST"])
@admin_required
def testimonial_delete(testimonial_id):
    db = _require_db()
    if db is not None:
        db.collection("testimonials").document(testimonial_id).delete()
        flash("Testimonial deleted.", "info")
    return redirect(url_for("admin.testimonials_list"))


# ---------------------------------------------------------------- Gallery

@admin_bp.route("/gallery")
@admin_required
def gallery_list():
    db = _require_db()
    items = []
    if db is not None:
        docs = db.collection("gallery").stream()
        items = [{**d.to_dict(), "id": d.id} for d in docs]
    else:
        items = content.get_gallery()
    return render_template("admin/gallery.html", items=items, categories=["Clinic", "Doctor", "Infrastructure", "Events", "Certificates"])


@admin_bp.route("/gallery/upload", methods=["POST"])
@admin_required
def gallery_upload():
    db = _require_db()
    if db is None:
        flash("Firebase isn't configured — can't upload yet.", "error")
        return redirect(url_for("admin.gallery_list"))

    image_file = request.files.get("image")
    category = request.form.get("category", "Clinic")
    caption = request.form.get("caption", "").strip()

    if not image_file or not image_file.filename:
        flash("Please choose a photo to upload.", "error")
        return redirect(url_for("admin.gallery_list"))

    image_url_result = upload_patient_report(image_file, "gallery", subfolder="gallery")
    if not image_url_result:
        flash(
            "Upload failed — check that the file is a jpg/png/webp under 8MB. "
            "If this keeps happening, see the server logs for the exact Storage error.",
            "error",
        )
        return redirect(url_for("admin.gallery_list"))

    db.collection("gallery").document().set(
        {"category": category, "caption": caption, "image": image_url_result}
    )
    flash("Photo added to gallery.", "info")
    return redirect(url_for("admin.gallery_list"))


@admin_bp.route("/gallery/<item_id>/delete", methods=["POST"])
@admin_required
def gallery_delete(item_id):
    db = _require_db()
    if db is not None:
        db.collection("gallery").document(item_id).delete()
        flash("Photo removed.", "info")
    return redirect(url_for("admin.gallery_list"))


# ---------------------------------------------------------------- Patients

@admin_bp.route("/patients")
@admin_required
def patients_list():
    db = _require_db()
    patients = []
    if db is not None:
        docs = db.collection("users").where("role", "==", "patient").stream()
        patients = [{**d.to_dict(), "id": d.id} for d in docs]
    return render_template("admin/patients.html", patients=patients)


# ---------------------------------------------------------------- Consultations (chat)

@admin_bp.route("/consultations")
@admin_required
def consultations_list():
    threads = _fetch_consultation_threads()
    return render_template("admin/consultations.html", threads=threads)


@admin_bp.route("/consultations/table")
@admin_required
def consultations_table_fragment():
    threads = _fetch_consultation_threads()
    return render_template("admin/_consultations_table.html", threads=threads)


def _fetch_consultation_threads():
    db = _require_db()
    threads = []
    if db is not None:
        appts = db.collection("appointments").where("consultation_type", "==", "online").stream()
        for a in appts:
            appt = {**a.to_dict(), "id": a.id}
            messages = list(
                db.collection("appointments").document(a.id).collection("messages").stream()
            )
            messages_sorted = sorted((m.to_dict() for m in messages), key=lambda m: m.get("created_at", ""))
            last_message = messages_sorted[-1] if messages_sorted else None
            unread = sum(
                1 for m in messages_sorted
                if m.get("sender_role") != "admin" and not m.get("read_by_admin", False)
            )
            threads.append(
                {
                    **appt,
                    "message_count": len(messages_sorted),
                    "last_message": last_message,
                    "unread_count": unread,
                }
            )
        threads.sort(
            key=lambda t: (t["last_message"]["created_at"] if t["last_message"] else t.get("date", "")),
            reverse=True,
        )
    return threads


@admin_bp.route("/consultations/<appointment_id>")
@admin_required
def consultation_thread(appointment_id):
    db = _require_db()
    if db is None:
        flash("Firebase isn't configured yet.", "error")
        return redirect(url_for("admin.consultations_list"))

    doc = db.collection("appointments").document(appointment_id).get()
    if not doc.exists:
        flash("Consultation not found.", "error")
        return redirect(url_for("admin.consultations_list"))

    appointment = {**doc.to_dict(), "id": doc.id}

    messages_ref = db.collection("appointments").document(appointment_id).collection("messages")
    messages = [{**m.to_dict(), "id": m.id} for m in messages_ref.stream()]
    messages.sort(key=lambda m: m.get("created_at", ""))

    # Mark incoming (patient) messages as read the moment admin opens the thread.
    for m in messages:
        if m.get("sender_role") != "admin" and not m.get("read_by_admin", False):
            messages_ref.document(m["id"]).update({"read_by_admin": True})

    return render_template("admin/consultation_thread.html", appointment=appointment, messages=messages)


@admin_bp.route("/consultations/<appointment_id>/messages")
@admin_required
def consultation_messages_fragment(appointment_id):
    db = _require_db()
    if db is None:
        return "", 204

    messages_ref = db.collection("appointments").document(appointment_id).collection("messages")
    messages = [{**m.to_dict(), "id": m.id} for m in messages_ref.stream()]
    messages.sort(key=lambda m: m.get("created_at", ""))

    for m in messages:
        if m.get("sender_role") != "admin" and not m.get("read_by_admin", False):
            messages_ref.document(m["id"]).update({"read_by_admin": True})

    return render_template("admin/_consultation_messages.html", messages=messages)


@admin_bp.route("/consultations/<appointment_id>/message", methods=["POST"])
@admin_required
def consultation_reply(appointment_id):
    db = _require_db()
    if db is None:
        return redirect(url_for("admin.consultations_list"))

    doc_ref = db.collection("appointments").document(appointment_id)
    doc = doc_ref.get()
    if not doc.exists:
        flash("Consultation not found.", "error")
        return redirect(url_for("admin.consultations_list"))

    appointment = doc.to_dict()
    text = request.form.get("text", "").strip()
    if text:
        doc_ref.collection("messages").document().set(
            {
                "sender_uid": "admin",
                "sender_name": f"{app_config_clinic_name()} Team",
                "sender_role": "admin",
                "text": text,
                "read_by_admin": True,
                "created_at": datetime.datetime.utcnow().isoformat(),
            }
        )
        if appointment.get("patient_uid"):
            from app.utils.notifications import notify

            notify(
                appointment["patient_uid"],
                "The clinic replied to your consultation chat.",
                link=f"/appointments/{appointment_id}/consult",
            )

    return redirect(url_for("admin.consultation_thread", appointment_id=appointment_id))


def app_config_clinic_name():
    from flask import current_app

    return current_app.config.get("CLINIC_NAME", "Pandey Health Clinic")


# ---------------------------------------------------------------- Site CMS

CMS_SECTIONS = {
    "hero": content.get_hero,
    "about": content.get_about,
    "vision": content.get_vision,
    "doctor": content.get_doctor,
    "contact": content.get_contact,
}


@admin_bp.route("/content")
@admin_required
def content_list():
    sections = {name: getter() for name, getter in CMS_SECTIONS.items()}
    return render_template("admin/content.html", sections=sections)


@admin_bp.route("/content/<section>", methods=["POST"])
@admin_required
def content_save(section):
    if section not in CMS_SECTIONS:
        flash("Unknown content section.", "error")
        return redirect(url_for("admin.content_list"))

    db = _require_db()
    if db is None:
        flash("Firebase isn't configured — can't save yet.", "error")
        return redirect(url_for("admin.content_list"))

    # Flat text-field sections only (hero/about/doctor/contact). Vision's
    # nested "points" list isn't editable from this simple form yet —
    # it still displays live from Firestore/seed data.
    payload = {k: v for k, v in request.form.items() if k != "csrf_token"}
    db.collection("site_content").document(section).set(payload, merge=True)
    flash(f"{section.capitalize()} content updated.", "info")
    return redirect(url_for("admin.content_list"))
