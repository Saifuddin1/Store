from flask import session
from app.models import Product, ProductImage


def get_cart():
    """
    Get cart from session or initialize it
    """
    if "cart" not in session:
        session["cart"] = {}
    return session["cart"]

def add_to_cart(product_id, qty=1):
    cart = get_cart()
    product = Product.query.get_or_404(product_id)

    # ❌ Product inactive or out of stock
    if not product.is_active or product.stock_quantity <= 0:
        return False, "Product is out of stock"

    qty = max(1, qty)
    key = str(product_id)

    existing_qty = cart.get(key, {}).get("qty", 0)

    # ❌ Stock validation (STRICT)
    if existing_qty + qty > product.stock_quantity:
        if existing_qty >= product.stock_quantity:
            return False, f"Only {product.stock_quantity} item(s) available"
        else:
            return False, (
                f"You already have {existing_qty} in cart. "
                f"Only {product.stock_quantity} available."
            )

    # ✅ Add or update cart
    if key in cart:
        cart[key]["qty"] += qty
    else:
        primary_image = next(
            (img for img in product.images if img.is_primary),
            None
        )

        cart[key] = {
            "product_id": product.id,
            "name": product.name,
            "price": product.price,
            "final_price": product.final_price,
            "qty": qty,
            "image": primary_image.image_path if primary_image else None,
        }

    session.modified = True
    return True, "Added to cart"



def update_cart(product_id, qty):
    cart = get_cart()
    key = str(product_id)

    if key not in cart:
        return False

    product = Product.query.get_or_404(product_id)

    qty = max(1, qty)
    qty = min(qty, product.stock_quantity)

    cart[key]["qty"] = qty

    # 🔥 THIS LINE WAS MISSING
    session["cart"] = cart
    session.modified = True

    return True



def remove_from_cart(product_id):
    cart = get_cart()
    key = str(product_id)

    if key in cart:
        del cart[key]
        session.modified = True


def clear_cart():
    session.pop("cart", None)
    session.modified = True


# def cart_items():
#     return list(get_cart().values())


def cart_items():
    cart = get_cart()
    items = []

    for key, data in cart.items():
        product = Product.query.get(int(key))
        if not product or not product.is_active:
            continue

        primary_image = next(
            (img for img in product.images if img.is_primary),
            None
        )

        items.append({
            "product_id": product.id,
            "name": product.name,
            "price": product.price,
            "final_price": product.final_price,
            "stock_quantity": product.stock_quantity,  # ✅ NOW AVAILABLE
            "qty": data["qty"],
            "image": primary_image.image_path if primary_image else None,
        })

    return items


def cart_totals():
    items = cart_items()

    total_qty = 0
    subtotal = 0.0

    for item in items:
        # Supports both dict-style and object-style items
        qty = item["qty"] if isinstance(item, dict) else item.qty
        price = item["final_price"] if isinstance(item, dict) else item.final_price

        total_qty += qty
        subtotal += price * qty

    subtotal = round(subtotal, 2)

    # 🚚 Delivery fee rule
    delivery_fee = 0 if subtotal >= 500 else 49

    grand_total = round(subtotal + delivery_fee, 2)

    return {
        "total_qty": total_qty,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "grand_total": grand_total,
    }

