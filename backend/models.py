#!/usr/bin/env python3
"""
Pydantic models for AWS Cost SaaS API
"""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SubscriptionPlan(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class WorkloadType(str, Enum):
    WEB = "web"
    DATA = "data"
    ML = "ml"
    STORAGE = "storage"
    COMPUTE = "compute"

class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class ImplementationEffort(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    COMPLEX = "Complex"

class Category(str, Enum):
    COMPUTE = "Compute"
    STORAGE = "Storage"
    NETWORK = "Network"
    DATABASE = "Database"

# User models
class UserBase(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserCreate(UserBase):
    pass

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    subscription_plan: Optional[SubscriptionPlan] = None
    token: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

# Cost analysis models
class CostAnalysisRequest(BaseModel):
    monthly_bill: float = Field(..., gt=0, description="Monthly AWS bill in USD")
    services: List[str] = Field(..., description="List of AWS services used")
    region: str = Field(default="us-east-1", description="Primary AWS region")
    workload_type: WorkloadType = Field(default=WorkloadType.WEB, description="Type of workload")

class CostRecommendation(BaseModel):
    title: str
    description: str
    potential_savings: float
    priority: Priority
    implementation_effort: ImplementationEffort
    category: Category

class CostAnalysisResponse(BaseModel):
    current_bill: float
    potential_savings: float
    optimized_bill: float
    wasted_spend: float
    recommendations: List[CostRecommendation]
    service_breakdown: Dict[str, float]
    confidence_score: float
    analysis_date: str
    region: str
    workload_type: str

# Subscription models
class SubscriptionPlanInfo(BaseModel):
    id: str
    name: str
    price: float
    currency: str
    interval: str
    features: List[str]

class PaymentIntent(BaseModel):
    client_secret: str
    payment_intent_id: str

class SubscriptionUpdate(BaseModel):
    plan_id: SubscriptionPlan

# File upload models
class FileUploadResponse(BaseModel):
    message: str
    analysis: CostAnalysisResponse

# Admin models
class AdminStats(BaseModel):
    total_users: int
    active_subscriptions: int
    total_revenue: float
    analyses_performed: int
    average_savings: float

# Error models
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# Webhook models
class StripeWebhookEvent(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]
    created: int

# Database models (for internal use)
class User(BaseModel):
    id: int
    email: str
    name: str
    hashed_password: str
    subscription_plan: Optional[SubscriptionPlan] = None
    subscription_status: str = "inactive"
    stripe_customer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_analysis: Optional[datetime] = None
    role: str = "user"

class CostAnalysis(BaseModel):
    id: int
    user_id: int
    analysis_data: Dict[str, Any]
    created_at: datetime
    file_name: Optional[str] = None
    file_type: Optional[str] = None

# API Response models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

# Health check model
class HealthCheck(BaseModel):
    status: str
    timestamp: str
    version: str
    database_status: str = "unknown"
    stripe_status: str = "unknown"
