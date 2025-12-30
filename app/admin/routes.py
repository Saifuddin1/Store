from flask import (
    Blueprint, render_template,current_app,
    redirect, url_for, flash, request,
    jsonify
    )
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.models import (
    ALLOWED_STATUS_TRANSITIONS,
    FAQ,
    AboutPage, 
    Category,
    OrderItem, 
    OrderStatusHistory,
    PrivacyPolicy, 
    Product, 
    ProductImage,
    Order,
    ShippingReturns,
    SiteSettings,
    StockNotification,
    User,
    TermsConditions
)
from app import db
from slugify import slugify
import os
from werkzeug.utils import secure_filename
from app.utils.email import send_email
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm.attributes import flag_modified
import json




admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():

    total_categories = Category.query.count()
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_active=True).count()

    return render_template(
        "admin/dashboard.html",
        total_categories=total_categories,
        total_products=total_products,
        active_products=active_products,
    )


@admin_bp.route("/categories")
@login_required
@admin_required
def categories():
    categories = Category.query.order_by(Category.created_at.desc()).all()
    return render_template("admin/categories.html", categories=categories)


@admin_bp.route("/categories/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_category():
    if request.method == "POST":
        name = request.form.get("name")

        if not name:
            flash("Category name is required", "danger")
            return redirect(url_for("admin.add_category"))

        slug = slugify(name)

        exists = Category.query.filter(
            (Category.name == name) | (Category.slug == slug)
        ).first()
        if exists:
            flash("Category already exists", "danger")
            return redirect(url_for("admin.add_category"))

        category = Category(name=name, slug=slug)
        db.session.add(category)
        db.session.commit()

        flash("Category added successfully", "success")
        return redirect(url_for("admin.categories"))

    return render_template("admin/category_form.html", category=None)


@admin_bp.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)

    if request.method == "POST":
        name = request.form.get("name")
        is_active = bool(request.form.get("is_active"))

        if not name:
            flash("Category name is required", "danger")
            return redirect(url_for("admin.edit_category", category_id=category.id))

        category.name = name
        category.slug = slugify(name)
        category.is_active = is_active

        db.session.commit()

        flash("Category updated successfully", "success")
        return redirect(url_for("admin.categories"))

    return render_template("admin/category_form.html", category=category)


@admin_bp.route("/categories/delete/<int:category_id>", methods=["POST"])
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    db.session.delete(category)
    db.session.commit()

    flash("Category deleted", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/products")
@login_required
@admin_required
def products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products.html", products=products)


@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_product():
    categories = Category.query.filter_by(is_active=True).all()

    if not categories:
        flash("Please add a category first", "danger")
        return redirect(url_for("admin.categories"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = request.form.get("price", type=float)
        discount_type = request.form.get("discount_type")
        discount_value = request.form.get("discount_value", type=float)
        stock = request.form.get("stock_quantity", type=int)
        category_id = request.form.get("category_id", type=int)

        if not name or price is None or stock is None:
            flash("Required fields missing", "danger")
            return redirect(url_for("admin.add_product"))

        slug = slugify(name)

        exists = Product.query.filter_by(slug=slug).first()
        if exists:
            flash("Product with same name already exists", "danger")
            return redirect(url_for("admin.add_product"))

        product = Product(
            name=name,
            slug=slug,
            description=description,
            price=price,
            discount_type=discount_type,
            discount_value=discount_value or 0,
            stock_quantity=stock,
            category_id=category_id,
            is_active=True,
        )

        db.session.add(product)
        db.session.commit()

        flash("Product added successfully", "success")
        return redirect(url_for("admin.products"))

    return render_template(
        "admin/product_form.html",
        product=None,
        categories=categories,
    )


def send_stock_available_email(user_email, product):
    subject = f"🎉 {product.name} is back in stock!"

    body = f"""
        Hi 👋

        Good news!

        The product you were waiting for is back in stock:

        🛍 {product.name}
        💰 Price: ₹{product.final_price}

        👉 Visit now:
        http://yourdomain.com/product/{product.slug}
        http://127.0.0.1:5000/product/airplane

        Hurry! Stock may run out again.

        – My Store
    """

    send_email(
        subject=subject,
        recipients=[user_email],
        body=body
    )



@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.filter_by(is_active=True).all()

    if request.method == "POST":

        # 🔹 SAVE OLD STOCK (IMPORTANT)
        old_stock = product.stock_quantity

        # 🔹 UPDATE PRODUCT
        product.name = request.form.get("name")
        product.slug = slugify(product.name)
        product.description = request.form.get("description")
        product.price = request.form.get("price", type=float)
        product.discount_type = request.form.get("discount_type")
        product.discount_value = request.form.get("discount_value", type=float)
        product.stock_quantity = request.form.get("stock_quantity", type=int)
        product.category_id = request.form.get("category_id", type=int)
        product.is_active = bool(request.form.get("is_active"))

        db.session.commit()

        # 🔔 AUTO-NOTIFY USERS (0 → >0)
        if old_stock == 0 and product.stock_quantity > 0:

            from app.models import StockNotification, User

            notifications = (
                db.session.query(StockNotification, User.email)
                .join(User, User.id == StockNotification.user_id)
                .filter(StockNotification.product_id == product.id)
                .all()
            )

            for notify, email in notifications:
                try:
                    send_stock_available_email(email, product)
                except Exception as e:
                    current_app.logger.error(
                        f"Email notify failed for {email}: {e}"
                    )

            # ❌ Clear notify list after sending
            StockNotification.query.filter_by(
                product_id=product.id
            ).delete()

            db.session.commit()

        flash("Product updated successfully", "success")
        return redirect(url_for("admin.products"))

    return render_template(
        "admin/product_form.html",
        product=product,
        categories=categories,
    )


@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    db.session.delete(product)
    db.session.commit()

    flash("Product deleted", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:product_id>/images", methods=["GET", "POST"])
@login_required
@admin_required
def product_images(product_id):
    product = Product.query.get_or_404(product_id)
    images = ProductImage.query.filter_by(product_id=product.id).all()

    if request.method == "POST":
        file = request.files.get("image")

        if not file or file.filename == "":
            flash("No image selected", "danger")
            return redirect(url_for("admin.product_images", product_id=product.id))

        filename = secure_filename(file.filename)

        upload_dir = os.path.join(
            current_app.root_path,
            "static",
            "uploads",
            "products"
        )
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        # If no primary image exists, make this primary
        has_primary = ProductImage.query.filter_by(
            product_id=product.id,
            is_primary=True
        ).first()

        image = ProductImage(
            product_id=product.id,
            image_path=f"uploads/products/{filename}",
            is_primary=False if has_primary else True,
        )

        db.session.add(image)
        db.session.commit()

        flash("Image uploaded", "success")
        return redirect(url_for("admin.product_images", product_id=product.id))

    return render_template(
        "admin/product_images.html",
        product=product,
        images=images,
    )

@admin_bp.route("/products/images/<int:image_id>/primary", methods=["POST"])
@login_required
@admin_required
def set_primary_image(image_id):
    image = ProductImage.query.get_or_404(image_id)

    # Remove primary from other images
    ProductImage.query.filter_by(
        product_id=image.product_id,
        is_primary=True
    ).update({"is_primary": False})

    image.is_primary = True
    db.session.commit()

    flash("Primary image updated", "success")
    return redirect(url_for(
        "admin.product_images",
        product_id=image.product_id
    ))


@admin_bp.route("/products/images/<int:image_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_product_image(image_id):
    image = ProductImage.query.get_or_404(image_id)

    # Delete file from disk
    file_path = os.path.join(
        current_app.root_path,
        "static",
        image.image_path
    )
    if os.path.exists(file_path):
        os.remove(file_path)

    product_id = image.product_id
    db.session.delete(image)
    db.session.commit()

    flash("Image deleted", "success")
    return redirect(url_for("admin.product_images", product_id=product_id))




@admin_bp.route("/orders")
@login_required
@admin_required
def orders():
    status = request.args.get("status")

    query = Order.query.order_by(Order.created_at.desc())

    if status:
        query = query.filter_by(status=status)

    orders = query.all()

    return render_template(
        "admin/orders/orders_list.html",
        orders=orders,
        selected_status=status
    )


@admin_bp.route("/orders/<int:order_id>")
@login_required
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    return render_template(
        "admin/orders/order_detail.html",
        order=order
    )


def send_order_cancel_email(order, reason):
    subject = f"Order #{order.id} Cancelled"
    recipients = [order.user.email]

    body = f"""
    Hello {order.user.email},

    Your order #{order.id} has been cancelled by the store.

    Reason:
    {reason}

    If you have questions, please contact support.

    Regards,
    My Store
    """

    send_email(subject, recipients, body)




# @admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
# @login_required
# @admin_required
# def update_order_status(order_id):
#     order = Order.query.get_or_404(order_id)

#     new_status = request.form.get("status")
#     remark = request.form.get("remark")

#     allowed = ALLOWED_STATUS_TRANSITIONS.get(order.status, [])

#     if new_status not in allowed:
#         flash("Invalid status transition", "danger")
#         return redirect(url_for("admin.order_detail", order_id=order.id))

#     history = OrderStatusHistory(
#         order_id=order.id,
#         old_status=order.status,
#         new_status=new_status,
#         changed_by=current_user.id,
#         remark=remark
#     )

#     order.status = new_status

#     db.session.add(history)
#     db.session.commit()

#     # 🔔 Send cancellation email
#     if new_status == "CANCELLED":
#         send_order_cancel_email(order, remark)

#     flash(f"Order marked as {new_status}", "success")
#     return redirect(url_for("admin.order_detail", order_id=order.id))


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)

    new_status = request.form.get("status")
    remark = request.form.get("remark")

    allowed = ALLOWED_STATUS_TRANSITIONS.get(order.status, [])

    if new_status not in allowed:
        flash("Invalid status transition", "danger")
        return redirect(url_for("admin.order_detail", order_id=order.id))

    try:
        # 🔁 RESTORE STOCK ONLY IF ADMIN CANCELS
        if new_status == "CANCELLED":
            for item in order.items:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock_quantity += item.qty

        # 🧾 STATUS HISTORY
        history = OrderStatusHistory(
            order_id=order.id,
            old_status=order.status,
            new_status=new_status,
            changed_by=current_user.id,
            remark=remark
        )

        order.status = new_status

        db.session.add(history)
        db.session.commit()

        # 🔔 Send cancellation email
        if new_status == "CANCELLED":
            send_order_cancel_email(order, remark)

        flash(f"Order marked as {new_status}", "success")

    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")

    return redirect(url_for("admin.order_detail", order_id=order.id))



@admin_bp.route("/analytics")
@login_required
@admin_required
def analytics_dashboard():
    return render_template("admin/analytics/dashboard.html")


@admin_bp.route("/api/analytics/summary")
@login_required
@admin_required
def analytics_summary():
    """
    Cards / KPIs
    """
    now = datetime.utcnow()
    start_30 = now - timedelta(days=30)

    total_orders = Order.query.count()

    total_revenue = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).scalar()

    orders_30 = Order.query.filter(Order.created_at >= start_30).count()

    revenue_30 = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(Order.created_at >= start_30).scalar()

    total_customers = User.query.filter(User.role == "customer").count()
    total_products = Product.query.count()
    total_categories = Category.query.count()

    low_stock = Product.query.filter(Product.stock_quantity <= 5).count()

    cancelled = Order.query.filter(Order.status == "CANCELLED").count()
    delivered = Order.query.filter(Order.status == "DELIVERED").count()

    return jsonify({
        "total_orders": int(total_orders),
        "total_revenue": float(total_revenue),
        "orders_30": int(orders_30),
        "revenue_30": float(revenue_30),
        "total_customers": int(total_customers),
        "total_products": int(total_products),
        "total_categories": int(total_categories),
        "low_stock": int(low_stock),
        "cancelled": int(cancelled),
        "delivered": int(delivered),
    })


@admin_bp.route("/api/analytics/orders_by_status")
@login_required
@admin_required
def analytics_orders_by_status():
    """
    Pie / Doughnut chart - orders grouped by status
    """
    rows = db.session.query(
        Order.status,
        func.count(Order.id)
    ).group_by(Order.status).all()

    labels = [r[0] for r in rows]
    values = [int(r[1]) for r in rows]

    return jsonify({"labels": labels, "values": values})


@admin_bp.route("/api/analytics/orders_timeseries")
@login_required
@admin_required
def analytics_orders_timeseries():
    """
    Line chart - last 30 days orders count (daily)
    """
    now = datetime.utcnow()
    start = now - timedelta(days=30)

    rows = db.session.query(
        func.date(Order.created_at).label("d"),
        func.count(Order.id).label("cnt")
    ).filter(
        Order.created_at >= start
    ).group_by(
        func.date(Order.created_at)
    ).order_by(
        func.date(Order.created_at)
    ).all()

    labels = [r[0].strftime("%d %b") if hasattr(r[0], "strftime") else str(r[0]) for r in rows]
    values = [int(r[1]) for r in rows]

    return jsonify({"labels": labels, "values": values})


@admin_bp.route("/api/analytics/revenue_timeseries")
@login_required
@admin_required
def analytics_revenue_timeseries():
    """
    Line chart - last 30 days revenue sum (daily)
    """
    now = datetime.utcnow()
    start = now - timedelta(days=30)

    rows = db.session.query(
        func.date(Order.created_at).label("d"),
        func.coalesce(func.sum(Order.total_amount), 0).label("amt")
    ).filter(
        Order.created_at >= start
    ).group_by(
        func.date(Order.created_at)
    ).order_by(
        func.date(Order.created_at)
    ).all()

    labels = [r[0].strftime("%d %b") if hasattr(r[0], "strftime") else str(r[0]) for r in rows]
    values = [float(r[1]) for r in rows]

    return jsonify({"labels": labels, "values": values})


@admin_bp.route("/api/analytics/top_products")
@login_required
@admin_required
def analytics_top_products():
    """
    Bar chart - Top products by qty (last 30 days)
    """
    now = datetime.utcnow()
    start = now - timedelta(days=30)

    rows = db.session.query(
        OrderItem.product_name,
        func.sum(OrderItem.qty).label("qty_sum")
    ).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.created_at >= start
    ).group_by(
        OrderItem.product_name
    ).order_by(
        func.sum(OrderItem.qty).desc()
    ).limit(10).all()

    labels = [r[0] for r in rows]
    values = [int(r[1]) for r in rows]

    return jsonify({"labels": labels, "values": values})


@admin_bp.route("/about", methods=["GET", "POST"])
@login_required
@admin_required
def edit_about_page():
    about = AboutPage.query.first()

    if not about:
        about = AboutPage(
            hero_title="About MyStore",
            hero_subtitle="Trusted online store delivering quality products.",
            hero_image="https://images.unsplash.com/photo-1521334884684-d80222895322",
            who_title="Who We Are",
            who_content="We are an Indian e-commerce platform...",
            mission_title="Our Mission",
            mission_content="To make shopping simple and reliable.",
            why_blocks=[]
        )
        db.session.add(about)
        db.session.commit()

    if request.method == "POST":
        about.hero_title = request.form.get("hero_title")
        about.hero_subtitle = request.form.get("hero_subtitle")
        about.hero_image = request.form.get("hero_image")

        about.who_title = request.form.get("who_title")
        about.who_content = request.form.get("who_content")

        about.mission_title = request.form.get("mission_title")
        about.mission_content = request.form.get("mission_content")

        blocks = []
        index = 0
        while True:
            icon = request.form.get(f"icon_{index}")
            title = request.form.get(f"title_{index}")
            text = request.form.get(f"text_{index}")

            if icon is None and title is None and text is None:
                break

            blocks.append({
                "icon": icon,
                "title": title,
                "text": text
            })
            index += 1

        about.why_blocks = blocks
        db.session.commit()

        flash("About page updated successfully", "success")
        return redirect(url_for("admin.edit_about_page"))

    return render_template("admin/about_edit.html", about=about)


@admin_bp.route("/about/why/create", methods=["POST"])
@login_required
@admin_required
def create_why_block():
    about = AboutPage.query.first_or_404()
    blocks = about.why_blocks or []

    blocks.append({
        "icon": request.form.get("icon"),
        "title": request.form.get("title"),
        "text": request.form.get("text"),
    })
    flag_modified(about, "why_blocks")
    about.why_blocks = blocks
    db.session.commit()

    flash("Why block added", "success")
    return redirect(url_for("admin.edit_about_page"))


@admin_bp.route("/about/why/delete/<int:index>", methods=["POST"])
@login_required
@admin_required
def delete_why_block(index):
    about = AboutPage.query.first_or_404()

    blocks = list(about.why_blocks or [])  # 🔑 MAKE A COPY

    if 0 <= index < len(blocks):
        blocks.pop(index)

        about.why_blocks = blocks           # 🔑 REASSIGN
        flag_modified(about, "why_blocks")  # 🔑 FORCE CHANGE TRACKING

        db.session.commit()
        flash("Why block deleted", "success")

    return redirect(url_for("admin.edit_about_page"))


@admin_bp.route("/faqs")
def faq_list():
    faqs = FAQ.query.order_by(FAQ.display_order, FAQ.created_at).all()
    return render_template("admin/faq/list.html", faqs=faqs)


@admin_bp.route("/faqs/add", methods=["GET", "POST"])
def add_faq():
    if request.method == "POST":
        faq = FAQ(
            question=request.form["question"],
            answer=request.form["answer"],
            display_order=int(request.form.get("display_order", 0)),
            is_active=True if request.form.get("is_active") else False
        )
        db.session.add(faq)
        db.session.commit()
        flash("FAQ added successfully", "success")
        return redirect(url_for("admin.faq_list"))

    return render_template("admin/faq/form.html", faq=None)


@admin_bp.route("/faqs/edit/<int:faq_id>", methods=["GET", "POST"])
def edit_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)

    if request.method == "POST":
        faq.question = request.form["question"]
        faq.answer = request.form["answer"]
        faq.display_order = int(request.form.get("display_order", 0))
        faq.is_active = True if request.form.get("is_active") else False

        db.session.commit()
        flash("FAQ updated successfully", "success")
        return redirect(url_for("admin.faq_list"))

    return render_template("admin/faq/form.html", faq=faq)


def handle_policy_editor(model):

    record = model.query.first()

    if not record:
        record = model(sections=[])
        db.session.add(record)
        db.session.commit()

    if request.method == "POST":
        raw_json = request.form.get("sections_json", "")

        try:
            incoming = json.loads(raw_json)

            if not isinstance(incoming, list):
                raise ValueError("Sections must be a list")

            cleaned_sections = []
            seen_headings = set()

            for s in incoming:
                if not isinstance(s, dict):
                    continue

                heading = (s.get("heading") or "").strip()
                content = (s.get("content") or "").strip()

                if not heading or not content:
                    continue

                key = heading.lower()
                if key in seen_headings:
                    continue
                seen_headings.add(key)

                cleaned_sections.append({
                    "heading": heading,
                    "content": content
                })

            record.sections = cleaned_sections
            db.session.commit()

            flash("Content updated successfully", "success")

        except Exception:
            db.session.rollback()
            flash("Invalid or corrupted data. Nothing was saved.", "danger")

    return record


@admin_bp.route("/terms-and-conditions", methods=["GET", "POST"])
def edit_terms_conditions():
    terms = handle_policy_editor(TermsConditions)
    return render_template(
        "admin/terms_conditions.html",
        terms=terms
    )


@admin_bp.route("/shipping-returns", methods=["GET", "POST"])
def edit_shipping_returns():
    page = handle_policy_editor(ShippingReturns)
    return render_template(
        "admin/shipping_returns.html",
        page=page
    )


@admin_bp.route("/privacy-policy", methods=["GET", "POST"])
def edit_privacy_policy():
    policy = handle_policy_editor(PrivacyPolicy)
    return render_template(
        "admin/privacy_policy.html",
        policy=policy
    )


@admin_bp.route("/site-settings", methods=["GET", "POST"])
@login_required
@admin_required
def site_settings():

    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings(site_name="MyStore")
        db.session.add(settings)
        db.session.commit()

    if request.method == "POST":
        site_name = request.form.get("site_name", "").strip()
        logo_light = request.files.get("logo_light")
        logo_dark = request.files.get("logo_dark")

        if site_name:
            settings.site_name = site_name

        # ✅ ABSOLUTE PATH to static/images/logo
        upload_dir = os.path.join(
            current_app.root_path,
            "static",
            "images",
            "logo"
        )
        os.makedirs(upload_dir, exist_ok=True)

        # ===== LIGHT LOGO =====
        if logo_light and logo_light.filename:
            filename = secure_filename(logo_light.filename)
            save_path = os.path.join(upload_dir, filename)
            logo_light.save(save_path)

            # Save RELATIVE path for url_for('static')
            settings.logo_light = f"images/logo/{filename}"

        # ===== DARK LOGO =====
        if logo_dark and logo_dark.filename:
            filename = secure_filename(logo_dark.filename)
            save_path = os.path.join(upload_dir, filename)
            logo_dark.save(save_path)

            settings.logo_dark = f"images/logo/{filename}"

        db.session.commit()
        flash("Site settings updated successfully", "success")

        return redirect(url_for("admin.site_settings"))

    return render_template(
        "admin/site_settings.html",
        settings=settings
    )


@admin_bp.route("/stock-notify")
@login_required
@admin_required
def stock_notify_list():
    print("jskdhskjh")
    rows = (
        db.session.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.stock_quantity,
            func.count(StockNotification.id).label("waiting_count")
        )
        .join(StockNotification, StockNotification.product_id == Product.id)
        .group_by(Product.id)
        .order_by(func.count(StockNotification.id).desc())
        .all()
    )
    print(rows)

    return render_template(
        "admin/stock_notify_list.html",
        rows=rows
    )


@admin_bp.route("/stock-notify/<int:product_id>")
@login_required
@admin_required
def stock_notify_detail(product_id):

    product = Product.query.get_or_404(product_id)

    notifications = (
        db.session.query(
            StockNotification.created_at,
            User.email
        )
        .join(User, User.id == StockNotification.user_id)
        .filter(StockNotification.product_id == product_id)
        .order_by(StockNotification.created_at.desc())
        .all()
    )

    return render_template(
        "admin/stock_notify_detail.html",
        product=product,
        notifications=notifications
    )
