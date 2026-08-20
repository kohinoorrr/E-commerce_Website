# EcoShop – E-Commerce Sustainability Management System

> A full-stack DBMS + AI academic project simulating an eco-friendly e-commerce platform with real-time carbon emission tracking and AI-powered product classification.

---

## 🖥️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Bootstrap 5, JavaScript |
| Backend | Python Flask |
| Database | PostgreSQL |
| AI / ML | scikit-learn (RandomForestClassifier) |

---

## 📁 Project Structure

```
DBMS_Project/
├── app.py                  ← Flask backend (all routes)
├── requirements.txt        ← Python dependencies
│
├── database/
│   ├── schema.sql          ← PostgreSQL table definitions
│   └── seed.sql            ← Sample data
│
├── ml/
│   ├── carbon_model.py     ← AI classifier (train + predict)
│   └── carbon_classifier.pkl  ← Saved model (auto-generated)
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── cart.html
│   ├── checkout.html
│   ├── orders.html
│   ├── dashboard.html
│   ├── admin.html
│   └── add_product.html
│
└── static/
    ├── css/style.css
    └── js/main.js
```

---

## ⚙️ Setup Instructions

### Step 1 – Software to Install

| Software | Download |
|---|---|
| Python 3.10+ | https://python.org |
| PostgreSQL 16+ | https://postgresql.org/download |
| Git (optional) | https://git-scm.com |
| VS Code | https://code.visualstudio.com |

> During PostgreSQL install on Windows, note the **password** you set for the `postgres` user. You'll need it below.

---

### Step 2 – Install Python Dependencies

Open a terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

---

### Step 3 – Set Up the Database

1. Open **pgAdmin 4** (installed with PostgreSQL)
2. Right-click **Databases** → **Create** → **Database** → name it `eco_ecommerce`
3. Open a **Query Tool** for the new database
4. Paste and run `database/schema.sql` (creates all tables)
5. Paste and run `database/seed.sql` (inserts sample data)

---

### Step 4 – Configure Database Password

Open `app.py` and find `DB_CONFIG`:

```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "eco_ecommerce",
    "user":     "postgres",
    "password": "your_password",   ← change this
}
```

Replace `"your_password"` with your PostgreSQL password.

---

### Step 5 – Train the AI Model

Run once to train the carbon classifier:

```bash
python ml/carbon_model.py
```

This saves `ml/carbon_classifier.pkl`.

---

### Step 6 – Run the App

```bash
python app.py
```

Open your browser at: **http://127.0.0.1:5000**

---

## 🔑 Demo Accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@eco.com | admin123 |
| User | jane@eco.com | user123 |

---

## 🌿 Features

- **Product Browsing** with carbon badges (🟢 Low / 🟡 Medium / 🔴 High)
- **Cart** with per-item and total carbon footprint
- **AI Suggestion** – warns when cart carbon is high
- **Checkout** with carbon acknowledgment
- **Order History** with carbon per order
- **Carbon Dashboard** with Chart.js analytics
- **Admin Panel** – add products, categories, view orders
- **AI Carbon Classifier** – Random Forest with TF-IDF on descriptions
- **Live AI Predict** – test descriptions before adding products

---

## 📐 Database Schema

```
Users ──────┐
            ├── Cart ── Cart_Items ── Products ── Categories
            └── Orders ── Order_Items
```

All tables are normalized to **3NF**. Carbon emission is computed dynamically:

```sql
SELECT SUM(P.base_carbon_emission * CI.quantity)
FROM cart_items CI
JOIN products P ON CI.product_id = P.product_id
WHERE CI.cart_id = %s;
```

---

## 🤖 AI Component

The `ml/carbon_model.py` module:
- Trains a **RandomForestClassifier** (200 estimators)
- Features: **TF-IDF** on product description + numeric (category, price, CO₂)
- Labels: `low` | `medium` | `high`
- Exposes `predict()` for Flask and `get_cart_suggestion()` for cart tips
- Accuracy: ~85–95% on test split

---

*DBMS + AI Academic Project · 2025*
