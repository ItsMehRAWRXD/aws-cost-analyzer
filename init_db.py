import os
import sys

def init_database():
    try:
        # Use Render's PostgreSQL database
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            print(f"Initializing PostgreSQL database...")
            print(f"DATABASE_URL: {database_url[:20]}...")
            import psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id SERIAL PRIMARY KEY, email VARCHAR(255) UNIQUE, password VARCHAR(255), 
                             stripe_customer_id VARCHAR(255), subscription_status VARCHAR(50) DEFAULT 'free')''')
            
            # Verify table was created
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ PostgreSQL database initialized successfully - {user_count} existing users")
            return True
            
        else:
            print("No DATABASE_URL found, using SQLite for local development")
            # Fallback to SQLite for local development
            import sqlite3
            db_path = os.path.join(os.path.dirname(__file__), 'users.db')
            conn = sqlite3.connect(db_path)
            conn.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, 
                             stripe_customer_id TEXT, subscription_status TEXT DEFAULT 'free')''')
            
            # Verify table was created
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            print(f"✅ SQLite database initialized at {db_path} - {user_count} existing users")
            return True
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
