#!/usr/bin/env python3
"""
Sales Angel Buddy - Main FastAPI Application v1.0.0
Enterprise-grade AI-powered sales co-pilot platform with multi-tenant knowledge management
Complete Application Release
"""

import logging
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://xxdahmkfioqzgqvyabek.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Defer Supabase client creation
supabase: Client = None

def get_supabase_client():
    """Lazy initialization of Supabase client"""
    global supabase
    if supabase is None and SUPABASE_SERVICE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            # Continue without Supabase - app will work in degraded mode
    return supabase

# Create FastAPI application
app = FastAPI(
    title="Sales Angel Buddy API",
    description="Enterprise-grade AI-powered sales co-pilot platform with multi-tenant knowledge management",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None,
)

# Configure CORS properly - allow env override
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3005").split(",")]

# Add CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ✅ Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # ✅ Specific methods
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],  # ✅ Specific headers
)

# Authentication dependency
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token with Supabase"""
    supabase_client = get_supabase_client()
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )
    
    try:
        # Verify the token with Supabase
        response = supabase_client.auth.get_user(credentials.credentials)
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return response.user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Organization validation dependency
async def verify_organization_access(user, org_id: str):
    """Verify user has access to the organization"""
    supabase_client = get_supabase_client()
    if not supabase_client:
        return True  # Skip validation if Supabase not configured
    
    try:
        # Check if user belongs to the organization
        response = supabase_client.table("profiles").select("organization_id").eq("user_id", user.id).single().execute()
        
        if not response.data or response.data.get("organization_id") != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
    except Exception as e:
        logger.error(f"Organization access verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )

# Protected API endpoints with authentication
@app.get("/api/v1/rag-features/catalog")
async def get_rag_features_catalog(
    is_active: bool = True,
    user = Depends(verify_token)
):
    """Get RAG features catalog - requires authentication"""
    logger.info(f"RAG catalog requested by user: {user.email}")
    return {
        "success": True,
        "data": [
            {
                "id": "feature-1",
                "rag_feature": "sales_intelligence",
                "name": "Sales Intelligence",
                "description": "AI-powered sales insights and recommendations",
                "category": "sales",
                "is_active": True
            },
            {
                "id": "feature-2",
                "rag_feature": "customer_insights", 
                "name": "Customer Insights",
                "description": "Deep customer behavior analysis",
                "category": "sales",
                "is_active": True
            },
            {
                "id": "feature-3",
                "rag_feature": "call_analysis",
                "name": "Call Analysis",
                "description": "Real-time call analysis and coaching",
                "category": "sales",
                "is_active": True
            },
            {
                "id": "feature-4",
                "rag_feature": "lead_scoring",
                "name": "Lead Scoring",
                "description": "AI-powered lead qualification and scoring",
                "category": "sales",
                "is_active": True
            }
        ]
    }

@app.get("/api/v1/orgs/{org_id}/rag-toggles")
async def get_rag_toggles(
    org_id: str,
    user = Depends(verify_token)
):
    """Get RAG feature toggles for organization - requires authentication and org access"""
    await verify_organization_access(user, org_id)
    logger.info(f"RAG toggles requested for org {org_id} by user: {user.email}")
    
    return {
        "success": True,
        "data": [
            {
                "id": "toggle-1",
                "rag_feature": "sales_intelligence",
                "enabled": True,
                "organization_id": org_id,
                "is_inherited": False
            },
            {
                "id": "toggle-2",
                "rag_feature": "customer_insights",
                "enabled": True,
                "organization_id": org_id,
                "is_inherited": False
            },
            {
                "id": "toggle-3",
                "rag_feature": "call_analysis",
                "enabled": False,
                "organization_id": org_id,
                "is_inherited": False
            },
            {
                "id": "toggle-4",
                "rag_feature": "lead_scoring",
                "enabled": True,
                "organization_id": org_id,
                "is_inherited": False
            }
        ]
    }

@app.get("/api/v1/orgs/{org_id}/rag-toggles/enabled")
async def get_enabled_features(
    org_id: str, 
    category: str = None,
    user = Depends(verify_token)
):
    """Get enabled RAG features for organization - requires authentication and org access"""
    await verify_organization_access(user, org_id)
    logger.info(f"Enabled features requested for org {org_id} by user: {user.email}")
    
    return {
        "features": [
            {
                "id": "feature-1",
                "rag_feature": "sales_intelligence",
                "name": "Sales Intelligence",
                "category": "sales",
                "enabled": True
            },
            {
                "id": "feature-2", 
                "rag_feature": "customer_insights",
                "name": "Customer Insights",
                "category": "sales",
                "enabled": True
            }
        ]
    }

@app.get("/api/v1/rag-features")
async def get_rag_features(user = Depends(verify_token)):
    """Get RAG features catalog - requires authentication"""
    logger.info(f"RAG features requested by user: {user.email}")
    return {
        "features": [
            {
                "id": "feature-1",
                "rag_feature": "sales_intelligence",
                "name": "Sales Intelligence",
                "description": "AI-powered sales insights and recommendations",
                "category": "sales"
            },
            {
                "id": "feature-2",
                "rag_feature": "customer_insights", 
                "name": "Customer Insights",
                "description": "Deep customer behavior analysis",
                "category": "sales"
            }
        ]
    }

# Public endpoints (no authentication required)
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "Sales Angel Buddy API",
            "version": "1.0.0"
        }
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return JSONResponse(
        status_code=200,
        content={
            "message": "Sales Angel Buddy API",
            "description": "Enterprise-grade AI-powered sales co-pilot platform",
            "version": "1.0.0",
            "docs": "/docs" if os.getenv("ENVIRONMENT") == "development" else "Contact administrator",
            "health": "/health"
        }
    )

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    )
