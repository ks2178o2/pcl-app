"""
Organization RAG Toggle API endpoints
Provides CRUD operations for organization-level RAG feature toggles
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.supabase_client import get_supabase_client
from ..services.tenant_isolation_service import TenantIsolationService
from ..middleware.permissions import (
    require_org_admin,
    require_admin_access,
    PermissionChecker,
    UserRole
)

logger = logging.getLogger(__name__)

# Create router for organization toggle endpoints
router = APIRouter(prefix="/api/v1/orgs", tags=["Organization RAG Toggles"])

# Pydantic models
class RAGToggle(BaseModel):
    """RAG toggle model"""
    id: Optional[str] = None
    organization_id: str
    rag_feature: str
    enabled: bool
    category: Optional[str] = None
    is_inherited: bool = False
    inherited_from: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RAGToggleUpdateRequest(BaseModel):
    """Request model for updating RAG toggles"""
    enabled: bool

class BulkToggleUpdateRequest(BaseModel):
    """Request model for bulk toggle updates"""
    updates: Dict[str, bool] = Field(..., description="Dictionary of rag_feature -> enabled")

class RAGToggleResponse(BaseModel):
    """Response model for RAG toggle operations"""
    success: bool
    data: Optional[RAGToggle] = None
    error: Optional[str] = None

class RAGToggleListResponse(BaseModel):
    """Response model for RAG toggle lists"""
    success: bool
    data: Optional[List[RAGToggle]] = None
    error: Optional[str] = None
    total: Optional[int] = None

class EnabledFeaturesResponse(BaseModel):
    """Response model for enabled features only"""
    success: bool
    data: Optional[List[str]] = None
    error: Optional[str] = None

# Dependency to get TenantIsolationService
def get_tenant_isolation_service():
    return TenantIsolationService()

# Dependency to get Supabase client
def get_supabase():
    return get_supabase_client()

# Dependency to get user data (would be implemented based on your auth system)
def get_current_user():
    # This would be implemented based on your authentication system
    # For now, returning a mock user
    return {
        "id": "user-123",
        "role": "org_admin",
        "organization_id": "org-123"
    }

@router.get("/{org_id}/rag-toggles", response_model=RAGToggleListResponse)
async def get_organization_rag_toggles(
    org_id: str,
    category: Optional[str] = Query(None, regex="^(sales|manager|admin)$"),
    enabled_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant_service=Depends(get_tenant_isolation_service),
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Get RAG feature toggles for an organization
    
    - **org_id**: Organization ID
    - **category**: Filter by category (sales, manager, admin)
    - **enabled_only**: Return only enabled features
    - **limit**: Maximum number of toggles to return
    - **offset**: Number of toggles to skip
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_manage_rag_features(org_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view RAG toggles for this organization"
            )
        
        # Use the existing service method
        result = await tenant_service.get_rag_feature_toggles(org_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get RAG toggles")
            )
        
        toggles = result["toggles"]
        
        # Apply filters
        if category:
            toggles = [t for t in toggles if t.get("category") == category]
        
        if enabled_only:
            toggles = [t for t in toggles if t.get("enabled", False)]
        
        # Apply pagination
        total = len(toggles)
        toggles = toggles[offset:offset + limit]
        
        # Convert to response models
        toggle_models = [RAGToggle(**toggle) for toggle in toggles]
        
        return RAGToggleListResponse(
            success=True,
            data=toggle_models,
            total=total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RAG toggles for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching RAG toggles"
        )

@router.get("/{org_id}/rag-toggles/{feature_name}", response_model=RAGToggleResponse)
async def get_organization_rag_toggle(
    org_id: str,
    feature_name: str,
    tenant_service=Depends(get_tenant_isolation_service),
    current_user=Depends(get_current_user)
):
    """
    Get a specific RAG feature toggle for an organization
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_manage_rag_features(org_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view RAG toggle for this organization"
            )
        
        # Get all toggles and find the specific one
        result = await tenant_service.get_rag_feature_toggles(org_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get RAG toggles")
            )
        
        toggles = result["toggles"]
        toggle = next((t for t in toggles if t.get("rag_feature") == feature_name), None)
        
        if not toggle:
            raise HTTPException(
                status_code=404,
                detail=f"RAG feature toggle '{feature_name}' not found for organization {org_id}"
            )
        
        return RAGToggleResponse(
            success=True,
            data=RAGToggle(**toggle)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RAG toggle {feature_name} for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching RAG toggle"
        )

@router.patch("/{org_id}/rag-toggles/{feature_name}", response_model=RAGToggleResponse)
@require_admin_access
async def update_organization_rag_toggle(
    org_id: str,
    feature_name: str,
    request: RAGToggleUpdateRequest,
    tenant_service=Depends(get_tenant_isolation_service),
    current_user=Depends(get_current_user)
):
    """
    Update a RAG feature toggle for an organization (Admin only)
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_manage_rag_features(org_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to update RAG toggle for this organization"
            )
        
        # Use the existing service method
        result = await tenant_service.update_rag_feature_toggle(
            organization_id=org_id,
            rag_feature=feature_name,
            enabled=request.enabled
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to update RAG toggle")
            )
        
        toggle = RAGToggle(**result["toggle"])
        
        logger.info(f"Updated RAG toggle {feature_name} for org {org_id} to {request.enabled} by user {current_user['id']}")
        
        return RAGToggleResponse(
            success=True,
            data=toggle
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating RAG toggle {feature_name} for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating RAG toggle"
        )

@router.post("/{org_id}/rag-toggles/bulk", response_model=RAGToggleListResponse)
@require_admin_access
async def bulk_update_organization_rag_toggles(
    org_id: str,
    request: BulkToggleUpdateRequest,
    tenant_service=Depends(get_tenant_isolation_service),
    current_user=Depends(get_current_user)
):
    """
    Bulk update RAG feature toggles for an organization (Admin only)
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_manage_rag_features(org_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to bulk update RAG toggles for this organization"
            )
        
        # Use the existing service method
        result = await tenant_service.bulk_update_rag_toggles(
            organization_id=org_id,
            toggle_updates=request.updates
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to bulk update RAG toggles")
            )
        
        # Convert updated toggles to response models
        updated_toggles = [RAGToggle(**toggle) for toggle in result["updated_toggles"]]
        
        logger.info(f"Bulk updated {len(request.updates)} RAG toggles for org {org_id} by user {current_user['id']}")
        
        return RAGToggleListResponse(
            success=True,
            data=updated_toggles,
            total=len(updated_toggles)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk updating RAG toggles for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while bulk updating RAG toggles"
        )

@router.get("/{org_id}/rag-toggles/enabled", response_model=EnabledFeaturesResponse)
async def get_enabled_rag_features(
    org_id: str,
    category: Optional[str] = Query(None, regex="^(sales|manager|admin)$"),
    tenant_service=Depends(get_tenant_isolation_service),
    current_user=Depends(get_current_user)
):
    """
    Get only enabled RAG features for an organization
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_view_rag_features(org_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view enabled RAG features for this organization"
            )
        
        # Get all toggles
        result = await tenant_service.get_rag_feature_toggles(org_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get RAG toggles")
            )
        
        # Filter for enabled features
        enabled_features = []
        for toggle in result["toggles"]:
            if toggle.get("enabled", False):
                if not category or toggle.get("category") == category:
                    enabled_features.append(toggle["rag_feature"])
        
        return EnabledFeaturesResponse(
            success=True,
            data=enabled_features
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting enabled RAG features for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching enabled RAG features"
        )

@router.get("/{org_id}/rag-toggles/inherited", response_model=RAGToggleListResponse)
async def get_inherited_rag_features(
    org_id: str,
    tenant_service=Depends(get_tenant_isolation_service),
    current_user=Depends(get_current_user)
):
    """
    Get RAG features inherited from parent organization
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_view_rag_features(org_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view inherited RAG features for this organization"
            )
        
        # Get all toggles
        result = await tenant_service.get_rag_feature_toggles(org_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get RAG toggles")
            )
        
        # Filter for inherited features
        inherited_toggles = []
        for toggle in result["toggles"]:
            if toggle.get("is_inherited", False):
                inherited_toggles.append(RAGToggle(**toggle))
        
        return RAGToggleListResponse(
            success=True,
            data=inherited_toggles,
            total=len(inherited_toggles)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inherited RAG features for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching inherited RAG features"
        )

@router.get("/{org_id}/rag-toggles/summary")
async def get_rag_toggle_summary(
    org_id: str,
    tenant_service=Depends(get_tenant_isolation_service),
    current_user=Depends(get_current_user)
):
    """
    Get summary statistics for RAG feature toggles
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_view_rag_features(org_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view RAG toggle summary for this organization"
            )
        
        # Get all toggles
        result = await tenant_service.get_rag_feature_toggles(org_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get RAG toggles")
            )
        
        toggles = result["toggles"]
        
        # Calculate summary statistics
        total_features = len(toggles)
        enabled_features = len([t for t in toggles if t.get("enabled", False)])
        inherited_features = len([t for t in toggles if t.get("is_inherited", False)])
        
        # Count by category
        category_counts = {}
        for toggle in toggles:
            category = toggle.get("category", "unknown")
            if category not in category_counts:
                category_counts[category] = {"total": 0, "enabled": 0}
            category_counts[category]["total"] += 1
            if toggle.get("enabled", False):
                category_counts[category]["enabled"] += 1
        
        return {
            "success": True,
            "data": {
                "total_features": total_features,
                "enabled_features": enabled_features,
                "disabled_features": total_features - enabled_features,
                "inherited_features": inherited_features,
                "own_features": total_features - inherited_features,
                "category_breakdown": category_counts,
                "enabled_percentage": round((enabled_features / total_features * 100) if total_features > 0 else 0, 2)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RAG toggle summary for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching RAG toggle summary"
        )
