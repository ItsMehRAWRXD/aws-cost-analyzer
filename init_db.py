import os
import psycopg2

# Use Render's PostgreSQL database
database_url = os.getenv('DATABASE_URL')
if database_url:
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                    (id SERIAL PRIMARY KEY, email VARCHAR(255) UNIQUE, password VARCHAR(255), 
                     stripe_customer_id VARCHAR(255), subscription_status VARCHAR(50) DEFAULT 'free')''')
    conn.commit()
    cursor.close()
    conn.close()
    print("PostgreSQL database initialized successfully")
else:
    # Fallback to SQLite for local development
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                    (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, 
                     stripe_customer_id TEXT, subscription_status TEXT DEFAULT 'free')''')
    conn.commit()
    conn.close()
    print(f"SQLite database initialized at {db_path}")
