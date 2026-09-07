"""
app.py – E-Commerce Sustainability Management System
======================================================
Flask backend using psycopg2 (PostgreSQL).
"""

import os
import time
import threading
import psycopg2
import psycopg2.extras
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash

# Add ml/ to path so we can import carbon_model
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ml"))
import carbon_model

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "eco_secret_key_change_in_prod")

# ----------------------------------------------------------------
# Database configuration  – update with your credentials
# Supports local fallback and environment variables for cloud deployment
# ----------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")

DB_CONFIG = {
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", 5433)),
    "dbname":   os.environ.get("DB_NAME", "eco_ecommerce"),
    "user":     os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "tiger"),
}


def get_db():
    """Return a new psycopg2 connection."""
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    return psycopg2.connect(**DB_CONFIG)



def query(sql, params=None, fetchone=False, fetchall=False, commit=False):
    """Helper: execute a query and optionally fetch results."""
    conn = get_db()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params or ())
                if commit:
                    conn.commit()
                    return cur.rowcount
                if fetchone:
                    return cur.fetchone()
                if fetchall:
                    return cur.fetchall()
    finally:
        conn.close()


# ----------------------------------------------------------------
# Auth helpers
# ----------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin access only.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


def merchant_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_merchant"):
            flash("Merchant access only.", "warning")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


def get_or_create_cart(user_id):
    """Return cart_id for user, creating one if missing."""
    row = query("SELECT cart_id FROM cart WHERE user_id=%s", (user_id,), fetchone=True)
    if row:
        return row["cart_id"]
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO cart(user_id) VALUES(%s) RETURNING cart_id", (user_id,))
                cart_id = cur.fetchone()[0]
        conn.commit()
        return cart_id
    finally:
        conn.close()


def cart_item_count(user_id):
    cart_id = get_or_create_cart(user_id)
    row = query(
        "SELECT COALESCE(SUM(quantity),0) AS cnt FROM cart_items WHERE cart_id=%s",
        (cart_id,), fetchone=True
    )
    return int(row["cnt"]) if row else 0


# ----------------------------------------------------------------
# Context processor – inject cart count into all templates
# ----------------------------------------------------------------
@app.context_processor
def inject_cart_count():
    count = 0
    if "user_id" in session:
        count = cart_item_count(session["user_id"])
    return {"cart_count": count}


# ----------------------------------------------------------------
# HOME – product listing
# ----------------------------------------------------------------
@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    cat_id = request.args.get("cat", "")
    carbon_filter = request.args.get("carbon", "")

    sql = """
        SELECT p.*, c.category_name, u.name AS merchant_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN users u ON p.merchant_id = u.user_id
        WHERE p.status = 'active'
    """
    params = []
    if search:
        sql += " AND (p.name ILIKE %s OR p.description ILIKE %s)"
        params += [f"%{search}%", f"%{search}%"]
    if cat_id:
        sql += " AND p.category_id=%s"
        params.append(cat_id)
    if carbon_filter:
        sql += " AND p.carbon_level=%s"
        params.append(carbon_filter)
    sql += " ORDER BY p.product_id"

    products = query(sql, params, fetchall=True)
    categories = query("SELECT * FROM categories ORDER BY category_name", fetchall=True)

    return render_template("index.html",
                           products=products,
                           categories=categories,
                           search=search,
                           selected_cat=cat_id,
                           carbon_filter=carbon_filter)


# ----------------------------------------------------------------
# SIGNUP
# ----------------------------------------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name    = request.form["name"].strip()
        email   = request.form["email"].strip().lower()
        pwd     = request.form["password"]
        address = request.form.get("address", "")
        phone   = request.form.get("phone", "")

        existing = query("SELECT user_id FROM users WHERE email=%s", (email,), fetchone=True)
        if existing:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("signup"))

        hashed = generate_password_hash(pwd)
        conn = get_db()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users(name,email,password,address,phone) VALUES(%s,%s,%s,%s,%s)",
                        (name, email, hashed, address, phone)
                    )
            conn.commit()
        finally:
            conn.close()

        flash("Account created! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("signup.html")


# ----------------------------------------------------------------
# LOGIN
# ----------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pwd   = request.form["password"]

        user = query("SELECT * FROM users WHERE email=%s", (email,), fetchone=True)
        if not user:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))

        # Allow plain-text seed passwords OR hashed passwords
        pwd_ok = False
        stored = user["password"]
        if stored.startswith("pbkdf2:") or stored.startswith("scrypt:"):
            pwd_ok = check_password_hash(stored, pwd)
        else:
            pwd_ok = (stored == pwd)  # seed data plain-text

        if not pwd_ok:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))

        session["user_id"]  = user["user_id"]
        session["name"]     = user["name"]
        session["is_admin"] = user["is_admin"]
        session["is_merchant"] = user["is_merchant"]
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("index"))
    return render_template("login.html")


# ----------------------------------------------------------------
# LOGOUT
# ----------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


# ----------------------------------------------------------------
# CART
# ----------------------------------------------------------------
@app.route("/cart")
@login_required
def cart():
    cart_id = get_or_create_cart(session["user_id"])
    items = query("""
        SELECT ci.cart_item_id, ci.quantity,
               p.product_id, p.name, p.price, p.base_carbon_emission,
               p.carbon_level,
               (p.price * ci.quantity)                AS item_total,
               (p.base_carbon_emission * ci.quantity) AS item_carbon
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.product_id
        WHERE ci.cart_id=%s
    """, (cart_id,), fetchall=True)

    total_price  = sum(float(i["item_total"]) for i in items) if items else 0
    total_carbon = sum(float(i["item_carbon"]) for i in items) if items else 0
    suggestion   = carbon_model.get_cart_suggestion(total_carbon)

    return render_template("cart.html",
                           items=items,
                           total_price=total_price,
                           total_carbon=total_carbon,
                           suggestion=suggestion)


@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    qty     = int(request.form.get("quantity", 1))
    cart_id = get_or_create_cart(session["user_id"])

    existing = query(
        "SELECT cart_item_id, quantity FROM cart_items WHERE cart_id=%s AND product_id=%s",
        (cart_id, product_id), fetchone=True
    )
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                if existing:
                    cur.execute(
                        "UPDATE cart_items SET quantity=quantity+%s WHERE cart_item_id=%s",
                        (qty, existing["cart_item_id"])
                    )
                else:
                    cur.execute(
                        "INSERT INTO cart_items(cart_id,product_id,quantity) VALUES(%s,%s,%s)",
                        (cart_id, product_id, qty)
                    )
        conn.commit()
    finally:
        conn.close()

    flash("Item added to cart!", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/remove_from_cart/<int:cart_item_id>", methods=["POST"])
@login_required
def remove_from_cart(cart_item_id):
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM cart_items WHERE cart_item_id=%s", (cart_item_id,))
        conn.commit()
    finally:
        conn.close()
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart"))


@app.route("/update_cart/<int:cart_item_id>", methods=["POST"])
@login_required
def update_cart(cart_item_id):
    qty = int(request.form.get("quantity", 1))
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                if qty <= 0:
                    cur.execute("DELETE FROM cart_items WHERE cart_item_id=%s", (cart_item_id,))
                else:
                    cur.execute(
                        "UPDATE cart_items SET quantity=%s WHERE cart_item_id=%s",
                        (qty, cart_item_id)
                    )
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("cart"))


# ----------------------------------------------------------------
# CHECKOUT
# ----------------------------------------------------------------
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_id = get_or_create_cart(session["user_id"])
    
    # Fetch cart items, including seller's warehouse location
    items = query("""
        SELECT ci.quantity, p.price, p.base_carbon_emission, p.product_id, p.name,
               u.address AS warehouse_city, u.name AS merchant_name
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.product_id
        LEFT JOIN users u ON p.merchant_id = u.user_id
        WHERE ci.cart_id=%s
    """, (cart_id,), fetchall=True)

    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart"))
        
    # Get buyer's location
    buyer = query("SELECT address FROM users WHERE user_id=%s", (session["user_id"],), fetchone=True)
    buyer_city = buyer["address"] if buyer and buyer["address"] else "Unknown"

    total_amount = 0.0
    total_base_carbon = 0.0
    total_shipping_carbon = 0.0
    
    # Calculate dynamic shipping for each item
    for item in items:
        warehouse = item["warehouse_city"] if item["warehouse_city"] else "Central Hub"
        
        distance_km = 500  # Default 500km fallback
        if warehouse.lower() == buyer_city.lower() and buyer_city != "Unknown":
            distance_km = 20 # Local delivery
        elif warehouse != "Unknown" and buyer_city != "Unknown":
            # Deterministic pseudo-distance based on city letters
            hash_val = sum(ord(c) for c in f"{warehouse.lower()}-{buyer_city.lower()}")
            distance_km = 50 + (hash_val % 1950)
                
        # Shipping emission = distance * 0.015 kg CO2e per km per unit * quantity
        shipping_carbon = (distance_km * 0.015) * item["quantity"]
        base_carbon = float(item["base_carbon_emission"]) * item["quantity"]
        
        item["distance_km"] = distance_km
        item["shipping_carbon"] = shipping_carbon
        item["total_item_carbon"] = base_carbon + shipping_carbon
        item["amount"] = float(item["price"]) * item["quantity"]
        
        total_amount += item["amount"]
        total_base_carbon += base_carbon
        total_shipping_carbon += shipping_carbon
        
    total_carbon = total_base_carbon + total_shipping_carbon

    if request.method == "POST":
        conn = get_db()
        try:
            with conn:
                with conn.cursor() as cur:
                    # Insert order
                    cur.execute(
                        """INSERT INTO orders(user_id, total_amount, total_carbon)
                           VALUES(%s,%s,%s) RETURNING order_id""",
                        (session["user_id"], total_amount, total_carbon)
                    )
                    order_id = cur.fetchone()[0]

                    # Insert order items saving the total combined carbon
                    for item in items:
                        cur.execute(
                            """INSERT INTO order_items(order_id,product_id,quantity,price,carbon_contribution)
                               VALUES(%s,%s,%s,%s,%s)""",
                            (order_id, item["product_id"], item["quantity"],
                             item["price"], item["total_item_carbon"])
                        )
                        # Reduce stock
                        cur.execute(
                            "UPDATE products SET stock=stock-%s WHERE product_id=%s",
                            (item["quantity"], item["product_id"])
                        )

                    # Clear cart
                    cur.execute("DELETE FROM cart_items WHERE cart_id=%s", (cart_id,))
            conn.commit()
        finally:
            conn.close()

        flash(f"Order placed! Total carbon footprint: {total_carbon:.2f} kg CO₂e", "success")
        return redirect(url_for("orders"))

    return render_template("checkout.html",
                           items=items,
                           buyer_city=buyer_city,
                           total_amount=total_amount,
                           total_base_carbon=total_base_carbon,
                           total_shipping_carbon=total_shipping_carbon,
                           total_carbon=total_carbon)


# ----------------------------------------------------------------
# ORDER HISTORY
# ----------------------------------------------------------------
@app.route("/orders")
@login_required
def orders():
    user_orders = query("""
        SELECT o.order_id, o.order_date, o.total_amount, o.total_carbon, o.status
        FROM orders o
        WHERE o.user_id=%s
        ORDER BY o.order_date DESC
    """, (session["user_id"],), fetchall=True)

    order_details = {}
    for ord_ in user_orders:
        items = query("""
            SELECT oi.quantity, oi.price, oi.carbon_contribution,
                   p.name, p.carbon_level
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id=%s
        """, (ord_["order_id"],), fetchall=True)
        order_details[ord_["order_id"]] = items

    return render_template("orders.html",
                           orders=user_orders,
                           order_details=order_details)


# ----------------------------------------------------------------
# CARBON ANALYTICS DASHBOARD
# ----------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    analytics = query("SELECT * FROM carbon_analytics", fetchone=True)

    top_green = query("""
        SELECT name, base_carbon_emission, carbon_level
        FROM products
        ORDER BY base_carbon_emission ASC LIMIT 5
    """, fetchall=True)

    top_high = query("""
        SELECT name, base_carbon_emission, carbon_level
        FROM products
        ORDER BY base_carbon_emission DESC LIMIT 5
    """, fetchall=True)

    by_category = query("""
        SELECT c.category_name,
               ROUND(AVG(p.base_carbon_emission)::NUMERIC, 2) AS avg_carbon,
               COUNT(p.product_id) AS product_count
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        GROUP BY c.category_name
        ORDER BY avg_carbon DESC
    """, fetchall=True)

    user_footprint = query("""
        SELECT COALESCE(SUM(total_carbon),0) AS my_total
        FROM orders WHERE user_id=%s
    """, (session["user_id"],), fetchone=True)

    return render_template("dashboard.html",
                           analytics=analytics,
                           top_green=top_green,
                           top_high=top_high,
                           by_category=by_category,
                           user_footprint=user_footprint)


# ----------------------------------------------------------------
# AI SUGGESTION ENDPOINT  (AJAX)
# ----------------------------------------------------------------
@app.route("/ai-suggest", methods=["POST"])
def ai_suggest():
    data = request.get_json()
    desc = data.get("description", "")
    cat_id = data.get("category_id", 1)
    price = data.get("price", 0)
    
    # Auto-estimate base carbon
    base_co2 = carbon_model.estimate_base_carbon(desc, cat_id, price)
    
    result = carbon_model.predict(
        description          = desc,
        category_id          = cat_id,
        price                = price,
        base_carbon_emission = base_co2,
    )
    return jsonify(result)


# ----------------------------------------------------------------
# MERCHANT - dashboard and features
# ----------------------------------------------------------------
@app.route("/merchant-signup", methods=["GET", "POST"])
def merchant_signup():
    if request.method == "POST":
        name    = request.form["name"].strip()
        email   = request.form["email"].strip().lower()
        pwd     = request.form["password"]
        warehouse = request.form.get("warehouse", "").strip()

        existing = query("SELECT user_id FROM users WHERE email=%s", (email,), fetchone=True)
        if existing:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("merchant_signup"))

        hashed = generate_password_hash(pwd)
        conn = get_db()
        try:
            with conn:
                with conn.cursor() as cur:
                    # Store warehouse location in address field for merchants
                    cur.execute(
                        "INSERT INTO users(name,email,password,address,is_merchant) VALUES(%s,%s,%s,%s,TRUE)",
                        (name, email, hashed, warehouse)
                    )
            conn.commit()
        finally:
            conn.close()

        flash("Merchant account created! Please login.", "success")
        return redirect(url_for("merchant_login"))
    return render_template("merchant_signup.html")


@app.route("/merchant-login", methods=["GET", "POST"])
def merchant_login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pwd   = request.form["password"]

        user = query("SELECT * FROM users WHERE email=%s AND is_merchant=TRUE", (email,), fetchone=True)
        if not user:
            flash("Invalid merchant credentials or not a merchant.", "danger")
            return redirect(url_for("merchant_login"))

        pwd_ok = False
        stored = user["password"]
        if stored.startswith("pbkdf2:") or stored.startswith("scrypt:"):
            pwd_ok = check_password_hash(stored, pwd)
        else:
            pwd_ok = (stored == pwd)

        if not pwd_ok:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("merchant_login"))

        session["user_id"]  = user["user_id"]
        session["name"]     = user["name"]
        session["is_admin"] = user["is_admin"]
        session["is_merchant"] = True
        flash(f"Welcome to Merchant Panel, {user['name']}!", "success")
        return redirect(url_for("merchant_dashboard"))
    return render_template("merchant_login.html")


@app.route("/merchant")
@login_required
@merchant_required
def merchant_dashboard():
    products = query("""
        SELECT p.*, c.category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE p.merchant_id=%s
        ORDER BY p.product_id
    """, (session["user_id"],), fetchall=True)
    
    categories = query("SELECT * FROM categories ORDER BY category_name", fetchall=True)
    
    orders_qs = query("""
        SELECT o.order_date, oi.quantity, oi.price, p.name AS product_name, u.name AS buyer_name
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN users u ON o.user_id = u.user_id
        WHERE p.merchant_id = %s
        ORDER BY o.order_date DESC
    """, (session["user_id"],), fetchall=True)

    return render_template("merchant.html", products=products, categories=categories, orders=orders_qs)


@app.route("/merchant/add-product", methods=["POST"])
@login_required
@merchant_required
def merchant_add_product():
    name        = request.form["name"].strip()
    description = request.form["description"].strip()
    price       = float(request.form["price"])
    stock       = int(request.form["stock"])
    category_id = int(request.form["category_id"])

    # Temporarily set placeholders while AI scans
    base_co2 = 0.0
    carbon_level = "medium"

    conn = get_db()
    product_id = None
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO products
                       (name,description,price,stock,category_id,base_carbon_emission,carbon_level,merchant_id,status)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'scanning') RETURNING product_id""",
                    (name, description, price, stock, category_id, base_co2, carbon_level, session["user_id"])
                )
                product_id = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    # Background function to perform the AI Scan
    def scan_product_background(pid, desc, cat_id, prc):
        time.sleep(5)  # Simulate AI scanning delay
        try:
            # 1. AI estimates base emission
            ai_base_co2 = carbon_model.estimate_base_carbon(desc, cat_id, prc)
            # 2. AI classifies level
            ai_res = carbon_model.predict(desc, cat_id, prc, ai_base_co2)
            c_level = ai_res["label"]
            
            # Update database
            bg_conn = get_db()
            with bg_conn:
                with bg_conn.cursor() as bg_cur:
                    bg_cur.execute(
                        "UPDATE products SET base_carbon_emission=%s, carbon_level=%s, status='active' WHERE product_id=%s",
                        (ai_base_co2, c_level, pid)
                    )
            bg_conn.commit()
            bg_conn.close()
        except Exception as e:
            print(f"Error in background AI scan for product {pid}: {e}")

    # Spawn thread to avoid blocking the user
    thread = threading.Thread(target=scan_product_background, args=(product_id, description, category_id, price))
    thread.start()

    flash(f"Product added! Our AI is currently scanning the description to estimate its carbon footprint. It will be listed shortly.", "info")
    return redirect(url_for("merchant_dashboard"))


# ----------------------------------------------------------------
# ADMIN – main panel
# ----------------------------------------------------------------
@app.route("/admin")
@login_required
@admin_required
def admin():
    products   = query("""
        SELECT p.*, c.category_name FROM products p
        LEFT JOIN categories c ON p.category_id=c.category_id
        ORDER BY p.product_id
    """, fetchall=True)
    categories = query("SELECT * FROM categories ORDER BY category_name", fetchall=True)
    orders_all = query("""
        SELECT o.*, u.name AS user_name
        FROM orders o JOIN users u ON o.user_id=u.user_id
        ORDER BY o.order_date DESC LIMIT 50
    """, fetchall=True)
    users_all = query("SELECT * FROM users ORDER BY created_at DESC", fetchall=True)
    return render_template("admin.html",
                           products=products,
                           categories=categories,
                           orders=orders_all,
                           users=users_all)


@app.route("/admin/add-product", methods=["GET", "POST"])
@login_required
@admin_required
def add_product():
    categories = query("SELECT * FROM categories ORDER BY category_name", fetchall=True)
    ai_result  = None

    if request.method == "POST":
        name        = request.form["name"].strip()
        description = request.form["description"].strip()
        price       = float(request.form["price"])
        stock       = int(request.form["stock"])
        category_id = int(request.form["category_id"])

        # Automatically estimate base emission
        base_co2 = carbon_model.estimate_base_carbon(description, category_id, price)

        # AI predict label
        ai_result = carbon_model.predict(description, category_id, price, base_co2)
        carbon_level = ai_result["label"]

        conn = get_db()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO products
                           (name,description,price,stock,category_id,base_carbon_emission,carbon_level)
                           VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                        (name, description, price, stock, category_id, base_co2, carbon_level)
                    )
            conn.commit()
        finally:
            conn.close()

        flash(f"Product added! AI classified as: {carbon_level.upper()} carbon.", "success")
        return redirect(url_for("admin"))

    return render_template("add_product.html",
                           categories=categories,
                           ai_result=ai_result)


@app.route("/admin/add-category", methods=["POST"])
@login_required
@admin_required
def add_category():
    name = request.form["category_name"].strip()
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO categories(category_name) VALUES(%s)", (name,))
        conn.commit()
        flash(f"Category '{name}' added.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("admin"))


@app.route("/admin/delete-product/<int:product_id>", methods=["POST"])
@login_required
@admin_required
def delete_product(product_id):
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM products WHERE product_id=%s", (product_id,))
        conn.commit()
        flash("Product deleted.", "info")
    finally:
        conn.close()
    return redirect(url_for("admin"))


# ----------------------------------------------------------------
# Run
# ----------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
