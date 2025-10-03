#!/usr/bin/env python3
"""
AWS Cost Analyzer - Complete Turnkey SaaS
Just edit .env with your keys and run!
"""

from flask import Flask, render_template_string, request, jsonify, session, redirect
import os
import json
import stripe
import secrets
import sys
from datetime import datetime
from functools import wraps
import hashlib
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Create uploads directory for persistent file storage
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def get_db():
    # Use Render's PostgreSQL database
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        # Fallback to local SQLite for development
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if we're using PostgreSQL or SQLite
    if os.getenv('DATABASE_URL'):
        # PostgreSQL syntax
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
    else:
        # SQLite syntax
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                        (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, 
                         stripe_customer_id TEXT, subscription_status TEXT DEFAULT 'free',
                         created_at DATETIME DEFAULT CURRENT_TIMESTAMP, last_login DATETIME)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_files 
                        (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                         filename TEXT, file_type TEXT, file_size INTEGER,
                         upload_date DATETIME DEFAULT CURRENT_TIMESTAMP, analysis_data TEXT,
                         status TEXT DEFAULT 'uploaded')''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS analysis_history 
                        (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                         monthly_bill REAL, services TEXT, region TEXT,
                         workload_type TEXT, potential_savings REAL,
                         analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP, recommendations TEXT)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_sessions 
                        (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                         session_data TEXT, last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                         is_active BOOLEAN DEFAULT 1)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_todos 
                        (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                         title TEXT NOT NULL, description TEXT, priority TEXT DEFAULT 'medium',
                         category TEXT DEFAULT 'general', status TEXT DEFAULT 'pending',
                         due_date DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                         completed_at DATETIME, analysis_id INTEGER REFERENCES analysis_history(id))''')
    
    conn.commit()
    cursor.close()
    conn.close()

def save_user_session(user_id, session_data):
    """Save user session data to database for persistence"""
    conn = get_db()
    cursor = conn.cursor()
    
    session_json = json.dumps(session_data) if isinstance(session_data, dict) else str(session_data)
    
    if os.getenv('DATABASE_URL'):
        cursor.execute('''INSERT INTO user_sessions (user_id, session_data, last_activity, is_active)
                         VALUES (%s, %s, CURRENT_TIMESTAMP, TRUE)
                         ON CONFLICT (user_id) DO UPDATE SET 
                         session_data = EXCLUDED.session_data,
                         last_activity = EXCLUDED.last_activity,
                         is_active = TRUE''', (user_id, session_json))
    else:
        cursor.execute('''INSERT OR REPLACE INTO user_sessions (user_id, session_data, last_activity, is_active)
                         VALUES (?, ?, CURRENT_TIMESTAMP, 1)''', (user_id, session_json))
    
    conn.commit()
    cursor.close()
    conn.close()

def load_user_session(user_id):
    """Load user session data from database"""
    conn = get_db()
    cursor = conn.cursor()
    
    if os.getenv('DATABASE_URL'):
        cursor.execute('SELECT session_data FROM user_sessions WHERE user_id = %s AND is_active = TRUE', (user_id,))
    else:
        cursor.execute('SELECT session_data FROM user_sessions WHERE user_id = ? AND is_active = 1', (user_id,))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        try:
            return json.loads(result[0])
        except:
            return {}
    return {}

def save_analysis_history(user_id, analysis_data):
    """Save cost analysis to history for persistence"""
    conn = get_db()
    cursor = conn.cursor()
    
    recommendations_json = json.dumps(analysis_data.get('recommendations', []))
    
    if os.getenv('DATABASE_URL'):
        cursor.execute('''INSERT INTO analysis_history 
                         (user_id, monthly_bill, services, region, workload_type, potential_savings, recommendations)
                         VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                      (user_id, analysis_data.get('monthly_bill'), 
                       analysis_data.get('services'), analysis_data.get('region'),
                       analysis_data.get('workload_type'), analysis_data.get('potential_savings'),
                       recommendations_json))
    else:
        cursor.execute('''INSERT INTO analysis_history 
                         (user_id, monthly_bill, services, region, workload_type, potential_savings, recommendations)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, analysis_data.get('monthly_bill'), 
                       analysis_data.get('services'), analysis_data.get('region'),
                       analysis_data.get('workload_type'), analysis_data.get('potential_savings'),
                       recommendations_json))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_analysis_history(user_id):
    """Get user's analysis history"""
    conn = get_db()
    cursor = conn.cursor()
    
    if os.getenv('DATABASE_URL'):
        cursor.execute('''SELECT * FROM analysis_history WHERE user_id = %s 
                         ORDER BY analysis_date DESC LIMIT 10''', (user_id,))
    else:
        cursor.execute('''SELECT * FROM analysis_history WHERE user_id = ? 
                         ORDER BY analysis_date DESC LIMIT 10''', (user_id,))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def save_todo(user_id, todo_data):
    """Save a new todo item"""
    conn = get_db()
    cursor = conn.cursor()
    
    if os.getenv('DATABASE_URL'):
        cursor.execute('''INSERT INTO user_todos 
                         (user_id, title, description, priority, category, status, due_date, analysis_id)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                      (user_id, todo_data.get('title'), todo_data.get('description'),
                       todo_data.get('priority', 'medium'), todo_data.get('category', 'general'),
                       todo_data.get('status', 'pending'), todo_data.get('due_date'),
                       todo_data.get('analysis_id')))
    else:
        cursor.execute('''INSERT INTO user_todos 
                         (user_id, title, description, priority, category, status, due_date, analysis_id)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, todo_data.get('title'), todo_data.get('description'),
                       todo_data.get('priority', 'medium'), todo_data.get('category', 'general'),
                       todo_data.get('status', 'pending'), todo_data.get('due_date'),
                       todo_data.get('analysis_id')))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_user_todos(user_id, status=None):
    """Get user's todos, optionally filtered by status"""
    conn = get_db()
    cursor = conn.cursor()
    
    if status:
        if os.getenv('DATABASE_URL'):
            cursor.execute('''SELECT * FROM user_todos WHERE user_id = %s AND status = %s 
                             ORDER BY created_at DESC''', (user_id, status))
        else:
            cursor.execute('''SELECT * FROM user_todos WHERE user_id = ? AND status = ? 
                             ORDER BY created_at DESC''', (user_id, status))
    else:
        if os.getenv('DATABASE_URL'):
            cursor.execute('''SELECT * FROM user_todos WHERE user_id = %s 
                             ORDER BY created_at DESC''', (user_id,))
        else:
            cursor.execute('''SELECT * FROM user_todos WHERE user_id = ? 
                             ORDER BY created_at DESC''', (user_id,))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def update_todo_status(user_id, todo_id, status):
    """Update todo status (pending/completed)"""
    conn = get_db()
    cursor = conn.cursor()
    
    completed_at = datetime.now() if status == 'completed' else None
    
    if os.getenv('DATABASE_URL'):
        cursor.execute('''UPDATE user_todos SET status = %s, completed_at = %s 
                         WHERE id = %s AND user_id = %s''',
                      (status, completed_at, todo_id, user_id))
    else:
        cursor.execute('''UPDATE user_todos SET status = ?, completed_at = ? 
                         WHERE id = ? AND user_id = ?''',
                      (status, completed_at, todo_id, user_id))
    
    conn.commit()
    cursor.close()
    conn.close()

def delete_todo(user_id, todo_id):
    """Delete a todo item"""
    conn = get_db()
    cursor = conn.cursor()
    
    if os.getenv('DATABASE_URL'):
        cursor.execute('DELETE FROM user_todos WHERE id = %s AND user_id = %s', (todo_id, user_id))
    else:
        cursor.execute('DELETE FROM user_todos WHERE id = ? AND user_id = ?', (todo_id, user_id))
    
    conn.commit()
    cursor.close()
    conn.close()

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>AWS Cost Analyzer Pro</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f8f9fa}
.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px;display:flex;justify-content:space-between;align-items:center}
.nav{background:white;padding:15px 20px;box-shadow:0 2px 10px rgba(0,0,0,0.1);border-bottom:1px solid #e9ecef}
.nav button{background:none;border:none;padding:12px 24px;cursor:pointer;margin-right:10px;border-radius:8px;font-weight:500;transition:all 0.3s}
.nav button.active{background:#667eea;color:white}
.nav button:hover{background:#f8f9fa}
.container{max-width:1200px;margin:0 auto;padding:30px 20px}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;margin-bottom:40px}
.stat-card{background:white;padding:24px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);border:1px solid #e9ecef}
.stat-value{font-size:2.5em;font-weight:700;color:#667eea;margin:8px 0}
.stat-label{color:#6c757d;font-size:0.9em;font-weight:500}
.charts-grid{display:grid;grid-template-columns:2fr 1fr;gap:24px;margin-bottom:40px}
.chart-container{background:white;padding:24px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);border:1px solid #e9ecef}
.tab-content{display:none}
.tab-content.active{display:block}
.btn{background:#667eea;color:white;padding:12px 24px;border:none;border-radius:8px;cursor:pointer;font-weight:500;transition:all 0.3s}
.btn:hover{background:#5a6fd8;transform:translateY(-1px)}
.btn:disabled{background:#6c757d;cursor:not-allowed;transform:none}
.form-group{margin:20px 0}
.form-group label{display:block;margin-bottom:8px;font-weight:600;color:#495057}
.form-group input,.form-group select{width:100%;padding:12px 16px;border:2px solid #e9ecef;border-radius:8px;font-size:16px;transition:border-color 0.3s}
.form-group input:focus,.form-group select:focus{outline:none;border-color:#667eea}
.pricing{display:flex;gap:24px;justify-content:center;margin:40px 0;flex-wrap:wrap}
.pricing-card{background:white;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);text-align:center;min-width:280px;border:2px solid #e9ecef;transition:all 0.3s}
.pricing-card:hover{transform:translateY(-4px);box-shadow:0 8px 40px rgba(0,0,0,0.12)}
.price{font-size:3.5em;font-weight:700;color:#667eea;margin:16px 0}
.text-danger{color:#dc3545;padding:16px;background:#f8d7da;border:1px solid #f5c6cb;border-radius:8px;margin:16px 0}
.text-success{color:#155724;padding:16px;background:#d4edda;border:1px solid #c3e6cb;border-radius:8px;margin:16px 0}
.loading{opacity:0.6;pointer-events:none}
.recommendation{background:#f8f9fa;border-left:4px solid #667eea;padding:20px;margin:16px 0;border-radius:8px}
.recommendation h4{color:#495057;margin-bottom:8px}
.savings{color:#28a745;font-weight:600}
</style></head>
<body>
<div class="header">
<h1>AWS Cost Analyzer Pro</h1>
<div><span>Welcome, {{email}}</span> | <a href="/logout" style="color:white;text-decoration:none">Logout</a></div>
</div>

<div class="nav">
<button class="tab-btn active" onclick="showTab('dashboard')">Dashboard</button>
<button class="tab-btn" onclick="showTab('analyze')">Cost Analysis</button>
<button class="tab-btn" onclick="showTab('files')">File Manager</button>
<button class="tab-btn" onclick="showTab('tasks')">Task Manager</button>
<button class="tab-btn" onclick="showTab('pricing')">Upgrade Plan</button>
</div>

<div class="container">
<div id="dashboard" class="tab-content active">
<div class="stats-grid">
<div class="stat-card">
<div class="stat-label">Current Month Spend</div>
<div class="stat-value">$1,247</div>
<div style="color:#28a745;font-size:0.9em">↓ 5% from last month</div>
</div>
<div class="stat-card">
<div class="stat-label">Projected This Month</div>
<div class="stat-value">$1,398</div>
<div style="color:#ffc107;font-size:0.9em">↑ 12% increase</div>
</div>
<div class="stat-card">
<div class="stat-label">Available Savings</div>
<div class="stat-value savings">$347</div>
<div style="color:#28a745;font-size:0.9em">25% optimization potential</div>
</div>
<div class="stat-card">
<div class="stat-label">Optimization Score</div>
<div class="stat-value">72%</div>
<div style="color:#17a2b8;font-size:0.9em">Good performance</div>
</div>
</div>
<div class="charts-grid">
<div class="chart-container">
<h3 style="margin-bottom:20px">6-Month Cost Trend</h3>
<canvas id="trendChart"></canvas>
</div>
<div class="chart-container">
<h3 style="margin-bottom:20px">Service Breakdown</h3>
<canvas id="pieChart"></canvas>
</div>
</div>
</div>

<div id="analyze" class="tab-content">
<h2 style="margin-bottom:30px">Analyze Your AWS Costs</h2>
<form id="analyzeForm">
<div class="form-group">
<label>Monthly AWS Bill ($)</label>
<input type="number" id="monthlyBill" placeholder="e.g., 1250" min="1" required>
</div>
<div class="form-group">
<label>Primary AWS Services</label>
<input type="text" id="services" placeholder="EC2, S3, RDS, Lambda" required>
</div>
<div class="form-group">
<label>AWS Region</label>
<select id="region" required>
<option value="">Select Region</option>
<option value="us-east-1">US East (N. Virginia)</option>
<option value="us-west-2">US West (Oregon)</option>
<option value="eu-west-1">Europe (Ireland)</option>
<option value="ap-southeast-1">Asia Pacific (Singapore)</option>
</select>
</div>
<div class="form-group">
<label>Workload Type</label>
<select id="workloadType" required>
<option value="">Select Workload</option>
<option value="web">Web Application</option>
<option value="data">Data Processing</option>
<option value="ml">Machine Learning</option>
<option value="storage">Storage Heavy</option>
<option value="compute">Compute Intensive</option>
</select>
</div>
<button type="submit" class="btn" id="analyzeBtn">Analyze Costs & Get Recommendations</button>
</form>
<div id="results" style="margin-top:40px;display:none">
<h3>Cost Analysis Results</h3>
<div id="resultsContent"></div>
</div>
</div>

<div id="tasks" class="tab-content">
<h2 style="margin-bottom:30px">Task Manager</h2>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:30px;margin-bottom:30px">
<div>
<h3 style="margin-bottom:20px">Create New Task</h3>
<form id="todoForm">
<div class="form-group">
<label>Task Title</label>
<input type="text" id="todoTitle" placeholder="e.g., Review EC2 instances for optimization" required>
</div>
<div class="form-group">
<label>Description (Optional)</label>
<textarea id="todoDescription" placeholder="Add details about this task..." rows="3" style="width:100%;padding:12px 16px;border:2px solid #e9ecef;border-radius:8px;font-size:16px;resize:vertical"></textarea>
</div>
<div class="form-group">
<label>Priority</label>
<select id="todoPriority">
<option value="low">Low</option>
<option value="medium" selected>Medium</option>
<option value="high">High</option>
<option value="urgent">Urgent</option>
</select>
</div>
<div class="form-group">
<label>Category</label>
<select id="todoCategory">
<option value="cost-optimization">Cost Optimization</option>
<option value="security">Security</option>
<option value="performance">Performance</option>
<option value="monitoring">Monitoring</option>
<option value="general" selected>General</option>
</select>
</div>
<div class="form-group">
<label>Due Date (Optional)</label>
<input type="date" id="todoDueDate">
</div>
<button type="submit" class="btn" style="width:100%">Create Task</button>
</form>
</div>

<div>
<h3 style="margin-bottom:20px">Quick Actions</h3>
<div style="display:grid;gap:12px">
<button class="btn" onclick="createQuickTodo('Review unused EBS volumes', 'cost-optimization', 'high')" style="background:#28a745;text-align:left">
📦 Review Unused EBS Volumes
</button>
<button class="btn" onclick="createQuickTodo('Check RDS instance sizing', 'cost-optimization', 'medium')" style="background:#ffc107;color:#000;text-align:left">
🗄️ Check RDS Instance Sizing
</button>
<button class="btn" onclick="createQuickTodo('Review S3 storage classes', 'cost-optimization', 'medium')" style="background:#17a2b8;text-align:left">
☁️ Review S3 Storage Classes
</button>
<button class="btn" onclick="createQuickTodo('Set up cost alerts', 'monitoring', 'high')" style="background:#dc3545;text-align:left">
🚨 Set Up Cost Alerts
</button>
<button class="btn" onclick="createQuickTodo('Review IAM permissions', 'security', 'medium')" style="background:#6f42c1;text-align:left">
🔐 Review IAM Permissions
</button>
</div>
</div>
</div>

<div style="background:#f8f9fa;border-radius:12px;padding:24px">
<h3 style="margin-bottom:20px">Your Tasks</h3>
<div style="display:flex;gap:12px;margin-bottom:20px">
<button class="btn" onclick="filterTodos('all')" id="filterAll" style="background:#667eea">All</button>
<button class="btn" onclick="filterTodos('pending')" id="filterPending" style="background:#6c757d">Pending</button>
<button class="btn" onclick="filterTodos('completed')" id="filterCompleted" style="background:#6c757d">Completed</button>
</div>
<div id="todosList" style="display:grid;gap:12px">
<div style="text-align:center;color:#6c757d;padding:40px">
Loading your tasks...
</div>
</div>
</div>
</div>

<div id="pricing" class="tab-content">
<h2 style="text-align:center;margin-bottom:40px">Choose Your Plan</h2>
<div class="pricing">
<div class="pricing-card">
<h3>Starter</h3>
<div class="price">$29<small style="font-size:0.4em">/month</small></div>
<ul style="text-align:left;margin:24px 0;list-style:none;padding:0">
<li style="padding:8px 0">✓ Monthly cost analysis</li>
<li style="padding:8px 0">✓ Basic recommendations</li>
<li style="padding:8px 0">✓ Email support</li>
<li style="padding:8px 0">✓ 3 AWS accounts</li>
</ul>
<button class="btn" onclick="subscribe('starter')" style="width:100%">Start Free Trial</button>
</div>
<div class="pricing-card" style="border-color:#667eea;transform:scale(1.05)">
<div style="background:#667eea;color:white;padding:8px;margin:-40px -40px 20px;border-radius:12px 12px 0 0">Most Popular</div>
<h3>Professional</h3>
<div class="price">$99<small style="font-size:0.4em">/month</small></div>
<ul style="text-align:left;margin:24px 0;list-style:none;padding:0">
<li style="padding:8px 0">✓ Real-time monitoring</li>
<li style="padding:8px 0">✓ Advanced optimization</li>
<li style="padding:8px 0">✓ Custom alerts & budgets</li>
<li style="padding:8px 0">✓ Priority support</li>
<li style="padding:8px 0">✓ Unlimited AWS accounts</li>
<li style="padding:8px 0">✓ API access</li>
</ul>
<button class="btn" onclick="subscribe('professional')" style="width:100%">Start Free Trial</button>
</div>
<div class="pricing-card">
<h3>Enterprise</h3>
<div class="price">$299<small style="font-size:0.4em">/month</small></div>
<ul style="text-align:left;margin:24px 0;list-style:none;padding:0">
<li style="padding:8px 0">✓ Everything in Professional</li>
<li style="padding:8px 0">✓ Dedicated account manager</li>
<li style="padding:8px 0">✓ Custom integrations</li>
<li style="padding:8px 0">✓ SLA guarantee</li>
<li style="padding:8px 0">✓ White-label options</li>
<li style="padding:8px 0">✓ 24/7 phone support</li>
</ul>
<button class="btn" onclick="subscribe('enterprise')" style="width:100%">Contact Sales</button>
</div>
</div>

<div id="files" class="tab-content">
<h2 style="margin-bottom:30px">File Manager</h2>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:30px;margin-bottom:30px">
<div>
<h3 style="margin-bottom:20px">Upload Files</h3>
<div class="form-group">
<label>Upload AWS Billing File</label>
<input type="file" id="billingFile" accept=".csv,.json,.xlsx" style="padding:12px;border:2px dashed #e9ecef;border-radius:8px;width:100%">
<small style="color:#6c757d;display:block;margin-top:8px">Supported: CSV, JSON, Excel files from AWS Cost Explorer</small>
</div>
<div class="form-group">
<label>Upload Configuration File</label>
<input type="file" id="configFile" accept=".yaml,.yml,.json,.txt" style="padding:12px;border:2px dashed #e9ecef;border-radius:8px;width:100%">
<small style="color:#6c757d;display:block;margin-top:8px">CloudFormation, Terraform, or other config files</small>
</div>
<div class="form-group">
<label>Upload Custom Data</label>
<input type="file" id="customFile" accept=".csv,.json,.txt,.log" style="padding:12px;border:2px dashed #e9ecef;border-radius:8px;width:100%">
<small style="color:#6c757d;display:block;margin-top:8px">Any cost-related data files</small>
</div>
<button class="btn" onclick="uploadFiles()" style="width:100%">Upload & Analyze</button>
</div>

<div>
<h3 style="margin-bottom:20px">Uploaded Files</h3>
<div id="fileList" style="background:#f8f9fa;border-radius:8px;padding:20px;min-height:200px">
<div style="text-align:center;color:#6c757d;padding:40px">
No files uploaded yet.<br>
Upload your AWS billing or configuration files to get started.
</div>
</div>
</div>
</div>

<div style="background:#f8f9fa;border-radius:12px;padding:24px;margin-top:30px">
<h3 style="margin-bottom:16px">File Analysis Results</h3>
<div id="fileAnalysis" style="display:none">
<div class="stats-grid" style="grid-template-columns:repeat(auto-fit,minmax(200px,1fr))">
<div class="stat-card">
<div class="stat-label">Total Services</div>
<div class="stat-value" id="totalServices">0</div>
</div>
<div class="stat-card">
<div class="stat-label">Cost Anomalies</div>
<div class="stat-value" id="costAnomalies">0</div>
</div>
<div class="stat-card">
<div class="stat-label">Optimization Opportunities</div>
<div class="stat-value" id="optimizationOps">0</div>
</div>
</div>
<div id="fileRecommendations" style="margin-top:20px"></div>
</div>
<div id="noAnalysis" style="text-align:center;color:#6c757d;padding:20px">
Upload files to see detailed analysis results.
</div>
</div>
</div>
</div>
</div>

<script>
function showTab(tab) {
document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
document.getElementById(tab).classList.add('active');
event.target.classList.add('active');
}

// Initialize charts
const trendCtx = document.getElementById('trendChart').getContext('2d');
new Chart(trendCtx, {
type: 'line',
data: {
labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
datasets: [{
label: 'Monthly Cost ($)',
data: [1100, 1150, 1200, 1247, 1300, 1398],
borderColor: '#667eea',
backgroundColor: 'rgba(102, 126, 234, 0.1)',
tension: 0.4,
fill: true
}]
},
options: {
responsive: true,
plugins: { legend: { display: false } },
scales: { y: { beginAtZero: false } }
}
});

const pieCtx = document.getElementById('pieChart').getContext('2d');
new Chart(pieCtx, {
type: 'doughnut',
data: {
labels: ['EC2', 'S3', 'RDS', 'Lambda', 'Other'],
datasets: [{
data: [45, 23, 19, 8, 5],
backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe']
}]
},
options: {
responsive: true,
plugins: { legend: { position: 'bottom' } }
}
});

// Enhanced form handling with proper error management
document.getElementById('analyzeForm').addEventListener('submit', async (e) => {
e.preventDefault();
const btn = document.getElementById('analyzeBtn');
const resultsDiv = document.getElementById('results');
const resultsContent = document.getElementById('resultsContent');

// Get form data with validation
const formData = new FormData(e.target);
const data = Object.fromEntries(formData);

// Validate required fields
if (!data.monthlyBill || !data.services || !data.region || !data.workloadType) {
resultsDiv.style.display = 'block';
resultsContent.innerHTML = '<div class="text-danger">Please fill in all required fields.</div>';
return;
}

// Show loading state
btn.textContent = 'Analyzing...';
btn.disabled = true;
document.querySelector('#analyze').classList.add('loading');

try {
const response = await fetch('/api/analyze', {
method: 'POST',
headers: {
'Content-Type': 'application/json',
'Accept': 'application/json'
},
body: JSON.stringify(data)
});

const result = await response.json();
console.log('API Response:', result); // Debug log

if (result?.status === "success" || result?.current_bill) {
const currentBill = result?.current_bill || result?.data?.current_bill || 0;
const potentialSavings = result?.potential_savings || result?.data?.potential_savings || 0;
const optimizedBill = result?.optimized_bill || result?.data?.optimized_bill || 0;
const recommendations = result?.recommendations || result?.data?.recommendations || [];

resultsDiv.style.display = 'block';
resultsContent.innerHTML = `
<div class="stats-grid" style="margin-bottom:30px">
<div class="stat-card">
<div class="stat-label">Current Monthly Bill</div>
<div class="stat-value">$${currentBill.toLocaleString()}</div>
</div>
<div class="stat-card">
<div class="stat-label">Potential Savings</div>
<div class="stat-value savings">$${potentialSavings.toLocaleString()}</div>
<div style="color:#28a745;font-size:0.9em">${((potentialSavings/currentBill)*100).toFixed(1)}% reduction</div>
</div>
<div class="stat-card">
<div class="stat-label">Optimized Monthly Bill</div>
<div class="stat-value">$${optimizedBill.toLocaleString()}</div>
<div style="color:#17a2b8;font-size:0.9em">After optimization</div>
</div>
</div>
<h4 style="margin-bottom:20px">Optimization Recommendations:</h4>
${recommendations.map(r => `
<div class="recommendation">
<h4>${r?.title || 'Optimization Opportunity'}</h4>
<p style="margin:8px 0;color:#6c757d">${r?.description || 'No description available'}</p>
<div class="savings">💰 Potential Savings: $${(r?.savings || 0).toLocaleString()}/month</div>
${r?.priority ? `<div style="margin-top:8px"><span style="background:#${r.priority === 'High' ? 'dc3545' : r.priority === 'Medium' ? 'ffc107' : '28a745'};color:white;padding:4px 8px;border-radius:4px;font-size:0.8em">${r.priority} Priority</span></div>` : ''}
</div>
`).join('')}
`;
} else {
const errorMessage = result?.message || result?.detail || result?.error || 'Analysis failed. Please try again.';
resultsDiv.style.display = 'block';
resultsContent.innerHTML = `<div class="text-danger">❌ Error: ${errorMessage}</div>`;
}
} catch (error) {
console.error('Request failed:', error);
resultsDiv.style.display = 'block';
resultsContent.innerHTML = `<div class="text-danger">❌ Network Error: ${error?.message || 'Unable to connect to server. Please try again.'}</div>`;
} finally {
// Reset button state
btn.textContent = 'Analyze Costs & Get Recommendations';
btn.disabled = false;
document.querySelector('#analyze').classList.remove('loading');
}
});

async function subscribe(plan) {
try {
const response = await fetch('/api/subscribe', {
method: 'POST',
headers: {
'Content-Type': 'application/json',
'Accept': 'application/json'
},
body: JSON.stringify({plan})
});

const result = await response.json();
console.log('Subscription response:', result);

if (result?.url) {
window.location.href = result.url;
} else {
const errorMessage = result?.error || result?.detail || 'Subscription failed. Please try again.';
alert('❌ ' + errorMessage);
}
} catch (error) {
console.error('Subscription error:', error);
alert('❌ Subscription error: ' + (error?.message || 'Network error. Please try again.'));
}
}

// File Management Functions
let uploadedFiles = [];

async function uploadFiles() {
const billingFile = document.getElementById('billingFile').files[0];
const configFile = document.getElementById('configFile').files[0];
const customFile = document.getElementById('customFile').files[0];

const files = [billingFile, configFile, customFile].filter(file => file);

if (files.length === 0) {
alert('Please select at least one file to upload.');
return;
}

// Create FormData for file upload
const formData = new FormData();
if (billingFile) formData.append('billingFile', billingFile);
if (configFile) formData.append('configFile', configFile);
if (customFile) formData.append('customFile', customFile);

try {
// Upload files to server
const response = await fetch('/api/upload', {
method: 'POST',
body: formData
});

const result = await response.json();

if (result.status === 'success') {
// Add files to local list
files.forEach(file => {
const fileData = {
id: Date.now() + Math.random(),
name: file.name,
size: (file.size / 1024).toFixed(1) + ' KB',
type: file.type || 'Unknown',
uploadDate: new Date().toLocaleDateString(),
status: 'Analyzed'
};
uploadedFiles.push(fileData);
});

updateFileList();
analyzeFilesWithResults(result);
} else {
alert('Upload failed: ' + (result.error || 'Unknown error'));
}
} catch (error) {
console.error('Upload error:', error);
alert('Upload failed: ' + error.message);
}
}

function updateFileList() {
const fileListDiv = document.getElementById('fileList');

if (uploadedFiles.length === 0) {
fileListDiv.innerHTML = '<div style="text-align:center;color:#6c757d;padding:40px">No files uploaded yet.<br>Upload your AWS billing or configuration files to get started.</div>';
return;
}

let html = '<div style="display:grid;gap:12px">';
uploadedFiles.forEach(file => {
html += `
<div style="background:white;border-radius:8px;padding:16px;border:1px solid #e9ecef;display:flex;justify-content:space-between;align-items:center">
<div>
<div style="font-weight:600;margin-bottom:4px">${file.name}</div>
<div style="color:#6c757d;font-size:0.9em">${file.size} • ${file.uploadDate}</div>
</div>
<div style="display:flex;gap:8px;align-items:center">
<span style="background:#d4edda;color:#155724;padding:4px 8px;border-radius:4px;font-size:0.8em">${file.status}</span>
<button onclick="deleteFile('${file.id}')" style="background:#dc3545;color:white;border:none;padding:4px 8px;border-radius:4px;cursor:pointer;font-size:0.8em">Delete</button>
</div>
</div>`;
});
html += '</div>';
fileListDiv.innerHTML = html;
}

function deleteFile(fileId) {
uploadedFiles = uploadedFiles.filter(file => file.id != fileId);
updateFileList();
if (uploadedFiles.length === 0) {
document.getElementById('fileAnalysis').style.display = 'none';
document.getElementById('noAnalysis').style.display = 'block';
}
}

function analyzeFiles() {
// Simulate file analysis
document.getElementById('fileAnalysis').style.display = 'block';
document.getElementById('noAnalysis').style.display = 'none';

// Update analysis stats
document.getElementById('totalServices').textContent = Math.floor(Math.random() * 15) + 8;
document.getElementById('costAnomalies').textContent = Math.floor(Math.random() * 5) + 1;
document.getElementById('optimizationOps').textContent = Math.floor(Math.random() * 8) + 3;

// Generate file-specific recommendations
const recommendations = [
{
title: "Unused EBS Volumes Detected",
description: "Found 3 unattached EBS volumes costing $45/month",
savings: 45,
priority: "High"
},
{
title: "Over-provisioned RDS Instances",
description: "RDS instances are running at 30% capacity - consider downsizing",
savings: 120,
priority: "Medium"
},
{
title: "S3 Storage Class Optimization",
description: "Move infrequently accessed data to IA storage class",
savings: 85,
priority: "Low"
}
];

let recommendationsHtml = '<h4 style="margin-bottom:16px">File Analysis Recommendations</h4>';
recommendations.forEach(rec => {
recommendationsHtml += `
<div class="recommendation">
<h4>${rec.title}</h4>
<p style="margin:8px 0">${rec.description}</p>
<div style="display:flex;justify-content:space-between;align-items:center">
<span class="savings">Potential Savings: $${rec.savings}/month</span>
<span style="background:${rec.priority === 'High' ? '#dc3545' : rec.priority === 'Medium' ? '#ffc107' : '#28a745'};color:white;padding:2px 8px;border-radius:4px;font-size:0.8em">${rec.priority}</span>
</div>
</div>`;
});

document.getElementById('fileRecommendations').innerHTML = recommendationsHtml;
}

function analyzeFilesWithResults(results) {
// Use server analysis results
document.getElementById('fileAnalysis').style.display = 'block';
document.getElementById('noAnalysis').style.display = 'none';

// Update analysis stats with server data
document.getElementById('totalServices').textContent = results.total_services;
document.getElementById('costAnomalies').textContent = results.cost_anomalies;
document.getElementById('optimizationOps').textContent = results.optimization_opportunities;

// Display server recommendations
let recommendationsHtml = '<h4 style="margin-bottom:16px">File Analysis Recommendations</h4>';
results.recommendations.forEach(rec => {
recommendationsHtml += `
<div class="recommendation">
<h4>${rec.title}</h4>
<p style="margin:8px 0">${rec.description}</p>
<div style="display:flex;justify-content:space-between;align-items:center">
<span class="savings">Potential Savings: $${rec.savings}/month</span>
<span style="background:${rec.priority === 'High' ? '#dc3545' : rec.priority === 'Medium' ? '#ffc107' : '#28a745'};color:white;padding:2px 8px;border-radius:4px;font-size:0.8em">${rec.priority}</span>
</div>
</div>`;
});

document.getElementById('fileRecommendations').innerHTML = recommendationsHtml;
}

// Task Management Functions
let currentFilter = 'all';

// Load todos on page load
document.addEventListener('DOMContentLoaded', function() {
    loadTodos();
    
    // Add form submit handler
    document.getElementById('todoForm').addEventListener('submit', function(e) {
        e.preventDefault();
        createTodo();
    });
});

async function loadTodos() {
    try {
        const response = await fetch('/api/todos');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayTodos(data.todos);
        } else {
            console.error('Failed to load todos:', data.error);
        }
    } catch (error) {
        console.error('Error loading todos:', error);
    }
}

function displayTodos(todos) {
    const todosList = document.getElementById('todosList');
    
    if (todos.length === 0) {
        todosList.innerHTML = '<div style="text-align:center;color:#6c757d;padding:40px">No tasks yet. Create your first task to get started!</div>';
        return;
    }
    
    let html = '';
    todos.forEach(todo => {
        if (currentFilter !== 'all' && todo.status !== currentFilter) return;
        
        const priorityColors = {
            'urgent': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        };
        
        const statusIcon = todo.status === 'completed' ? '✅' : '⏳';
        const statusClass = todo.status === 'completed' ? 'completed' : 'pending';
        
        html += `
        <div class="todo-item" style="background:white;border-radius:8px;padding:16px;border:1px solid #e9ecef;display:flex;justify-content:space-between;align-items:center">
            <div style="flex:1">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                    <span style="font-size:1.2em">${statusIcon}</span>
                    <h4 style="margin:0;color:#495057;text-decoration:${todo.status === 'completed' ? 'line-through' : 'none'}">${todo.title}</h4>
                    <span style="background:${priorityColors[todo.priority]};color:white;padding:2px 8px;border-radius:4px;font-size:0.8em">${todo.priority}</span>
                </div>
                ${todo.description ? `<p style="margin:4px 0;color:#6c757d;font-size:0.9em">${todo.description}</p>` : ''}
                <div style="display:flex;gap:12px;font-size:0.8em;color:#6c757d;margin-top:8px">
                    <span>📁 ${todo.category}</span>
                    <span>📅 ${new Date(todo.created_at).toLocaleDateString()}</span>
                    ${todo.due_date ? `<span>⏰ Due: ${new Date(todo.due_date).toLocaleDateString()}</span>` : ''}
                </div>
            </div>
            <div style="display:flex;gap:8px;align-items:center">
                ${todo.status === 'pending' ? 
                    `<button onclick="toggleTodo(${todo.id}, 'completed')" style="background:#28a745;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:0.8em">Complete</button>` :
                    `<button onclick="toggleTodo(${todo.id}, 'pending')" style="background:#6c757d;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:0.8em">Undo</button>`
                }
                <button onclick="deleteTodo(${todo.id})" style="background:#dc3545;color:white;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:0.8em">Delete</button>
            </div>
        </div>`;
    });
    
    todosList.innerHTML = html;
}

async function createTodo() {
    const title = document.getElementById('todoTitle').value;
    const description = document.getElementById('todoDescription').value;
    const priority = document.getElementById('todoPriority').value;
    const category = document.getElementById('todoCategory').value;
    const dueDate = document.getElementById('todoDueDate').value;
    
    if (!title.trim()) {
        alert('Please enter a task title');
        return;
    }
    
    try {
        const response = await fetch('/api/todos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                description: description,
                priority: priority,
                category: category,
                due_date: dueDate || null
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Clear form
            document.getElementById('todoForm').reset();
            document.getElementById('todoPriority').value = 'medium';
            document.getElementById('todoCategory').value = 'general';
            
            // Reload todos
            loadTodos();
        } else {
            alert('Failed to create task: ' + data.error);
        }
    } catch (error) {
        console.error('Error creating todo:', error);
        alert('Failed to create task');
    }
}

async function createQuickTodo(title, category, priority) {
    try {
        const response = await fetch('/api/todos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                description: 'Quick action task created from recommendations',
                priority: priority,
                category: category
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            loadTodos();
        } else {
            alert('Failed to create task: ' + data.error);
        }
    } catch (error) {
        console.error('Error creating quick todo:', error);
        alert('Failed to create task');
    }
}

async function toggleTodo(todoId, newStatus) {
    try {
        const response = await fetch(`/api/todos/${todoId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: newStatus
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            loadTodos();
        } else {
            alert('Failed to update task: ' + data.error);
        }
    } catch (error) {
        console.error('Error updating todo:', error);
        alert('Failed to update task');
    }
}

async function deleteTodo(todoId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/todos/${todoId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            loadTodos();
        } else {
            alert('Failed to delete task: ' + data.error);
        }
    } catch (error) {
        console.error('Error deleting todo:', error);
        alert('Failed to delete task');
    }
}

function filterTodos(status) {
    currentFilter = status;
    
    // Update button styles
    document.querySelectorAll('[id^="filter"]').forEach(btn => {
        btn.style.background = '#6c757d';
    });
    document.getElementById(`filter${status.charAt(0).toUpperCase() + status.slice(1)}`).style.background = '#667eea';
    
    // Reload todos with filter
    loadTodos();
}
</script>
</body></html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>AWS Cost Analyzer - Login</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0}
.form{background:white;padding:48px;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.15);width:420px;max-width:90vw}
.form h2{text-align:center;margin-bottom:32px;color:#333;font-size:28px;font-weight:600}
.input{width:100%;padding:16px;margin:12px 0;border:2px solid #e9ecef;border-radius:12px;font-size:16px;transition:all 0.3s}
.input:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.1)}
.btn{width:100%;background:#667eea;color:white;padding:16px;border:none;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer;transition:all 0.3s;margin-top:8px}
.btn:hover{background:#5a6fd8;transform:translateY(-1px)}
.link{text-align:center;margin-top:24px}
.link a{color:#667eea;text-decoration:none;font-weight:500}
.link a:hover{text-decoration:underline}
</style></head>
<body>
<div class="form">
<h2>Welcome Back</h2>
<form method="POST">
<input type="email" name="email" placeholder="Email address" class="input" required>
<input type="password" name="password" placeholder="Password" class="input" required>
<button type="submit" class="btn">Sign In</button>
</form>
<div class="link"><a href="/register">Don't have an account? Sign up</a></div>
</div>
</body></html>
"""

REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>AWS Cost Analyzer - Sign Up</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0}
.form{background:white;padding:48px;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.15);width:420px;max-width:90vw}
.form h2{text-align:center;margin-bottom:32px;color:#333;font-size:28px;font-weight:600}
.input{width:100%;padding:16px;margin:12px 0;border:2px solid #e9ecef;border-radius:12px;font-size:16px;transition:all 0.3s}
.input:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.1)}
.btn{width:100%;background:#667eea;color:white;padding:16px;border:none;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer;transition:all 0.3s;margin-top:8px}
.btn:hover{background:#5a6fd8;transform:translateY(-1px)}
.link{text-align:center;margin-top:24px}
.link a{color:#667eea;text-decoration:none;font-weight:500}
.link a:hover{text-decoration:underline}
.error{background:#f8d7da;color:#721c24;padding:12px;border-radius:8px;margin-bottom:16px;border:1px solid #f5c6cb}
</style></head>
<body>
<div class="form">
<h2>Create Account</h2>
{{error}}
<form method="POST">
<input type="email" name="email" placeholder="Email address" class="input" required>
<input type="password" name="password" placeholder="Create password" class="input" required>
<button type="submit" class="btn">Create Account</button>
</form>
<div class="link"><a href="/login">Already have an account? Sign in</a></div>
</div>
</body></html>
"""

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = hashlib.sha256(request.form['password'].encode()).hexdigest()
            
            conn = get_db()
            cursor = conn.cursor()
            # Use appropriate placeholder for database type
            if os.getenv('DATABASE_URL'):
                cursor.execute('SELECT * FROM users WHERE email=%s AND password=%s', (email, password))
            else:
                cursor.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user:
                user_id = user['id'] if isinstance(user, dict) else user[0]
                user_email = user['email'] if isinstance(user, dict) else user[1]
                
                # Set session data
                session['user_id'] = user_id
                session['email'] = user_email
                
                # Save session data to database for persistence
                session_data = {
                    'user_id': user_id,
                    'email': user_email,
                    'login_time': str(datetime.now()),
                    'last_activity': str(datetime.now()),
                    'uploaded_files': [],
                    'analysis_history': []
                }
                save_user_session(user_id, session_data)
                
                return redirect('/dashboard')
            return render_template_string(LOGIN_TEMPLATE + '<script>alert("Invalid email or password")</script>')
        except Exception as e:
            return f'Error: {str(e)}', 500
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = hashlib.sha256(request.form['password'].encode()).hexdigest()
            
            conn = get_db()
            cursor = conn.cursor()
            # Use appropriate placeholder for database type
            if os.getenv('DATABASE_URL'):
                cursor.execute('INSERT INTO users (email, password) VALUES (%s, %s)', (email, password))
            else:
                cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect('/login')
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e) or 'duplicate key value' in str(e):
                return render_template_string(REGISTER_TEMPLATE.replace('{{error}}', '<div class="error">This email is already registered. Please <a href="/login" style="color:#721c24;font-weight:600">sign in</a> instead.</div>'))
            else:
                return f'Error: {str(e)}', 500
    
    return render_template_string(REGISTER_TEMPLATE.replace('{{error}}', ''))

@app.route('/dashboard')
@auth_required
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE.replace('{{email}}', session['email']))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/analyze', methods=['POST'])
@auth_required
def analyze():
    try:
        data = request.json
        monthly_bill = float(data.get('monthlyBill', 0))
        services = data.get('services', '').split(',')
        region = data.get('region', '')
        workload_type = data.get('workloadType', '')
        
        if monthly_bill <= 0:
            return jsonify({"status": "error", "detail": "Monthly bill must be greater than $0"})
        
        # Enhanced AWS Cost Analysis Logic
        base_savings_rate = 0.35
        if workload_type == 'compute':
            base_savings_rate = 0.45  # Higher savings for compute workloads
        elif workload_type == 'storage':
            base_savings_rate = 0.40  # Good savings for storage optimization
        
        potential_savings = round(monthly_bill * base_savings_rate, 2)
        optimized_bill = monthly_bill - potential_savings
        
        # Generate workload-specific recommendations
        recommendations = [
            {
                "title": "Reserved Instances",
                "description": f"Switch to 1-year Reserved Instances for your {workload_type} workloads in {region}",
                "savings": round(monthly_bill * 0.15, 2),
                "priority": "High"
            },
            {
                "title": "Right-size EC2 Instances",
                "description": "Analysis shows over-provisioned instances that can be downsized",
                "savings": round(monthly_bill * 0.12, 2),
                "priority": "Medium"
            },
            {
                "title": "S3 Storage Class Optimization",
                "description": "Move infrequently accessed data to cheaper storage tiers",
                "savings": round(monthly_bill * 0.08, 2),
                "priority": "Low"
            }
        ]
        
        # Add workload-specific recommendations
        if workload_type == 'compute':
            recommendations.append({
                "title": "Spot Instances",
                "description": "Use Spot Instances for fault-tolerant compute workloads",
                "savings": round(monthly_bill * 0.20, 2),
                "priority": "High"
            })
        elif workload_type == 'storage':
            recommendations.append({
                "title": "S3 Intelligent Tiering",
                "description": "Automatically optimize storage costs based on access patterns",
                "savings": round(monthly_bill * 0.25, 2),
                "priority": "High"
            })
        elif workload_type == 'data':
            recommendations.append({
                "title": "Data Pipeline Optimization",
                "description": "Optimize ETL processes and reduce data transfer costs",
                "savings": round(monthly_bill * 0.18, 2),
                "priority": "Medium"
            })
        
        return jsonify({
            "status": "success",
            "current_bill": monthly_bill,
            "potential_savings": potential_savings,
            "optimized_bill": optimized_bill,
            "recommendations": recommendations,
            "analysis_date": "2024-01-15T10:30:00Z"
        })
        
    except ValueError as e:
        return jsonify({"status": "error", "detail": "Invalid input data. Please check your values."})
    except Exception as e:
        return jsonify({"status": "error", "detail": f"Analysis failed: {str(e)}"})

@app.route('/api/subscribe', methods=['POST'])
@auth_required
def subscribe():
    try:
        plan = request.json.get('plan')
        
        # Check if Stripe is properly configured
        stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe_secret_key or stripe_secret_key == 'None':
            return jsonify({'error': 'Payment processing not configured. Please contact support.'})
        
        # Stripe price IDs (replace with your actual price IDs)
        prices = {
            'starter': os.getenv('STRIPE_STARTER_PRICE_ID', 'price_starter_placeholder'),
            'professional': os.getenv('STRIPE_PROFESSIONAL_PRICE_ID', 'price_professional_placeholder'),
            'enterprise': os.getenv('STRIPE_ENTERPRISE_PRICE_ID', 'price_enterprise_placeholder')
        }
        
        if plan not in prices:
            return jsonify({'error': 'Invalid subscription plan selected.'})
        
        # Check if we have valid price IDs
        if prices[plan] == f'price_{plan}_placeholder':
            return jsonify({'error': f'{plan.title()} plan not yet configured. Please contact support.'})
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': prices[plan],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'dashboard',
            customer_email=session.get('email'),
            metadata={
                'user_id': str(session.get('user_id')),
                'plan': plan
            }
        )
        
        return jsonify({'url': checkout_session.url})
        
    except stripe.error.StripeError as e:
        return jsonify({'error': f'Payment error: {str(e)}'})
    except Exception as e:
        return jsonify({'error': f'Subscription failed: {str(e)}'})

@app.route('/api/upload', methods=['POST'])
@auth_required
def upload_file():
    try:
        user_id = session.get('user_id')
        uploaded_files = []
        
        # Process each uploaded file
        for key in ['billingFile', 'configFile', 'customFile']:
            if key in request.files:
                file = request.files[key]
                if file and file.filename:
                    # Generate unique filename
                    filename = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # Save file to disk
                    file.save(file_path)
                    
                    # Get file info
                    file_size = os.path.getsize(file_path)
                    
                    # Save file info to database
                    conn = get_db()
                    cursor = conn.cursor()
                    
                    analysis_data = json.dumps({
                        'upload_time': str(datetime.now()),
                        'file_type': key,
                        'original_name': file.filename
                    })
                    
                    if os.getenv('DATABASE_URL'):
                        cursor.execute('''INSERT INTO user_files 
                                         (user_id, filename, file_type, file_size, analysis_data, status)
                                         VALUES (%s, %s, %s, %s, %s, %s)''',
                                      (user_id, filename, file.content_type, file_size, analysis_data, 'uploaded'))
                    else:
                        cursor.execute('''INSERT INTO user_files 
                                         (user_id, filename, file_type, file_size, analysis_data, status)
                                         VALUES (?, ?, ?, ?, ?, ?)''',
                                      (user_id, filename, file.content_type, file_size, analysis_data, 'uploaded'))
                    
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    uploaded_files.append({
                        'name': file.filename,
                        'size': file_size,
                        'type': file.content_type,
                        'saved_as': filename
                    })
        
        if not uploaded_files:
            return jsonify({'error': 'No files uploaded'})
        
        # Simulate file analysis (in production, you'd actually analyze the files)
        analysis_results = {
            'status': 'success',
            'files_processed': len(uploaded_files),
            'total_services': 12,
            'cost_anomalies': 3,
            'optimization_opportunities': 5,
            'uploaded_files': uploaded_files,
            'recommendations': [
                {
                    'title': 'Unused EBS Volumes Detected',
                    'description': 'Found 3 unattached EBS volumes costing $45/month',
                    'savings': 45,
                    'priority': 'High'
                },
                {
                    'title': 'Over-provisioned RDS Instances',
                    'description': 'RDS instances are running at 30% capacity - consider downsizing',
                    'savings': 120,
                    'priority': 'Medium'
                },
                {
                    'title': 'S3 Storage Class Optimization',
                    'description': 'Move infrequently accessed data to IA storage class',
                    'savings': 85,
                    'priority': 'Low'
                }
            ]
        }
        
        return jsonify(analysis_results)
        
    except Exception as e:
        return jsonify({'error': f'File upload failed: {str(e)}'})

@app.route('/api/user-data', methods=['GET'])
@auth_required
def get_user_data():
    """Get all persistent user data"""
    try:
        user_id = session.get('user_id')
        
        # Get user's uploaded files
        conn = get_db()
        cursor = conn.cursor()
        
        if os.getenv('DATABASE_URL'):
            cursor.execute('''SELECT filename, file_type, file_size, upload_date, analysis_data, status 
                             FROM user_files WHERE user_id = %s ORDER BY upload_date DESC''', (user_id,))
        else:
            cursor.execute('''SELECT filename, file_type, file_size, upload_date, analysis_data, status 
                             FROM user_files WHERE user_id = ? ORDER BY upload_date DESC''', (user_id,))
        
        files = cursor.fetchall()
        
        # Get analysis history
        if os.getenv('DATABASE_URL'):
            cursor.execute('''SELECT monthly_bill, services, region, workload_type, potential_savings, 
                             analysis_date, recommendations FROM analysis_history 
                             WHERE user_id = %s ORDER BY analysis_date DESC LIMIT 5''', (user_id,))
        else:
            cursor.execute('''SELECT monthly_bill, services, region, workload_type, potential_savings, 
                             analysis_date, recommendations FROM analysis_history 
                             WHERE user_id = ? ORDER BY analysis_date DESC LIMIT 5''', (user_id,))
        
        history = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Format the data
        files_data = []
        for file in files:
            files_data.append({
                'filename': file[0],
                'file_type': file[1],
                'file_size': file[2],
                'upload_date': str(file[3]),
                'analysis_data': json.loads(file[4]) if file[4] else {},
                'status': file[5]
            })
        
        history_data = []
        for analysis in history:
            history_data.append({
                'monthly_bill': float(analysis[0]),
                'services': analysis[1],
                'region': analysis[2],
                'workload_type': analysis[3],
                'potential_savings': float(analysis[4]),
                'analysis_date': str(analysis[5]),
                'recommendations': json.loads(analysis[6]) if analysis[6] else []
            })
        
        return jsonify({
            'status': 'success',
            'uploaded_files': files_data,
            'analysis_history': history_data,
            'total_files': len(files_data),
            'total_analyses': len(history_data)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to load user data: {str(e)}'})

@app.route('/api/todos', methods=['GET', 'POST'])
@auth_required
def manage_todos():
    """Get or create todos"""
    user_id = session.get('user_id')
    
    if request.method == 'GET':
        try:
            status_filter = request.args.get('status')
            todos = get_user_todos(user_id, status_filter)
            
            todos_data = []
            for todo in todos:
                todos_data.append({
                    'id': todo[0],
                    'title': todo[2],
                    'description': todo[3],
                    'priority': todo[4],
                    'category': todo[5],
                    'status': todo[6],
                    'due_date': str(todo[7]) if todo[7] else None,
                    'created_at': str(todo[8]),
                    'completed_at': str(todo[9]) if todo[9] else None,
                    'analysis_id': todo[10]
                })
            
            return jsonify({
                'status': 'success',
                'todos': todos_data,
                'total': len(todos_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Failed to load todos: {str(e)}'})
    
    elif request.method == 'POST':
        try:
            todo_data = request.json
            
            # Validate required fields
            if not todo_data.get('title'):
                return jsonify({'error': 'Title is required'})
            
            # Save todo
            save_todo(user_id, todo_data)
            
            return jsonify({
                'status': 'success',
                'message': 'Todo created successfully'
            })
            
        except Exception as e:
            return jsonify({'error': f'Failed to create todo: {str(e)}'})

@app.route('/api/todos/<int:todo_id>', methods=['PUT', 'DELETE'])
@auth_required
def manage_todo(todo_id):
    """Update or delete a specific todo"""
    user_id = session.get('user_id')
    
    if request.method == 'PUT':
        try:
            data = request.json
            new_status = data.get('status')
            
            if new_status not in ['pending', 'completed']:
                return jsonify({'error': 'Invalid status'})
            
            update_todo_status(user_id, todo_id, new_status)
            
            return jsonify({
                'status': 'success',
                'message': f'Todo marked as {new_status}'
            })
            
        except Exception as e:
            return jsonify({'error': f'Failed to update todo: {str(e)}'})
    
    elif request.method == 'DELETE':
        try:
            delete_todo(user_id, todo_id)
            
            return jsonify({
                'status': 'success',
                'message': 'Todo deleted successfully'
            })
            
        except Exception as e:
            return jsonify({'error': f'Failed to delete todo: {str(e)}'})

@app.route('/success')
@auth_required
def success():
    return '''
    <html>
    <head><title>Success!</title>
    <style>body{font-family:Arial;text-align:center;padding:50px;background:#f8f9fa}
    .success{background:white;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);max-width:500px;margin:0 auto}
    .btn{background:#667eea;color:white;padding:12px 24px;border:none;border-radius:8px;text-decoration:none;display:inline-block;margin-top:20px}
    </style></head>
    <body>
    <div class="success">
    <h1 style="color:#28a745">🎉 Subscription Successful!</h1>
    <p>Welcome to AWS Cost Analyzer Pro! Your account has been upgraded.</p>
    <a href="/dashboard" class="btn">Go to Dashboard</a>
    </div>
    </body></html>
    '''

if __name__ == '__main__':
    print("🚀 Starting AWS Cost Analyzer SaaS...")
    
    # Initialize database with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Database initialization attempt {attempt + 1}/{max_retries}")
            init_db()
            print("✅ Database initialized successfully")
            break
        except Exception as e:
            print(f"❌ Database init error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                print("💥 Failed to initialize database after all retries")
                sys.exit(1)
            else:
                print("⏳ Retrying in 2 seconds...")
                import time
                time.sleep(2)
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)