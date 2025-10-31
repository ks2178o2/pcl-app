"""
RAG Feature Catalog API endpoints
Provides CRUD operations for the global RAG feature catalog
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime

from services.supabase_client import get_supabase_client
from middleware.permissions import (
    require_system_admin, 
    require_org_admin,
    PermissionChecker,
    UserRole
)

logger = logging.getLogger(__name__)

# Create router for RAG feature catalog endpoints
router = APIRouter(prefix="/api/v1/rag-features", tags=["RAG Feature Catalog"])

# Pydantic models for request/response
class RAGFeatureMetadata(BaseModel):
    """RAG feature metadata model"""
    id: Optional[str] = None
    rag_feature: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field(..., pattern="^(sales|manager|admin)$")
    icon: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=20)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class RAGFeatureCreateRequest(BaseModel):
    """Request model for creating RAG features"""
    rag_feature: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field(..., pattern="^(sales|manager|admin)$")
    icon: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=20)

class RAGFeatureUpdateRequest(BaseModel):
    """Request model for updating RAG features"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, pattern="^(sales|manager|admin)$")
    icon: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None

class RAGFeatureResponse(BaseModel):
    """Response model for RAG features"""
    success: bool
    data: Optional[RAGFeatureMetadata] = None
    error: Optional[str] = None

class RAGFeatureListResponse(BaseModel):
    """Response model for RAG feature lists"""
    success: bool
    data: Optional[List[RAGFeatureMetadata]] = None
    error: Optional[str] = None
    total: Optional[int] = None

# Dependency to get Supabase client
def get_supabase():
    return get_supabase_client()

# Dependency to get user data (would be implemented based on your auth system)
def get_current_user():
    # This would be implemented based on your authentication system
    # For now, returning a mock user
    return {
        "id": "user-123",
        "role": "system_admin",
        "organization_id": "org-123"
    }

@router.get("/catalog", response_model=RAGFeatureListResponse)
async def get_rag_feature_catalog(
    category: Optional[str] = Query(None, pattern="^(sales|manager|admin)$"),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Get the global RAG feature catalog
    
    - **category**: Filter by category (sales, manager, admin)
    - **is_active**: Filter by active status
    - **limit**: Maximum number of features to return
    - **offset**: Number of features to skip
    """
    try:
        # Check permissions - org admins and system admins can view catalog
        checker = PermissionChecker(current_user)
        if not checker.can_view_rag_features("system"):
            raise HTTPException(
                status_code=403, 
                detail="Insufficient permissions to view RAG feature catalog"
            )
        
        # Build query
        query = supabase.from_('rag_feature_metadata').select('*')
        
        # Apply filters
        if category:
            query = query.eq('category', category)
        if is_active is not None:
            query = query.eq('is_active', is_active)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        result = query.execute()
        
        if result.data is None:
            return RAGFeatureListResponse(
                success=True,
                data=[],
                total=0
            )
        
        # Convert to response models
        features = [RAGFeatureMetadata(**feature) for feature in result.data]
        
        # Get total count for pagination
        count_query = supabase.from_('rag_feature_metadata').select('count', count='exact')
        if category:
            count_query = count_query.eq('category', category)
        if is_active is not None:
            count_query = count_query.eq('is_active', is_active)
        
        count_result = count_query.execute()
        total = count_result.count if count_result.count else len(features)
        
        return RAGFeatureListResponse(
            success=True,
            data=features,
            total=total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RAG feature catalog: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching RAG feature catalog"
        )

@router.get("/catalog/{feature_name}", response_model=RAGFeatureResponse)
async def get_rag_feature(
    feature_name: str,
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Get a specific RAG feature by name
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_view_rag_features("system"):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view RAG feature"
            )
        
        # Query for specific feature
        result = supabase.from_('rag_feature_metadata').select('*').eq('rag_feature', feature_name).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404,
                detail=f"RAG feature '{feature_name}' not found"
            )
        
        feature = RAGFeatureMetadata(**result.data[0])
        
        return RAGFeatureResponse(
            success=True,
            data=feature
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RAG feature {feature_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching RAG feature"
        )

@router.post("/catalog", response_model=RAGFeatureResponse)
@require_system_admin
async def create_rag_feature(
    request: RAGFeatureCreateRequest,
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Create a new RAG feature (System Admin only)
    """
    try:
        # Check if feature already exists
        existing = supabase.from_('rag_feature_metadata').select('rag_feature').eq('rag_feature', request.rag_feature).execute()
        
        if existing.data:
            raise HTTPException(
                status_code=409,
                detail=f"RAG feature '{request.rag_feature}' already exists"
            )
        
        # Create new feature
        feature_data = {
            'rag_feature': request.rag_feature,
            'name': request.name,
            'description': request.description,
            'category': request.category,
            'icon': request.icon,
            'color': request.color,
            'is_active': True,
            'created_by': current_user['id'],
            'updated_by': current_user['id']
        }
        
        result = supabase.from_('rag_feature_metadata').insert(feature_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create RAG feature"
            )
        
        feature = RAGFeatureMetadata(**result.data[0])
        
        logger.info(f"Created RAG feature '{request.rag_feature}' by user {current_user['id']}")
        
        return RAGFeatureResponse(
            success=True,
            data=feature
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating RAG feature: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while creating RAG feature"
        )

@router.patch("/catalog/{feature_name}", response_model=RAGFeatureResponse)
@require_system_admin
async def update_rag_feature(
    feature_name: str,
    request: RAGFeatureUpdateRequest,
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Update an existing RAG feature (System Admin only)
    """
    try:
        # Check if feature exists
        existing = supabase.from_('rag_feature_metadata').select('*').eq('rag_feature', feature_name).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=404,
                detail=f"RAG feature '{feature_name}' not found"
            )
        
        # Prepare update data (only include non-None values)
        update_data = {}
        if request.name is not None:
            update_data['name'] = request.name
        if request.description is not None:
            update_data['description'] = request.description
        if request.category is not None:
            update_data['category'] = request.category
        if request.icon is not None:
            update_data['icon'] = request.icon
        if request.color is not None:
            update_data['color'] = request.color
        if request.is_active is not None:
            update_data['is_active'] = request.is_active
        
        update_data['updated_by'] = current_user['id']
        
        # Update feature
        result = supabase.from_('rag_feature_metadata').update(update_data).eq('rag_feature', feature_name).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to update RAG feature"
            )
        
        feature = RAGFeatureMetadata(**result.data[0])
        
        logger.info(f"Updated RAG feature '{feature_name}' by user {current_user['id']}")
        
        return RAGFeatureResponse(
            success=True,
            data=feature
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating RAG feature {feature_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating RAG feature"
        )

@router.delete("/catalog/{feature_name}")
@require_system_admin
async def delete_rag_feature(
    feature_name: str,
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Delete a RAG feature (System Admin only)
    Note: This will soft delete by setting is_active=False
    """
    try:
        # Check if feature exists
        existing = supabase.from_('rag_feature_metadata').select('rag_feature').eq('rag_feature', feature_name).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=404,
                detail=f"RAG feature '{feature_name}' not found"
            )
        
        # Soft delete by setting is_active=False
        result = supabase.from_('rag_feature_metadata').update({
            'is_active': False,
            'updated_by': current_user['id']
        }).eq('rag_feature', feature_name).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete RAG feature"
            )
        
        logger.info(f"Deleted RAG feature '{feature_name}' by user {current_user['id']}")
        
        return {"success": True, "message": f"RAG feature '{feature_name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting RAG feature {feature_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while deleting RAG feature"
        )

@router.get("/catalog/categories")
async def get_rag_feature_categories(
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Get available RAG feature categories with counts
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_view_rag_features("system"):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view RAG feature categories"
            )
        
        # Get category counts
        result = supabase.from_('rag_feature_metadata').select('category, count').eq('is_active', True).execute()
        
        categories = {
            'sales': {'label': 'Sales-Focused', 'color': 'blue', 'icon': 'users', 'count': 0},
            'manager': {'label': 'Manager-Focused', 'color': 'purple', 'icon': 'bar-chart', 'count': 0},
            'admin': {'label': 'Admin-Focused', 'color': 'red', 'icon': 'shield', 'count': 0}
        }
        
        # Update counts from database
        if result.data:
            for item in result.data:
                category = item.get('category')
                if category in categories:
                    categories[category]['count'] = item.get('count', 0)
        
        return {
            "success": True,
            "data": categories
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RAG feature categories: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching categories"
        )
