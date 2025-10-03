import os

# Use Render's PostgreSQL database
database_url = os.getenv('DATABASE_URL')
if database_url:
    import psycopg2
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id SERIAL PRIMARY KEY, email VARCHAR(255) UNIQUE, password VARCHAR(255), 
                             stripe_customer_id VARCHAR(255), subscription_status VARCHAR(50) DEFAULT 'free',
                             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP)''')
            
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_files 
                    (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                     filename VARCHAR(255), file_type VARCHAR(50), file_size INTEGER,
                     upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, analysis_data JSON,
                     status VARCHAR(50) DEFAULT 'uploaded')''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS analysis_history 
                    (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                     monthly_bill DECIMAL(10,2), services TEXT, region VARCHAR(100),
                     workload_type VARCHAR(50), potential_savings DECIMAL(10,2),
                     analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, recommendations JSON)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_sessions 
                    (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                     session_data JSON, last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     is_active BOOLEAN DEFAULT TRUE)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_todos 
                    (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                     title VARCHAR(255) NOT NULL, description TEXT, priority VARCHAR(20) DEFAULT 'medium',
                     category VARCHAR(50) DEFAULT 'general', status VARCHAR(20) DEFAULT 'pending',
                     due_date TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     completed_at TIMESTAMP, analysis_id INTEGER REFERENCES analysis_history(id))''')
    
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
                     stripe_customer_id TEXT, subscription_status TEXT DEFAULT 'free',
                     created_at DATETIME DEFAULT CURRENT_TIMESTAMP, last_login DATETIME)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS user_files 
                    (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                     filename TEXT, file_type TEXT, file_size INTEGER,
                     upload_date DATETIME DEFAULT CURRENT_TIMESTAMP, analysis_data TEXT,
                     status TEXT DEFAULT 'uploaded')''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS analysis_history 
                    (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                     monthly_bill REAL, services TEXT, region TEXT,
                     workload_type TEXT, potential_savings REAL,
                     analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP, recommendations TEXT)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS user_sessions 
                    (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                     session_data TEXT, last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                     is_active BOOLEAN DEFAULT 1)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS user_todos 
                    (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                     title TEXT NOT NULL, description TEXT, priority TEXT DEFAULT 'medium',
                     category TEXT DEFAULT 'general', status TEXT DEFAULT 'pending',
                     due_date DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                     completed_at DATETIME, analysis_id INTEGER REFERENCES analysis_history(id))''')
    
    conn.commit()
    conn.close()
    print(f"SQLite database initialized at {db_path}")
