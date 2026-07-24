import datetime
import logging
import math

from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify

from app.firebase import get_db
from app.utils import content_service as content
from app.utils import cart as cart_service
from app.utils.decorators import login_required

logger = logging.getLogger(__name__)

medicines_bp = Blueprint("medicines", __name__, url_prefix="/medicines")

PAGE_SIZE = 9


@medicines_bp.route("/")
def store():
    medicines = content.get_medicines()

    query = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "")
    sort = request.args.get("sort", "")
    page = max(1, request.args.get("page", 1, type=int))

    if query:
        medicines = [m for m in medicines if query in m["name"].lower() or query in m["description"].lower()]
    if category:
        medicines = [m for m in medicines if m["category"] == category]

    if sort == "price_low":
        medicines.sort(key=lambda m: m["offer_price"])
    elif sort == "price_high":
        medicines.sort(key=lambda m: -m["offer_price"])
    elif sort == "rating":
        medicines.sort(key=lambda m: -m.get("rating", 0))
    elif sort == "name":
        medicines.sort(key=lambda m: m["name"])

    total_pages = max(1, math.ceil(len(medicines) / PAGE_SIZE))
    page = min(page, total_pages)
    start = (page - 1) * PAGE_SIZE
    page_items = medicines[start:start + PAGE_SIZE]

    return render_template(
        "medicines/store.html",
        medicines=page_items,
        categories=content.get_medicine_categories(),
        query=query,
        selected_category=category,
        sort=sort,
        page=page,
        total_pages=total_pages,
        total_results=len(medicines),
        wishlist_ids=cart_service.get_wishlist_ids(),
        cart_count=cart_service.cart_count(),
    )


@medicines_bp.route("/wishlist")
def wishlist():
    return render_template(
        "medicines/wishlist.html",
        items=cart_service.wishlist_items(),
        cart_count=cart_service.cart_count(),
    )


@medicines_bp.route("/<medicine_id>")
def detail(medicine_id):
    medicine = content.get_medicine(medicine_id)
    if not medicine:
        flash("That medicine couldn't be found.", "error")
        return redirect(url_for("medicines.store"))

    related = [
        m for m in content.get_medicines()
        if m["category"] == medicine["category"] and m["id"] != medicine_id
    ][:4]

    return render_template(
        "medicines/detail.html",
        medicine=medicine,
        related=related,
        in_wishlist=medicine_id in cart_service.get_wishlist_ids(),
        cart_count=cart_service.cart_count(),
    )


@medicines_bp.route("/cart")
def view_cart():
    return render_template(
        "medicines/cart.html",
        items=cart_service.cart_line_items(),
        total=cart_service.cart_total(),
    )


@medicines_bp.route("/cart/add", methods=["POST"])
def add_to_cart():
    medicine_id = request.form.get("medicine_id")
    qty = request.form.get("qty", 1, type=int)
    medicine = content.get_medicine(medicine_id)

    if not medicine:
        flash("That medicine couldn't be found.", "error")
        return redirect(url_for("medicines.store"))
    if medicine["stock"] <= 0:
        flash(f"{medicine['name']} is currently out of stock.", "error")
        return redirect(request.referrer or url_for("medicines.store"))

    cart_service.add_to_cart(medicine_id, qty)
    flash(f"Added {medicine['name']} to your cart.", "info")

    if request.form.get("buy_now"):
        return redirect(url_for("medicines.view_cart"))
    return redirect(request.referrer or url_for("medicines.store"))


@medicines_bp.route("/cart/update", methods=["POST"])
def update_cart():
    medicine_id = request.form.get("medicine_id")
    qty = request.form.get("qty", 0, type=int)
    cart_service.update_cart_item(medicine_id, qty)
    return redirect(url_for("medicines.view_cart"))


@medicines_bp.route("/cart/remove", methods=["POST"])
def remove_cart_item():
    medicine_id = request.form.get("medicine_id")
    cart_service.remove_from_cart(medicine_id)
    return redirect(url_for("medicines.view_cart"))


@medicines_bp.route("/wishlist/toggle", methods=["POST"])
def toggle_wishlist():
    medicine_id = request.form.get("medicine_id")
    is_saved = cart_service.toggle_wishlist(medicine_id)
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify({"in_wishlist": is_saved})
    flash("Saved to wishlist." if is_saved else "Removed from wishlist.", "info")
    return redirect(request.referrer or url_for("medicines.store"))


@medicines_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items = cart_service.cart_line_items()
    if not items:
        flash("Your cart is empty.", "info")
        return redirect(url_for("medicines.store"))

    needs_prescription = any(item["medicine"]["prescription_required"] for item in items)

    if request.method == "POST":
        db = get_db()
        payment_method = request.form.get("payment_method", "cod")
        address = request.form.get("address", "").strip()

        if not address:
            flash("Please enter a delivery address.", "error")
            return redirect(url_for("medicines.checkout"))

        if db is None:
            flash(
                "Orders aren't connected to the clinic system yet (Firebase not configured). "
                "Please call the clinic to place this order directly.",
                "info",
            )
            return redirect(url_for("main.home"))

        user = g.user
        order_ref = db.collection("orders").document()
        order_ref.set(
            {
                "patient_uid": user["uid"],
                "patient_name": user.get("name", ""),
                "patient_email": user.get("email", ""),
                "patient_phone": user.get("phone", ""),
                "items": [
                    {
                        "medicine_id": item["medicine"]["id"],
                        "name": item["medicine"]["name"],
                        "qty": item["qty"],
                        "price": item["medicine"]["offer_price"],
                    }
                    for item in items
                ],
                "total": cart_service.cart_total(),
                "address": address,
                "payment_method": payment_method,
                "needs_prescription": needs_prescription,
                "status": "pending",
                "created_at": datetime.datetime.utcnow().isoformat(),
            }
        )
        cart_service.clear_cart()
        flash("Order placed! We'll confirm it shortly.", "info")
        return redirect(url_for("medicines.order_confirmation", order_id=order_ref.id))

    return render_template(
        "medicines/checkout.html",
        items=items,
        total=cart_service.cart_total(),
        needs_prescription=needs_prescription,
    )


@medicines_bp.route("/order-confirmation/<order_id>")
@login_required
def order_confirmation(order_id):
    db = get_db()
    order = None
    if db is not None:
        doc = db.collection("orders").document(order_id).get()
        if doc.exists and doc.to_dict().get("patient_uid") == g.user["uid"]:
            order = {**doc.to_dict(), "id": doc.id}
    return render_template("medicines/order_confirmation.html", order=order)
