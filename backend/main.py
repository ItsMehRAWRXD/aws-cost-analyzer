#!/usr/bin/env python3
"""
AWS Cost SaaS - FastAPI Backend
Complete turnkey SaaS system for AWS cost analysis and optimization
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import asyncio
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Import our modules
from billing_parser import EnhancedBillingParser
from auth.jwt_handler import JWTHandler
from auth.database import DatabaseManager
from stripe.payment_handler import StripeHandler
from models import (
    UserCreate, UserLogin, UserResponse, 
    CostAnalysisRequest, CostAnalysisResponse,
    SubscriptionPlan, PaymentIntent
)

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.db = DatabaseManager()
    app.state.jwt_handler = JWTHandler()
    app.state.billing_parser = EnhancedBillingParser()
    app.state.stripe_handler = StripeHandler()
    
    # Initialize database
    await app.state.db.initialize()
    
    yield
    
    # Shutdown
    await app.state.db.close()

app = FastAPI(
    title="AWS Cost SaaS API",
    description="Complete SaaS platform for AWS cost analysis and optimization",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        user_data = app.state.jwt_handler.verify_token(token)
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0")
    }

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await app.state.db.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create user
        user = await app.state.db.create_user(user_data)
        
        # Generate JWT token
        token = app.state.jwt_handler.create_token(user.id, user.email)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            subscription_plan=user.subscription_plan,
            token=token
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/auth/login", response_model=UserResponse)
async def login_user(login_data: UserLogin):
    """Login user"""
    try:
        user = await app.state.db.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate JWT token
        token = app.state.jwt_handler.create_token(user.id, user.email)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            subscription_plan=user.subscription_plan,
            token=token
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

# Cost analysis endpoints
@app.post("/api/analyze", response_model=CostAnalysisResponse)
async def analyze_costs(
    request: CostAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze AWS costs and provide optimization recommendations"""
    try:
        # Check user subscription
        user = await app.state.db.get_user_by_id(current_user["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Perform cost analysis
        analysis = await app.state.billing_parser.analyze_costs(
            monthly_bill=request.monthly_bill,
            services=request.services,
            region=request.region,
            workload_type=request.workload_type,
            user_plan=user.subscription_plan
        )
        
        # Save analysis to database
        await app.state.db.save_analysis(user.id, analysis)
        
        return CostAnalysisResponse(**analysis)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/api/upload-billing")
async def upload_billing_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and analyze billing file"""
    try:
        # Validate file type
        if not file.filename.endswith(('.json', '.csv', '.xlsx')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JSON, CSV, and Excel files are supported"
            )
        
        # Read file content
        content = await file.read()
        
        # Parse billing data
        analysis = await app.state.billing_parser.parse_billing_file(
            content, file.filename
        )
        
        # Save analysis to database
        await app.state.db.save_analysis(current_user["user_id"], analysis)
        
        return {
            "message": "File uploaded and analyzed successfully",
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )

# Subscription and payment endpoints
@app.get("/api/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return [
        {
            "id": "starter",
            "name": "Starter",
            "price": 29,
            "currency": "usd",
            "interval": "month",
            "features": [
                "Monthly cost analysis",
                "Basic recommendations",
                "Email support",
                "Up to 5 AWS accounts"
            ]
        },
        {
            "id": "professional",
            "name": "Professional", 
            "price": 99,
            "currency": "usd",
            "interval": "month",
            "features": [
                "Real-time monitoring",
                "Advanced optimization",
                "Custom alerts",
                "Priority support",
                "Up to 20 AWS accounts"
            ]
        },
        {
            "id": "enterprise",
            "name": "Enterprise",
            "price": 299,
            "currency": "usd", 
            "interval": "month",
            "features": [
                "Unlimited AWS accounts",
                "Custom integrations",
                "Dedicated support",
                "Advanced reporting",
                "API access"
            ]
        }
    ]

@app.post("/api/subscription/create-payment-intent")
async def create_payment_intent(
    plan_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Create Stripe payment intent for subscription"""
    try:
        payment_intent = await app.state.stripe_handler.create_subscription(
            user_id=current_user["user_id"],
            plan_id=plan_id
        )
        
        return {
            "client_secret": payment_intent.client_secret,
            "payment_intent_id": payment_intent.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment intent creation failed: {str(e)}"
        )

@app.post("/api/subscription/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        event = app.state.stripe_handler.verify_webhook(payload, sig_header)
        
        # Handle different event types
        if event['type'] == 'payment_intent.succeeded':
            await app.state.db.update_subscription_status(
                event['data']['object']['metadata']['user_id'],
                'active'
            )
        elif event['type'] == 'customer.subscription.deleted':
            await app.state.db.update_subscription_status(
                event['data']['object']['metadata']['user_id'],
                'cancelled'
            )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}"
        )

# User profile endpoints
@app.get("/api/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    user = await app.state.db.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "subscription_plan": user.subscription_plan,
        "created_at": user.created_at.isoformat(),
        "last_analysis": user.last_analysis.isoformat() if user.last_analysis else None
    }

@app.get("/api/user/analyses")
async def get_user_analyses(
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get user's cost analyses"""
    analyses = await app.state.db.get_user_analyses(
        current_user["user_id"], limit, offset
    )
    return analyses

# Admin endpoints (for monitoring)
@app.get("/api/admin/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
    """Get admin statistics (requires admin role)"""
    # Check if user is admin
    user = await app.state.db.get_user_by_id(current_user["user_id"])
    if not user or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    stats = await app.state.db.get_admin_stats()
    return stats

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )
