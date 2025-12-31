from flask import (
    Blueprint,
    abort, 
    render_template,
    redirect, url_for, request, flash, current_app
)
from sqlalchemy import func
from flask_login import login_required, current_user
from app.models import (
    FAQ, AboutPage, Category, PrivacyPolicy, 
    Product, Order, Address, OrderItem, ProductReview, ShippingReturns, StockNotification, 
    TermsConditions,OrderStatusHistory, Wishlist
)
from app.utils.cart import (
    cart_items,
    cart_totals,
    update_cart,
    remove_from_cart,
    add_to_cart,
    clear_cart
)
from app import db
from flask_mail import Message
from app import mail
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, func



main_bp = Blueprint("main", __name__)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("store/user_dashboard.html")


@main_bp.route("/orders")
@login_required
def orders():
    orders = (
        Order.query
        .filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return render_template(
        "store/my_orders.html",
        orders=orders
    )


@main_bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.filter_by(
        id=order_id,
        user_id=current_user.id
    ).first_or_404()

    return render_template(
        "store/order_success.html",
        order=order
    )


# @main_bp.route("/")
# def home():
#     q = request.args.get("q", "").strip()

#     products_query = (
#         Product.query
#         .join(Category)
#         .filter(
#             Product.is_active == True,
#             Category.is_active == True
#         )
#     )
#     print(products_query.count())

#     # 🔍 SEARCH LOGIC
#     if q:
#         products_query = products_query.filter(
#             or_(
#                 Product.name.ilike(f"%{q}%"),
#                 Category.name.ilike(f"%{q}%")
#             )
#         )
#     products = (
#         products_query
#         .order_by(Product.created_at.desc())
#         .limit(8)
#         .all()
#     )

#     # ⭐ Rating summary (avg + count)
#     ratings = (
#         db.session.query(
#             ProductReview.product_id,
#             func.avg(ProductReview.rating).label("avg_rating"),
#             func.count(ProductReview.id).label("total_reviews")
#         )
#         .filter(ProductReview.is_approved == True)
#         .group_by(ProductReview.product_id)
#         .all()
#     )

#     rating_map = {
#         r.product_id: {
#             "avg": round(float(r.avg_rating), 1),
#             "count": r.total_reviews
#         }
#         for r in ratings
#     }


#     return render_template(
#         "store/home.html",
#         products=products,
#         rating_map=rating_map,
#         search_query=q
#     )


from flask_login import current_user
from flask import redirect, url_for

@main_bp.route("/")
def home():

    # 🔐 Redirect admin users to admin dashboard
    if current_user.is_authenticated:
        if getattr(current_user, "role", None) == "admin":
            return redirect(url_for("admin.dashboard"))


    q = request.args.get("q", "").strip()

    products_query = (
        Product.query
        .join(Category)
        .filter(
            Product.is_active == True,
            Category.is_active == True
        )
    )

    # 🔍 SEARCH
    if q:
        products_query = products_query.filter(
            or_(
                Product.name.ilike(f"%{q}%"),
                Category.name.ilike(f"%{q}%")
            )
        )

    products = (
        products_query
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )

    # ⭐ Rating summary
    ratings = (
        db.session.query(
            ProductReview.product_id,
            func.avg(ProductReview.rating).label("avg_rating"),
            func.count(ProductReview.id).label("total_reviews")
        )
        .filter(ProductReview.is_approved == True)
        .group_by(ProductReview.product_id)
        .all()
    )

    rating_map = {
        r.product_id: {
            "avg": round(float(r.avg_rating), 1),
            "count": r.total_reviews
        }
        for r in ratings
    }

    return render_template(
        "store/home.html",
        products=products,
        rating_map=rating_map,
        search_query=q
    )


from sqlalchemy import or_, func

@main_bp.route("/products")
def product_list():
    q = request.args.get("q", "").strip()

    products_query = (
        Product.query
        .join(Category)
        .filter(
            Product.is_active == True,
            Category.is_active == True
        )
    )

    # 🔍 SEARCH LOGIC
    if q:
        products_query = products_query.filter(
            or_(
                Product.name.ilike(f"%{q}%"),
                Category.name.ilike(f"%{q}%")
            )
        )

    products = (
        products_query
        .order_by(Product.created_at.desc())
        .all()
    )

    # ⭐ Rating summary (avg + count)
    ratings = (
        db.session.query(
            ProductReview.product_id,
            func.avg(ProductReview.rating).label("avg_rating"),
            func.count(ProductReview.id).label("total_reviews")
        )
        .filter(ProductReview.is_approved == True)
        .group_by(ProductReview.product_id)
        .all()
    )

    rating_map = {
        r.product_id: {
            "avg": round(float(r.avg_rating), 1),
            "count": r.total_reviews
        }
        for r in ratings
    }

    return render_template(
        "store/products.html",
        products=products,
        rating_map=rating_map,
        search_query=q  # optional UX improvement
    )


@main_bp.route("/category/<slug>")
def category_products(slug):
    q = request.args.get("q", "").strip()

    category = Category.query.filter_by(
        slug=slug,
        is_active=True
    ).first_or_404()

    products_query = (
        Product.query
        .filter(
            Product.category_id == category.id,
            Product.is_active == True
        )
    )

    # 🔍 SEARCH WITHIN CATEGORY
    if q:
        products_query = products_query.filter(
            or_(
                Product.name.ilike(f"%{q}%"),
                Category.name.ilike(f"%{q}%")
            )
        )

    products = (
        products_query
        .order_by(Product.created_at.desc())
        .all()
    )

    # ⭐ Rating summary (avg + count)
    ratings = (
        db.session.query(
            ProductReview.product_id,
            func.avg(ProductReview.rating).label("avg_rating"),
            func.count(ProductReview.id).label("total_reviews")
        )
        .filter(ProductReview.is_approved == True)
        .group_by(ProductReview.product_id)
        .all()
    )

    rating_map = {
        r.product_id: {
            "avg": round(float(r.avg_rating), 1),
            "count": r.total_reviews
        }
        for r in ratings
    }

    return render_template(
        "store/category.html",
        category=category,
        products=products,
        rating_map=rating_map,
        search_query=q  # optional UX
    )



@main_bp.route("/product/<slug>")
def product_detail(slug):
    product = (
        Product.query
        .filter_by(slug=slug, is_active=True)
        .first_or_404()
    )

    images = product.images
    primary_image = next((img for img in images if img.is_primary), None)

    reviews = (
        ProductReview.query
        .filter_by(product_id=product.id, is_approved=True)
        .order_by(ProductReview.created_at.desc())
        .all()
    )

    # ⭐ Average rating
    avg_rating = None
    if reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)

    # 🔑 Map reviewer name from delivered order address
    reviewer_names = {}

    if reviews:
        delivered_orders = (
            Order.query
            .join(OrderItem)
            .join(Address)
            .filter(
                OrderItem.product_id == product.id,
                Order.status == "DELIVERED"
            )
            .all()
        )

        for o in delivered_orders:
            reviewer_names[o.user_id] = o.address.full_name
        # 🔔 COUNT WAITING USERS
    wait_count = (
        db.session.query(func.count(StockNotification.id))
        .filter(StockNotification.product_id == product.id)
        .scalar()
    )

    return render_template(
        "store/product_detail.html",
        product=product,
        images=images,
        primary_image=primary_image,
        reviews=reviews,
        avg_rating=avg_rating,
        reviewer_names=reviewer_names,
        wait_count=wait_count
    )




@main_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    qty = request.form.get("qty", type=int, default=1)

    success, message = add_to_cart(product_id, qty)

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    # Redirect back to product page if possible
    return redirect(request.referrer or url_for("main.product_list"))


@main_bp.route("/cart")
def cart_view():
    items = cart_items()
    totals = cart_totals()

    return render_template(
        "store/cart.html",
        items=items,
        totals=totals,
    )


@main_bp.route("/cart/update", methods=["POST"])
def cart_update():
    product_id = request.form.get("product_id")
    qty = request.form.get("qty", type=int)

    if product_id and qty:
        update_cart(product_id, qty)

    return redirect(url_for("main.cart_view"))


@main_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
def cart_remove(product_id):
    remove_from_cart(product_id)
    return redirect(url_for("main.cart_view"))



def validate_cart_stock(items):
    """
    Validate stock before checkout.
    items = cart_items()
    """

    for item in items:
        product = Product.query.get(item["product_id"])

        if not product or not product.is_active:
            return False, f"{item['name']} is no longer available"

        if product.stock_quantity <= 0:
            return False, f"{product.name} is out of stock"

        if item["qty"] > product.stock_quantity:
            return (
                False,
                f"Only {product.stock_quantity} item(s) left for {product.name}"
            )

    return True, None


@main_bp.route("/checkout")
@login_required
def checkout():
    items = cart_items()
    totals = cart_totals()

    if not items:
        flash("Your cart is empty", "warning")
        return redirect(url_for("main.cart_view"))

    # 🔐 FINAL STOCK VALIDATION
    is_valid, error = validate_cart_stock(items)

    if not is_valid:
        flash(error, "danger")
        return redirect(url_for("main.cart_view"))

    addresses = Address.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "store/checkout.html",
        items=items,
        totals=totals,
        addresses=addresses,
    )


@main_bp.route("/place-order", methods=["POST"])
@login_required
def place_order():
    items = cart_items()
    totals = cart_totals()

    if not items:
        return redirect(url_for("main.cart_view"))

    address_id = request.form.get("address_id", type=int)
    if not address_id:
        return redirect(url_for("main.checkout"))

    address = Address.query.filter_by(
        id=address_id,
        user_id=current_user.id
    ).first_or_404()

    try:
        product_ids = [item["product_id"] for item in items]

        # 🔒 LOCK PRODUCT ROWS (safe even if SQLite ignores it)
        products = (
            db.session.execute(
                select(Product)
                .where(Product.id.in_(product_ids))
                .with_for_update()
            )
            .scalars()
            .all()
        )

        product_map = {p.id: p for p in products}

        # ✅ FINAL STOCK CHECK
        for item in items:
            product = product_map.get(item["product_id"])
            if not product or product.stock_quantity < item["qty"]:
                raise Exception(
                    f"Product {item['name']} is out of stock"
                )

        # 🧾 CREATE ORDER
        order = Order(
            user_id=current_user.id,
            address_id=address.id,
            total_amount=totals["total_price"],
            status="PLACED",
        )
        db.session.add(order)
        db.session.flush()  # get order.id safely

        # 📦 CREATE ORDER ITEMS + DEDUCT STOCK
        for item in items:
            product = product_map[item["product_id"]]
            product.stock_quantity -= item["qty"]

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=item["name"],
                price=item["final_price"],
                qty=item["qty"],
                subtotal=item["final_price"] * item["qty"],
            )
            db.session.add(order_item)

        # ✅ SINGLE COMMIT (THIS IS THE ATOMIC POINT)
        db.session.commit()

        clear_cart()

        return redirect(
            url_for("main.order_success", order_id=order.id)
        )

    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")
        return redirect(url_for("main.checkout"))

    except SQLAlchemyError:
        db.session.rollback()
        flash("Something went wrong. Please try again.", "danger")
        return redirect(url_for("main.checkout"))




@main_bp.route("/address/add", methods=["GET", "POST"])
@login_required
def add_address():
    if request.method == "POST":
        address = Address(
            user_id=current_user.id,
            full_name=request.form["full_name"],
            phone=request.form["phone"],
            address_line1=request.form["address_line1"],
            address_line2=request.form.get("address_line2"),
            city=request.form["city"],
            state=request.form["state"],
            postal_code=request.form["postal_code"],
            country=request.form.get("country", "India"),
            is_default=True,
        )

        # unset previous default address
        Address.query.filter_by(
            user_id=current_user.id,
            is_default=True
        ).update({"is_default": False})

        db.session.add(address)
        db.session.commit()

        return redirect(url_for("main.checkout"))

    return render_template("store/address_form.html")


@main_bp.route("/order-success/<int:order_id>")
@login_required
def order_success(order_id):
    order = Order.query.filter_by(
        id=order_id,
        user_id=current_user.id
    ).first_or_404()

    return render_template(
        "store/order_success.html",
        order=order
    )


@main_bp.route("/products")
def products():
    products = Product.query.filter_by(is_active=True).all()
    return render_template(
        "store/products.html",
        products=products
    )


@main_bp.route("/orders/<int:order_id>/cancel", methods=["GET", "POST"])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)

    # 🔒 Security: Only owner can cancel
    if order.user_id != current_user.id:
        abort(403)

    # 🔒 Allow cancel only before dispatch
    if order.status not in ["PLACED", "CONFIRMED"]:
        flash("This order cannot be cancelled now", "danger")
        return redirect(url_for("main.orders"))

    if request.method == "POST":
        reason = request.form.get("reason")

        if not reason:
            flash("Cancellation reason is required", "danger")
            return redirect(request.url)

        try:
            # 🔁 RESTORE STOCK
            for item in order.items:
                product = Product.query.get(item.product_id)

                if product:
                    product.stock_quantity += item.qty
                

            # 🧾 STATUS HISTORY
            history = OrderStatusHistory(
                order_id=order.id,
                old_status=order.status,
                new_status="CANCELLED",
                changed_by=current_user.id,
                remark=reason
            )

            order.status = "CANCELLED"

            db.session.add(history)
            db.session.commit()

            flash("Your order has been cancelled successfully", "success")
            return redirect(url_for("main.orders"))

        except Exception:
            db.session.rollback()
            flash("Something went wrong. Please try again.", "danger")
            return redirect(url_for("main.orders"))

    return render_template("main/cancel_order.html", order=order)


@main_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order_post(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        abort(403)

    if order.status not in ["PLACED", "CONFIRMED"]:
        flash("This order cannot be cancelled at this stage.", "danger")
        return redirect(url_for("main.orders"))

    reason = request.form.get("reason")

    if not reason:
        flash("Cancellation reason is required.", "danger")
        return redirect(
            url_for("main.cancel_order", order_id=order.id)
        )

    # 📝 Save history
    history = OrderStatusHistory(
        order_id=order.id,
        old_status=order.status,
        new_status="CANCELLED",
        changed_by=current_user.id,
        remark=reason
    )

    order.status = "CANCELLED"

    db.session.add(history)
    db.session.commit()

    flash("Order cancelled successfully.", "success")
    return redirect(url_for("main.orders"))



@main_bp.route("/about")
def about():
    about = AboutPage.query.first()
    return render_template("main/about.html", about=about)


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        if not all([name, email, subject, message]):
            flash("All fields are required", "danger")
            return redirect(url_for("main.contact"))

        try:
            msg = Message(
                subject=f"[Contact Us] {subject}",
                sender=email,
                recipients=[current_app.config["MAIL_USERNAME"]],
            )

            msg.body = f"""
                New Contact Request

                Name: {name}
                Email: {email}

                Message:
                {message}
            """

            mail.send(msg)

            flash("Your message has been sent successfully!", "success")

        except Exception as e:
            flash("Unable to send message. Please try again later.", "danger")

        return redirect(url_for("main.contact"))
    email = "mdsaifuddinrs1@gmail.com"
    mobile = "9581170036"
    working_hours = "Mon – Sat (10:00 AM – 6:00 PM)"
    address = "MyStore Pvt Ltd, New Delhi, India"
    info_data = {
        "email": email,
        "mobile": mobile,
        "working_hours": working_hours,
        "address": address
    }

    return render_template("main/contact.html", info_data=info_data)


@main_bp.route("/privacy-policy")
def privacy_policy():
    policy = PrivacyPolicy.query.first()
    return render_template(
        "main/privacy_policy.html",
        policy=policy
    )


@main_bp.route("/terms-and-conditions")
def terms_and_conditions():
    terms = TermsConditions.query.first()
    return render_template("main/terms.html", terms=terms)


@main_bp.route("/faq")
def faq():
    faqs = FAQ.query.filter_by(is_active=True)\
                    .order_by(FAQ.display_order, FAQ.created_at)\
                    .all()
    return render_template("main/faq.html", faqs=faqs)


@main_bp.route("/shipping-returns")
def shipping_returns():
    page = ShippingReturns.query.first()
    return render_template(
        "main/shipping_returns.html",
        page=page
    )


@main_bp.route("/support")
def support():
    return render_template("main/support.html")


# ==============Add review============

def can_review_product(user_id, product_id):
    return (
        db.session.query(OrderItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == user_id,
            OrderItem.product_id == product_id,
            Order.status == "DELIVERED"   # 🔥 ONLY delivered
        )
        .first()
        is not None
    )



@main_bp.route("/review/<int:product_id>", methods=["POST"])
@login_required
def submit_review_from_order(product_id):

    product = Product.query.get_or_404(product_id)

    rating = request.form.get("rating", type=int)
    title = request.form.get("title", "").strip()
    comment = request.form.get("comment", "").strip()

    if not rating or rating not in range(1, 6):
        flash("Please select a valid rating.", "danger")
        return redirect(request.referrer)

    if not comment:
        flash("Review comment is required.", "danger")
        return redirect(request.referrer)

    # 🔒 Delivered check
    if not can_review_product(current_user.id, product.id):
        flash("You can review only after the product is delivered.", "danger")
        return redirect(request.referrer)

    try:
        review = ProductReview(
            product_id=product.id,
            user_id=current_user.id,
            rating=rating,
            title=title or None,
            comment=comment,
            is_approved=True
        )
        db.session.add(review)
        db.session.commit()
        flash("Thank you for reviewing the product!", "success")

    except Exception:
        db.session.rollback()
        flash("You have already reviewed this product.", "warning")

    return redirect(request.referrer)


@main_bp.route("/wishlist/toggle/<int:product_id>", methods=["POST"])
@login_required
def toggle_wishlist(product_id):

    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Removed from wishlist", "info")
    else:
        db.session.add(
            Wishlist(
                user_id=current_user.id,
                product_id=product_id
            )
        )
        db.session.commit()
        flash("Added to wishlist ❤️", "success")

    return redirect(request.referrer or url_for("main.home"))


@main_bp.route("/wishlist")
@login_required
def wishlist():

    q = request.args.get("q", "").strip()

    query = (
        Wishlist.query
        .join(Product, Wishlist.product_id == Product.id)
        .join(Category, Product.category_id == Category.id)
        .filter(Wishlist.user_id == current_user.id)
    )

    # 🔍 APPLY SEARCH (product + category)
    if q:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{q}%"),
                Category.name.ilike(f"%{q}%")
            )
        )

    items = (
        query
        .order_by(Wishlist.created_at.desc())
        .all()
    )

    return render_template(
        "store/wishlist.html",
        items=items,
        search_query=q
    )


@main_bp.route("/notify-me/<int:product_id>", methods=["POST"])
@login_required
def notify_me(product_id):
    product = Product.query.get_or_404(product_id)

    # If product already in stock, no need
    if product.stock_quantity > 0:
        flash("This product is already available.", "info")
        return redirect(request.referrer)

    # Check existing notification
    existing = StockNotification.query.filter_by(
        user_id=current_user.id,
        product_id=product.id
    ).first()

    if existing:
        flash("You will be notified when the product is back in stock.", "info")
        return redirect(request.referrer)

    notify = StockNotification(
        user_id=current_user.id,
        product_id=product.id
    )
    db.session.add(notify)
    db.session.commit()

    flash("We’ll notify you when this product is back in stock.", "success")
    return redirect(request.referrer)
