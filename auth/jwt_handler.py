#!/usr/bin/env python3
"""
JWT Authentication Handler
Secure token management for AWS Cost SaaS
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
from passlib.context import CryptContext
import secrets

class JWTHandler:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_token(self, user_id: int, email: str, token_type: str = "access") -> str:
        """Create JWT token"""
        try:
            if token_type == "access":
                expire_delta = timedelta(minutes=self.access_token_expire_minutes)
            else:  # refresh token
                expire_delta = timedelta(days=self.refresh_token_expire_days)
            
            expire = datetime.utcnow() + expire_delta
            
            payload = {
                "user_id": user_id,
                "email": email,
                "token_type": token_type,
                "exp": expire,
                "iat": datetime.utcnow()
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
        except Exception as e:
            raise Exception(f"Token creation failed: {str(e)}")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("token_type") != "access":
                raise jwt.InvalidTokenError("Invalid token type")
            
            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
                raise jwt.ExpiredSignatureError("Token has expired")
            
            return {
                "user_id": payload["user_id"],
                "email": payload["email"],
                "token_type": payload["token_type"]
            }
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
        except Exception as e:
            raise Exception(f"Token verification failed: {str(e)}")
    
    def refresh_token(self, refresh_token: str) -> str:
        """Create new access token from refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("token_type") != "refresh":
                raise jwt.InvalidTokenError("Invalid refresh token")
            
            # Create new access token
            new_token = self.create_token(
                payload["user_id"], 
                payload["email"], 
                "access"
            )
            
            return new_token
        except jwt.ExpiredSignatureError:
            raise Exception("Refresh token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid refresh token")
        except Exception as e:
            raise Exception(f"Token refresh failed: {str(e)}")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        try:
            return self.pwd_context.hash(password)
        except Exception as e:
            raise Exception(f"Password hashing failed: {str(e)}")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            raise Exception(f"Password verification failed: {str(e)}")
    
    def create_token_pair(self, user_id: int, email: str) -> Dict[str, str]:
        """Create both access and refresh tokens"""
        try:
            access_token = self.create_token(user_id, email, "access")
            refresh_token = self.create_token(user_id, email, "refresh")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
        except Exception as e:
            raise Exception(f"Token pair creation failed: {str(e)}")
