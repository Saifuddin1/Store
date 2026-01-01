from flask_login import UserMixin
from app import db, bcrypt
from datetime import datetime
from sqlalchemy.sql import func
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

ALLOWED_STATUS_TRANSITIONS = {
    "PLACED": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["PACKED", "CANCELLED"],
    "PACKED": ["SHIPPED"],
    "SHIPPED": ["DELIVERED"],
    "DELIVERED": [],
    "CANCELLED": [],
}


ORDER_STATUS_PLACED = "PLACED"
ORDER_STATUS_CONFIRMED = "CONFIRMED"
ORDER_STATUS_PACKED = "PACKED"
ORDER_STATUS_SHIPPED = "SHIPPED"
ORDER_STATUS_OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
ORDER_STATUS_DELIVERED = "DELIVERED"
ORDER_STATUS_CANCELLED = "CANCELLED"
ORDER_STATUS_RETURNED = "RETURNED"

ORDER_STATUSES = [
    ORDER_STATUS_PLACED,
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_PACKED,
    ORDER_STATUS_SHIPPED,
    ORDER_STATUS_OUT_FOR_DELIVERY,
    ORDER_STATUS_DELIVERED,
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_RETURNED,
]


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, raw_password):
        self.password = bcrypt.generate_password_hash(
            raw_password
        ).decode("utf-8")

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password, raw_password)

    @property
    def is_admin(self):
        return self.role == "admin"

    # ==============================
    # 🔐 PASSWORD RESET TOKENS
    # ==============================

    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps({"user_id": self.id})

    @staticmethod
    def verify_reset_token(token, max_age=1800):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token, max_age=max_age)
            return User.query.get(data["user_id"])
        except Exception:
            return None



class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Category {self.name}>"
    

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False)

    description = db.Column(db.Text)

    price = db.Column(db.Float, nullable=False)
    discount_type = db.Column(
        db.String(10), nullable=False, default="none"
    )  # none / percent / flat
    discount_value = db.Column(db.Float, default=0.0)

    stock_quantity = db.Column(db.Integer, nullable=False, default=0)

    is_active = db.Column(db.Boolean, default=True)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationship (optional but recommended)
    category = db.relationship("Category", backref="products")

    @property
    def final_price(self):
        """
        Calculate final price after discount
        """
        if self.discount_type == "percent":
            return max(
                0,
                self.price - (self.price * self.discount_value / 100)
            )
        elif self.discount_type == "flat":
            return max(0, self.price - self.discount_value)
        return self.price
    
    @property
    def primary_image(self):
        """
        Returns primary image path or None
        """
        for img in self.images:
            if img.is_primary:
                return img.image_path
        return None
    

    def __repr__(self):
        return f"<Product {self.name}>"


class ProductImage(db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    image_path = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationship
    product = db.relationship("Product", backref="images")

    def __repr__(self):
        return f"<ProductImage {self.image_path}>"


class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    address_line1 = db.Column(db.String(255), nullable=False)
    address_line2 = db.Column(db.String(255))

    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False, default="India")

    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationship
    user = db.relationship("User", backref="addresses")

    def __repr__(self):
        return f"<Address {self.full_name} - {self.city}>"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey("addresses.id"), nullable=False)

    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="PLACED")

    # ✅ STEP 7.1 — Dispatch fields
    courier_name = db.Column(db.String(100), nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    dispatched_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref="orders")
    address = db.relationship("Address")

    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )




class OrderStatusHistory(db.Model):
    __tablename__ = "order_status_history"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False
    )

    old_status = db.Column(db.String(30), nullable=True)
    new_status = db.Column(db.String(30), nullable=False)

    changed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )  # admin user id

    remark = db.Column(db.Text, nullable=True)

    changed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # relationships
    order = db.relationship("Order", backref="status_history")
    admin = db.relationship("User")

    def __repr__(self):
        return f"<OrderStatusHistory Order#{self.order_id} {self.old_status} → {self.new_status}>"



class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    product_name = db.Column(db.String(255), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    order = db.relationship(
        "Order",
        back_populates="items"
    )


class AboutPage(db.Model):
    __tablename__ = "about_page"

    id = db.Column(db.Integer, primary_key=True)

    hero_title = db.Column(db.String(200), nullable=False)
    hero_subtitle = db.Column(db.Text, nullable=False)
    hero_image = db.Column(db.String(500), nullable=True)

    who_title = db.Column(db.String(200), nullable=False)
    who_content = db.Column(db.Text, nullable=False)

    mission_title = db.Column(db.String(200), nullable=False)
    mission_content = db.Column(db.Text, nullable=False)

    why_blocks = db.Column(db.JSON, nullable=False)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class FAQ(db.Model):
    __tablename__ = "faqs"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)

    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PolicyBase(db.Model):
    __abstract__ = True  # ⬅️ VERY IMPORTANT

    id = db.Column(db.Integer, primary_key=True)

    sections = db.Column(
        db.JSON,
        nullable=False,
        default=list
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class TermsConditions(PolicyBase):
    __tablename__ = "terms_conditions"


class ShippingReturns(PolicyBase):
    __tablename__ = "shipping_returns"


class PrivacyPolicy(PolicyBase):
    __tablename__ = "privacy_policy"


class SiteSettings(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)

    site_name = db.Column(db.String(100), default="MyStore")

    logo_light = db.Column(db.String(255))   # for light bg
    logo_dark = db.Column(db.String(255))    # for dark navbar

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class ProductReview(db.Model):
    __tablename__ = "product_reviews"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    rating = db.Column(db.Integer, nullable=False)  # 1–5
    title = db.Column(db.String(150))
    comment = db.Column(db.Text, nullable=False)

    is_approved = db.Column(db.Boolean, default=True)

    created_at = db.Column(
        db.DateTime,
        server_default=func.now()
    )

    product = db.relationship("Product", backref="reviews")
    user = db.relationship("User", backref="reviews")

    __table_args__ = (
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating"),
        db.UniqueConstraint("product_id", "user_id", name="uq_user_product_review"),
    )

    def __repr__(self):
        return f"<Review product={self.product_id} user={self.user_id}>"

class Wishlist(db.Model):
    __tablename__ = "wishlists"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_user_product_wishlist"),
    )

    user = db.relationship("User", backref="wishlists")
    product = db.relationship("Product")


class StockNotification(db.Model):
    __tablename__ = "stock_notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_user_product_notify"),
    )
