#!/usr/bin/env python3
"""
Sales Angel Buddy - Main FastAPI Application v1.0.0
Enterprise-grade AI-powered sales co-pilot platform with multi-tenant knowledge management
Complete Application Release
"""

import logging
import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status

# Load environment variables from .env/.env.test if available
try:
    from dotenv import load_dotenv
    env_candidates = []

    # Allow tests to inject a safe dotenv file (e.g. .env.test)
    dotenv_override = os.getenv("DOTENV_PATH")
    if dotenv_override:
        env_candidates.append(Path(dotenv_override).expanduser())

    # Legacy fallback order
    env_candidates.extend(
        [
            Path(__file__).parent / ".env",
            Path(__file__).parent.parent.parent / ".env",
            Path(__file__).parent.parent.parent / ".env.local",
        ]
    )

    for env_path in env_candidates:
        try:
            if env_path.exists():
                load_dotenv(env_path)
                logging.info(f"Loaded environment from {env_path}")
                break
        except (PermissionError, OSError) as exc:
            logging.warning(f"Skipping environment file {env_path}: {exc}")
            continue
except ImportError:
    logging.warning("python-dotenv not installed, .env files will not be loaded automatically")

# Ensure requests uses an accessible certificate bundle in sandboxed environments
try:
    import certifi

    ca_path = certifi.where()
    os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_path)
    os.environ.setdefault("SSL_CERT_FILE", ca_path)
except ImportError:
    logging.debug("certifi not available; proceeding without overriding CA bundle")
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from supabase import create_client, Client

# Import API routers v1.0.4
try:
    from api import invitations_api, auth_api, auth_2fa_api
    V1_0_4_ROUTERS_AVAILABLE = True
except Exception as e:
    logging.debug(f"v1.0.4 routers not available: {e}")
    V1_0_4_ROUTERS_AVAILABLE = False

# Import API routers v1.0.5
try:
    from api import transcribe_api
    V1_0_5_ROUTERS_AVAILABLE = True
except Exception as e:
    logging.warning(f"v1.0.5 routers not available: {e}")
    V1_0_5_ROUTERS_AVAILABLE = False

# Analysis API router
try:
    from api import analysis_api
    ANALYSIS_ROUTER_AVAILABLE = True
except Exception as e:
    logging.warning(f"analysis router not available: {e}")
    ANALYSIS_ROUTER_AVAILABLE = False

# Follow-up API router
try:
    from api import followup_api
    FOLLOWUP_ROUTER_AVAILABLE = True
except Exception as e:
    logging.debug(f"followup router not available: {e}")
    FOLLOWUP_ROUTER_AVAILABLE = False

# Call Center Follow-up API router (separate from general followup)
try:
    from api import call_center_followup_api
    CALL_CENTER_FOLLOWUP_ROUTER_AVAILABLE = True
except Exception as e:
    logging.debug(f"call center followup router not available: {e}")
    CALL_CENTER_FOLLOWUP_ROUTER_AVAILABLE = False

# Call Statistics API router
try:
    from api import call_statistics_api
    CALL_STATISTICS_ROUTER_AVAILABLE = True
except Exception as e:
    logging.debug(f"call statistics router not available: {e}")
    CALL_STATISTICS_ROUTER_AVAILABLE = False

# Twilio API router (separate import to avoid blocking followup)
try:
    from api import twilio_api
    TWILIO_ROUTER_AVAILABLE = True
except Exception as e:
    logging.debug(f"twilio router not available: {e}")
    TWILIO_ROUTER_AVAILABLE = False

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
    version="1.0.4",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None,
)

# Configure CORS properly - allow env override (MUST be before routes)
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3005").split(",")]

# Add CORS middleware with proper configuration (BEFORE routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ✅ Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # ✅ Specific methods
    allow_headers=[
        "Authorization",
        "authorization",
        "Content-Type",
        "content-type",
        "X-Requested-With",
        "x-client-info",
        "apikey",
        "Accept",
        "accept",
        "Origin",
        "origin",
    ],  # ✅ Wider header allowlist for FE auth
)

# Custom exception handler to ensure CORS headers are always included for HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """HTTPException handler to ensure CORS headers are always present"""
    from fastapi.responses import JSONResponse
    
    # Get origin from request
    origin = request.headers.get("origin")
    headers = {}
    if origin and origin in ALLOWED_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    
    # Return error response with CORS headers
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers
    )

# General exception handler to ensure CORS headers are always included
@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """General exception handler to ensure CORS headers are always present"""
    from fastapi.responses import JSONResponse
    
    # Log the exception
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Get origin from request
    origin = request.headers.get("origin")
    headers = {}
    if origin and origin in ALLOWED_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    
    # Return error response with CORS headers
    # Always show detailed errors in development
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    error_detail = str(exc) if is_dev else "Internal server error"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": error_detail, "type": type(exc).__name__},
        headers=headers
    )

# Register v1.0.4 API routers
if V1_0_4_ROUTERS_AVAILABLE:
    try:
        app.include_router(invitations_api.router)
        app.include_router(auth_api.router)
        app.include_router(auth_2fa_api.router)
        logger.info("✅ v1.0.4 authentication routers registered successfully")
    except Exception as e:
        logger.error(f"Failed to register v1.0.4 routers: {e}")

# Register v1.0.5 API routers
if V1_0_5_ROUTERS_AVAILABLE:
    try:
        app.include_router(transcribe_api.router)
        logger.info("✅ v1.0.5 transcribe router registered successfully")
    except Exception as e:
        logger.error(f"Failed to register v1.0.5 router: {e}")

# Register analysis router
if ANALYSIS_ROUTER_AVAILABLE:
    try:
        app.include_router(analysis_api.router)
        logger.info("✅ analysis router registered successfully")
    except Exception as e:
        logger.error(f"Failed to register analysis router: {e}")

# Register follow-up router
if FOLLOWUP_ROUTER_AVAILABLE:
    try:
        app.include_router(followup_api.router)
        logger.info("✅ followup router registered successfully")
    except Exception as e:
        logger.error(f"Failed to register followup router: {e}")

# Register call center follow-up router
if CALL_CENTER_FOLLOWUP_ROUTER_AVAILABLE:
    try:
        app.include_router(call_center_followup_api.router)
        logger.info("✅ call center followup router registered successfully")
    except Exception as e:
        logger.error(f"Failed to register call center followup router: {e}")

# Register Twilio router
if TWILIO_ROUTER_AVAILABLE:
    try:
        app.include_router(twilio_api.router)
        logger.info("✅ twilio router registered successfully")
    except Exception as e:
        logger.error(f"Failed to register twilio router: {e}")

# Register bulk import router
try:
    from api import bulk_import_api
    app.include_router(bulk_import_api.router)
    logger.info("✅ bulk import router registered successfully")
except ImportError as e:
    logger.warning(f"bulk import router not available: {e}")
except Exception as e:
    logger.error(f"Failed to register bulk import router: {e}")

# Register call statistics router
if CALL_STATISTICS_ROUTER_AVAILABLE:
    try:
        app.include_router(call_statistics_api.router)
        logger.info("✅ call statistics router registered successfully")
    except Exception as e:
        logger.error(f"Failed to register call statistics router: {e}")

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
