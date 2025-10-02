#!/bin/bash

# AWS Cost SaaS - Quick Start Script
# This script sets up and runs the complete SaaS application

echo "🚀 AWS Cost SaaS - Quick Start"
echo "================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📋 Copying env.template to .env..."
    cp env.template .env
    echo "✅ Please edit .env with your actual values before continuing"
    echo "🔧 Required: DATABASE_URL, JWT_SECRET_KEY, STRIPE keys, AWS credentials"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if PostgreSQL is running
echo "🗄️  Checking database connection..."
if ! pg_isready -q; then
    echo "⚠️  PostgreSQL is not running!"
    echo "💡 Start PostgreSQL or use Docker:"
    echo "   docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15"
    echo ""
    read -p "Press Enter after starting PostgreSQL..."
fi

# Create database if it doesn't exist
echo "🗄️  Setting up database..."
DB_NAME=$(grep DATABASE_URL .env | cut -d'/' -f4)
if [ -z "$DB_NAME" ]; then
    DB_NAME="aws_cost_saas"
fi

createdb $DB_NAME 2>/dev/null || echo "Database $DB_NAME already exists"

# Start the application
echo "🚀 Starting AWS Cost SaaS..."
echo "📱 Frontend: http://localhost:8000"
echo "🔧 API Docs: http://localhost:8000/docs"
echo "❤️  Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python main.py
