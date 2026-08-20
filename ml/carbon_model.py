"""
Carbon Emission Classifier
==========================
Trains a RandomForestClassifier on product features to predict
carbon impact level: 0=Low | 1=Medium | 2=High

Run this file once to train and save the model:
    uv run python ml/carbon_model.py
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# ----------------------------------------------------------------
# Model save path (relative to project root)
# ----------------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "carbon_classifier.pkl")

# ----------------------------------------------------------------
# Label map
# ----------------------------------------------------------------
LABEL_MAP   = {0: "low", 1: "medium", 2: "high"}
REVERSE_MAP = {"low": 0, "medium": 1, "high": 2}

LABEL_COLORS = {
    "low":    ("Low Carbon",    "success"),
    "medium": ("Medium Carbon", "warning"),
    "high":   ("High Carbon",   "danger"),
}

# ----------------------------------------------------------------
# Training dataset  (manually curated; expand as needed)
# ----------------------------------------------------------------
TRAINING_DATA = [
    # description, category_id, price, base_co2, label
    # --- HIGH ---
    ("High-performance laptop with 8GB RAM and SSD storage",              1, 85000, 350.0, 2),
    ("Flagship smartphone with OLED display and 5G modem",                1, 74999, 70.0,  2),
    ("Gaming desktop PC with RTX 4080 graphics card",                     1, 150000,420.0, 2),
    ("Large refrigerator with freezer compartment energy intensive",       1, 45000, 250.0, 2),
    ("Denim jeans water intensive cotton synthetic dyes chemical wash",    2, 2499,  33.4,  2),
    ("Leather jacket from cow hide chemical tanning process",              2, 8999,  115.0, 2),
    ("Synthetic polyester dress petroleum-based fiber",                    2, 1599,  25.0,  2),
    ("Hardwood dining table solid teak logging deforestation",             5, 22000, 180.0, 2),
    ("Sofa set imported hardwood foam upholstery chemical treatment",      5, 35000, 220.0, 2),
    ("Imported instant coffee freeze-dried freight shipped",               3, 599,   4.6,   2),
    ("Beef jerky high methane emissions cattle ranching",                  3, 899,   27.0,  2),
    ("Electric oven high power consumption metal fabrication",             1, 18000, 95.0,  2),
    ("Air conditioner refrigerant HFC emission high energy",               1, 35000, 310.0, 2),

    # --- MEDIUM ---
    ("Portable bluetooth speaker lithium battery plastic casing",         1, 3499,  18.5,  1),
    ("Tablet with aluminum body and lithium battery",                      1, 25000, 45.0,  1),
    ("Recycled polyester jacket made from plastic bottles",                2, 3999,  7.8,   1),
    ("Cotton hoodie conventional farming moderate processing",             2, 1999,  15.0,  1),
    ("Instant noodles processed food packaging plastic",                   3, 49,    1.2,   1),
    ("Chocolate bar imported cocoa sugar processing packaging",            3, 99,    2.3,   1),
    ("Ceramic coffee mug kiln fired high temperature",                     4, 399,   3.5,   1),
    ("Wooden photo frame lacquered moderate forestry impact",              5, 799,   8.0,   1),
    ("Printed paperback novel conventional paper ink",                     6, 399,   1.1,   1),
    ("Ballpoint pen plastic body conventional ink",                        6, 29,    0.9,   1),
    ("Steel spatula kitchen tool metal fabrication",                       4, 249,   2.8,   1),
    ("Olive oil imported glass bottled moderate shipping",                 3, 399,   1.8,   1),
    ("Running shoes EVA foam rubber sole conventional manufacturing",      2, 4999,  14.0,  1),
    ("Wall clock plastic ABS battery operated",                            1, 599,   3.2,   1),

    # --- LOW ---
    ("LED energy efficient desk lamp low power consumption",               1, 999,   5.2,   0),
    ("Organic cotton t-shirt GOTS certified natural dyes sustainable",     2, 799,   2.1,   0),
    ("Stainless steel reusable water bottle BPA free replaces plastic",    4, 699,   1.2,   0),
    ("Bamboo toothbrush biodegradable natural material",                   4, 299,   0.3,   0),
    ("Beeswax food wraps reusable handmade zero chemicals",                4, 499,   0.8,   0),
    ("Seed paper notebook recycled wildflower seeds plantable",            6, 249,   0.6,   0),
    ("FSC certified recycled paper sketchbook soy inks",                   6, 349,   0.7,   0),
    ("Organic green tea sun dried locally sourced minimal processing",     3, 349,   0.5,   0),
    ("Solar powered phone charger renewable energy zero emissions",        1, 2499,  4.9,   0),
    ("Hemp tote bag biodegradable natural fiber reusable",                 4, 349,   0.4,   0),
    ("Compostable garbage bags plant starch biodegradable",                4, 199,   0.2,   0),
    ("Refillable glass spray bottle cleaning zero plastic",                4, 449,   0.9,   0),
    ("Digital e-book zero physical material carbon neutral",               6, 199,   0.01,  0),
    ("Locally grown organic apple zero transport emission",                3, 80,    0.1,   0),
    ("Beeswax candle natural soy blend renewable ingredients",             4, 599,   1.0,   0),
]


# ----------------------------------------------------------------
# Build & train pipeline (using ColumnTransformer to avoid pickle errors)
# ----------------------------------------------------------------
def build_pipeline():
    # Use standard scikit-learn ColumnTransformer referencing dataframe columns
    preprocessor = ColumnTransformer(
        transformers=[
            ('text', TfidfVectorizer(ngram_range=(1, 2), max_features=500, stop_words="english"), 'description'),
            ('num', StandardScaler(), ['category_id', 'price', 'base_carbon_emission'])
        ],
        remainder='drop'
    )
    
    clf = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            random_state=42,
            class_weight="balanced"
        )),
    ])
    return clf


def train_and_save():
    # Build a pandas DataFrame to use with ColumnTransformer
    df = pd.DataFrame(TRAINING_DATA, columns=["description", "category_id", "price", "base_carbon_emission", "label"])
    
    X = df[["description", "category_id", "price", "base_carbon_emission"]]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = build_pipeline()
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    print(f"\n✅  Model trained. Test accuracy: {acc:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Low", "Medium", "High"]))

    joblib.dump(clf, MODEL_PATH)
    print(f"✅  Model saved to: {MODEL_PATH}")
    return clf


# ----------------------------------------------------------------
# Public API used by Flask app
# ----------------------------------------------------------------
def load_model():
    """Load saved model or train a new one if missing."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    print("⚠️  Model not found – training fresh model …")
    return train_and_save()

def estimate_base_carbon(description: str, category_id: int, price: float) -> float:
    """
    Returns an estimated base carbon footprint (kg CO2e) for a product
    based on its category, price, and description, simulating an AI system.
    """
    desc = description.lower()
    
    # Base multipliers by category (rough estimates)
    cat_multipliers = {
        1: 25.0,  # Electronics: high base
        2: 12.0,  # Clothing
        3: 5.0,   # Food
        4: 2.0,   # Reusables: very low base
        5: 35.0,  # Furniture: highest base due to weight/wood
        6: 1.5    # Stationery/Books: low base
    }
    base_co2 = cat_multipliers.get(int(category_id), 10.0)
    
    # Scale slightly by price (proxy for complexity/size)
    # E.g. a ₹150,000 laptop has higher footprint than a ₹3000 speaker
    price_factor = np.log10(max(price, 10)) * 2.5
    base_co2 += price_factor
    
    # Adjust based on keywords in description
    if any(k in desc for k in ["plastic", "synthetic", "leather", "imported", "refrigerant", "hardwood"]):
        base_co2 *= 1.5
    if any(k in desc for k in ["organic", "recycled", "biodegradable", "sustainable", "bamboo", "local"]):
        base_co2 *= 0.4
        
    return float(round(max(0.01, base_co2), 2))


def predict(description: str, category_id: int, price: float,
            base_carbon_emission: float = 0.0) -> dict:
    """
    Predict carbon impact level for a single product.

    Returns:
        {
            "label":   "low" | "medium" | "high",
            "label_int": 0 | 1 | 2,
            "badge_text":  "Low Carbon" | ...,
            "badge_color": "success" | "warning" | "danger",
            "suggestion": str,
            "estimated_base_carbon": float
        }
    """
    model = load_model()
    
    # Wrap input in pandas dataframe for ColumnTransformer
    X_new = pd.DataFrame([{
        "description":          description,
        "category_id":          int(category_id),
        "price":                float(price),
        "base_carbon_emission": float(base_carbon_emission),
    }])
    
    label_int = int(model.predict(X_new)[0])
    label_str = LABEL_MAP[label_int]
    badge_text, badge_color = LABEL_COLORS[label_str]

    suggestions = {
        "low":    "Great choice! This is an eco-friendly, low-carbon product. 🌿",
        "medium": "Moderate carbon footprint. Consider reusable alternatives where possible. ♻️",
        "high":   "High carbon product. Consider choosing low-carbon alternatives for a greener cart. 🌍",
    }

    return {
        "label":       label_str,
        "label_int":   label_int,
        "badge_text":  badge_text,
        "badge_color": badge_color,
        "suggestion":  suggestions[label_str],
    }


def get_cart_suggestion(total_carbon_kg: float) -> str:
    """Return a sustainability suggestion based on total cart carbon."""
    if total_carbon_kg < 5:
        return "🌿 Excellent! Your cart has a very low carbon footprint. Keep it up!"
    elif total_carbon_kg < 30:
        return "♻️ Your cart has a moderate carbon footprint. Try swapping high-emission items for eco-friendly alternatives."
    else:
        return "🌍 Your cart has a high carbon footprint. Consider choosing low-carbon alternatives to reduce your environmental impact."


# ----------------------------------------------------------------
# CLI entry-point
# ----------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  Carbon Emission Classifier – Training")
    print("=" * 60)
    train_and_save()

    # Quick smoke test
    print("\n--- Smoke Tests ---")
    tests = [
        ("High-performance gaming laptop with RTX graphics", 1, 85000, 350.0),
        ("Recycled organic cotton t-shirt sustainable farming", 2, 799, 2.1),
        ("Bamboo toothbrush biodegradable natural material", 4, 299, 0.3),
    ]
    for desc, cat, price, co2 in tests:
        result = predict(desc, cat, price, co2)
        print(f"  [{result['badge_text']:15}] {desc[:55]}")
