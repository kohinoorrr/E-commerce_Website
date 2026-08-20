import psycopg2

DB_CONFIG = {
    "host":     "localhost",
    "port":     5433,
    "dbname":   "eco_ecommerce",
    "user":     "postgres",
    "password": "tiger",
}

def migrate():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        print("Modifying users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_merchant BOOLEAN DEFAULT FALSE;")
        
        print("Modifying products table...")
        cursor.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS merchant_id INT REFERENCES users(user_id) ON DELETE CASCADE;")
        
        print("Migration complete!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
