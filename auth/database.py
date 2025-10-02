#!/usr/bin/env python3
"""
Database Manager for AWS Cost SaaS
Handles user management, cost analyses, and subscription data
"""

import asyncpg
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from models import User, CostAnalysis, SubscriptionPlan

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://localhost/aws_cost_saas")
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            await self.create_tables()
        except Exception as e:
            raise Exception(f"Database initialization failed: {str(e)}")
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            async with self.pool.acquire() as conn:
                # Users table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        hashed_password VARCHAR(255) NOT NULL,
                        subscription_plan VARCHAR(50) DEFAULT 'starter',
                        subscription_status VARCHAR(50) DEFAULT 'inactive',
                        stripe_customer_id VARCHAR(255),
                        role VARCHAR(50) DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_analysis TIMESTAMP
                    )
                """)
                
                # Cost analyses table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS cost_analyses (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        analysis_data JSONB NOT NULL,
                        file_name VARCHAR(255),
                        file_type VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Subscriptions table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS subscriptions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        stripe_subscription_id VARCHAR(255) UNIQUE,
                        plan_id VARCHAR(50) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        current_period_start TIMESTAMP,
                        current_period_end TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON cost_analyses(user_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)")
                
        except Exception as e:
            raise Exception(f"Table creation failed: {str(e)}")
    
    async def create_user(self, user_data) -> User:
        """Create a new user"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO users (email, name, hashed_password)
                    VALUES ($1, $2, $3)
                    RETURNING id, email, name, subscription_plan, subscription_status,
                             stripe_customer_id, role, created_at, updated_at, last_analysis
                """
                row = await conn.fetchrow(
                    query,
                    user_data.email,
                    user_data.name,
                    user_data.hashed_password
                )
                
                return User(
                    id=row['id'],
                    email=row['email'],
                    name=row['name'],
                    hashed_password=row['hashed_password'],
                    subscription_plan=row['subscription_plan'],
                    subscription_status=row['subscription_status'],
                    stripe_customer_id=row['stripe_customer_id'],
                    role=row['role'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_analysis=row['last_analysis']
                )
        except Exception as e:
            raise Exception(f"User creation failed: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT id, email, name, hashed_password, subscription_plan,
                           subscription_status, stripe_customer_id, role,
                           created_at, updated_at, last_analysis
                    FROM users WHERE email = $1
                """
                row = await conn.fetchrow(query, email)
                
                if row:
                    return User(
                        id=row['id'],
                        email=row['email'],
                        name=row['name'],
                        hashed_password=row['hashed_password'],
                        subscription_plan=row['subscription_plan'],
                        subscription_status=row['subscription_status'],
                        stripe_customer_id=row['stripe_customer_id'],
                        role=row['role'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        last_analysis=row['last_analysis']
                    )
                return None
        except Exception as e:
            raise Exception(f"User lookup failed: {str(e)}")
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT id, email, name, hashed_password, subscription_plan,
                           subscription_status, stripe_customer_id, role,
                           created_at, updated_at, last_analysis
                    FROM users WHERE id = $1
                """
                row = await conn.fetchrow(query, user_id)
                
                if row:
                    return User(
                        id=row['id'],
                        email=row['email'],
                        name=row['name'],
                        hashed_password=row['hashed_password'],
                        subscription_plan=row['subscription_plan'],
                        subscription_status=row['subscription_status'],
                        stripe_customer_id=row['stripe_customer_id'],
                        role=row['role'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        last_analysis=row['last_analysis']
                    )
                return None
        except Exception as e:
            raise Exception(f"User lookup failed: {str(e)}")
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = await self.get_user_by_email(email)
            if user:
                # Password verification will be done in the JWT handler
                return user
            return None
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    async def save_analysis(self, user_id: int, analysis_data: Dict[str, Any]) -> int:
        """Save cost analysis to database"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO cost_analyses (user_id, analysis_data, file_name, file_type)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                """
                analysis_id = await conn.fetchval(
                    query,
                    user_id,
                    json.dumps(analysis_data),
                    analysis_data.get('file_name'),
                    analysis_data.get('file_type')
                )
                
                # Update user's last analysis timestamp
                await conn.execute(
                    "UPDATE users SET last_analysis = CURRENT_TIMESTAMP WHERE id = $1",
                    user_id
                )
                
                return analysis_id
        except Exception as e:
            raise Exception(f"Analysis save failed: {str(e)}")
    
    async def get_user_analyses(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's cost analyses"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT id, analysis_data, file_name, file_type, created_at
                    FROM cost_analyses
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                """
                rows = await conn.fetch(query, user_id, limit, offset)
                
                analyses = []
                for row in rows:
                    analyses.append({
                        'id': row['id'],
                        'analysis_data': row['analysis_data'],
                        'file_name': row['file_name'],
                        'file_type': row['file_type'],
                        'created_at': row['created_at'].isoformat()
                    })
                
                return analyses
        except Exception as e:
            raise Exception(f"Analyses retrieval failed: {str(e)}")
    
    async def update_subscription_status(self, user_id: int, status: str):
        """Update user's subscription status"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE users SET subscription_status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                    status, user_id
                )
        except Exception as e:
            raise Exception(f"Subscription update failed: {str(e)}")
    
    async def update_stripe_customer_id(self, user_id: int, customer_id: str):
        """Update user's Stripe customer ID"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE users SET stripe_customer_id = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                    customer_id, user_id
                )
        except Exception as e:
            raise Exception(f"Stripe customer ID update failed: {str(e)}")
    
    async def get_admin_stats(self) -> Dict[str, Any]:
        """Get admin statistics"""
        try:
            async with self.pool.acquire() as conn:
                # Total users
                total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
                
                # Active subscriptions
                active_subscriptions = await conn.fetchval(
                    "SELECT COUNT(*) FROM users WHERE subscription_status = 'active'"
                )
                
                # Total analyses
                total_analyses = await conn.fetchval("SELECT COUNT(*) FROM cost_analyses")
                
                # Average savings (simulated)
                avg_savings = 1250.50  # This would be calculated from actual data
                
                return {
                    'total_users': total_users,
                    'active_subscriptions': active_subscriptions,
                    'total_analyses': total_analyses,
                    'average_savings': avg_savings
                }
        except Exception as e:
            raise Exception(f"Admin stats retrieval failed: {str(e)}")
