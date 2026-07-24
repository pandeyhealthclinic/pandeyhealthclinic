"""
Server-side session cart + wishlist for the medicine store.

Deliberately session-based (not Firestore) so anonymous visitors can
browse and add to cart before creating an account — matching typical
pharmacy UX. Checkout is where login_required kicks in and the cart
gets converted into a Firestore order.
"""
from flask import session

from app.utils import content_service as content

CART_KEY = "cart"
WISHLIST_KEY = "wishlist"


def get_cart():
    return session.get(CART_KEY, {})


def add_to_cart(medicine_id, qty=1):
    cart = session.get(CART_KEY, {})
    cart[medicine_id] = cart.get(medicine_id, 0) + max(1, qty)
    session[CART_KEY] = cart
    session.modified = True


def update_cart_item(medicine_id, qty):
    cart = session.get(CART_KEY, {})
    if qty <= 0:
        cart.pop(medicine_id, None)
    else:
        cart[medicine_id] = qty
    session[CART_KEY] = cart
    session.modified = True


def remove_from_cart(medicine_id):
    cart = session.get(CART_KEY, {})
    cart.pop(medicine_id, None)
    session[CART_KEY] = cart
    session.modified = True


def clear_cart():
    session.pop(CART_KEY, None)
    session.modified = True


def cart_line_items():
    """Return [{medicine, qty, line_total}, ...] for everything in the cart,
    silently dropping any ids that no longer exist in the catalog."""
    cart = get_cart()
    medicines = {m["id"]: m for m in content.get_medicines()}
    items = []
    for medicine_id, qty in cart.items():
        medicine = medicines.get(medicine_id)
        if not medicine:
            continue
        items.append(
            {
                "medicine": medicine,
                "qty": qty,
                "line_total": medicine["offer_price"] * qty,
            }
        )
    return items


def cart_total():
    return sum(item["line_total"] for item in cart_line_items())


def cart_count():
    return sum(get_cart().values())


# ---------------- Wishlist ----------------

def get_wishlist_ids():
    return session.get(WISHLIST_KEY, [])


def toggle_wishlist(medicine_id):
    wishlist = session.get(WISHLIST_KEY, [])
    if medicine_id in wishlist:
        wishlist.remove(medicine_id)
    else:
        wishlist.append(medicine_id)
    session[WISHLIST_KEY] = wishlist
    session.modified = True
    return medicine_id in wishlist


def wishlist_items():
    ids = get_wishlist_ids()
    medicines = {m["id"]: m for m in content.get_medicines()}
    return [medicines[i] for i in ids if i in medicines]
