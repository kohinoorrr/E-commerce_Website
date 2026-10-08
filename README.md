# Vmart Supermart – Digital Marketing & E-Commerce Platform

> A full-stack Python Flask supermarket e-commerce web application tailored for **Digital Marketing** academic projects. Features zero-setup SQLite database, promotional coupon engine, price discount perception, customer loyalty points, and digital marketing analytics dashboard.

---

## 🖥️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Backend | Python 3 Flask |
| Database | SQLite3 (`vmart.db` - zero setup, auto-initialized) |
| Analytics | Chart.js (Marketing Campaign Metrics) |

---

## 📁 Project Structure

```
DBMS_Project/
├── app.py                  ← Flask backend (all routes & SQLite setup)
├── vmart.db                ← Local SQLite database (auto-generated)
├── requirements.txt        ← Lightweight dependencies (Flask, Gunicorn)
├── Procfile                ← Deployment configuration
│
├── templates/
│   ├── base.html           ← Vmart branding & navbar
│   ├── index.html          ← Supermarket catalog & promo banners
│   ├── cart.html           ← Basket & coupon code validation
│   ├── checkout.html       ← Shipping, payment & V-Points
│   ├── orders.html         ← Order receipts & loyalty points
│   ├── dashboard.html      ← Digital Marketing Analytics & Charts
│   ├── admin.html          ← Inventory & Store Admin
│   ├── add_product.html    ← Add supermarket item with discounts
│   ├── login.html          ← User login
│   └── signup.html         ← User signup
│
└── static/
    ├── css/style.css       ← Vmart Supermart styling
    └── js/main.js
```

---

## ⚙️ Quick Start (Local Execution)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the App**:
   ```bash
   python app.py
   ```

3. Open your browser at: **http://127.0.0.1:5000**

---

## 🔑 Demo Accounts

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@vmart.com` | `admin123` |
| **User** | `jane@vmart.com` | `user123` |

---

## 🎯 Digital Marketing Features

- **Promotional Coupon Engine**: Test coupon codes like `VMART20` (20% OFF) and `FRESH50` ($5 OFF on $25+).
- **Psychological Pricing**: Displays original MRP alongside Vmart discounted sale price and savings percentage.
- **Customer Loyalty Rewards**: Earn 1 V-Point for every $1 spent.
- **Marketing Analytics Dashboard**: Real-time charts showing sales revenue by product category, customer savings, and coupon redemptions.
- **Zero-Setup Database**: Uses built-in SQLite so no external database hosting or paid subscriptions are required.
