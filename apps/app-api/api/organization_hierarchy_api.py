"""
Organization Hierarchy API endpoints
Provides CRUD operations for parent-child organization relationships
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime

from services.supabase_client import get_supabase_client
from middleware.permissions import (
    require_system_admin,
    require_admin_access,
    PermissionChecker,
    UserRole
)

logger = logging.getLogger(__name__)

# Create router for organization hierarchy endpoints
router = APIRouter(prefix="/api/v1/orgs", tags=["Organization Hierarchy"])

# Pydantic models
class Organization(BaseModel):
    """Organization model"""
    id: str
    name: str
    parent_organization_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    feature_count: Optional[int] = None
    enabled_features: Optional[int] = None
    
    class Config:
        extra = "allow"  # Allow dynamically added fields

class OrganizationTreeNode(BaseModel):
    """Organization tree node model"""
    id: str
    name: str
    parent_organization_id: Optional[str] = None
    children: List['OrganizationTreeNode'] = []
    level: int = 0
    path: List[str] = []
    feature_count: Optional[int] = None
    enabled_features: Optional[int] = None

class CreateChildOrganizationRequest(BaseModel):
    """Request model for creating child organization"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None

class UpdateParentRequest(BaseModel):
    """Request model for updating parent organization"""
    parent_organization_id: Optional[str] = None

class OrganizationResponse(BaseModel):
    """Response model for organization operations"""
    success: bool
    data: Optional[Organization] = None
    error: Optional[str] = None

class OrganizationListResponse(BaseModel):
    """Response model for organization lists"""
    success: bool
    data: Optional[List[Organization]] = None
    error: Optional[str] = None
    total: Optional[int] = None

class OrganizationTreeResponse(BaseModel):
    """Response model for organization tree"""
    success: bool
    data: Optional[OrganizationTreeNode] = None
    error: Optional[str] = None

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

@router.get("/{org_id}/children", response_model=OrganizationListResponse)
async def get_child_organizations(
    org_id: str,
    include_feature_stats: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Get child organizations for a parent organization
    
    - **org_id**: Parent organization ID
    - **include_feature_stats**: Include RAG feature statistics
    - **limit**: Maximum number of children to return
    - **offset**: Number of children to skip
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_access_organization_hierarchy(org_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view organization hierarchy"
            )
        
        # Get child organizations
        query = supabase.from_('organizations').select('*').eq('parent_organization_id', org_id)
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        if result.data is None:
            return OrganizationListResponse(
                success=True,
                data=[],
                total=0
            )
        
        # Convert to response models
        organizations = [Organization(**org) for org in result.data]
        
        # Add feature statistics if requested
        if include_feature_stats:
            for org in organizations:
                try:
                    # Get feature count for this organization
                    feature_result = supabase.from_('organization_rag_toggles').select('count', count='exact').eq('organization_id', org.id).execute()
                    org.feature_count = feature_result.count if feature_result.count else 0
                    
                    # Get enabled feature count
                    enabled_result = supabase.from_('organization_rag_toggles').select('count', count='exact').eq('organization_id', org.id).eq('enabled', True).execute()
                    org.enabled_features = enabled_result.count if enabled_result.count else 0
                except Exception as e:
                    logger.warning(f"Error getting feature stats for org {org.id}: {e}")
                    org.feature_count = 0
                    org.enabled_features = 0
        
        # Get total count for pagination
        count_query = supabase.from_('organizations').select('count', count='exact').eq('parent_organization_id', org_id)
        count_result = count_query.execute()
        total = count_result.count if count_result.count else len(organizations)
        
        return OrganizationListResponse(
            success=True,
            data=organizations,
            total=total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting child organizations for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching child organizations"
        )

@router.get("/{org_id}/parent", response_model=OrganizationResponse)
async def get_parent_organization(
    org_id: str,
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Get parent organization for a child organization
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_access_organization_hierarchy(org_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view organization hierarchy"
            )
        
        # Get organization's parent
        org_result = supabase.from_('organizations').select('parent_organization_id').eq('id', org_id).execute()
        
        if not org_result.data or not org_result.data[0].get('parent_organization_id'):
            raise HTTPException(
                status_code=404,
                detail=f"Organization {org_id} has no parent organization"
            )
        
        parent_id = org_result.data[0]['parent_organization_id']
        
        # Get parent organization details
        parent_result = supabase.from_('organizations').select('*').eq('id', parent_id).execute()
        
        if not parent_result.data:
            raise HTTPException(
                status_code=404,
                detail=f"Parent organization {parent_id} not found"
            )
        
        parent = Organization(**parent_result.data[0])
        
        return OrganizationResponse(
            success=True,
            data=parent
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parent organization for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching parent organization"
        )

@router.get("/{org_id}/hierarchy", response_model=OrganizationTreeResponse)
async def get_organization_hierarchy(
    org_id: str,
    include_feature_stats: bool = Query(False),
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Get full organization hierarchy tree
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_access_organization_hierarchy(org_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view organization hierarchy"
            )
        
        # Use the database view for hierarchy
        result = supabase.from_('organization_hierarchy').select('*').eq('root_id', org_id).order('path').execute()
        
        if not result.data:
            # If no hierarchy found, return the organization itself
            org_result = supabase.from_('organizations').select('*').eq('id', org_id).execute()
            if not org_result.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Organization {org_id} not found"
                )
            
            org_data = org_result.data[0]
            root_node = OrganizationTreeNode(
                id=org_data['id'],
                name=org_data['name'],
                parent_organization_id=org_data.get('parent_organization_id'),
                children=[],
                level=0,
                path=[org_data['id']]
            )
            
            return OrganizationTreeResponse(
                success=True,
                data=root_node
            )
        
        # Build tree structure
        nodes_by_id = {}
        root_node = None
        
        for row in result.data:
            node = OrganizationTreeNode(
                id=row['id'],
                name=row['name'],
                parent_organization_id=row.get('parent_organization_id'),
                children=[],
                level=row['level'],
                path=row['path']
            )
            
            nodes_by_id[row['id']] = node
            
            if row['level'] == 0:
                root_node = node
        
        # Build parent-child relationships
        for row in result.data:
            node = nodes_by_id[row['id']]
            if row.get('parent_organization_id') and row['parent_organization_id'] in nodes_by_id:
                parent_node = nodes_by_id[row['parent_organization_id']]
                parent_node.children.append(node)
        
        # Add feature statistics if requested
        if include_feature_stats and root_node:
            for node in nodes_by_id.values():
                try:
                    # Get feature count for this organization
                    feature_result = supabase.from_('organization_rag_toggles').select('count', count='exact').eq('organization_id', node.id).execute()
                    node.feature_count = feature_result.count if feature_result.count else 0
                    
                    # Get enabled feature count
                    enabled_result = supabase.from_('organization_rag_toggles').select('count', count='exact').eq('organization_id', node.id).eq('enabled', True).execute()
                    node.enabled_features = enabled_result.count if enabled_result.count else 0
                except Exception as e:
                    logger.warning(f"Error getting feature stats for org {node.id}: {e}")
                    node.feature_count = 0
                    node.enabled_features = 0
        
        return OrganizationTreeResponse(
            success=True,
            data=root_node
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization hierarchy for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching organization hierarchy"
        )

@router.post("/{org_id}/children", response_model=OrganizationResponse)
@require_system_admin
async def create_child_organization(
    org_id: str,
    request: CreateChildOrganizationRequest,
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Create a child organization (System Admin only)
    """
    try:
        # Verify parent organization exists
        parent_result = supabase.from_('organizations').select('id').eq('id', org_id).execute()
        
        if not parent_result.data:
            raise HTTPException(
                status_code=404,
                detail=f"Parent organization {org_id} not found"
            )
        
        # Create child organization
        child_data = {
            'name': request.name,
            'parent_organization_id': org_id,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('organizations').insert(child_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create child organization"
            )
        
        child = Organization(**result.data[0])
        
        logger.info(f"Created child organization '{request.name}' under parent {org_id} by user {current_user['id']}")
        
        return OrganizationResponse(
            success=True,
            data=child
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating child organization: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while creating child organization"
        )

@router.patch("/{org_id}/parent", response_model=OrganizationResponse)
@require_system_admin
async def update_parent_organization(
    org_id: str,
    request: UpdateParentRequest,
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Change parent organization (System Admin only)
    """
    try:
        # Verify organization exists
        org_result = supabase.from_('organizations').select('*').eq('id', org_id).execute()
        
        if not org_result.data:
            raise HTTPException(
                status_code=404,
                detail=f"Organization {org_id} not found"
            )
        
        # If setting a new parent, verify it exists
        if request.parent_organization_id:
            parent_result = supabase.from_('organizations').select('id').eq('id', request.parent_organization_id).execute()
            
            if not parent_result.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Parent organization {request.parent_organization_id} not found"
                )
            
            # Check for circular dependency
            if request.parent_organization_id == org_id:
                raise HTTPException(
                    status_code=400,
                    detail="Organization cannot be its own parent"
                )
        
        # Update parent organization
        update_data = {
            'parent_organization_id': request.parent_organization_id,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('organizations').update(update_data).eq('id', org_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to update parent organization"
            )
        
        updated_org = Organization(**result.data[0])
        
        logger.info(f"Updated parent organization for {org_id} to {request.parent_organization_id} by user {current_user['id']}")
        
        return OrganizationResponse(
            success=True,
            data=updated_org
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating parent organization: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating parent organization"
        )

@router.get("/{org_id}/inheritance-chain")
async def get_inheritance_chain(
    org_id: str,
    supabase=Depends(get_supabase),
    current_user=Depends(get_current_user)
):
    """
    Get the inheritance chain for an organization (parent -> grandparent -> etc.)
    """
    try:
        # Check permissions
        checker = PermissionChecker(current_user)
        if not checker.can_access_organization_hierarchy(org_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view inheritance chain"
            )
        
        # Walk up the hierarchy
        chain = []
        current_org_id = org_id
        
        while current_org_id:
            org_result = supabase.from_('organizations').select('id, name, parent_organization_id').eq('id', current_org_id).execute()
            
            if not org_result.data:
                break
            
            org_data = org_result.data[0]
            chain.append({
                'id': org_data['id'],
                'name': org_data['name'],
                'parent_organization_id': org_data.get('parent_organization_id')
            })
            
            current_org_id = org_data.get('parent_organization_id')
        
        return {
            "success": True,
            "data": {
                "inheritance_chain": chain,
                "depth": len(chain) - 1  # Exclude the organization itself
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inheritance chain for org {org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching inheritance chain"
        )
