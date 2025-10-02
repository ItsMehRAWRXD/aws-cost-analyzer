import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'users.db')
conn = sqlite3.connect(db_path)
conn.execute('''CREATE TABLE IF NOT EXISTS users 
                (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, 
                 stripe_customer_id TEXT, subscription_status TEXT DEFAULT 'free')''')
conn.commit()
conn.close()
print(f"Database initialized at {db_path}")
