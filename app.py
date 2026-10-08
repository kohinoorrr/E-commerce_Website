"""
app.py – Vmart Supermart Application
======================================
Full-stack Python Flask web app backed by SQLite (zero external setup).
Tailored for Digital Marketing & Supermarket Management.
"""

import os
import sqlite3
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "vmart_supermart_secret_key_2026")

DB_PATH = os.path.join(os.path.dirname(__file__), "vmart.db")


def get_db():
    """Return a new sqlite3 connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize SQLite database with schema and default supermart seed data."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL UNIQUE,
        icon_class TEXT DEFAULT 'bi-basket'
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        category_id INTEGER REFERENCES categories(category_id),
        mrp REAL NOT NULL,
        price REAL NOT NULL,
        stock INTEGER DEFAULT 100,
        deal_tag TEXT DEFAULT 'Fresh',
        rating REAL DEFAULT 4.5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
        coupon_code TEXT DEFAULT NULL,
        discount_amount REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart_items (
        cart_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cart_id INTEGER REFERENCES cart(cart_id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,
        quantity INTEGER DEFAULT 1,
        UNIQUE(cart_id, product_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
        total_mrp REAL NOT NULL,
        total_price REAL NOT NULL,
        discount_applied REAL DEFAULT 0.0,
        final_amount REAL NOT NULL,
        loyalty_points INTEGER DEFAULT 0,
        shipping_address TEXT,
        payment_method TEXT DEFAULT 'Cash on Delivery',
        status TEXT DEFAULT 'Completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(product_id),
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS marketing_coupons (
        coupon_id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_percent REAL DEFAULT 0,
        flat_discount REAL DEFAULT 0,
        min_order REAL DEFAULT 0,
        description TEXT
    );
    """)

    # Check if default data exists
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        # Seed users
        admin_pass = generate_password_hash("admin123")
        user_pass = generate_password_hash("user123")
        cur.execute("INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, 1)",
                    ("Vmart Admin", "admin@vmart.com", admin_pass))
        cur.execute("INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, 0)",
                    ("Jane Doe", "jane@vmart.com", user_pass))

        # Seed categories
        categories = [
            ("Fresh Fruits & Veggies", "bi-apple"),
            ("Dairy & Bakery", "bi-cup-hot"),
            ("Snacks & Beverages", "bi-cup-straw"),
            ("Pantry & Staples", "bi-box-seam"),
            ("Personal Care", "bi-heart-pulse"),
            ("Household Essentials", "bi-house-heart")
        ]
        cur.executemany("INSERT INTO categories (category_name, icon_class) VALUES (?, ?)", categories)

        # Seed products
        products = [
            ("Fresh Organic Bananas (1 Dozen)", "Farm fresh sweet organic bananas rich in potassium.", 1, 3.50, 2.80, 150, "20% OFF", 4.8),
            ("Farm Fresh Red Apples (1 kg)", "Crisp and juicy red apples sourced directly from local orchards.", 1, 4.99, 3.99, 120, "Best Seller", 4.9),
            ("Organic Whole Milk (1 Gallon)", "Grade-A pasteurized whole milk, rich in calcium and vitamins.", 2, 4.50, 3.49, 80, "Daily Deal", 4.7),
            ("Artisanal Whole Wheat Bread", "Freshly baked whole wheat bread with high fiber content.", 2, 3.20, 2.50, 60, "Fresh Baked", 4.6),
            ("Fresh Greek Yogurt Pack (500g)", "Thick, creamy probiotic Greek yogurt.", 2, 5.00, 3.99, 90, "Hot Deal", 4.8),
            ("Premium Roasted Almonds (250g)", "Crunchy dry-roasted Californian almonds with light sea salt.", 3, 8.99, 6.99, 200, "Super Saver", 4.9),
            ("Natural Orange Juice (1L)", "100% pure squeezed orange juice with pulp.", 3, 3.99, 2.99, 100, "25% OFF", 4.7),
            ("Dark Chocolate Bar 70% (100g)", "Rich Swiss dark chocolate bar made from fine cocoa beans.", 3, 3.00, 2.20, 150, "BOGO", 4.8),
            ("Extra Virgin Olive Oil (500ml)", "Cold-pressed extra virgin olive oil for healthy cooking.", 4, 12.99, 9.99, 70, "Mega Saver", 4.9),
            ("Basmati Premium Rice (5 kg)", "Long-grain aromatic Basmati rice perfect for biryani and daily meals.", 4, 18.99, 14.99, 50, "Best Value", 4.9),
            ("Organic Wild Honey Jar (500g)", "Unfiltered 100% natural wild forest honey.", 4, 7.50, 5.99, 110, "Popular", 4.8),
            ("Herbal Body Wash Lavender (500ml)", "Nourishing lavender herbal body shower gel.", 5, 8.00, 5.99, 90, "25% OFF", 4.6),
            ("Gentle Foam Hand Soap (250ml)", "Antibacterial foaming hand soap with aloe vera.", 5, 4.00, 2.99, 140, "Hot Deal", 4.7),
            ("Eco Laundry Detergent Liquid (2L)", "Plant-based powerful stain removing laundry liquid.", 6, 14.99, 11.99, 65, "20% OFF", 4.8),
            ("Biodegradable Dishwashing Gel", "Tough on grease lemon dishwashing liquid gel.", 6, 4.50, 3.29, 130, "Super Deal", 4.6),
            ("Bamboo Paper Towel Pack (4 Rolls)", "Ultra-absorbent 2-ply sustainable paper towels.", 6, 6.50, 4.99, 100, "Eco Choice", 4.7),
        ]
        cur.executemany("""
        INSERT INTO products (name, description, category_id, mrp, price, stock, deal_tag, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, products)

        # Seed marketing coupons
        coupons = [
            ("VMART20", 20.0, 0.0, 10.0, "Flat 20% OFF on orders over $10"),
            ("FRESH50", 0.0, 5.0, 25.0, "Flat $5.00 OFF on orders over $25"),
            ("WELCOME10", 10.0, 0.0, 0.0, "10% OFF Welcome Bonus")
        ]
        cur.executemany("""
        INSERT INTO marketing_coupons (code, discount_percent, flat_discount, min_order, description)
        VALUES (?, ?, ?, ?, ?)
        """, coupons)

        # Seed sample completed orders for marketing analytics
        cur.execute("""
        INSERT INTO orders (user_id, total_mrp, total_price, discount_applied, final_amount, loyalty_points, shipping_address, payment_method)
        VALUES (2, 28.48, 22.48, 4.50, 17.98, 18, '742 Evergreen Terrace, Springfield', 'Credit Card')
        """)
        cur.execute("""
        INSERT INTO orders (user_id, total_mrp, total_price, discount_applied, final_amount, loyalty_points, shipping_address, payment_method)
        VALUES (2, 45.97, 36.96, 7.39, 29.57, 30, '100 Main Street, New York', 'UPI / NetBanking')
        """)

    conn.commit()
    conn.close()


# Initialize database on startup
init_db()


# ----------------------------------------------------------------
# Auth Decorators & Helpers
# ----------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin access required.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


def get_cart_count(user_id):
    if not user_id:
        return 0
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT SUM(ci.quantity)
        FROM cart_items ci
        JOIN cart c ON ci.cart_id = c.cart_id
        WHERE c.user_id = ?
    """, (user_id,))
    res = cur.fetchone()[0]
    conn.close()
    return res if res else 0


@app.context_processor
def inject_global_data():
    cart_count = get_cart_count(session.get("user_id"))
    return dict(cart_count=cart_count)


# ----------------------------------------------------------------
# Public Routes
# ----------------------------------------------------------------
@app.route("/")
def index():
    cat_id = request.args.get("category", type=int)
    search_q = request.args.get("q", "").strip()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM categories ORDER BY category_name")
    categories = cur.fetchall()

    sql = """
        SELECT p.*, c.category_name,
               ROUND(((p.mrp - p.price) / p.mrp) * 100) AS discount_pct
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        WHERE 1=1
    """
    params = []

    if cat_id:
        sql += " AND p.category_id = ?"
        params.append(cat_id)
    if search_q:
        sql += " AND (p.name LIKE ? OR p.description LIKE ?)"
        params.append(f"%{search_q}%")
        params.append(f"%{search_q}%")

    sql += " ORDER BY p.product_id DESC"

    cur.execute(sql, params)
    products = cur.fetchall()

    # Promotional marketing banners
    cur.execute("SELECT * FROM marketing_coupons")
    coupons = cur.fetchall()

    conn.close()

    return render_template("index.html",
                           categories=categories,
                           products=products,
                           coupons=coupons,
                           selected_cat=cat_id,
                           search_q=search_q)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["user_id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["is_admin"] = bool(user["is_admin"])
            flash(f"Welcome back to Vmart, {user['name']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "warning")
            return render_template("signup.html")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            conn.close()
            flash("Email already registered.", "warning")
            return render_template("signup.html")

        pass_hash = generate_password_hash(password)
        cur.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, pass_hash))
        conn.commit()

        cur.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        new_user_id = cur.fetchone()["user_id"]
        conn.close()

        session["user_id"] = new_user_id
        session["name"] = name
        session["email"] = email
        session["is_admin"] = False

        flash("Registration successful! Welcome to Vmart Supermart.", "success")
        return redirect(url_for("index"))

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("index"))


# ----------------------------------------------------------------
# Cart & Checkout Routes
# ----------------------------------------------------------------
@app.route("/cart")
@login_required
def cart():
    user_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    # Ensure user has a cart
    cur.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,))
    cart_obj = cur.fetchone()
    if not cart_obj:
        cur.execute("INSERT INTO cart (user_id) VALUES (?)", (user_id,))
        conn.commit()
        cur.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,))
        cart_obj = cur.fetchone()

    cart_id = cart_obj["cart_id"]

    cur.execute("""
        SELECT ci.cart_item_id, ci.quantity, p.*,
               (p.mrp * ci.quantity) AS item_total_mrp,
               (p.price * ci.quantity) AS item_total_price,
               ROUND(((p.mrp - p.price) * ci.quantity), 2) AS item_savings
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.product_id
        WHERE ci.cart_id = ?
    """, (cart_id,))
    items = cur.fetchall()

    total_mrp = sum(item["item_total_mrp"] for item in items)
    total_price = sum(item["item_total_price"] for item in items)
    total_savings = total_mrp - total_price

    # Apply promo coupon
    coupon_code = cart_obj["coupon_code"]
    discount_amount = cart_obj["discount_amount"] or 0.0

    if coupon_code and total_price > 0:
        cur.execute("SELECT * FROM marketing_coupons WHERE code = ?", (coupon_code,))
        cp = cur.fetchone()
        if cp:
            if total_price >= cp["min_order"]:
                if cp["discount_percent"] > 0:
                    discount_amount = round((total_price * cp["discount_percent"]) / 100, 2)
                elif cp["flat_discount"] > 0:
                    discount_amount = min(cp["flat_discount"], total_price)
                cur.execute("UPDATE cart SET discount_amount = ? WHERE cart_id = ?", (discount_amount, cart_id))
                conn.commit()
            else:
                cur.execute("UPDATE cart SET coupon_code = NULL, discount_amount = 0.0 WHERE cart_id = ?", (cart_id,))
                conn.commit()
                flash(f"Coupon '{coupon_code}' removed. Minimum order for this coupon is ${cp['min_order']:.2f}", "warning")
                coupon_code = None
                discount_amount = 0.0

    final_total = max(0.0, round(total_price - discount_amount, 2))

    conn.close()

    return render_template("cart.html",
                           items=items,
                           total_mrp=round(total_mrp, 2),
                           total_price=round(total_price, 2),
                           total_savings=round(total_savings, 2),
                           coupon_code=coupon_code,
                           discount_amount=round(discount_amount, 2),
                           final_total=final_total)


@app.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    user_id = session["user_id"]
    quantity = request.form.get("quantity", 1, type=int)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,))
    cart_obj = cur.fetchone()
    if not cart_obj:
        cur.execute("INSERT INTO cart (user_id) VALUES (?)", (user_id,))
        conn.commit()
        cur.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,))
        cart_obj = cur.fetchone()

    cart_id = cart_obj["cart_id"]

    cur.execute("SELECT * FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id))
    existing = cur.fetchone()

    if existing:
        new_qty = existing["quantity"] + quantity
        cur.execute("UPDATE cart_items SET quantity = ? WHERE cart_item_id = ?", (new_qty, existing["cart_item_id"]))
    else:
        cur.execute("INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (?, ?, ?)",
                    (cart_id, product_id, quantity))

    conn.commit()
    conn.close()

    flash("Item added to your Vmart basket!", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def update_cart_item(item_id):
    quantity = request.form.get("quantity", 1, type=int)
    conn = get_db()
    cur = conn.cursor()
    if quantity <= 0:
        cur.execute("DELETE FROM cart_items WHERE cart_item_id = ?", (item_id,))
    else:
        cur.execute("UPDATE cart_items SET quantity = ? WHERE cart_item_id = ?", (quantity, item_id))
    conn.commit()
    conn.close()
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_cart_item(item_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM cart_items WHERE cart_item_id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Item removed from basket.", "info")
    return redirect(url_for("cart"))


@app.route("/cart/apply-coupon", methods=["POST"])
@login_required
def apply_coupon():
    code = request.form.get("coupon_code", "").strip().upper()
    user_id = session["user_id"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM marketing_coupons WHERE code = ?", (code,))
    coupon = cur.fetchone()

    if not coupon:
        flash("Invalid coupon code.", "danger")
        conn.close()
        return redirect(url_for("cart"))

    cur.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,))
    cart_obj = cur.fetchone()
    if cart_obj:
        cur.execute("UPDATE cart SET coupon_code = ? WHERE cart_id = ?", (code, cart_obj["cart_id"]))
        conn.commit()
        flash(f"Coupon '{code}' applied successfully!", "success")

    conn.close()
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    user_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,))
    cart_obj = cur.fetchone()

    if not cart_obj:
        conn.close()
        return redirect(url_for("index"))

    cur.execute("""
        SELECT ci.quantity, p.*
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.product_id
        WHERE ci.cart_id = ?
    """, (cart_obj["cart_id"],))
    items = cur.fetchall()

    if not items:
        flash("Your basket is empty.", "warning")
        conn.close()
        return redirect(url_for("index"))

    total_mrp = sum(i["mrp"] * i["quantity"] for i in items)
    total_price = sum(i["price"] * i["quantity"] for i in items)
    discount_applied = cart_obj["discount_amount"] or 0.0
    final_amount = max(0.0, round(total_price - discount_applied, 2))
    loyalty_points = int(final_amount)  # $1 = 1 V-Point earned

    if request.method == "POST":
        address = request.form.get("address", "").strip()
        payment_method = request.form.get("payment_method", "Cash on Delivery")

        if not address:
            flash("Shipping address is required.", "danger")
            conn.close()
            return render_template("checkout.html", items=items, total_mrp=total_mrp,
                                   total_price=total_price, discount_applied=discount_applied,
                                   final_amount=final_amount, loyalty_points=loyalty_points)

        cur.execute("""
            INSERT INTO orders (user_id, total_mrp, total_price, discount_applied, final_amount, loyalty_points, shipping_address, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, round(total_mrp, 2), round(total_price, 2), round(discount_applied, 2),
              final_amount, loyalty_points, address, payment_method))
        order_id = cur.lastrowid

        for item in items:
            cur.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            """, (order_id, item["product_id"], item["quantity"], item["price"]))

        # Clear cart
        cur.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart_obj["cart_id"],))
        cur.execute("UPDATE cart SET coupon_code = NULL, discount_amount = 0.0 WHERE cart_id = ?", (cart_obj["cart_id"],))

        conn.commit()
        conn.close()

        flash(f"Order #{order_id} placed successfully! You earned {loyalty_points} V-Points.", "success")
        return redirect(url_for("orders"))

    conn.close()
    return render_template("checkout.html",
                           items=items,
                           total_mrp=round(total_mrp, 2),
                           total_price=round(total_price, 2),
                           discount_applied=round(discount_applied, 2),
                           final_amount=final_amount,
                           loyalty_points=loyalty_points)


@app.route("/orders")
@login_required
def orders():
    user_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY order_id DESC", (user_id,))
    orders_list = cur.fetchall()

    detailed_orders = []
    for order in orders_list:
        cur.execute("""
            SELECT oi.quantity, oi.unit_price, p.name, p.deal_tag
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = ?
        """, (order["order_id"],))
        items = cur.fetchall()
        detailed_orders.append({
            "order": order,
            "items": items
        })

    conn.close()
    return render_template("orders.html", orders=detailed_orders)


# ----------------------------------------------------------------
# Digital Marketing & Analytics Dashboard
# ----------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()

    # Total orders, revenue, average order value, savings generated
    cur.execute("SELECT COUNT(*), SUM(final_amount), SUM(total_mrp - final_amount), SUM(loyalty_points) FROM orders")
    stats = cur.fetchone()
    total_orders = stats[0] or 0
    total_revenue = stats[1] or 0.0
    total_customer_savings = stats[2] or 0.0
    total_loyalty_points = stats[3] or 0

    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    # Sales breakdown by Category (for Marketing charts)
    cur.execute("""
        SELECT c.category_name, SUM(oi.quantity * oi.unit_price) AS category_revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN categories c ON p.category_id = c.category_id
        GROUP BY c.category_name
        ORDER BY category_revenue DESC
    """)
    cat_sales = cur.fetchall()

    # Marketing coupon usage stats
    cur.execute("SELECT * FROM marketing_coupons")
    coupons = cur.fetchall()

    conn.close()

    return render_template("dashboard.html",
                           total_orders=total_orders,
                           total_revenue=round(total_revenue, 2),
                           total_customer_savings=round(total_customer_savings, 2),
                           avg_order_value=avg_order_value,
                           total_loyalty_points=total_loyalty_points,
                           cat_sales=cat_sales,
                           coupons=coupons)


# ----------------------------------------------------------------
# Admin Panel Routes
# ----------------------------------------------------------------
@app.route("/admin")
@login_required
@admin_required
def admin():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.*, c.category_name
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        ORDER BY p.product_id DESC
    """)
    products = cur.fetchall()

    cur.execute("SELECT * FROM categories ORDER BY category_name")
    categories = cur.fetchall()

    cur.execute("""
        SELECT o.*, u.name AS customer_name, u.email AS customer_email
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        ORDER BY o.order_id DESC
    """)
    orders_list = cur.fetchall()

    conn.close()

    return render_template("admin.html",
                           products=products,
                           categories=categories,
                           orders=orders_list)


@app.route("/admin/add-product", methods=["GET", "POST"])
@login_required
@admin_required
def add_product():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id", type=int)
        mrp = request.form.get("mrp", type=float)
        price = request.form.get("price", type=float)
        stock = request.form.get("stock", 100, type=int)
        deal_tag = request.form.get("deal_tag", "Hot Deal")

        if not name or not category_id or mrp is None or price is None:
            flash("Name, category, MRP, and sale price are required.", "warning")
        else:
            cur.execute("""
                INSERT INTO products (name, description, category_id, mrp, price, stock, deal_tag)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, description, category_id, mrp, price, stock, deal_tag))
            conn.commit()
            flash(f"Supermarket Product '{name}' added successfully!", "success")
            conn.close()
            return redirect(url_for("admin"))

    cur.execute("SELECT * FROM categories ORDER BY category_name")
    categories = cur.fetchall()
    conn.close()

    return render_template("add_product.html", categories=categories)


@app.route("/admin/delete-product/<int:product_id>", methods=["POST"])
@login_required
@admin_required
def delete_product(product_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()
    flash("Product deleted from inventory.", "info")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
